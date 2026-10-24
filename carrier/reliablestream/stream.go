package reliablestream

import (
	"context"
	"crypto/rand"
	"errors"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/localwrite"
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
	stream.state.stats.Limits.LocalWriteCompletion = localwrite.Enabled(ctx)
	stream.bindDiagnosticAllocation(ctx)
	go stream.run(ctx)
	return stream, nil
}

func (stream *Stream) Stats() Stats {
	stream.mu.Lock()
	defer stream.mu.Unlock()
	stats := stream.state.stats
	stats.Limits.LocalSend = stream.state.config.SendWindow
	stats.Limits.LocalReceive = stream.state.config.ReceiveWindow
	stats.Limits.PeerReceive = stream.state.remoteWindow
	stats.Limits.EffectiveSend = min(stream.state.config.SendWindow, stream.state.remoteWindow)
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
	completionEnabled := localwrite.Enabled(ctx)
	type queuedFrame struct {
		packet   frame
		attempt  uint32
		done     chan error
		block    *pending
		obsolete chan struct{}
		queued   time.Time
	}
	type writeResult struct {
		job queuedFrame
		err error
	}
	outgoing := make(chan queuedFrame)
	written := make(chan writeResult, 1)
	writerDone := make(chan struct{})
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
		stream.cancel()
		<-writerDone
		if packet.target != (epoch{}) && terminal != ErrReset {
			resetContext, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
			_ = stream.endpoint.SendContext(resetContext, encode(packet))
			cancel()
		}
		stream.endpoint.Close()
		<-readerDone
		stream.err = terminal
		close(stream.done)
	}()
	transmit := func(job queuedFrame) error {
		packet := job.packet
		deadline := time.Now().Add(min(stream.state.config.MaxAge, 2*time.Second))
		if completionEnabled {
			deadline = job.queued.Add(min(stream.state.config.MaxAge, 2*time.Second))
		}
		sendContext, cancel := context.WithDeadline(ctx, deadline)
		point := sessiontrace.Boundary{Direction: "tx", Result: "ok"}
		if packet.kind == dataFrame {
			sendContext = sessiontrace.WithAttempt(sendContext, packet.seq, job.attempt)
			point = sessiontrace.AttemptFrom(sendContext)
			point.Direction, point.Stage, point.Result = "tx", "reliable_send", "ok"
			sessiontrace.From(ctx).Boundary(point)
			if sessiontrace.From(ctx).DropDiagnostic(point) {
				cancel()
				return nil
			}
		} else if packet.kind == ackFrame {
			sendContext = sessiontrace.WithACKObservation(sendContext, packet.observation, packet.ack, packet.bits)
			point.Stage, point.ACKBase, point.ACKMask = "ack_generated", packet.ack, packet.bits
			sessiontrace.From(ctx).Boundary(point)
		}
		var completion *localwrite.Write
		if completionEnabled {
			sendContext, completion = localwrite.Observe(sendContext, job.obsolete)
		}
		err := stream.endpoint.SendContext(sendContext, encode(packet))
		if err == nil && completionEnabled {
			err = completion.Wait()
		}
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
		return nil
	}
	go func() {
		defer close(writerDone)
		for {
			select {
			case <-ctx.Done():
				return
			case job := <-outgoing:
				err := transmit(job)
				select {
				case written <- writeResult{job: job, err: err}:
				case <-ctx.Done():
					return
				}
				if err != nil {
					return
				}
			}
		}
	}()
	pending := make([]queuedFrame, 0, MaxWindow+2)
	var activeData map[uint64]queuedFrame
	if completionEnabled {
		activeData = make(map[uint64]queuedFrame)
	}
	queue := func(packets []frame, done chan error) error {
		for _, packet := range packets {
			job := queuedFrame{packet: packet, done: done, queued: time.Now()}
			if packet.kind == dataFrame {
				stream.mu.Lock()
				if state := stream.state.sent[packet.seq]; state != nil {
					job.attempt = uint32(state.retries)
					job.block = state
				}
				stream.mu.Unlock()
				if completionEnabled {
					job.obsolete = make(chan struct{})
					activeData[packet.seq] = job
				}
			}
			coalesced := false
			if packet.kind == ackFrame || packet.kind == openFrame {
				for index := range pending {
					previous := pending[index].packet
					if previous.kind == packet.kind && previous.target == packet.target {
						pending[index] = job
						coalesced = true
						break
					}
				}
			}
			if coalesced {
				continue
			}
			if len(pending) == cap(pending) {
				return ErrBackpressure
			}
			pending = append(pending, job)
		}
		return nil
	}
	busy := false
	ticker := time.NewTicker(min(stream.state.config.RTO/4, 100*time.Millisecond))
	defer ticker.Stop()
	ready := false
	for {
		for len(pending) > 0 && pending[0].obsolete != nil {
			select {
			case <-pending[0].obsolete:
				if pending[0].done != nil {
					pending[0].done <- nil
				}
				copy(pending, pending[1:])
				pending[len(pending)-1] = queuedFrame{}
				pending = pending[:len(pending)-1]
				continue
			default:
			}
			break
		}
		stream.mu.Lock()
		if !ready && stream.state.remote != (epoch{}) {
			close(stream.ready)
			ready = true
		}
		var writes chan request
		if !busy && len(pending) == 0 && stream.state.writable() {
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
		var dispatch chan queuedFrame
		var next queuedFrame
		var tick <-chan time.Time
		if !busy && len(pending) > 0 {
			dispatch, next = outgoing, pending[0]
		}
		if !busy && len(pending) == 0 {
			tick = ticker.C
		}
		select {
		case <-ctx.Done():
			terminal = ctx.Err()
			return
		case dispatch <- next:
			copy(pending, pending[1:])
			pending[len(pending)-1] = queuedFrame{}
			pending = pending[:len(pending)-1]
			busy = true
		case result := <-written:
			busy = false
			err = result.err
			if completionEnabled && result.job.packet.kind == dataFrame {
				stream.mu.Lock()
				if block := stream.state.sent[result.job.packet.seq]; err == nil && block != nil && block == result.job.block && block.retries == int(result.job.attempt) && !block.sacked {
					block.last = time.Now()
				}
				stream.mu.Unlock()
				delete(activeData, result.job.packet.seq)
			}
			if result.job.done != nil {
				result.job.done <- err
			}
		case op := <-writes:
			stream.mu.Lock()
			packet, sendErr := stream.state.send(op.data, time.Now())
			stream.mu.Unlock()
			err = sendErr
			if err == nil {
				err = queue([]frame{packet}, op.done)
			}
			if err != nil {
				op.done <- err
			}
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
					for sequence, job := range activeData {
						if block := stream.state.sent[sequence]; block != job.block || block == nil || block.sacked {
							close(job.obsolete)
							delete(activeData, sequence)
						}
					}
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
		case now := <-tick:
			stream.mu.Lock()
			packets, err = stream.state.tick(now)
			stream.mu.Unlock()
		}
		if err == nil {
			err = queue(packets, nil)
		}
		if err != nil {
			terminal = err
			return
		}
	}
}
