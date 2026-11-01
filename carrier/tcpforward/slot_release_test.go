package tcpforward

import (
	"bytes"
	"context"
	"io"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

type closeAckGate struct {
	familysession.PacketEndpoint
	once      sync.Once
	delivered chan struct{}
	release   chan struct{}
}

func TestMuxRemovedStreamWaitsForForwardWorker(test *testing.T) {
	port := muxFixture(test, muxEcho)
	ctx, client, server := muxPair(test, port, 1, 1)
	entered, cancelled, release := make(chan struct{}), make(chan struct{}), make(chan struct{})
	var calls atomic.Int32
	var releaseOnce sync.Once
	test.Cleanup(func() { releaseOnce.Do(func() { close(release) }) })
	server.mu.Lock()
	normalDial := server.dial
	server.dial = func(dialContext context.Context, network, address string) (socket, error) {
		if calls.Add(1) == 1 {
			close(entered)
			<-dialContext.Done()
			close(cancelled)
			select {
			case <-release:
			case <-ctx.Done():
			}
			return nil, dialContext.Err()
		}
		return normalDial(dialContext, network, address)
	}
	server.mu.Unlock()
	firstContext, cancelFirst := context.WithCancel(ctx)
	defer cancelFirst()
	firstDone := make(chan error, 1)
	go func() {
		_, err := client.OpenTCP(firstContext, OpenRequest{Host: "127.0.0.1", Port: port})
		firstDone <- err
	}()
	select {
	case <-entered:
	case <-ctx.Done():
		test.Fatal("forward worker did not acquire its slot")
	}
	cancelFirst()
	if err := <-firstDone; err != ErrReset {
		test.Fatal("cancelled OPEN", err)
	}
	<-cancelled
	awaitMuxState(test, client, func(stats MuxStats) bool { return stats.ActiveStreams == 0 })
	awaitMuxState(test, server, func(stats MuxStats) bool { return stats.ActiveStreams == 0 })
	if len(server.jobs) != 1 {
		test.Fatal("worker gate did not retain the closing job slot")
	}
	nextDone := make(chan error, 1)
	go func() {
		stream, err := client.OpenTCP(ctx, OpenRequest{Host: "127.0.0.1", Port: port})
		if err == nil {
			err = exactMux(stream, []byte("after worker release"))
		}
		nextDone <- err
	}()
	stats := awaitMuxState(test, server, func(stats MuxStats) bool { return stats.AdmissionWaiting == 1 || stats.OpenErrors != 0 })
	releaseOnce.Do(func() { close(release) })
	if err := <-nextDone; err != nil {
		test.Fatal(err)
	}
	if stats.OpenErrors != 0 {
		test.Fatal("closing worker caused stream_limit")
	}
	client.Close()
	server.Close()
	for _, mux := range []*Mux{client, server} {
		stats := mux.Stats()
		if stats.ActiveStreams != 0 || stats.ActiveSockets != 0 || stats.RetainedBytes != 0 || stats.AdmissionWaiting != 0 || len(mux.jobs) != 0 {
			test.Fatalf("worker release retained state: %+v", stats)
		}
	}
}

func (point *closeAckGate) SendContext(ctx context.Context, payload []byte) error {
	if err := point.PacketEndpoint.SendContext(ctx, payload); err != nil {
		return err
	}
	frame, err := decodeMux(payload)
	if err != nil {
		return err
	}
	if frame.kind == closeFrame {
		point.once.Do(func() {
			close(point.delivered)
			select {
			case <-point.release:
			case <-ctx.Done():
			}
		})
	}
	return ctx.Err()
}

type batchCloseAckGate struct{ *closeAckGate }

func (point *batchCloseAckGate) SendBatchContext(ctx context.Context, payloads [][]byte) error {
	for _, payload := range payloads {
		if err := point.SendContext(ctx, payload); err != nil {
			return err
		}
	}
	return nil
}

func awaitMuxState(test *testing.T, mux *Mux, accept func(MuxStats) bool) MuxStats {
	test.Helper()
	for {
		mux.mu.Lock()
		mux.measureLocked()
		stats, changed := mux.stats, mux.changed
		mux.mu.Unlock()
		if accept(stats) {
			return stats
		}
		select {
		case <-changed:
		case <-mux.ctx.Done():
			test.Fatalf("mux state deadline: active=%d retained=%d errors=%d waiting=%d", stats.ActiveStreams, stats.RetainedBytes, stats.OpenErrors, stats.AdmissionWaiting)
		}
	}
}

func TestMuxCloseAcknowledgementSlotRelease(test *testing.T) {
	for _, sides := range []string{"client", "server", "both"} {
		for _, scenario := range []string{"sequential", "bulk", "shutdown"} {
			test.Run(sides+"/"+scenario, func(test *testing.T) {
				port := muxFixture(test, muxEcho)
				ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
				left, right := pipePair()
				gate := &closeAckGate{PacketEndpoint: right, delivered: make(chan struct{}), release: make(chan struct{})}
				var clientPoint, serverPoint familysession.PacketEndpoint = left, gate
				if sides != "server" {
					clientPoint = &batchingPipe{packetPipe: left}
				}
				if sides != "client" {
					serverPoint = &batchCloseAckGate{gate}
				}
				limit := 1
				if scenario == "bulk" {
					limit = 2
				}
				client := newMux(ctx, clientPoint, false, MuxConfig{MaxStreams: limit, WaitForSlot: true})
				server := newMux(ctx, serverPoint, true, MuxConfig{MaxStreams: limit, Policy: Policy{TestOnlyLoopbackPort: port}})
				var tasks sync.WaitGroup
				test.Cleanup(func() {
					cancel()
					joined := make(chan struct{})
					go func() { client.Close(); server.Close(); tasks.Wait(); close(joined) }()
					select {
					case <-joined:
					case <-time.After(3 * time.Second):
						test.Fatal("mux or fixture goroutine did not join")
					}
					for _, mux := range []*Mux{client, server} {
						stats := mux.Stats()
						if stats.ActiveStreams != 0 || stats.ActiveSockets != 0 || stats.RetainedBytes != 0 || stats.AdmissionWaiting != 0 || len(mux.jobs) != 0 {
							test.Fatalf("shutdown retained state: %+v", stats)
						}
					}
				})
				var bulk *MuxStream
				if scenario == "bulk" {
					bulk = muxOpen(test, ctx, client, port)
				}
				stream := muxOpen(test, ctx, client, port)
				if err := exactMux(stream, bytes.Repeat([]byte("finished"), 16<<10)); err != nil {
					test.Fatal(err)
				}
				<-gate.delivered
				if client.Stats().ActiveStreams != limit-1 || server.Stats().ActiveStreams != limit {
					test.Fatal("close ACK did not precede server send-return bookkeeping")
				}
				type openResult struct {
					stream *MuxStream
					err    error
				}
				opened := make(chan openResult, 1)
				tasks.Add(1)
				go func() {
					defer tasks.Done()
					next, err := client.OpenTCP(ctx, OpenRequest{Host: "127.0.0.1", Port: port})
					opened <- openResult{next, err}
				}()
				stats := awaitMuxState(test, server, func(stats MuxStats) bool { return stats.OpenErrors > 0 || stats.AdmissionWaiting == 1 })
				if stats.OpenErrors != 0 {
					test.Fatalf("valid OPEN after successful Close rejected: active=%d retained=%d rejected=%d", stats.ActiveStreams, stats.RetainedBytes, stats.AdmissionRejected)
				}
				if scenario == "shutdown" {
					cancel()
					if result := <-opened; result.err == nil {
						test.Fatal("pending admission survived mux shutdown")
					}
					return
				}
				close(gate.release)
				result := <-opened
				if result.err != nil {
					test.Fatal(result.err)
				}
				if bulk != nil {
					bulkDone := make(chan error, 1)
					tasks.Add(1)
					go func() { defer tasks.Done(); bulkDone <- exactMux(bulk, bytes.Repeat([]byte("bulk"), 64<<10)) }()
					if err := exactMux(result.stream, []byte("peer during bulk")); err != nil {
						test.Fatal(err)
					}
					if err := <-bulkDone; err != nil {
						test.Fatal(err)
					}
				} else if err := exactMux(result.stream, []byte("reused slot")); err != nil {
					test.Fatal(err)
				}
				for _, mux := range []*Mux{client, server} {
					stats := awaitMuxState(test, mux, func(stats MuxStats) bool {
						return stats.ActiveStreams == 0 && stats.RetainedBytes == 0 && stats.ActiveSockets == 0
					})
					if stats.MaxActiveStreams > limit || stats.OpenErrors != 0 || stats.ProtocolErrors != 0 {
						test.Fatalf("mux limits or ordering changed: %+v", stats)
					}
				}
				if stream.Stats().State != "closed" {
					test.Fatal(io.ErrUnexpectedEOF)
				}
			})
		}
	}
}
