package tcpforward

import (
	"context"
	"encoding/binary"
	"encoding/json"
	"errors"
	"io"
	"net"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

type MuxConfig struct {
	MaxStreams  int
	Policy      Policy
	DNSUpstream string
}

type MuxStats struct {
	Destination        DestinationStats
	ActiveSockets      int
	ActiveStreams      int
	MaxActiveStreams   int
	Opened             uint64
	OpenOK             uint64
	OpenErrors         uint64
	Resets             uint64
	ProtocolErrors     uint64
	SentBytes          uint64
	ReceivedBytes      uint64
	FlowStalls         uint64
	RetainedBytes      int
	RetainedHighWater  int
	SendHighWater      int
	ReceiveHighWater   int
	QueueHighWater     int
	SchedulerFrames    uint64
	SchedulerWaitMaxMS float64
	DNSRequests        uint64
	DNSResponses       uint64
	DNSErrors          uint64
	DNSTimeouts        uint64
}

type Mux struct {
	mu            sync.Mutex
	ctx           context.Context
	cancel        context.CancelFunc
	endpoint      familysession.PacketEndpoint
	server        bool
	config        MuxConfig
	streams       map[uint32]*MuxStream
	order         []uint32
	cursor        int
	nextID        uint32
	lastID        uint32
	control       []muxFrame
	priorityBurst int
	changed       chan struct{}
	done          chan struct{}
	workers       sync.WaitGroup
	jobs          chan struct{}
	err           error
	failureAt     time.Time
	stats         MuxStats
	lookup        resolver
	dial          dialer
	dns           map[uint32]*dnsCall
	dnsNext       uint32
	dnsLast       uint32
	dnsJobs       chan struct{}
	exchange      func(context.Context, []byte) ([]byte, error)
}

func NewMux(ctx context.Context, session *familysession.Session, server bool, config MuxConfig) (*Mux, error) {
	if session == nil {
		return nil, familysession.ErrRejected
	}
	if err := validateMuxConfig(config); err != nil {
		return nil, err
	}
	if server {
		var err error
		config.Policy, err = gatewayPolicy(config.Policy)
		if err != nil {
			return nil, err
		}
	}
	if err := session.ClaimTCP(server); err != nil {
		return nil, err
	}
	return newMux(ctx, session, server, config), nil
}

func validateMuxConfig(config MuxConfig) error {
	if config.MaxStreams < 0 || config.MaxStreams > MuxMaxStreams {
		return ErrProtocol
	}
	if config.DNSUpstream != "" {
		host, port, err := net.SplitHostPort(config.DNSUpstream)
		if err != nil || net.ParseIP(host) == nil || port != "53" {
			return ErrProtocol
		}
	}
	return nil
}

func newMux(parent context.Context, endpoint familysession.PacketEndpoint, server bool, config MuxConfig) *Mux {
	if config.MaxStreams == 0 {
		config.MaxStreams = 16
	}
	ctx, cancel := context.WithCancel(parent)
	mux := &Mux{ctx: ctx, cancel: cancel, endpoint: endpoint, server: server, config: config, streams: make(map[uint32]*MuxStream), nextID: 1, changed: make(chan struct{}), done: make(chan struct{}), jobs: make(chan struct{}, config.MaxStreams), lookup: net.DefaultResolver, dns: make(map[uint32]*dnsCall), dnsNext: 1, dnsJobs: make(chan struct{}, MuxMaxDNS)}
	mux.dial = func(ctx context.Context, network, address string) (socket, error) {
		connection, err := (&net.Dialer{KeepAlive: 30 * time.Second}).DialContext(ctx, network, address)
		if err != nil {
			return nil, err
		}
		return connection.(*net.TCPConn), nil
	}
	mux.exchange = mux.exchangeDNS
	go mux.run()
	return mux
}

func (mux *Mux) signalLocked() { close(mux.changed); mux.changed = make(chan struct{}) }

func (mux *Mux) run() {
	stop := context.AfterFunc(mux.ctx, func() { mux.endpoint.Close() })
	defer stop()
	written := make(chan struct{})
	go func() { defer close(written); mux.writeLoop() }()
	for {
		encoded, err := mux.endpoint.Recv(mux.ctx)
		if err != nil {
			mux.fail(err)
			break
		}
		frame, err := decodeMux(encoded)
		if err != nil {
			mux.fail(err)
			break
		}
		mux.mu.Lock()
		mux.dispatchLocked(frame)
		mux.measureLocked()
		mux.signalLocked()
		mux.mu.Unlock()
		if mux.ctx.Err() != nil {
			break
		}
	}
	mux.cancel()
	mux.endpoint.Close()
	<-written
	mux.workers.Wait()
	mux.mu.Lock()
	for _, stream := range mux.streams {
		stream.finishLocked(ErrReset)
	}
	for _, call := range mux.dns {
		call.cancel()
	}
	clear(mux.streams)
	clear(mux.dns)
	mux.order, mux.control = nil, nil
	mux.measureLocked()
	mux.signalLocked()
	mux.mu.Unlock()
	close(mux.done)
}

func (mux *Mux) fail(err error) {
	mux.mu.Lock()
	if mux.err == nil {
		mux.err = err
		mux.failureAt = time.Now()
	}
	mux.cancel()
	for _, stream := range mux.streams {
		stream.finishLocked(ErrReset)
	}
	for _, call := range mux.dns {
		call.cancel()
	}
	mux.signalLocked()
	mux.mu.Unlock()
}

func (mux *Mux) Close() error { mux.cancel(); mux.endpoint.Close(); <-mux.done; return nil }
func (mux *Mux) Wait() error  { <-mux.done; mux.mu.Lock(); defer mux.mu.Unlock(); return mux.err }
func (mux *Mux) Terminal() (error, time.Time) {
	mux.mu.Lock()
	defer mux.mu.Unlock()
	return mux.err, mux.failureAt
}
func (mux *Mux) Stats() MuxStats {
	mux.mu.Lock()
	defer mux.mu.Unlock()
	mux.measureLocked()
	return mux.stats
}

func (mux *Mux) measureLocked() {
	mux.stats.Destination = mux.config.Policy.Metrics.Snapshot()
	retained, queue := 0, len(mux.control)
	for _, frame := range mux.control {
		retained += len(frame.payload)
	}
	for _, stream := range mux.streams {
		retained += len(stream.receive)
		mux.stats.ReceiveHighWater = max(mux.stats.ReceiveHighWater, stream.used)
		for _, frame := range stream.send {
			retained += len(frame.payload)
		}
		queue += len(stream.send)
	}
	for _, call := range mux.dns {
		retained += len(call.query) + len(call.response)
	}
	mux.stats.ActiveStreams = len(mux.streams)
	mux.stats.MaxActiveStreams = max(mux.stats.MaxActiveStreams, len(mux.streams))
	mux.stats.RetainedBytes = retained
	mux.stats.RetainedHighWater = max(mux.stats.RetainedHighWater, retained)
	mux.stats.QueueHighWater = max(mux.stats.QueueHighWater, queue)
}

func (mux *Mux) controlLocked(frame muxFrame) {
	if mux.ctx.Err() != nil {
		return
	}
	if len(mux.control) >= 2*MuxMaxStreams+2*MuxMaxDNS {
		if mux.err == nil {
			mux.err = ErrProtocol
			mux.failureAt = time.Now()
		}
		mux.cancel()
		return
	}
	mux.control = append(mux.control, frame)
	mux.signalLocked()
}

func (mux *Mux) pickLocked(dataOnly bool) (muxFrame, bool) {
	for count := 0; count < len(mux.order); count++ {
		mux.cursor %= len(mux.order)
		id := mux.order[mux.cursor]
		mux.cursor++
		stream := mux.streams[id]
		if stream == nil {
			continue
		}
		if !dataOnly && stream.creditPending > 0 && stream.terminal == nil {
			credit := make([]byte, 4)
			binary.BigEndian.PutUint32(credit, uint32(stream.creditPending))
			stream.creditPending = 0
			return muxFrame{muxWindowUpdate, id, credit}, true
		}
		if len(stream.send) == 0 {
			continue
		}
		frame := stream.send[0]
		if dataOnly != (frame.kind == dataFrame) {
			continue
		}
		stream.send[0] = muxFrame{}
		stream.send = stream.send[1:]
		mux.stats.SchedulerWaitMaxMS = max(mux.stats.SchedulerWaitMaxMS, float64(time.Since(stream.queuedAt))/float64(time.Millisecond))
		return frame, true
	}
	return muxFrame{}, false
}

func (mux *Mux) nextLocked() (muxFrame, bool) {
	if mux.priorityBurst >= 8 {
		if frame, ok := mux.pickLocked(true); ok {
			mux.priorityBurst = 0
			return frame, true
		}
	}
	mux.priorityBurst++
	if len(mux.control) > 0 {
		frame := mux.control[0]
		mux.control[0] = muxFrame{}
		mux.control = mux.control[1:]
		return frame, true
	}
	if frame, ok := mux.pickLocked(false); ok {
		return frame, true
	}
	mux.priorityBurst = 0
	return mux.pickLocked(true)
}

func (mux *Mux) writeLoop() {
	for mux.ctx.Err() == nil {
		mux.mu.Lock()
		frame, ok := mux.nextLocked()
		changed := mux.changed
		mux.mu.Unlock()
		if !ok {
			select {
			case <-changed:
			case <-mux.ctx.Done():
			}
			continue
		}
		if err := mux.endpoint.SendContext(mux.ctx, frame.encode()); err != nil {
			mux.fail(err)
			return
		}
		mux.mu.Lock()
		mux.stats.SchedulerFrames++
		if stream := mux.streams[frame.id]; stream != nil && stream.terminal != nil && len(stream.send) == 0 {
			mux.removeLocked(frame.id)
		}
		mux.measureLocked()
		mux.signalLocked()
		mux.mu.Unlock()
	}
}

func (mux *Mux) removeLocked(id uint32) {
	delete(mux.streams, id)
	for index, current := range mux.order {
		if current == id {
			mux.order = append(mux.order[:index], mux.order[index+1:]...)
			break
		}
	}
}

func (mux *Mux) dispatchLocked(frame muxFrame) {
	if frame.id == 0 {
		mux.dnsFrameLocked(frame)
		return
	}
	stream := mux.streams[frame.id]
	if frame.kind == openFrame && mux.server && stream == nil {
		if frame.id <= mux.lastID {
			mux.stats.ProtocolErrors++
			return
		}
		mux.lastID = frame.id
		var request OpenRequest
		if decodeJSON(frame.payload, &request) != nil || validate(request) != nil {
			mux.controlLocked(muxFrame{openError, frame.id, []byte(`{"code":"malformed_request"}`)})
			return
		}
		if len(mux.streams) >= mux.config.MaxStreams || len(mux.jobs) >= cap(mux.jobs) {
			mux.stats.OpenErrors++
			mux.controlLocked(muxFrame{openError, frame.id, []byte(`{"code":"stream_limit"}`)})
			return
		}
		stream = mux.makeStreamLocked(frame.id)
		mux.jobs <- struct{}{}
		mux.workers.Add(1)
		go mux.forward(stream, request)
		return
	}
	if stream == nil {
		mux.stats.ProtocolErrors++
		return
	}
	if stream.terminal != nil {
		return
	}
	invalid := false
	switch frame.kind {
	case openOK:
		if mux.server || stream.opened {
			invalid = true
		} else {
			stream.opened = true
			mux.stats.OpenOK++
		}
	case openError:
		var failure OpenError
		if mux.server || stream.opened || decodeJSON(frame.payload, &failure) != nil || (!validError(failure.Code) && failure.Code != "stream_limit") {
			invalid = true
		} else {
			mux.stats.OpenErrors++
			stream.finishLocked(&failure)
			mux.removeLocked(frame.id)
		}
	case dataFrame:
		if !stream.opened || stream.remoteFIN || len(frame.payload) > stream.receiveCredit {
			invalid = true
		} else {
			stream.receiveCredit -= len(frame.payload)
			for _, value := range frame.payload {
				stream.receive[(stream.head+stream.used)%MuxWindow] = value
				stream.used++
			}
			stream.received += uint64(len(frame.payload))
			stream.receiveHighWater = max(stream.receiveHighWater, stream.used)
			mux.stats.ReceivedBytes += uint64(len(frame.payload))
		}
	case muxWindowUpdate:
		credit := int(binary.BigEndian.Uint32(frame.payload))
		if !stream.opened || credit > MuxWindow-stream.sendCredit {
			invalid = true
		} else {
			stream.sendCredit += credit
		}
	case finFrame:
		if !stream.opened || stream.remoteFIN {
			invalid = true
		} else {
			stream.remoteFIN = true
			stream.remoteFINCount++
		}
	case closeFrame:
		if !stream.localFIN || !stream.remoteFIN {
			invalid = true
		} else if !mux.server && stream.closing {
			stream.finishLocked(io.EOF)
			mux.removeLocked(frame.id)
		} else {
			stream.closeRequested = true
		}
	case resetFrame:
		mux.stats.Resets++
		stream.finishLocked(ErrReset)
		mux.removeLocked(frame.id)
	default:
		invalid = true
	}
	if invalid {
		mux.stats.ProtocolErrors++
		stream.resetLocked(ErrProtocol)
	}
}

func (mux *Mux) forward(stream *MuxStream, request OpenRequest) {
	defer mux.workers.Done()
	defer func() { <-mux.jobs }()
	connection, err := connect(stream.ctx, request, mux.config.Policy, mux.lookup, mux.dial)
	mux.mu.Lock()
	if stream.terminal != nil {
		mux.mu.Unlock()
		if connection != nil {
			connection.Close()
		}
		return
	}
	if err != nil {
		var failure *OpenError
		if !errors.As(err, &failure) {
			failure = &OpenError{Code: "connect_failed"}
		}
		payload, _ := json.Marshal(failure)
		stream.finishLocked(failure)
		stream.send = []muxFrame{{openError, stream.id, payload}}
		mux.stats.OpenErrors++
		mux.signalLocked()
		mux.mu.Unlock()
		return
	}
	stream.opened = true
	mux.stats.ActiveSockets++
	stream.send = append(stream.send, muxFrame{openOK, stream.id, nil})
	mux.stats.OpenOK++
	mux.signalLocked()
	mux.mu.Unlock()
	defer connection.Close()
	stop := context.AfterFunc(stream.ctx, func() { connection.Close() })
	defer stop()
	reverse := make(chan error, 1)
	go func() {
		buffer := make([]byte, MaxData)
		_, err := io.CopyBuffer(struct{ io.Writer }{stream}, struct{ io.Reader }{connection}, buffer)
		if err == nil {
			err = stream.CloseWrite()
		}
		if err != nil {
			stream.Reset()
		}
		reverse <- err
	}()
	buffer := make([]byte, MaxData)
	_, err = io.CopyBuffer(&muxTargetWriter{target: connection}, struct{ io.Reader }{stream}, buffer)
	if err == nil {
		err = connection.CloseWrite()
	}
	if err != nil {
		stream.Reset()
	}
	<-reverse
	connection.Close()
	mux.mu.Lock()
	mux.stats.ActiveSockets--
	for stream.terminal == nil && !stream.closeRequested && mux.ctx.Err() == nil {
		changed := mux.changed
		mux.mu.Unlock()
		select {
		case <-changed:
		case <-stream.ctx.Done():
		}
		mux.mu.Lock()
	}
	if stream.terminal == nil {
		stream.finishLocked(io.EOF)
		stream.send = []muxFrame{{closeFrame, stream.id, nil}}
		mux.signalLocked()
	}
	mux.mu.Unlock()
}

type muxTargetWriter struct {
	target  io.Writer
	metrics Metrics
}

func (writer *muxTargetWriter) Write(payload []byte) (int, error) {
	before := writer.metrics.Snapshot().ToTarget
	err := writeTarget(writer.target, payload, &writer.metrics)
	return int(writer.metrics.Snapshot().ToTarget - before), err
}
