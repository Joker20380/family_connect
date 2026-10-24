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
	Lifecycle    bool
	MaxStreams   int
	WaitForSlot  bool
	Policy       Policy
	DNSUpstream  string
	LeaseRenewal func(context.Context, *MuxStream)
}

const LeaseRenewalHost = "lease-renewal.family-connect.invalid"

type ProtocolErrorCounts struct {
	OpenReplay    uint64 `json:"open_replay"`
	UnknownStream uint64 `json:"unknown_stream"`
	OpenState     uint64 `json:"open_state"`
	DataState     uint64 `json:"data_state"`
	CreditState   uint64 `json:"credit_state"`
	FINState      uint64 `json:"fin_state"`
	CloseState    uint64 `json:"close_state"`
	FrameKind     uint64 `json:"frame_kind"`
	DNSReplay     uint64 `json:"dns_replay"`
	DNSRole       uint64 `json:"dns_role"`
	DNSUnmatched  uint64 `json:"dns_unmatched"`
}

func (mux *Mux) protocolErrorLocked(counter *uint64) {
	mux.stats.ProtocolErrors++
	*counter++
}

type MuxStats struct {
	Lifecycle            *MuxLifecycle
	ProtocolErrorReasons ProtocolErrorCounts
	Window               int
	Profile              string
	Destination          DestinationStats
	ActiveSockets        int
	ActiveStreams        int
	MaxActiveStreams     int
	Opened               uint64
	OpenOK               uint64
	OpenErrors           uint64
	AdmissionWaits       uint64
	AdmissionRejected    uint64
	AdmissionTimeouts    uint64
	AdmissionCancelled   uint64
	AdmissionWaiting     int
	LeaseRejected        uint64
	Resets               uint64
	ProtocolErrors       uint64
	SentBytes            uint64
	ReceivedBytes        uint64
	FlowStalls           uint64
	RetainedBytes        int
	RetainedHighWater    int
	SendHighWater        int
	ReceiveHighWater     int
	QueueHighWater       int
	SchedulerFrames      uint64
	SchedulerWaitMaxMS   float64
	DNSRequests          uint64
	DNSResponses         uint64
	DNSErrors            uint64
	DNSTimeouts          uint64
}

type Mux struct {
	life          muxLifeBuffer
	window        int
	mu            sync.Mutex
	ctx           context.Context
	cancel        context.CancelFunc
	endpoint      familysession.PacketEndpoint
	batchSend     func(context.Context, [][]byte) error
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
	leaseJobs     chan struct{}
	admission     []*admissionWaiter
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
	leaseOpen     bool
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
	window, err := session.MuxWindow()
	if err != nil {
		return nil, err
	}
	return newMuxWindow(ctx, session, server, config, window), nil
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
	return newMuxWindow(parent, endpoint, server, config, MuxWindow)
}

