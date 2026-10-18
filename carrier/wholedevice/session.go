package wholedevice

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"errors"
	"io"
	"net"
	"sync"
	"sync/atomic"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/sessiondiag"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
	"github.com/Joker20380/family_connect/carrier/telemost"
	"github.com/Joker20380/family_connect/carrier/underlay"
)

var ErrClosed = errors.New("restricted session unavailable")

type Stream interface {
	io.ReadWriteCloser
	CloseWrite() error
	Reset() error
}

type DataPlane interface {
	Open(context.Context, string, uint16) (Stream, error)
	QueryDNS(context.Context, []byte) ([]byte, error)
	Close() error
	Wait() error
}

type muxPlane struct{ *tcpforward.Mux }

func (plane muxPlane) Open(ctx context.Context, host string, port uint16) (Stream, error) {
	return plane.OpenTCP(ctx, tcpforward.OpenRequest{Host: host, Port: int(port)})
}

type Counters struct {
	TCP         atomic.Uint64
	DNS         atomic.Uint64
	UDPDenied   atomic.Uint64
	IPv6Denied  atomic.Uint64
	LimitDenied atomic.Uint64
	Active      atomic.Int64
	Peak        atomic.Int64
	TCPActive   atomic.Int64
	TCPPeak     atomic.Int64
}

type Session struct {
	ctx          context.Context
	cancel       context.CancelFunc
	plane        DataPlane
	closeCarrier func()
	mu           sync.Mutex
	closed       bool
	workers      sync.WaitGroup
	closeOnce    sync.Once
	tcpSlots     chan struct{}
	dnsSlots     chan struct{}
	metrics      func() map[string]any
	diagnostic   func() sessiondiag.Report
	terminal     string
	Counters     Counters
}

func Attach(parent context.Context, plane DataPlane, closeCarrier func()) *Session {
	ctx, cancel := context.WithCancel(parent)
	session := &Session{ctx: ctx, cancel: cancel, plane: plane, closeCarrier: closeCarrier,
		tcpSlots: make(chan struct{}, 32), dnsSlots: make(chan struct{}, 16)}
	go func() {
		reason := sessiondiag.Reason(plane.Wait())
		session.mu.Lock()
		session.terminal = reason
		session.mu.Unlock()
		cancel()
	}()
	return session
}

func (session *Session) Failed() bool { return session.ctx.Err() != nil }

func (session *Session) Close() {
	session.closeOnce.Do(func() {
		sessiontrace.From(session.ctx).Add("LOCAL_CLOSE", "STARTED", "NONE")
		session.mu.Lock()
		session.closed = true
		session.cancel()
		session.mu.Unlock()
		session.plane.Close()
		if session.closeCarrier != nil {
			session.closeCarrier()
		}
		session.workers.Wait()
	})
}

func (session *Session) Allow(protocol, host string, port uint16) bool {
	if session.Failed() {
		return false
	}
	ip := net.ParseIP(host)
	if ip == nil || ip.To4() == nil {
		session.Counters.IPv6Denied.Add(1)
		return false
	}
	if protocol == "tcp" {
		return true
	}
	if protocol == "udp" && port == 53 {
		return true
	}
	session.Counters.UDPDenied.Add(1)
	return false
}

