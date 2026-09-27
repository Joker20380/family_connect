package tcpforward

import (
	"context"
	"encoding/json"
	"io"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

type Stream struct {
	endpoint    familysession.PacketEndpoint
	ctx         context.Context
	cancel      context.CancelFunc
	stop        func() bool
	readMu      sync.Mutex
	writeMu     sync.Mutex
	stateMu     sync.Mutex
	readFIN     bool
	writeFIN    bool
	pending     []byte
	pendingSize int
	metrics     *Metrics
	closeOnce   sync.Once
	closeErr    error
}

func OpenTCP(ctx context.Context, session *familysession.Session, request OpenRequest) (*Stream, error) {
	if err := validate(request); err != nil {
		return nil, err
	}
	if session == nil {
		return nil, familysession.ErrRejected
	}
	if err := session.ClaimTCP(false); err != nil {
		return nil, err
	}
	return openTCP(ctx, session, request)
}

func openTCP(ctx context.Context, endpoint familysession.PacketEndpoint, request OpenRequest) (*Stream, error) {
	ctx, cancel := context.WithCancel(ctx)
	stream := &Stream{endpoint: endpoint, ctx: ctx, cancel: cancel, metrics: &Metrics{}}
	stream.stop = context.AfterFunc(ctx, func() { endpoint.Close() })
	openContext, stopOpen := context.WithTimeout(ctx, 40*time.Second)
	defer stopOpen()
	payload, err := json.Marshal(request)
	if err == nil {
		err = endpoint.SendContext(openContext, encode(openFrame, payload))
	}
	stream.metrics.update(func(stats *Stats) { stats.OpenRequests++ })
	started := time.Now()
	if err == nil {
		var kind byte
		kind, payload, err = receive(openContext, endpoint)
		if err == nil {
			switch kind {
			case openOK:
				stream.metrics.update(func(stats *Stats) {
					stats.OpenOK++
					stats.ConnectMS = float64(time.Since(started)) / float64(time.Millisecond)
				})
				return stream, nil
			case openError:
				var failure OpenError
				if decodeJSON(payload, &failure) != nil || !validError(failure.Code) {
					err = ErrProtocol
				} else {
					err = &failure
				}
			default:
				err = ErrProtocol
			}
		}
	}
	stream.stop()
	cancel()
	endpoint.Close()
	return nil, err
}

func validError(code string) bool {
	switch code {
	case "malformed_request", "policy_rejected", "dns_failure", "connection_refused", "timeout", "unreachable", "cancelled", "connect_failed":
		return true
	}
	return false
}

func (stream *Stream) Stats() Stats { return stream.metrics.Snapshot() }

func (stream *Stream) Read(buffer []byte) (int, error) {
	stream.readMu.Lock()
	defer stream.readMu.Unlock()
	if len(buffer) == 0 {
		return 0, nil
	}
	stream.stateMu.Lock()
	eof := stream.readFIN
	stream.stateMu.Unlock()
	if eof {
		return 0, io.EOF
	}
	if len(stream.pending) == 0 {
		kind, payload, err := receive(stream.ctx, stream.endpoint)
		if err != nil {
			stream.cancel()
			return 0, ErrReset
		}
		switch kind {
		case dataFrame:
			stream.pending = payload
			stream.pendingSize = headerSize + len(payload)
			stream.metrics.retain(stream.pendingSize)
			stream.metrics.update(func(stats *Stats) { stats.DataReceived++ })
		case finFrame:
			stream.stateMu.Lock()
			stream.readFIN = true
			stream.stateMu.Unlock()
			stream.metrics.update(func(stats *Stats) { stats.RemoteFIN++; stats.EOFs++ })
			return 0, io.EOF
		case resetFrame:
			stream.metrics.update(func(stats *Stats) { stats.Resets++; stats.CloseReason = "remote_reset" })
			stream.cancel()
			return 0, ErrReset
		default:
			stream.cancel()
			return 0, ErrProtocol
		}
	}
	count := copy(buffer, stream.pending)
	stream.pending = stream.pending[count:]
	if len(stream.pending) == 0 {
		stream.pending = nil
		stream.metrics.retain(-stream.pendingSize)
		stream.pendingSize = 0
	}
	stream.metrics.update(func(stats *Stats) { stats.FromTarget += uint64(count) })
	return count, nil
}

func (stream *Stream) Write(payload []byte) (int, error) {
	stream.writeMu.Lock()
	defer stream.writeMu.Unlock()
	stream.stateMu.Lock()
	eof := stream.writeFIN
	stream.stateMu.Unlock()
	if eof {
		return 0, io.ErrClosedPipe
	}
	total := 0
	for len(payload) > 0 {
		count := min(len(payload), MaxData)
		frame := encode(dataFrame, payload[:count])
		stream.metrics.retain(len(frame))
		err := stream.endpoint.SendContext(stream.ctx, frame)
		stream.metrics.retain(-len(frame))
		if err != nil {
			stream.cancel()
			return total, err
		}
		payload = payload[count:]
		total += count
		stream.metrics.update(func(stats *Stats) { stats.ToTarget += uint64(count); stats.DataSent++ })
	}
	return total, nil
}

func (stream *Stream) CloseWrite() error {
	stream.writeMu.Lock()
	defer stream.writeMu.Unlock()
	stream.stateMu.Lock()
	already := stream.writeFIN
	stream.writeFIN = true
	stream.stateMu.Unlock()
	if already {
		return nil
	}
	if err := stream.endpoint.SendContext(stream.ctx, encode(finFrame, nil)); err != nil {
		stream.cancel()
		return err
	}
	stream.metrics.update(func(stats *Stats) { stats.LocalFIN++ })
	return nil
}

func (stream *Stream) Close() error {
	stream.closeOnce.Do(func() {
		stream.stateMu.Lock()
		clean := stream.readFIN && stream.writeFIN
		stream.stateMu.Unlock()
		defer func() {
			stream.stop()
			stream.cancel()
			stream.endpoint.Close()
			stream.readMu.Lock()
			defer stream.readMu.Unlock()
			stream.pending = nil
			stream.metrics.retain(-stream.pendingSize)
			stream.pendingSize = 0
		}()
		if !clean {
			stream.cancel()
			stream.metrics.update(func(stats *Stats) { stats.CloseReason = "local_cancel" })
			return
		}
		ctx, cancel := context.WithTimeout(stream.ctx, 10*time.Second)
		defer cancel()
		stream.closeErr = stream.endpoint.SendContext(ctx, encode(closeFrame, nil))
		if stream.closeErr == nil {
			kind, _, err := receive(ctx, stream.endpoint)
			stream.closeErr = err
			if err == nil && kind != closeFrame {
				stream.closeErr = ErrProtocol
			}
		}
		stream.metrics.update(func(stats *Stats) {
			stats.CloseReason = "clean"
			if stream.closeErr != nil {
				stats.CloseReason = "close_failed"
			}
		})
	})
	return stream.closeErr
}

func (stream *Stream) Reset() error {
	err := boundedControl(stream.endpoint, resetFrame)
	stream.cancel()
	stream.Close()
	return err
}
