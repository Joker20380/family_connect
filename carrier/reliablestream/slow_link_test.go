package reliablestream

import (
	"bytes"
	"errors"
	"fmt"
	"testing"
	"time"
)

func TestSerializedSlowLinkDelivery(test *testing.T) {
	for _, window := range []int{8, 32} {
		for _, rate := range []int{256000, 512000, 1000000} {
			for _, loss := range []bool{false, true} {
				test.Run(fmt.Sprintf("window%d/rate%d/loss%t", window, rate, loss), func(test *testing.T) {
					started := time.Unix(100, 0)
					states := [2]*engine{newEngine(DefaultConfig(), epoch{1}, started), newEngine(DefaultConfig(), epoch{2}, started)}
					for _, state := range states {
						state.remote = epoch{}
						state.config.SendWindow, state.config.ReceiveWindow = window, window
						state.remoteWindow = window
					}
					source := make([]byte, 64*states[0].config.Payload)
					for index := range source {
						source[index] = byte(index*37 + index/1009)
					}
					var flights []throughputFlight
					var serialized [2]int
					attempts := make(map[uint64]int)
					clock, position := 0, 0
					queue := func(packet frame, destination int) {
						packetBytes := (len(encode(packet))*115 + 99) / 100
						wireRate := rate
						if destination == 0 {
							wireRate /= 4
						}
						serialized[destination] = max(clock, serialized[destination]) + (packetBytes*8*1000+wireRate-1)/wireRate
						if packet.kind == dataFrame {
							attempts[packet.seq]++
							if loss && packet.seq%17 == 0 && attempts[packet.seq] == 1 {
								return
							}
						}
						flights = append(flights, throughputFlight{packet, destination, serialized[destination] + 300})
						if len(flights) > 1024 {
							test.Fatal("unbounded retry backlog")
						}
					}
					var delivered []byte
					for clock = 0; clock <= 180000; clock += 10 {
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
						for states[1].buffer[states[1].receive] != nil {
							data, acknowledgement := states[1].consume()
							delivered = append(delivered, data...)
							queue(acknowledgement, 0)
						}
						if len(delivered) == len(source) && len(states[0].sent) == 0 {
							break
						}
						if clock%100 == 0 {
							for side, state := range states {
								responses, err := state.tick(now)
								if err != nil {
									test.Fatalf("slow link terminated at %dms: %v (%s)", clock, err, state.failureTrace.Reason)
								}
								for _, response := range responses {
									queue(response, 1-side)
								}
							}
						}
					}
					if !bytes.Equal(delivered, source) || len(states[0].sent) != 0 {
						test.Fatal("slow link did not complete exact delivery")
					}
					test.Logf("virtual_ms=%d bytes=%d retransmissions=%d", clock, len(delivered), states[0].stats.Retransmissions)
				})
			}
		}
	}
}

func TestSlowACKDoesNotExhaustOneRetryPerSecond(test *testing.T) {
	states := connectedEngines()
	sender, receiver := states[0], states[1]
	packet, err := sender.send([]byte("slow-link payload"), sender.started)
	if err != nil {
		test.Fatal(err)
	}
	for second := 1; second <= 12; second++ {
		if _, err := sender.tick(sender.started.Add(time.Duration(second) * time.Second)); err != nil {
			test.Fatal("delayed but live path exhausted before its delivery deadline", second, err)
		}
	}
	if sender.stats.Retransmissions > 4 {
		test.Fatal("retry storm on a slow path", sender.stats.Retransmissions)
	}
	if _, err := receiver.input(packet, sender.started.Add(12*time.Second)); err != nil {
		test.Fatal(err)
	}
	_, acknowledgement := receiver.consume()
	if _, err := sender.input(acknowledgement, sender.started.Add(13*time.Second)); err != nil || len(sender.sent) != 0 {
		test.Fatal("delayed authenticated-stream bytes were not acknowledged", err)
	}
}

func TestSlowLinkStillHasAnAbsoluteFailureDeadline(test *testing.T) {
	for _, sacked := range []bool{false, true} {
		sender := connectedEngines()[0]
		if _, err := sender.send([]byte{1}, sender.started); err != nil {
			test.Fatal(err)
		}
		sender.sent[0].sacked = sacked
		for elapsed := time.Second; elapsed < sender.config.MaxAge; elapsed += time.Second {
			if _, err := sender.tick(sender.started.Add(elapsed)); err != nil {
				test.Fatal("premature recovery exhaustion", elapsed, err)
			}
		}
		if _, err := sender.tick(sender.started.Add(sender.config.MaxAge)); !errors.Is(err, ErrExhausted) || sender.failureTrace.Reason != "RELIABLE_FRAME_TIMEOUT" {
			test.Fatal("dead or unconsumed stream outlived its hard bound", err)
		}
	}
}
