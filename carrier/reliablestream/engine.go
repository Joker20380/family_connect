package reliablestream

import (
	"bytes"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

type Event struct {
	Index    uint64  `json:"index"`
	Kind     string  `json:"kind"`
	Sequence uint64  `json:"sequence"`
	AtMS     float64 `json:"at_ms"`
	DelayMS  float64 `json:"delay_ms"`
	Depth    int     `json:"depth"`
}

type Stats struct {
	Flow               sessiontrace.Flow
	DataSent           uint64
	DataReceived       uint64
	ACKSent            uint64
	ACKReceived        uint64
	SACKSent           uint64
	SACKReceived       uint64
	Retransmissions    uint64
	RetransmittedBytes uint64
	Duplicates         uint64
	Reordered          uint64
	Stale              uint64
	Timeouts           uint64
	Resets             uint64
	DeliveredBytes     uint64
	WithheldBytes      uint64
	Gaps               uint64
	RecoveredGaps      uint64
	MaxRecoveryMS      float64
	SendHighWater      int
	ReorderHighWater   int
	BufferedBytes      int
	MaxBufferedBytes   int
	SendDepth          int
	ReorderDepth       int
	Events             []Event
	RecentEvents       []Event
	EventsDropped      uint64
	Terminal           string
}

type pending struct {
	data    []byte
	first   time.Time
	last    time.Time
	retries int
	sacked  bool
}

type engine struct {
	config       Config
	local        epoch
	remote       epoch
	remoteWindow int
	remoteSize   int
	started      time.Time
	lastOpen     time.Time
	lastRefresh  time.Time
	next         uint64
	base         uint64
	receive      uint64
	sent         map[uint64]*pending
	buffer       map[uint64][]byte
	gaps         map[uint64]time.Time
	stats        Stats
	lastACK      time.Time
	lastProgress time.Time
	ackSeen      bool
	ackBase      uint64
	ackMask      uint32
	failureTrace sessiontrace.Event
}

func newEngine(config Config, local epoch, now time.Time) *engine {
	return &engine{config: config, local: local, started: now, sent: make(map[uint64]*pending), buffer: make(map[uint64][]byte), gaps: make(map[uint64]time.Time)}
}

func (state *engine) packet(kind byte) frame {
	return frame{kind: kind, source: state.local, target: state.remote}
}

func (state *engine) opening(target epoch) frame {
	return frame{kind: openFrame, source: state.local, target: target, window: state.config.ReceiveWindow, payload: state.config.Payload}
}

func (state *engine) event(kind string, seq uint64, now time.Time, delay time.Duration) {
	event := Event{uint64(len(state.stats.Events)) + state.stats.EventsDropped + 1, kind, seq, float64(now.Sub(state.started)) / float64(time.Millisecond), float64(delay) / float64(time.Millisecond), len(state.buffer)}
	if len(state.stats.Events) == 128 {
		state.stats.EventsDropped++
		if len(state.stats.RecentEvents) == 128 {
			copy(state.stats.RecentEvents, state.stats.RecentEvents[1:])
			state.stats.RecentEvents = state.stats.RecentEvents[:127]
		}
		state.stats.RecentEvents = append(state.stats.RecentEvents, event)
		return
	}
	state.stats.Events = append(state.stats.Events, event)
}

func (state *engine) depths() {
	state.stats.SendDepth = len(state.sent)
	state.stats.ReorderDepth = len(state.buffer)
	state.stats.SendHighWater = max(state.stats.SendHighWater, len(state.sent))
	state.stats.ReorderHighWater = max(state.stats.ReorderHighWater, len(state.buffer))
	state.stats.MaxBufferedBytes = max(state.stats.MaxBufferedBytes, state.stats.BufferedBytes)
}

func (state *engine) ack() frame {
	packet := state.packet(ackFrame)
	packet.ack = state.receive
	for seq := range state.buffer {
		packet.bits |= 1 << (seq - state.receive)
	}
	state.stats.ACKSent++
	if packet.bits != 0 {
		state.stats.SACKSent++
	}
	return packet
}

func (state *engine) input(packet frame, now time.Time) ([]frame, error) {
	if packet.target != state.local && !(packet.kind == openFrame && packet.target == (epoch{})) || (state.remote != (epoch{}) && packet.source != state.remote) {
		state.stats.Stale++
		return nil, nil
	}
	if packet.kind == openFrame {
		if packet.target == (epoch{}) {
			return []frame{state.opening(packet.source)}, nil
		}
		if state.remote == (epoch{}) {
			state.remote, state.remoteWindow, state.remoteSize = packet.source, packet.window, packet.payload
			return []frame{state.opening(packet.source), state.ack()}, nil
		}
		if packet.window != state.remoteWindow || packet.payload != state.remoteSize {
			return nil, ErrProtocol
		}
		return []frame{state.ack()}, nil
	}
	if state.remote == (epoch{}) {
		state.stats.Stale++
		return nil, nil
	}
	switch packet.kind {
	case resetFrame:
		return nil, ErrReset
	case ackFrame:
		state.stats.ACKReceived++
		if packet.ack < state.base {
			return nil, nil
		}
		if packet.ack > state.next {
			return nil, ErrProtocol
		}
		for bit := uint64(0); bit < MaxWindow; bit++ {
			if packet.bits&(1<<bit) != 0 && bit >= state.next-packet.ack {
				return nil, ErrProtocol
			}
		}
		if packet.bits != 0 {
			state.stats.SACKReceived++
		}
		state.lastACK = now
		state.ackSeen, state.ackBase, state.ackMask = true, packet.ack, packet.bits
		if packet.ack > state.base {
			state.lastProgress = now
		}
		for seq, block := range state.sent {
			if seq < packet.ack {
				state.stats.BufferedBytes -= len(block.data)
				delete(state.sent, seq)
			} else if packet.bits&(1<<(seq-packet.ack)) != 0 {
				block.sacked = true
			}
		}
		state.base = packet.ack
		state.depths()
	case dataFrame:
		state.stats.DataReceived++
		if len(packet.data) > state.config.Payload || packet.seq == ^uint64(0) {
			return nil, ErrProtocol
		}
		if packet.seq < state.receive {
			state.stats.Duplicates++
			return []frame{state.ack()}, nil
		}
		if packet.seq-state.receive >= uint64(state.config.ReceiveWindow) {
			return nil, ErrProtocol
		}
		if previous, exists := state.buffer[packet.seq]; exists {
			if !bytes.Equal(previous, packet.data) {
				return nil, ErrProtocol
			}
			state.stats.Duplicates++
			return []frame{state.ack()}, nil
		}
		state.buffer[packet.seq] = bytes.Clone(packet.data)
		state.stats.BufferedBytes += len(packet.data)
		state.depths()
		if packet.seq > state.receive {
			state.stats.Reordered++
			state.stats.WithheldBytes += uint64(len(packet.data))
		}
		for missing := state.receive; missing < packet.seq; missing++ {
			if _, exists := state.buffer[missing]; exists {
				continue
			}
			if _, exists := state.gaps[missing]; !exists {
				state.gaps[missing] = now
				state.stats.Gaps++
				state.event("gap_sack", missing, now, 0)
			}
		}
		if detected, exists := state.gaps[packet.seq]; exists {
			delay := now.Sub(detected)
			state.stats.RecoveredGaps++
			state.stats.MaxRecoveryMS = max(state.stats.MaxRecoveryMS, float64(delay)/float64(time.Millisecond))
			state.event("recovered", packet.seq, now, delay)
			delete(state.gaps, packet.seq)
		}
		return []frame{state.ack()}, nil
	}
	return nil, nil
}

func (state *engine) writable() bool {
	return state.remote != (epoch{}) && state.next-state.base < uint64(min(state.config.SendWindow, state.remoteWindow))
}

func (state *engine) send(data []byte, now time.Time) (frame, error) {
	if !state.writable() || len(data) == 0 || len(data) > min(state.config.Payload, state.remoteSize) || state.next == ^uint64(0) {
		return frame{}, ErrProtocol
	}
	packet := state.packet(dataFrame)
	packet.seq, packet.data = state.next, bytes.Clone(data)
	state.sent[state.next] = &pending{data: packet.data, first: now, last: now}
	state.next++
	state.stats.DataSent++
	state.stats.BufferedBytes += len(data)
	state.depths()
	return packet, nil
}

func (state *engine) consume() ([]byte, frame) {
	data := state.buffer[state.receive]
	delete(state.buffer, state.receive)
	state.receive++
	state.stats.DeliveredBytes += uint64(len(data))
	state.stats.BufferedBytes -= len(data)
	state.depths()
	return data, state.ack()
}

func (state *engine) exhausted(reason string, block *pending, now time.Time) error {
	age := func(since time.Time) uint64 {
		if since.IsZero() {
			since = state.started
		}
		return uint64(max(0, now.Sub(since).Milliseconds()))
	}
	state.failureTrace = sessiontrace.Event{Stage: "CARRIER", State: "FAILED", Reason: reason,
		ReliablePending: uint64(len(state.sent)), ReliableACKReceived: state.stats.ACKReceived,
		ReliableACKAgeMS: age(state.lastACK), ReliableProgressAgeMS: age(state.lastProgress)}
	flow := state.flow()
	state.failureTrace.Delivery = &sessiontrace.Delivery{Flow: &flow}
	if block != nil {
		state.failureTrace.ReliableAgeMS = age(block.first)
		state.failureTrace.ReliableRetries = uint64(block.retries)
		if block.sacked {
			state.failureTrace.ReliableSacked = 1
		}
	}
	return ErrExhausted
}

func (state *engine) flow() sessiontrace.Flow {
	value := sessiontrace.Flow{SendBase: state.base, SendNext: state.next, ReceiveNext: state.receive,
		ACKSeen: state.ackSeen, ACKBase: state.ackBase, ACKMask: state.ackMask,
		Pending: uint32(len(state.sent)), Buffered: uint32(len(state.buffer))}
	for sequence := range state.buffer {
		value.ReceiveMask |= 1 << (sequence - state.receive)
	}
	if head := state.sent[state.base]; head != nil {
		value.HeadRetries, value.HeadSacked = uint32(head.retries), head.sacked
	}
	return value
}

func (state *engine) tick(now time.Time) ([]frame, error) {
	if state.remote == (epoch{}) {
		if now.Sub(state.started) >= state.config.MaxAge {
			return nil, state.exhausted("RELIABLE_HANDSHAKE_TIMEOUT", nil, now)
		}
		if state.lastOpen.IsZero() || now.Sub(state.lastOpen) >= state.config.RTO {
			state.lastOpen = now
			return []frame{state.opening(epoch{})}, nil
		}
		return nil, nil
	}
	var output []frame
	if now.Sub(state.lastRefresh) >= state.config.RTO {
		state.lastRefresh = now
		output = append(output, state.ack())
	}
	for seq := state.base; seq < state.next; seq++ {
		block := state.sent[seq]
		if now.Sub(block.first) >= state.config.MaxAge {
			return nil, state.exhausted("RELIABLE_FRAME_TIMEOUT", block, now)
		}
		if block.sacked || now.Sub(block.last) < state.config.RTO {
			continue
		}
		state.stats.Timeouts++
		if block.retries >= state.config.MaxRetries {
			return nil, state.exhausted("RELIABLE_RETRY_EXHAUSTED", block, now)
		}
		block.last, block.retries = now, block.retries+1
		packet := state.packet(dataFrame)
		packet.seq, packet.data = seq, block.data
		output = append(output, packet)
		state.stats.Retransmissions++
		state.stats.RetransmittedBytes += uint64(len(block.data))
		state.event("retransmit", seq, now, now.Sub(block.first))
	}
	return output, nil
}
