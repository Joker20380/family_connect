package reliablestream

import (
	"bytes"
	"context"
	"encoding/json"
	"os"
	"testing"
	"time"
)

type throughputCase struct {
	name          string
	missing       []uint64
	lossAttempts  int
	headDelayMS   int
	ackDelayMS    int
	ackDropUntil  int
	consumeFromMS int
	duplicateACK  bool
}

type throughputFlight struct {
	packet frame
	to     int
	due    int
}

type throughputResult struct {
	Variant        string  `json:"variant"`
	Case           string  `json:"case"`
	Bytes          int     `json:"bytes"`
	VirtualMS      int     `json:"virtual_ms"`
	MaxNoDelivery  int     `json:"max_no_delivery_ms"`
	ModelMbit      float64 `json:"model_mbit_s"`
	Retransmits    uint64  `json:"retransmits"`
	Timeouts       uint64  `json:"rto_timeouts"`
	ReceiverDupes  uint64  `json:"receiver_duplicates"`
	SendHighWater  int     `json:"send_high_water"`
	BytesIdentical bool    `json:"bytes_identical"`
}

func TestThroughputComparison(test *testing.T) {
	cases := []throughputCase{
		{name: "ordered"},
		{name: "head_loss", missing: []uint64{0}, lossAttempts: 1},
		{name: "middle_loss", missing: []uint64{2}, lossAttempts: 1},
		{name: "periodic_head_loss", missing: []uint64{0, 8, 16, 24, 32, 40, 48, 56}, lossAttempts: 1},
		{name: "three_holes", missing: []uint64{0, 1, 2}, lossAttempts: 1},
		{name: "fast_retry_lost", missing: []uint64{0}, lossAttempts: 2},
		{name: "tail_loss", missing: []uint64{63}, lossAttempts: 1},
		{name: "short_reordering", headDelayMS: 80},
		{name: "long_reordering", headDelayMS: 400},
		{name: "reverse_ack_delay", ackDelayMS: 400},
		{name: "reverse_ack_outage", ackDropUntil: 450},
		{name: "duplicate_acks", duplicateACK: true},
		{name: "slow_consumer", consumeFromMS: 450},
	}
	for _, scenario := range cases {
		test.Run(scenario.name, func(test *testing.T) {
			result := throughputSimulation(test, scenario)
			raw, err := json.Marshal(result)
			if err != nil {
				test.Fatal(err)
			}
			test.Log("THROUGHPUT_RESULT " + string(raw))
			if !result.BytesIdentical || result.SendHighWater > DefaultConfig().SendWindow {
				test.Fatal("byte identity or memory window bound changed", result)
			}
			if scenario.name == "ordered" || scenario.name == "short_reordering" || scenario.name == "reverse_ack_delay" || scenario.name == "duplicate_acks" || scenario.name == "slow_consumer" {
				if result.Retransmits != 0 {
					test.Fatal("spurious recovery in protected no-loss case", result)
				}
			}
		})
	}
}

