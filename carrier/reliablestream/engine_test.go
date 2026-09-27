package reliablestream

import (
	"bytes"
	"errors"
	"testing"
	"time"
)

type flight struct {
	packet frame
	to     int
	due    int
}

type faults struct {
	drop      map[uint64]int
	every     uint64
	burst     [2]uint64
	reorder   bool
	duplicate bool
	delay     int
	ackLoss   int
}

func connectedEngines() [2]*engine {
	config := DefaultConfig()
	now := time.Unix(100, 0)
	left := newEngine(config, epoch{1}, now)
	right := newEngine(config, epoch{2}, now)
	left.remote, left.remoteWindow, left.remoteSize = right.local, config.ReceiveWindow, config.Payload
	right.remote, right.remoteWindow, right.remoteSize = left.local, config.ReceiveWindow, config.Payload
	return [2]*engine{left, right}
}

func simulate(test *testing.T, injection faults) Stats {
	test.Helper()
	states := connectedEngines()
	var network []flight
	attempts := make(map[uint64]int)
	clock := 0
	queue := func(packet frame, to int) {
		if packet.kind == dataFrame {
			attempts[packet.seq]++
			if attempts[packet.seq] <= injection.drop[packet.seq] || (attempts[packet.seq] == 1 && (injection.every > 0 && packet.seq%injection.every == 0 || packet.seq >= injection.burst[0] && packet.seq < injection.burst[1])) {
				return
			}
		} else if packet.kind == ackFrame && injection.ackLoss > 0 {
			injection.ackLoss--
			return
		}
		delay := 0
		if packet.kind == dataFrame && packet.seq%3 == 0 {
			delay = injection.delay
		}
		network = append(network, flight{packet, to, clock + delay})
		if injection.duplicate && packet.kind == dataFrame {
			network = append(network, flight{packet, to, clock + delay + 130})
		}
	}
	source := make([]byte, 100*16384+317)
	for index := range source {
		source[index] = byte(index*37 + index/1009)
	}
	var delivered []byte
	position := 0
	for clock = 0; clock < 6000; clock++ {
		now := states[0].started.Add(time.Duration(clock) * 10 * time.Millisecond)
		for states[0].writable() && position < len(source) {
			end := min(position+16384, len(source))
			packet, err := states[0].send(source[position:end], now)
			if err != nil {
				test.Fatal(err)
			}
			queue(packet, 1)
			position = end
		}
		current := network
		network = nil
		if injection.reorder {
			for left, right := 0, len(current)-1; left < right; left, right = left+1, right-1 {
				current[left], current[right] = current[right], current[left]
			}
		}
		for _, transit := range current {
			if transit.due > clock {
				network = append(network, transit)
				continue
			}
			raw := encode(transit.packet)
			packet, err := decode(raw)
			if err != nil {
				test.Fatal(err)
			}
			responses, err := states[transit.to].input(packet, now)
			if err != nil {
				test.Fatalf("clock=%d: %v", clock, err)
			}
			for _, response := range responses {
				queue(response, 1-transit.to)
			}
		}
		for states[1].buffer[states[1].receive] != nil {
			data, ack := states[1].consume()
			delivered = append(delivered, data...)
			if !bytes.Equal(delivered, source[:len(delivered)]) {
				test.Fatal("non-identical prefix delivered")
			}
			queue(ack, 0)
		}
		for side, state := range states {
			packets, err := state.tick(now)
			if err != nil {
				test.Fatal(err)
			}
			for _, packet := range packets {
				queue(packet, 1-side)
			}
			if len(state.sent) > 8 || len(state.buffer) > 16 || state.stats.BufferedBytes > 24*16384 {
				test.Fatal("bounds exceeded")
			}
		}
		if len(delivered) == len(source) && len(states[0].sent) == 0 && clock > 300 {
			break
		}
	}
	if !bytes.Equal(source, delivered) || len(states[0].sent) != 0 {
		test.Fatal("incomplete reconstruction")
	}
	if states[0].stats.SendHighWater < 8 {
		test.Fatal("stop-and-wait")
	}
	return states[1].stats
}