func (session *Session) Handle(connection net.Conn, protocol, host string, port uint16) {
	defer connection.Close()
	if !session.Allow(protocol, host, port) {
		return
	}
	slots := session.tcpSlots
	if protocol == "udp" {
		slots = session.dnsSlots
	}
	session.mu.Lock()
	if session.closed || session.Failed() {
		session.mu.Unlock()
		return
	}
	select {
	case slots <- struct{}{}:
	default:
		session.mu.Unlock()
		session.Counters.LimitDenied.Add(1)
		return
	}
	session.workers.Add(1)
	session.mu.Unlock()
	defer session.workers.Done()
	defer func() { <-slots; session.Counters.Active.Add(-1) }()
	active := session.Counters.Active.Add(1)
	for peak := session.Counters.Peak.Load(); active > peak; peak = session.Counters.Peak.Load() {
		if session.Counters.Peak.CompareAndSwap(peak, active) {
			break
		}
	}
	ctx, cancel := context.WithCancel(session.ctx)
	defer cancel()
	stop := context.AfterFunc(ctx, func() { connection.Close() })
	defer stop()
	if protocol == "udp" || port == 53 {
		bounded, finish := context.WithTimeout(ctx, 10*time.Second)
		defer finish()
		closeDNS := context.AfterFunc(bounded, func() { connection.Close() })
		defer closeDNS()
		buffer := make([]byte, 4097)
		for {
			var count int
			var err error
			if protocol == "tcp" {
				var prefix [2]byte
				if _, err = io.ReadFull(connection, prefix[:]); err != nil {
					return
				}
				count = int(binary.BigEndian.Uint16(prefix[:]))
				if count < 12 || count > 4096 {
					return
				}
				_, err = io.ReadFull(connection, buffer[:count])
			} else {
				count, err = connection.Read(buffer)
			}
			if err != nil || count < 12 || count > 4096 {
				return
			}
			session.Counters.DNS.Add(1)
			answer, err := session.plane.QueryDNS(bounded, buffer[:count])
			if err != nil {
				return
			}
			if protocol == "tcp" {
				framed := make([]byte, 2+len(answer))
				binary.BigEndian.PutUint16(framed, uint16(len(answer)))
				copy(framed[2:], answer)
				answer = framed
			}
			if _, err = io.Copy(connection, bytes.NewReader(answer)); err != nil {
				return
			}
		}
	}
	stream, err := session.plane.Open(ctx, host, port)
	if err != nil {
		return
	}
	defer stream.Close()
	closeStream := context.AfterFunc(ctx, func() { stream.Reset() })
	defer closeStream()
	session.Counters.TCP.Add(1)
	tcpActive := session.Counters.TCPActive.Add(1)
	defer session.Counters.TCPActive.Add(-1)
	for peak := session.Counters.TCPPeak.Load(); tcpActive > peak; peak = session.Counters.TCPPeak.Load() {
		if session.Counters.TCPPeak.CompareAndSwap(peak, tcpActive) {
			break
		}
	}
	done := make(chan error, 1)
	go func() {
		_, err := io.CopyBuffer(stream, connection, make([]byte, 16<<10))
		if err == nil {
			err = stream.CloseWrite()
		}
		if err != nil {
			cancel()
		}
		done <- err
	}()
	_, err = io.CopyBuffer(connection, stream, make([]byte, 16<<10))
	if err == nil {
		if half, ok := connection.(interface{ CloseWrite() error }); ok {
			half.CloseWrite()
		} else {
			cancel()
		}
	} else {
		cancel()
	}
	select {
	case <-done:
	case <-ctx.Done():
		connection.Close()
		stream.Reset()
		<-done
	}
}

func profile(path, cachePath string) ([]byte, *bootstrap.Cache, error) {
	raw, err := roombroker.LoadCredentials(path)
	if err != nil {
		return nil, nil, err
	}
	var credentials familysession.Credentials
	if json.Unmarshal(raw, &credentials) != nil {
		clear(raw)
		return nil, nil, ErrClosed
	}
	return raw, &bootstrap.Cache{Path: cachePath, Family: credentials.Family, Gateway: credentials.Gateway}, nil
}

func Refresh(ctx context.Context, path, cachePath, control string, network *underlay.Network) error {
	if network == nil {
		return ErrClosed
	}
	raw, cache, err := profile(path, cachePath)
	if err != nil {
		return err
	}
	defer clear(raw)
	client, err := roombroker.NewClient(control, raw, network)
	if err != nil {
		return err
	}
	directory, err := client.BootstrapDirectory(ctx)
	if err != nil {
		return err
	}
	return cache.Store(directory, time.Now())
}

func Open(ctx context.Context, path, cachePath string, network *underlay.Network, event func(string)) (*Session, error) {
	if network == nil || event == nil {
		return nil, ErrClosed
	}
	raw, _, err := profile(path, cachePath)
	if err != nil {
		return nil, err
	}
	defer clear(raw)
	client, err := roombroker.NewClient("https://127.0.0.1:1", raw, network)
	if err != nil {
		return nil, err
	}
	probe, cancel := context.WithTimeout(ctx, 2*time.Second)
	_, err = client.BootstrapDirectory(probe)
	cancel()
	if err != roombroker.Code("control_unavailable") {
		return nil, ErrClosed
	}
	event("bootstrap_normal_control_unavailable")
	return OpenCached(ctx, path, cachePath, network, event)
}

func OpenCached(ctx context.Context, path, cachePath string, network *underlay.Network, event func(string)) (*Session, error) {
	if network == nil || event == nil {
		return nil, ErrClosed
	}
	raw, cache, err := profile(path, cachePath)
	if err != nil {
		return nil, err
	}
	defer clear(raw)
	directory, err := cache.Load(time.Now())
	if err != nil {
		return nil, err
	}
	return openDirectory(ctx, raw, directory, network, event)
}

func OpenProvisioned(ctx context.Context, raw, directoryRaw []byte, network *underlay.Network, event func(string)) (*Session, error) {
	if network == nil || event == nil {
		return nil, ErrClosed
	}
	var credentials familysession.Credentials
	if json.Unmarshal(raw, &credentials) != nil {
		return nil, ErrClosed
	}
	directory, err := bootstrap.ParseDirectory(directoryRaw, credentials.Family, credentials.Gateway, time.Now())
	if err != nil {
		return nil, err
	}
	return openDirectory(ctx, raw, directory, network, event)
}