func throughputSimulation(test *testing.T, scenario throughputCase) throughputResult {
	test.Helper()
	states := connectedEngines()
	const blockCount = 64
	source := make([]byte, blockCount*DefaultConfig().Payload)
	for index := range source {
		source[index] = byte(index*37 + index/1009)
	}
	var flights []throughputFlight
	attempts := make(map[uint64]int)
	clock, serializedUntil, position := 0, 0, 0
	lastDelivery, maxNoDelivery := 0, 0
	var delivered []byte
	queue := func(packet frame, destination int) {
		due := clock + 60
		if packet.kind == dataFrame {
			attempts[packet.seq]++
			due = max(clock, serializedUntil) + 60
			serializedUntil = max(clock, serializedUntil) + 6
			for _, missing := range scenario.missing {
				if packet.seq == missing && attempts[packet.seq] <= scenario.lossAttempts {
					return
				}
			}
			if packet.seq%8 == 0 && attempts[packet.seq] == 1 {
				due += scenario.headDelayMS
			}
		} else if packet.kind == ackFrame {
			if clock < scenario.ackDropUntil {
				return
			}
			due += scenario.ackDelayMS
		}
		flights = append(flights, throughputFlight{packet, destination, due})
		if scenario.duplicateACK && packet.kind == ackFrame {
			for extra := 1; extra <= 3; extra++ {
				flights = append(flights, throughputFlight{packet, destination, due + extra*10})
			}
		}
	}
	for clock = 0; clock <= 20000; clock += 10 {
		now := states[0].started.Add(time.Duration(clock) * time.Millisecond)
		for states[0].writable() && position < len(source) {
			end := min(position+states[0].config.Payload, len(source))
			packet, err := states[0].send(source[position:end], now)
			if err != nil {
				test.Fatal(err)
			}
			queue(packet, 1)
			position = end
		}
		current := flights
		flights = nil
		for _, transit := range current {
			if transit.due > clock {
				flights = append(flights, transit)
				continue
			}
			packet, err := decode(encode(transit.packet))
			if err != nil {
				test.Fatal(err)
			}
			responses, err := states[transit.to].input(packet, now)
			if err != nil {
				test.Fatal(err)
			}
			for _, response := range responses {
				queue(response, 1-transit.to)
			}
		}
		for clock >= scenario.consumeFromMS && states[1].buffer[states[1].receive] != nil {
			data, ack := states[1].consume()
			delivered = append(delivered, data...)
			maxNoDelivery = max(maxNoDelivery, clock-lastDelivery)
			lastDelivery = clock
			queue(ack, 0)
		}
		if clock%100 == 0 {
			for side, state := range states {
				responses, err := state.tick(now)
				if err != nil {
					test.Fatal(err)
				}
				for _, response := range responses {
					queue(response, 1-side)
				}
			}
		}
		if len(delivered) == len(source) && states[0].base == blockCount {
			return throughputResult{Variant: os.Getenv("FC_PERF_VARIANT"), Case: scenario.name,
				Bytes: len(source), VirtualMS: lastDelivery, MaxNoDelivery: maxNoDelivery,
				ModelMbit:   float64(len(source)*8) / float64(lastDelivery) / 1000,
				Retransmits: states[0].stats.Retransmissions, Timeouts: states[0].stats.Timeouts,
				ReceiverDupes: states[1].stats.Duplicates, SendHighWater: states[0].stats.SendHighWater,
				BytesIdentical: bytes.Equal(delivered, source)}
		}
	}
	test.Fatal("finite virtual transfer budget exceeded")
	return throughputResult{}
}

func TestThroughputAdapterHeadLoss(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 4*time.Second)
	defer cancel()
	leftEndpoint, rightEndpoint := endpoints()
	dropped := false
	leftEndpoint.drop = func(raw []byte) bool {
		packet, err := decode(raw)
		if err == nil && packet.kind == dataFrame && packet.seq == 0 && !dropped {
			dropped = true
			return true
		}
		return false
	}
	left, err := New(ctx, leftEndpoint, DefaultConfig())
	if err != nil {
		test.Fatal(err)
	}
	defer left.Close()
	right, err := New(ctx, rightEndpoint, DefaultConfig())
	if err != nil {
		test.Fatal(err)
	}
	defer right.Close()
	payload := bytes.Repeat([]byte("synthetic-byte-exact-stream"), 600)
	started := time.Now()
	finished := make(chan error, 1)
	go func() {
		for index := 0; index < 8; index++ {
			if sendErr := left.SendContext(ctx, payload); sendErr != nil {
				finished <- sendErr
				return
			}
		}
		finished <- nil
	}()
	for index := 0; index < 8; index++ {
		data, receiveErr := right.Recv(ctx)
		if receiveErr != nil || !bytes.Equal(data, payload) {
			test.Fatal("runtime ordered transfer failed", receiveErr)
		}
	}
	if err := <-finished; err != nil {
		test.Fatal(err)
	}
	stats := left.Stats()
	if stats.Retransmissions != 1 {
		test.Fatal("single head loss generated repeated retransmits", stats.Retransmissions)
	}
	expectedTimeouts := uint64(0)
	if os.Getenv("FC_PERF_VARIANT") == "baseline" {
		expectedTimeouts = 1
	}
	if stats.Timeouts != expectedTimeouts {
		test.Fatal("runtime recovery did not use expected path", stats.Timeouts)
	}
	test.Logf("ADAPTER_RESULT variant=%s elapsed_ms=%d bytes=%d retransmits=%d rto_timeouts=%d", os.Getenv("FC_PERF_VARIANT"), time.Since(started).Milliseconds(), len(payload)*8, stats.Retransmissions, stats.Timeouts)
}