func TestDeterministicFaultMatrix(test *testing.T) {
	cases := map[string]faults{
		"ordered": {}, "one_missing": {drop: map[uint64]int{2: 1}},
		"multiple_missing": {drop: map[uint64]int{0: 1, 2: 1, 7: 1}},
		"every_nth":        {every: 5}, "burst": {burst: [2]uint64{2, 7}},
		"out_of_order": {reorder: true}, "duplicate": {duplicate: true},
		"delayed": {delay: 140}, "ack_loss": {ackLoss: 40},
		"retransmit_duplicate": {delay: 140, duplicate: true},
		"prolonged_gap":        {drop: map[uint64]int{2: 6}},
		"combined":             {every: 9, burst: [2]uint64{2, 6}, reorder: true, duplicate: true, delay: 120, ackLoss: 20},
	}
	for name, injection := range cases {
		test.Run(name, func(test *testing.T) {
			stats := simulate(test, injection)
			if len(injection.drop) > 0 && (stats.Gaps == 0 || stats.Gaps != stats.RecoveredGaps) {
				test.Fatal("gap evidence missing")
			}
		})
	}
}

func TestWindowBoundsRetryAndStale(test *testing.T) {
	states := connectedEngines()
	left, right := states[0], states[1]
	now := left.started
	for index := 0; index < 8; index++ {
		if _, err := left.send([]byte{byte(index)}, now); err != nil {
			test.Fatal(err)
		}
	}
	if left.writable() {
		test.Fatal("sender not backpressured")
	}
	bad := left.packet(dataFrame)
	bad.seq, bad.data = 16, []byte{1}
	if _, err := right.input(bad, now); !errors.Is(err, ErrProtocol) {
		test.Fatal("receive window overflow")
	}
	bad.seq = ^uint64(0) - 1
	if _, err := right.input(bad, now); !errors.Is(err, ErrProtocol) {
		test.Fatal("huge sequence accepted")
	}
	bad.target = epoch{3}
	if _, err := right.input(bad, now); err != nil || len(right.buffer) != 0 || right.stats.Stale != 1 {
		test.Fatal("stale frame accepted")
	}
	for attempt := 1; attempt <= left.config.MaxRetries; attempt++ {
		packets, err := left.tick(now.Add(time.Duration(attempt) * left.config.RTO))
		if err != nil || len(packets) != 9 {
			test.Fatal("retry batch", err, len(packets))
		}
	}
	if _, err := left.tick(now.Add(9 * left.config.RTO)); !errors.Is(err, ErrExhausted) {
		test.Fatal("retry exhaustion")
	}
	if _, err := right.input(left.packet(resetFrame), now); !errors.Is(err, ErrReset) {
		test.Fatal("reset not terminal")
	}
}

func TestSelectiveRetryAndConsumedACKLoss(test *testing.T) {
	states := connectedEngines()
	left, right := states[0], states[1]
	for index := 0; index < 8; index++ {
		packet, _ := left.send([]byte{byte(index)}, left.started)
		if index == 2 {
			continue
		}
		acks, err := right.input(packet, left.started)
		if err != nil {
			test.Fatal(err)
		}
		for _, ack := range acks {
			left.input(ack, left.started)
		}
	}
	packets, err := left.tick(left.started.Add(time.Second))
	if err != nil {
		test.Fatal(err)
	}
	var retried []uint64
	for _, packet := range packets {
		if packet.kind == dataFrame {
			retried = append(retried, packet.seq)
		}
	}
	if len(retried) != 1 || retried[0] != 2 {
		test.Fatal("nonmissing frames retransmitted", retried)
	}
	for _, packet := range packets {
		right.input(packet, left.started.Add(time.Second))
	}
	for right.buffer[right.receive] != nil {
		right.consume()
	}
	refresh, err := right.tick(left.started.Add(2 * time.Second))
	if err != nil {
		test.Fatal(err)
	}
	for _, packet := range refresh {
		left.input(packet, left.started.Add(2*time.Second))
	}
	if len(left.sent) != 0 {
		test.Fatal("lost cumulative ACK not repaired")
	}
}