func openDirectory(ctx context.Context, raw []byte, directory bootstrap.Directory, network *underlay.Network, event func(string)) (*Session, error) {
	event("bootstrap_cache_loaded")
	descriptor, err := bootstrap.Recover(ctx, directory, raw, event, network)
	if err != nil {
		return nil, err
	}
	event("bootstrap_closed_before_dedicated")
	trace := sessiontrace.From(ctx)
	if trace == nil {
		trace = sessiontrace.New(descriptor.SetupID, nil)
		sessiontrace.Publish(ctx, trace)
		trace.Add("DESCRIPTOR", "ISSUED", "NONE")
	}
	ctx = sessiontrace.With(ctx, trace)
	sessiontrace.StartDiagnosticControl(ctx, trace, "client")
	trace.Add("GATEWAY_JOIN", "STARTED", "NONE")
	carrier, err := telemost.New(ctx, telemost.Config{RoomURL: descriptor.JoinURL, DisplayName: "Family restricted device", Mode: telemost.ModeVP8, Underlay: network})
	if err != nil {
		return nil, err
	}
	success := false
	defer func() {
		if !success {
			carrier.Close()
		}
	}()
	connect, finish := context.WithTimeout(ctx, 45*time.Second)
	defer finish()
	if err = carrier.Connect(connect); err != nil {
		trace.Add("GATEWAY_JOIN", "FAILED", "RECOVERY_JOIN_FAILED")
		return nil, err
	}
	trace.Add("GATEWAY_JOIN", "ESTABLISHED", "NONE")
	stopHandshake := context.AfterFunc(connect, func() { carrier.Close() })
	defer stopHandshake()
	trace.Add("FAMILY_TLS", "STARTED", "NONE")
	secured, err := familysession.Open(ctx, carrier, raw, false)
	if err != nil {
		trace.Add("FAMILY_TLS", "FAILED", "FAMILY_TLS_ERROR")
		return nil, err
	}
	trace.Add("FAMILY_TLS", "ESTABLISHED", "NONE")
	defer func() {
		if !success {
			secured.Close()
		}
	}()
	if err = roombroker.BindClient(connect, secured, descriptor, raw); err != nil {
		trace.Add("GATEWAY_SESSION", "FAILED", "GATEWAY_CLOSE")
		return nil, err
	}
	mux, err := tcpforward.NewMux(ctx, secured, false, tcpforward.MuxConfig{MaxStreams: roombroker.DedicatedMaxStreams})
	if err != nil {
		trace.Add("GATEWAY_SESSION", "FAILED", "UNKNOWN_INTERNAL")
		return nil, err
	}
	event("dedicated_data_ready")
	trace.Add("GATEWAY_SESSION", "ESTABLISHED", "NONE")
	success = true
	stopSample := sessiondiag.Sample(ctx, trace, func() (uint64, uint64) { stats := carrier.Stats(); return stats.BytesSent, stats.BytesReceived },
		func() *sessiontrace.Delivery {
			return sessiondiag.Delivery(secured.ReliabilityStats(), carrier.Stats())
		})
	session := Attach(ctx, muxPlane{mux}, func() {
		trace.Add("LOCAL_CLOSE", "STARTED", "NONE")
		stopSample()
		secured.Close()
		carrier.Close()
		trace.Add("CLEANUP", "COMPLETED", "NONE")
	})
	session.diagnostic = func() sessiondiag.Report {
		failure, failedAt := mux.Terminal()
		report := sessiondiag.Capture(descriptor.SetupID, failure, failedAt, secured.ReliabilityStats(), carrier.Stats(), mux.Stats())
		snapshot := trace.Snapshot()
		report.Trace = &snapshot
		return report
	}
	session.metrics = func() map[string]any {
		reliable, media := secured.ReliabilityStats(), carrier.Stats()
		return map[string]any{"reliable_buffered": reliable.BufferedBytes, "reliable_peak": reliable.MaxBufferedBytes,
			"reliable_send_depth": reliable.SendDepth, "carrier_send_queue": media.SendQueueDepth,
			"carrier_receive_queue": media.ReceiveQueueDepth}
	}
	return session, nil
}

func (session *Session) Snapshot() map[string]any {
	stats := map[string]any{"tcp": session.Counters.TCP.Load(), "dns": session.Counters.DNS.Load(),
		"udp_denied": session.Counters.UDPDenied.Load(), "ipv6_denied": session.Counters.IPv6Denied.Load(),
		"limit_denied": session.Counters.LimitDenied.Load(), "active": session.Counters.Active.Load(), "peak": session.Counters.Peak.Load(), "failed": session.Failed()}
	stats["tcp_active"], stats["tcp_peak"] = session.Counters.TCPActive.Load(), session.Counters.TCPPeak.Load()
	session.mu.Lock()
	stats["terminal_reason"] = session.terminal
	session.mu.Unlock()
	if session.diagnostic != nil {
		stats["diagnostic"] = session.diagnostic()
	}
	if session.metrics != nil {
		stats["resources"] = session.metrics()
	}
	if plane, ok := session.plane.(muxPlane); ok {
		stats["mux"] = plane.Stats()
	}
	return stats
}
