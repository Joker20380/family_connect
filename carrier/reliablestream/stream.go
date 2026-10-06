package reliablestream

import (
	"context"
	"crypto/rand"
	"errors"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

type Endpoint interface {
	SendContext(context.Context, []byte) error
	Recv(context.Context) ([]byte, error)
	Close() error
}

type request struct {
	data []byte
	done chan error
}

type received struct {
	data     []byte
	err      error
	identity sessiontrace.ReceiveIdentity
}

type Stream struct {
	endpoint Endpoint
	state    *engine
	mu       sync.Mutex
	sendGate chan struct{}
	requests chan request
	output   chan []byte
	done     chan struct{}
	ready    chan struct{}
	cancel   context.CancelFunc
	err      error
}

func New(ctx context.Context, endpoint Endpoint, config Config) (*Stream, error) {
	if endpoint == nil || config.validate() != nil {
		return nil, ErrProtocol
	}
	var local epoch
	if _, err := rand.Read(local[:]); err != nil {
		return nil, err
	}
	ctx, cancel := context.WithCancel(ctx)
	stream := &Stream{endpoint: endpoint, state: newEngine(config, local, time.Now()), sendGate: make(chan struct{}, 1), requests: make(chan request), output: make(chan []byte), done: make(chan struct{}), ready: make(chan struct{}), cancel: cancel}
	go stream.run(ctx)
	return stream, nil
}

func (stream *Stream) Stats() Stats {
	stream.mu.Lock()
	defer stream.mu.Unlock()
	stats := stream.state.stats
	if stats.Terminal == "" {
		stats.Flow = stream.state.flow()
	}
	stats.Events = append([]Event(nil), stats.Events...)
	stats.RecentEvents = append([]Event(nil), stats.RecentEvents...)
	return stats
}

func (stream *Stream) failure() error {
	<-stream.done
	return stream.err
}

func (stream *Stream) SendContext(ctx context.Context, data []byte) error {
	select {
	case stream.sendGate <- struct{}{}:
		defer func() { <-stream.sendGate }()
	case <-ctx.Done():
		stream.cancel()
		return ctx.Err()
	case <-stream.done:
		return stream.failure()
	}
	if len(data) == 0 || len(data) > 65536 {
		return ErrProtocol
	}
	select {
	case <-ctx.Done():
		stream.cancel()
		return ctx.Err()
	case <-stream.done:
		return stream.failure()
	case <-stream.ready:
	}
	for len(data) > 0 {
		stream.mu.Lock()
		size := stream.state.config.Payload
		if stream.state.remoteSize > 0 {
			size = min(size, stream.state.remoteSize)
		}
		stream.mu.Unlock()
		size = min(size, len(data))
		op := request{data: data[:size], done: make(chan error, 1)}
		select {
		case <-ctx.Done():
			stream.cancel()
			return ctx.Err()
		case <-stream.done:
			return stream.failure()
		case stream.requests <- op:
		}
		select {
		case err := <-op.done:
			if err != nil {
				return err
			}
		case <-ctx.Done():
			stream.cancel()
			return ctx.Err()
		case <-stream.done:
			return stream.failure()
		}
		data = data[size:]
	}
	return nil
}

func (stream *Stream) Recv(ctx context.Context) ([]byte, error) {
	select {
	case <-ctx.Done():
		stream.cancel()
		return nil, ctx.Err()
	case <-stream.done:
		return nil, stream.failure()
	case data := <-stream.output:
		return data, nil
	}
}

func (stream *Stream) Close() error {
	stream.cancel()
	<-stream.done
	return nil
}

func (stream *Stream) run(ctx context.Context) {
	incoming := make(chan received, 1)
	readerDone := make(chan struct{})
	go func() {
		defer close(readerDone)
		for {
			receiveContext, observation := sessiontrace.WithReceiveObservation(ctx)
			data, err := stream.endpoint.Recv(receiveContext)
			select {
			case incoming <- received{data: data, err: err, identity: observation.Identity()}:
			case <-ctx.Done():
				return
			}
			if err != nil {
				return
			}
		}
	}()
	terminal := ErrClosed
	defer func() {
		stream.mu.Lock()
		failureTrace := stream.state.failureTrace
		stream.state.stats.Flow = stream.state.flow()
		packet := stream.state.packet(resetFrame)
		stream.state.stats.Resets++
		stream.state.stats.Terminal = "closed"
		switch {
		case errors.Is(terminal, ErrExhausted):
			stream.state.stats.Terminal = "recovery_exhausted"
		case errors.Is(terminal, ErrProtocol):
			stream.state.stats.Terminal = "protocol_violation"
		case errors.Is(terminal, ErrReset):
			stream.state.stats.Terminal = "remote_reset"
		case errors.Is(terminal, context.Canceled), errors.Is(terminal, context.DeadlineExceeded):
			stream.state.stats.Terminal = "cancelled"
		case terminal != ErrClosed:
			stream.state.stats.Terminal = "carrier_closed"
		}
		clear(stream.state.sent)
		clear(stream.state.buffer)
		clear(stream.state.gaps)
		stream.state.stats.BufferedBytes = 0
		stream.state.depths()
		stream.mu.Unlock()
		if errors.Is(terminal, ErrExhausted) {
			sessiontrace.From(ctx).Record(failureTrace)
		}
		if packet.target != (epoch{}) && terminal != ErrReset {
			resetContext, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
			_ = stream.endpoint.SendContext(resetContext, encode(packet))
			cancel()
		}
		stream.cancel()
		stream.endpoint.Close()
		<-readerDone
		stream.err = terminal
		close(stream.done)
	}()
	transmit := func(packets []frame) error {
		for _, packet := range packets {
			sendContext, cancel := context.WithTimeout(ctx, min(stream.state.config.MaxAge, 2*time.Second))
			point := sessiontrace.Boundary{Direction: "tx", Result: "ok"}
			if packet.kind == dataFrame {
				stream.mu.Lock()
				attempt := uint32(stream.state.sent[packet.seq].retries)
				stream.mu.Unlock()
				sendContext = sessiontrace.WithAttempt(sendContext, packet.seq, attempt)
				point = sessiontrace.AttemptFrom(sendContext)
				point.Direction, point.Stage, point.Result = "tx", "reliable_send", "ok"
				sessiontrace.From(ctx).Boundary(point)
				if sessiontrace.From(ctx).DropDiagnostic(point) {
					cancel()
					continue
				}
			} else if packet.kind == ackFrame {
				sendContext = sessiontrace.WithACKObservation(sendContext, packet.observation, packet.ack, packet.bits)
				point.Stage, point.ACKBase, point.ACKMask = "ack_generated", packet.ack, packet.bits
				sessiontrace.From(ctx).Boundary(point)
			}
			err := stream.endpoint.SendContext(sendContext, encode(packet))
			if packet.kind == ackFrame {
				point.Stage = "ack_sent"
				if err != nil {
					point.Result = "write_error"
				}
				sessiontrace.From(ctx).Boundary(point)
			}
			cancel()
			if err != nil {
				return err
			}
		}
		return nil
	}
	ticker := time.NewTicker(min(stream.state.config.RTO/4, 100*time.Millisecond))
	defer ticker.Stop()
	ready := false
	for {
		stream.mu.Lock()
		if !ready && stream.state.remote != (epoch{}) {
			close(stream.ready)
			ready = true
		}
		var writes chan request
		if stream.state.writable() {
			writes = stream.requests
		}
		var reads chan []byte
		data := stream.state.buffer[stream.state.receive]
		if data != nil {
			reads = stream.output
		}
		stream.mu.Unlock()
		var packets []frame
		var err error
		select {
		case <-ctx.Done():
			terminal = ctx.Err()
			return
		case op := <-writes:
			stream.mu.Lock()
			packet, sendErr := stream.state.send(op.data, time.Now())
			stream.mu.Unlock()
			err = sendErr
			if err == nil {
				err = transmit([]frame{packet})
			}
			op.done <- err
		case reads <- data:
			stream.mu.Lock()
			consumed := stream.state.receive
			before := stream.state.receiveObservation()
			_, packet := stream.state.consume()
			after := stream.state.receiveObservation()
			stream.mu.Unlock()
			sessiontrace.From(ctx).ReceiverConsumed(consumed, before, after, packet.observation, packet.ack, packet.bits)
			sessiontrace.From(ctx).RecordConsumed(consumed, packet.ack, packet.bits)
			packets = []frame{packet}
		case record := <-incoming:
			err = record.err
			if err == nil {
				var packet frame
				packet, err = decode(record.data)
				if err == nil {
					stream.mu.Lock()
					duplicates, stale, previousBase := stream.state.stats.Duplicates, stream.state.stats.Stale, stream.state.base
					before := stream.state.receiveObservation()
					packets, err = stream.state.input(packet, time.Now())
					after := stream.state.receiveObservation()
					advanced := stream.state.base > previousBase
					currentBase := stream.state.base
					point := sessiontrace.Boundary{Direction: "rx", Result: "ok"}
					if err != nil {
						point.Result = "protocol"
					} else if stream.state.stats.Stale != stale {
						point.Result = "stale"
					} else if stream.state.stats.Duplicates != duplicates {
						point.Result = "duplicate"
					}
					if packet.kind == dataFrame {
						point.Stage, point.DataKnown, point.DataSequence = "reliable_data_accepted", true, packet.seq
					} else if packet.kind == ackFrame {
						point.Stage, point.ACKBase, point.ACKMask = "ack_received", packet.ack, packet.bits
					}
					stream.mu.Unlock()
					if packet.kind == dataFrame {
						sessiontrace.From(ctx).ReceiverAccepted(record.identity, packet.seq, point.Result, before, after)
					}
					if point.Stage != "" {
						sessiontrace.From(ctx).Boundary(point)
					}
					if advanced {
						sessiontrace.From(ctx).RecordBaseAdvanced(currentBase, packet.bits)
					}
				}
			}
		case now := <-ticker.C:
			stream.mu.Lock()
			packets, err = stream.state.tick(now)
			stream.mu.Unlock()
		}
		if err == nil {
			err = transmit(packets)
		}
		if err != nil {
			terminal = err
			return
		}
	}
}