func FuzzFrame(test *testing.F) {
	test.Add(encode(frame{kind: dataFrame, source: epoch{1}, target: epoch{2}, data: []byte{1}}))
	test.Add([]byte("FRS1"))
	test.Fuzz(func(test *testing.T, raw []byte) {
		packet, err := decode(raw)
		if err == nil && !bytes.Equal(encode(packet), raw) {
			test.Fatal("noncanonical framing")
		}
	})
}

func FuzzEngine(test *testing.F) {
	test.Add(encode(frame{kind: dataFrame, source: epoch{1}, target: epoch{2}, data: []byte{1}}))
	test.Fuzz(func(test *testing.T, raw []byte) {
		packet, err := decode(raw)
		if err != nil {
			return
		}
		state := connectedEngines()[1]
		state.input(packet, state.started)
		if len(state.buffer) > 16 || state.stats.BufferedBytes > 16*16384 {
			test.Fatal("allocation bound")
		}
	})
}

func TestSlowReceiverAgeAndMalformedACK(test *testing.T) {
	states := connectedEngines()
	left, right := states[0], states[1]
	for index := 0; index < 8; index++ {
		packet, _ := left.send(bytes.Repeat([]byte{1}, 16384), left.started)
		responses, err := right.input(packet, left.started)
		if err != nil {
			test.Fatal(err)
		}
		for _, ack := range responses {
			left.input(ack, left.started)
		}
	}
	for attempt := 1; attempt < 20; attempt++ {
		packets, err := left.tick(left.started.Add(time.Duration(attempt) * time.Second))
		if err != nil || len(packets) != 1 || packets[0].kind != ackFrame {
			test.Fatal("SACK retransmission burst", err)
		}
	}
	if _, err := left.tick(left.started.Add(20 * time.Second)); !errors.Is(err, ErrExhausted) {
		test.Fatal("slow receiver not bounded")
	}
	bad := right.packet(ackFrame)
	bad.ack = 9
	if _, err := left.input(bad, left.started); !errors.Is(err, ErrProtocol) {
		test.Fatal("future ACK accepted")
	}
	bad.ack, bad.bits = 8, 1
	if _, err := left.input(bad, left.started); !errors.Is(err, ErrProtocol) {
		test.Fatal("future SACK accepted")
	}
}

func TestMalformedAndConfigurationBounds(test *testing.T) {
	valid := encode(frame{kind: dataFrame, source: epoch{1}, target: epoch{2}, data: []byte{1}})
	for _, raw := range [][]byte{nil, valid[:63], append(bytes.Clone(valid), 0), bytes.Repeat([]byte{1}, HeaderSize+MaxPayload+1)} {
		if _, err := decode(raw); err == nil {
			test.Fatal("invalid length accepted")
		}
	}
	for _, offset := range []int{0, 4, 5, 6, 48, 56, 60, 62} {
		raw := bytes.Clone(valid)
		raw[offset] = 255
		if _, err := decode(raw); err == nil {
			test.Fatal("invalid header accepted", offset)
		}
	}
	for _, mutate := range []func(*Config){func(config *Config) { config.Payload = MaxPayload + 1 }, func(config *Config) { config.SendWindow = 33 }, func(config *Config) { config.ReceiveWindow = 33 }, func(config *Config) { config.RTO = 0 }, func(config *Config) { config.MaxRetries = 33 }, func(config *Config) { config.MaxAge = time.Hour }} {
		config := DefaultConfig()
		mutate(&config)
		if config.validate() == nil {
			test.Fatal("unsafe config accepted")
		}
	}
}
