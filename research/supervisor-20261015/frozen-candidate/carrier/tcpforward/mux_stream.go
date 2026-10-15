package tcpforward

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"sync"
	"time"
)

type MuxStream struct {
	mux              *Mux
	id               uint32
	ctx              context.Context
	cancel           context.CancelFunc
	stop             func() bool
	writeMu          sync.Mutex
	opened           bool
	localFIN         bool
	remoteFIN        bool
	closeRequested   bool
	closing          bool
	terminal         error
	receive          []byte
	head             int
	used             int
	receiveCredit    int
	sendCredit       int
	creditPending    int
	send             []muxFrame
	queuedAt         time.Time
	sent             uint64
	received         uint64
	localFINCount    uint64
	remoteFINCount   uint64
	sendHighWater    int
	receiveHighWater int
}

type MuxStreamStats struct {
	ID               uint32
	State            string
	Sent             uint64
	Received         uint64
	LocalFIN         uint64
	RemoteFIN        uint64
	ReceiveBuffered  int
	SendCredit       int
	SendHighWater    int
	ReceiveHighWater int
}

func (mux *Mux) makeStreamLocked(id uint32) *MuxStream {
	ctx, cancel := context.WithCancel(mux.ctx)
	stream := &MuxStream{mux: mux, id: id, ctx: ctx, cancel: cancel, receive: make([]byte, MuxWindow), receiveCredit: MuxWindow, sendCredit: MuxWindow, queuedAt: time.Now()}
	mux.streams[id] = stream
	mux.order = append(mux.order, id)
	mux.stats.Opened++
	return stream
}

func (mux *Mux) OpenTCP(ctx context.Context, request OpenRequest) (*MuxStream, error) {
	if err := validate(request); err != nil {
		return nil, err
	}
	mux.mu.Lock()
	if mux.server || mux.ctx.Err() != nil || ctx.Err() != nil {
		mux.mu.Unlock()
		return nil, ErrReset
	}
	if len(mux.streams) >= mux.config.MaxStreams {
		mux.mu.Unlock()
		return nil, ErrStreamLimit
	}
	if mux.nextID > muxMaxID {
		mux.mu.Unlock()
		return nil, ErrIDExhausted
	}
	stream := mux.makeStreamLocked(mux.nextID)
	mux.nextID += 2
	payload, _ := json.Marshal(request)
	mux.controlLocked(muxFrame{openFrame, stream.id, payload})
	stream.stop = context.AfterFunc(ctx, func() { stream.Reset() })
	mux.measureLocked()
	mux.signalLocked()
	deadline := time.NewTimer(40 * time.Second)
	defer deadline.Stop()
	for !stream.opened && stream.terminal == nil && mux.ctx.Err() == nil {
		changed := mux.changed
		mux.mu.Unlock()
		select {
		case <-changed:
		case <-ctx.Done():
			stream.Reset()
		case <-mux.ctx.Done():
		case <-deadline.C:
			stream.Reset()
		}
		mux.mu.Lock()
	}
	err := stream.terminal
	if err == nil && mux.ctx.Err() != nil {
		err = ErrReset
	}
	mux.mu.Unlock()
	if err != nil {
		return nil, err
	}
	return stream, nil
}

func (stream *MuxStream) Stats() MuxStreamStats {
	stream.mux.mu.Lock()
	defer stream.mux.mu.Unlock()
	state := "opening"
	switch {
	case stream.terminal == io.EOF:
		state = "closed"
	case stream.terminal == ErrReset:
		state = "reset"
	case stream.terminal != nil:
		state = "failed"
	case stream.localFIN && stream.remoteFIN:
		state = "both-half-closed"
	case stream.localFIN:
		state = "local-half-closed"
	case stream.remoteFIN:
		state = "remote-half-closed"
	case stream.opened:
		state = "open"
	}
	return MuxStreamStats{stream.id, state, stream.sent, stream.received, stream.localFINCount, stream.remoteFINCount, stream.used, stream.sendCredit, stream.sendHighWater, stream.receiveHighWater}
}

func (stream *MuxStream) finishLocked(err error) {
	if stream.terminal != nil {
		return
	}
	stream.terminal = err
	stream.cancel()
	if stream.stop != nil {
		stream.stop()
	}
	stream.receive, stream.send = nil, nil
	stream.used, stream.creditPending = 0, 0
}