func newMuxWindow(parent context.Context, endpoint familysession.PacketEndpoint, server bool, config MuxConfig, window int) *Mux {
	if config.MaxStreams == 0 {
		config.MaxStreams = 16
	}
	ctx, cancel := context.WithCancel(parent)
	mux := &Mux{ctx: ctx, cancel: cancel, endpoint: endpoint, server: server, config: config, streams: make(map[uint32]*MuxStream), nextID: 1, changed: make(chan struct{}), done: make(chan struct{}), jobs: make(chan struct{}, config.MaxStreams), lookup: net.DefaultResolver, dns: make(map[uint32]*dnsCall), dnsNext: 1, dnsJobs: make(chan struct{}, MuxMaxDNS)}
	mux.leaseJobs = make(chan struct{}, 1)
	mux.window = window
	mux.stats.Window = window
	mux.stats.Profile = "LEGACY64"
	if window == 131072 {
		mux.stats.Profile = "CREDIT128"
	}
	if batch, ok := endpoint.(interface {
		SendBatchContext(context.Context, [][]byte) error
	}); ok {
		mux.batchSend = batch.SendBatchContext
	}
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
		frame, err := decodeMuxWindow(encoded, mux.window)
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
		mux.lifeLocked("failure", 0, 0, lifeReason(err))
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

func (mux *Mux) Close() error {
	mux.mu.Lock()
	mux.lifeLocked("close", 0, 0, "caller")
	mux.mu.Unlock()
	mux.cancel()
	mux.endpoint.Close()
	<-mux.done
	return nil
}
func (mux *Mux) Wait() error { <-mux.done; mux.mu.Lock(); defer mux.mu.Unlock(); return mux.err }
func (mux *Mux) Terminal() (error, time.Time) {
	mux.mu.Lock()
	defer mux.mu.Unlock()
	return mux.err, mux.failureAt
}
func (mux *Mux) Stats() MuxStats {
	mux.mu.Lock()
	defer mux.mu.Unlock()
	mux.measureLocked()
	stats := mux.stats
	stats.Lifecycle = mux.lifeSnapshotLocked()
	return stats
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
	mux.stats.AdmissionWaiting = len(mux.admission)
	mux.stats.MaxActiveStreams = max(mux.stats.MaxActiveStreams, len(mux.streams))
	mux.stats.RetainedBytes = retained
	mux.stats.RetainedHighWater = max(mux.stats.RetainedHighWater, retained)
	mux.stats.QueueHighWater = max(mux.stats.QueueHighWater, queue)
}

func (mux *Mux) controlLocked(frame muxFrame) {
	mux.lifeLocked("enqueue", frame.id, frame.kind, "control")
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
			mux.lifeLocked("enqueue", id, muxWindowUpdate, "control")
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
	var pending *muxFrame
	for mux.ctx.Err() == nil {
		mux.mu.Lock()
		var frame muxFrame
		ok := pending != nil
		if ok {
			frame, pending = *pending, nil
		} else {
			frame, ok = mux.nextLocked()
		}
		var frames []muxFrame
		if ok {
			frames = append(frames, frame)
			budget := familysession.BatchMessageHeaderSize + headerSize + len(frame.payload)
			for mux.batchSend != nil && len(frames) < familysession.MaxBatchMessages && budget < familysession.MaxBatchPlaintext {
				next, ready := mux.nextLocked()
				if !ready {
					break
				}
				cost := familysession.BatchMessageHeaderSize + headerSize + len(next.payload)
				if budget+cost > familysession.MaxBatchPlaintext {
					pending = &next
					break
				}
				frames = append(frames, next)
				budget += cost
			}
		}
		for _, current := range frames {
			mux.lifeLocked("send_start", current.id, current.kind, "batch")
		}
		changed := mux.changed
		mux.mu.Unlock()
		if !ok {
			select {
			case <-changed:
			case <-mux.ctx.Done():
			}
			continue
		}
		var err error
		if len(frames) == 1 {
			err = mux.endpoint.SendContext(mux.ctx, frame.encode())
		} else {
			payloads := make([][]byte, len(frames))
			for index, current := range frames {
				payloads[index] = current.encode()
			}
			err = mux.batchSend(mux.ctx, payloads)
		}
		if err != nil {
			mux.fail(err)
			return
		}
		mux.mu.Lock()
		mux.stats.SchedulerFrames += uint64(len(frames))
		for _, current := range frames {
			mux.lifeLocked("send_done", current.id, current.kind, "local")
			terminal := current.kind == resetFrame || current.kind == closeFrame || current.kind == openError
			if stream := mux.streams[current.id]; terminal && stream != nil && stream.terminal != nil && len(stream.send) == 0 {
				mux.removeLocked(current.id)
			}
		}
		mux.measureLocked()
		mux.signalLocked()
		mux.mu.Unlock()
	}
}

func (mux *Mux) removeLocked(id uint32) {
	mux.lifeLocked("remove", id, 0, "terminal")
	delete(mux.streams, id)
	for index, current := range mux.order {
		if current == id {
			mux.order = append(mux.order[:index], mux.order[index+1:]...)
			break
		}
	}
}

func (mux *Mux) dispatchLocked(frame muxFrame) {
	mux.lifeLocked("receive", frame.id, frame.kind, "wire")
	if frame.id == 0 {
		mux.dnsFrameLocked(frame)
		return
	}
	stream := mux.streams[frame.id]
	if frame.kind == openFrame && mux.server && stream == nil {
		if frame.id <= mux.lastID {
			mux.protocolErrorLocked(&mux.stats.ProtocolErrorReasons.OpenReplay)
			return
		}
		mux.lastID = frame.id
		var request OpenRequest
		if decodeJSON(frame.payload, &request) != nil || validate(request) != nil {
			mux.controlLocked(muxFrame{openError, frame.id, []byte(`{"code":"malformed_request"}`)})
			return
		}
		lease := leaseRequest(request) && mux.config.LeaseRenewal != nil
		jobs := mux.jobSlots(lease)
		if !mux.slotAvailableLocked(lease) || len(jobs) >= cap(jobs) {
			mux.stats.OpenErrors++
			mux.rejectAdmissionLocked(lease)
			mux.controlLocked(muxFrame{openError, frame.id, []byte(`{"code":"stream_limit"}`)})
			return
		}
		stream = mux.makeStreamLocked(frame.id)
		stream.lease = lease
		jobs <- struct{}{}
		mux.workers.Add(1)
		go mux.forward(stream, request)
		return
	}
	if stream == nil {
		mux.lifeLocked("unknown", frame.id, frame.kind, "missing")
		mux.lifeFrameLocked(frame, false)
		mux.protocolErrorLocked(&mux.stats.ProtocolErrorReasons.UnknownStream)
		return
	}
	if stream.terminal != nil {
		mux.lifeFrameLocked(frame, false)
		return
	}
	invalid := false
	reason := &mux.stats.ProtocolErrorReasons.FrameKind
	switch frame.kind {
	case openOK:
		reason = &mux.stats.ProtocolErrorReasons.OpenState
		if mux.server || stream.opened {
			invalid = true
		} else {
			stream.opened = true
			mux.lifeLocked("opened", stream.id, openOK, "peer")
			mux.stats.OpenOK++
		}
	case openError:
		reason = &mux.stats.ProtocolErrorReasons.OpenState
		var failure OpenError
		if mux.server || stream.opened || decodeJSON(frame.payload, &failure) != nil || (!validError(failure.Code) && failure.Code != "stream_limit") {
			invalid = true
		} else {
			mux.stats.OpenErrors++
			stream.finishLocked(&failure)
			mux.removeLocked(frame.id)
		}
	case dataFrame:
		reason = &mux.stats.ProtocolErrorReasons.DataState
		if !stream.opened || stream.remoteFIN || len(frame.payload) > stream.receiveCredit {
			invalid = true
		} else {
			stream.receiveCredit -= len(frame.payload)
			for _, value := range frame.payload {
				stream.receive[(stream.head+stream.used)%len(stream.receive)] = value
				stream.used++
			}
			stream.received += uint64(len(frame.payload))
			stream.receiveHighWater = max(stream.receiveHighWater, stream.used)
			mux.stats.ReceivedBytes += uint64(len(frame.payload))
		}
	case muxWindowUpdate:
		reason = &mux.stats.ProtocolErrorReasons.CreditState
		credit := int(binary.BigEndian.Uint32(frame.payload))
		if !stream.opened || credit > len(stream.receive)-stream.sendCredit {
			invalid = true
		} else {
			stream.sendCredit += credit
		}
	case finFrame:
		reason = &mux.stats.ProtocolErrorReasons.FINState
		if !stream.opened || stream.remoteFIN {
			invalid = true
		} else {
			stream.remoteFIN = true
			stream.remoteFINCount++
		}
	case closeFrame:
		reason = &mux.stats.ProtocolErrorReasons.CloseState
		if !stream.localFIN || !stream.remoteFIN {
			invalid = true
		} else if !mux.server && stream.closing {
			stream.finishLocked(io.EOF)
			mux.removeLocked(frame.id)
		} else {
			stream.closeRequested = true
		}
	case resetFrame:
		stream.life.PeerTerminal = true
		mux.stats.Resets++
		stream.finishLocked(ErrReset)
		mux.removeLocked(frame.id)
	default:
		invalid = true
	}
	if invalid {
		mux.lifeFrameLocked(frame, true)
		mux.protocolErrorLocked(reason)
		stream.resetLocked(ErrProtocol)
	}
}

func (mux *Mux) forward(stream *MuxStream, request OpenRequest) {
	defer mux.workers.Done()
	defer func() { <-mux.jobSlots(stream.lease) }()
	if canonicalHost(request.Host) == LeaseRenewalHost && request.Port == 1 && mux.config.LeaseRenewal != nil {
		mux.mu.Lock()
		for mux.leaseOpen && stream.terminal == nil && stream.ctx.Err() == nil {
			changed := mux.changed
			mux.mu.Unlock()
			select {
			case <-changed:
			case <-stream.ctx.Done():
			}
			mux.mu.Lock()
		}
		if stream.terminal != nil || stream.ctx.Err() != nil {
			stream.resetLocked(ErrProtocol)
			mux.mu.Unlock()
			return
		}
		mux.leaseOpen = true
		stream.opened = true
		mux.lifeLocked("opened", stream.id, openOK, "lease")
		stream.send = append(stream.send, muxFrame{openOK, stream.id, nil})
		mux.stats.OpenOK++
		mux.signalLocked()
		mux.mu.Unlock()
		defer func() { mux.mu.Lock(); mux.leaseOpen = false; mux.signalLocked(); mux.mu.Unlock(); stream.Reset() }()
		mux.config.LeaseRenewal(stream.ctx, stream)
		return
	}
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
	mux.lifeLocked("opened", stream.id, openOK, "socket")
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
