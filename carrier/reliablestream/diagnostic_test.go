package reliablestream

import (
	"bytes"
	"testing"
)

func TestDeliveryTracksHeadSACKAndConsumption(test *testing.T) {
	states := connectedEngines()
	sender, receiver := states[0], states[1]
	first, _ := sender.send([]byte("synthetic-first"), sender.started)
	second, _ := sender.send([]byte("synthetic-second"), sender.started)
	receiver.input(second, receiver.started)
	sender.input(receiver.ack(), sender.started)
	flow := sender.flow()
	remote := receiver.flow()
	if flow.SendBase != 0 || flow.SendNext != 2 || flow.Pending != 2 || !flow.ACKSeen || flow.ACKBase != 0 || flow.ACKMask != 2 || flow.HeadSacked || remote.ReceiveNext != 0 || remote.ReceiveMask != 2 || remote.Buffered != 1 {
		test.Fatal("head hole and SACK not distinguished", flow, remote)
	}
	receiver.input(first, receiver.started)
	sender.input(receiver.ack(), sender.started)
	if !sender.flow().HeadSacked || receiver.flow().ReceiveMask != 3 || receiver.flow().ReceiveNext != 0 {
		test.Fatal("arrival incorrectly implies consumption")
	}
	for index := 0; index < 2; index++ {
		_, ack := receiver.consume()
		sender.input(ack, sender.started)
	}
	if sender.flow().Pending != 0 || sender.flow().SendBase != 2 || receiver.flow().ReceiveNext != 2 || receiver.flow().ReceiveMask != 0 {
		test.Fatal("consumption progress missing")
	}
}

func TestDiagnosticPrefixDoesNotExposeBytes(test *testing.T) {
	raw := encode(frame{kind: dataFrame, seq: 0, data: bytes.Repeat([]byte("private-test-payload"), 1000)})
	sequence, known := DataSequencePrefix(raw[:8192], uint32(len(raw)))
	if !known || sequence != 0 {
		test.Fatal("zero sequence is valid even with an incomplete message")
	}
	for _, value := range [][]byte{nil, raw[:HeaderSize-1], encode(frame{kind: ackFrame}), bytes.Repeat([]byte{1}, HeaderSize)} {
		if _, known := DataSequencePrefix(value, uint32(len(value))); known {
			test.Fatal("invalid/non-DATA prefix accepted")
		}
	}
	if _, known := DataSequencePrefix(raw, uint32(len(raw)+1)); known {
		test.Fatal("length mismatch accepted")
	}
}
