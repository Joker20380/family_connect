package reliablestream

import (
	"bytes"
	"testing"
)

func TestDATA19ACKProofSemantics(test *testing.T) {
	states := connectedEngines()
	sender, receiver := states[0], states[1]
	sender.base, sender.next, receiver.receive = 19, 19, 19
	var head frame
	for offset := 0; offset < 8; offset++ {
		packet, err := sender.send([]byte{byte(offset + 1)}, sender.started)
		if err != nil {
			test.Fatal(err)
		}
		if offset == 0 {
			head = packet
			continue
		}
		if _, err := receiver.input(packet, receiver.started); err != nil {
			test.Fatal(err)
		}
	}
	gap := receiver.ack()
	if gap.ack != 19 || gap.bits != 254 || receiver.buffer[19] != nil {
		test.Fatal("gap state")
	}
	if _, err := receiver.tick(receiver.started.Add(receiver.config.RTO)); err != nil {
		test.Fatal(err)
	}
	if receiver.receive != 19 {
		test.Fatal("timer skipped missing head")
	}
	acks, err := receiver.input(head, receiver.started)
	if err != nil || acks[0].ack != 19 || acks[0].bits != 255 || receiver.receive != 19 {
		test.Fatal("acceptance is not consumption", err)
	}
	for offset := 0; offset < 8; offset++ {
		if receiver.buffer[receiver.receive] == nil {
			test.Fatal("runtime read channel must remain disabled")
		}
		data, ack := receiver.consume()
		if !bytes.Equal(data, []byte{byte(offset + 1)}) {
			test.Fatal("ordered delivery")
		}
		if offset == 0 && (ack.ack != 20 || ack.bits != 127) {
			test.Fatal("20/127")
		}
		if _, err := sender.input(ack, sender.started); err != nil {
			test.Fatal(err)
		}
	}
	if receiver.ack().ack != 27 || receiver.ack().bits != 0 || sender.base != 27 {
		test.Fatal("27/0 cumulative progress")
	}
}