func (stream *MuxStream) resetLocked(err error) {
	if stream.terminal != nil {
		return
	}
	stream.finishLocked(err)
	stream.send = []muxFrame{{resetFrame, stream.id, nil}}
	stream.mux.stats.Resets++
	stream.mux.signalLocked()
}

func (stream *MuxStream) Read(buffer []byte) (int, error) {
	if len(buffer) == 0 {
		return 0, nil
	}
	mux := stream.mux
	mux.mu.Lock()
	defer mux.mu.Unlock()
	for {
		if stream.terminal != nil {
			return 0, stream.terminal
		}
		if mux.ctx.Err() != nil {
			return 0, ErrReset
		}
		if stream.used > 0 {
			count := min(len(buffer), stream.used)
			first := min(count, MuxWindow-stream.head)
			copy(buffer, stream.receive[stream.head:stream.head+first])
			copy(buffer[first:count], stream.receive[:count-first])
			stream.head = (stream.head + count) % MuxWindow
			stream.used -= count
			stream.receiveCredit += count
			stream.creditPending += count
			mux.signalLocked()
			return count, nil
		}
		if stream.remoteFIN {
			return 0, io.EOF
		}
		changed := mux.changed
		mux.mu.Unlock()
		select {
		case <-changed:
		case <-mux.ctx.Done():
		}
		mux.mu.Lock()
	}
}

func (stream *MuxStream) Write(payload []byte) (int, error) {
	stream.writeMu.Lock()
	defer stream.writeMu.Unlock()
	mux := stream.mux
	mux.mu.Lock()
	defer mux.mu.Unlock()
	total := 0
	for len(payload) > 0 {
		if stream.terminal != nil {
			return total, stream.terminal
		}
		if stream.localFIN || mux.ctx.Err() != nil {
			return total, io.ErrClosedPipe
		}
		if stream.opened && len(stream.send) == 0 && stream.sendCredit > 0 {
			count := min(len(payload), MaxData, stream.sendCredit)
			stream.sendCredit -= count
			stream.sendHighWater = max(stream.sendHighWater, count)
			stream.send = append(stream.send, muxFrame{dataFrame, stream.id, bytes.Clone(payload[:count])})
			stream.queuedAt = time.Now()
			stream.sent += uint64(count)
			mux.stats.SentBytes += uint64(count)
			mux.stats.SendHighWater = max(mux.stats.SendHighWater, count)
			total += count
			payload = payload[count:]
			mux.measureLocked()
			mux.signalLocked()
			continue
		}
		mux.stats.FlowStalls++
		changed := mux.changed
		mux.mu.Unlock()
		select {
		case <-changed:
		case <-mux.ctx.Done():
		}
		mux.mu.Lock()
	}
	return total, nil
}

func (stream *MuxStream) CloseWrite() error {
	stream.writeMu.Lock()
	defer stream.writeMu.Unlock()
	mux := stream.mux
	mux.mu.Lock()
	defer mux.mu.Unlock()
	if stream.terminal != nil {
		return stream.terminal
	}
	if stream.localFIN {
		return nil
	}
	if !stream.opened {
		return ErrProtocol
	}
	stream.localFIN = true
	stream.localFINCount++
	stream.send = append(stream.send, muxFrame{finFrame, stream.id, nil})
	mux.signalLocked()
	return nil
}

func (stream *MuxStream) Reset() error {
	stream.mux.mu.Lock()
	defer stream.mux.mu.Unlock()
	stream.resetLocked(ErrReset)
	return nil
}

func (stream *MuxStream) Close() error {
	mux := stream.mux
	mux.mu.Lock()
	defer mux.mu.Unlock()
	if stream.terminal != nil {
		return nil
	}
	if stream.localFIN && stream.remoteFIN && stream.used == 0 {
		if !stream.closing {
			stream.closing = true
			stream.send = append(stream.send, muxFrame{closeFrame, stream.id, nil})
		}
		mux.signalLocked()
		timer := time.NewTimer(10 * time.Second)
		defer timer.Stop()
		for stream.terminal == nil && mux.ctx.Err() == nil {
			changed := mux.changed
			mux.mu.Unlock()
			select {
			case <-changed:
			case <-mux.ctx.Done():
			case <-timer.C:
				stream.Reset()
			}
			mux.mu.Lock()
		}
		if stream.terminal != io.EOF {
			return ErrReset
		}
	} else {
		stream.resetLocked(ErrReset)
	}
	return nil
}
