package reliablestream

import (
	"bytes"
	"testing"
	"time"
)

func TestSACKMultipleHolesFastRecovery(test *testing.T) {
	for _, lost := range []int{1, 2, 3, 4, 5} {
		states := connectedEngines()
		sender, receiver := states[0], states[1]
		start := sender.started
		var expected []byte
		for sequence := 0; sequence < 8; sequence++ {
			payload := bytes.Repeat([]byte{byte(sequence + 1)}, 97+sequence)
			expected = append(expected, payload...)
			packet, err := sender.send(payload, start)
			if err != nil {
				test.Fatal(err)
			}
			if sequence < lost {
				continue
			}
			acks, err := receiver.input(packet, start.Add(300*time.Millisecond))
			if err != nil {
				test.Fatal(err)
			}
			for _, ack := range acks {
				if _, err = sender.input(ack, start.Add(400*time.Millisecond)); err != nil {
					test.Fatal(err)
				}
			}
		}
		packets, err := sender.tick(start.Add(500 * time.Millisecond))
		if err != nil {
			test.Fatal(err)
		}
		attempts := 0
		for _, packet := range packets {
			if packet.kind != dataFrame {
				continue
			}
			attempts++
			if packet.seq >= uint64(lost) {
				test.Fatal("retransmitted SACKed data")
			}
			acks, err := receiver.input(packet, start.Add(600*time.Millisecond))
			if err != nil {
				test.Fatal(err)
			}
			for _, ack := range acks {
				if _, err = sender.input(ack, start.Add(700*time.Millisecond)); err != nil {
					test.Fatal(err)
				}
			}
		}
		if attempts != lost {
			test.Fatalf("lost=%d fast attempts=%d", lost, attempts)
		}
		if sender.base != 0 || len(sender.sent) != 8 {
			test.Fatal("SACK prematurely released retained window")
		}
		packets, err = sender.tick(start.Add(750 * time.Millisecond))
		if err != nil {
			test.Fatal(err)
		}
		for _, packet := range packets {
			if packet.kind == dataFrame {
				test.Fatal("duplicate fast retransmission")
			}
		}
		var actual []byte
		for receiver.buffer[receiver.receive] != nil {
			data, ack := receiver.consume()
			actual = append(actual, data...)
			if _, err = sender.input(ack, start.Add(800*time.Millisecond)); err != nil {
				test.Fatal(err)
			}
		}
		if !bytes.Equal(actual, expected) || sender.base != 8 || len(sender.sent) != 0 {
			test.Fatal("byte exact release failed")
		}
	}
}

func TestSACKFastRecoveryThresholdAndSingleAttempt(test *testing.T) {
	for _, count := range []int{2, 3} {
		state := connectedEngines()[0]
		start := state.started
		for sequence := 0; sequence < 8; sequence++ {
			if _, err := state.send([]byte{1}, start); err != nil {
				test.Fatal(err)
			}
		}
		for sequence := uint64(8 - count); sequence < 8; sequence++ {
			state.sent[sequence].sacked = true
		}
		if state.fastRetransmit(1, state.sent[1], start.Add(249*time.Millisecond)) {
			test.Fatal("age guard skipped")
		}
		if got := state.fastRetransmit(1, state.sent[1], start.Add(250*time.Millisecond)); got != (count == 3) {
			test.Fatalf("threshold=%d result=%v", count, got)
		}
		state.sent[1].retries = 1
		if state.fastRetransmit(1, state.sent[1], start.Add(900*time.Millisecond)) {
			test.Fatal("repeated fast retry")
		}
	}
}
