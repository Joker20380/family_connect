package reliablestream

import (
	"bytes"
	"fmt"
	"testing"
	"time"
)

func TestHeadLossAndDuplicateVirtualClock(test *testing.T) {
	for _, head := range []uint64{48, 58} {
		for _, late := range []bool{false, true} {
			test.Run(fmt.Sprintf("DATA%d/late=%t", head, late), func(test *testing.T) {
				states := connectedEngines()
				sender, receiver := states[0], states[1]
				sender.base, sender.next, receiver.receive = head, head, head
				now := sender.started
				var original frame
				for index := 0; index < 8; index++ {
					packet, err := sender.send([]byte{byte(index)}, now)
					if err != nil {
						test.Fatal(err)
					}
					if index == 0 {
						original = packet
						continue
					}
					acks, err := receiver.input(packet, now)
					if err != nil || len(acks) != 1 {
						test.Fatal("later DATA", err)
					}
					if _, err = sender.input(acks[0], now); err != nil {
						test.Fatal(err)
					}
				}
				if receiver.receive != head || len(receiver.buffer) != 7 || sender.flow().ACKMask != 254 {
					test.Fatal("head hole/SACK not reproduced")
				}
				now = now.Add(sender.config.RTO)
				packets, err := sender.tick(now)
				if err != nil {
					test.Fatal(err)
				}
				var retry frame
				count := 0
				for _, packet := range packets {
					if packet.kind == dataFrame {
						retry = packet
						count++
					}
				}
				if count != 1 || retry.seq != head || sender.sent[head].retries != 1 || !bytes.Equal(encode(original), encode(retry)) {
					test.Fatal("retry must keep FRS1 identity/bytes")
				}
				first, duplicate := original, retry
				if late {
					first, duplicate = retry, original
				}
				if _, err := receiver.input(first, now); err != nil {
					test.Fatal(err)
				}
				acks, err := receiver.input(duplicate, now)
				if err != nil || len(acks) != 1 || receiver.stats.Duplicates != 1 || len(receiver.buffer) != 8 || acks[0].bits != 255 {
					test.Fatal("buffered duplicate breaks ACK", err)
				}
				for index := 0; index < 8; index++ {
					data, ack := receiver.consume()
					if !bytes.Equal(data, []byte{byte(index)}) {
						test.Fatal("duplicate/reorder upward", index)
					}
					if _, err := sender.input(ack, now); err != nil {
						test.Fatal(err)
					}
				}
				acks, err = receiver.input(duplicate, now.Add(time.Millisecond))
				if err != nil || len(acks) != 1 || acks[0].ack != head+8 || len(receiver.buffer) != 0 || receiver.stats.Duplicates != 2 {
					test.Fatal("consumed duplicate redelivered")
				}
				if _, err = sender.tick(now.Add(sender.config.MaxAge)); err != nil || sender.base != head+8 || !sender.writable() {
					test.Fatal("permanent gap/exhaustion", err)
				}
			})
		}
	}
}
