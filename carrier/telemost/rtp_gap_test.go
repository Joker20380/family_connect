package telemost

import (
	"bytes"
	"reflect"
	"testing"
	"time"

	"github.com/pion/rtp"
	"github.com/pion/rtp/codecs"
)

func TestRTPReorderGivesEachGapItsOwnDeadline(test *testing.T) {
	for _, scenario := range []struct {
		name  string
		start uint16
		heal  bool
	}{
		{"healed_gap", 100, true},
		{"skipped_gap", 100, false},
		{"healed_gap_wrap", 65533, true},
		{"skipped_gap_wrap", 65533, false},
	} {
		test.Run(scenario.name, func(test *testing.T) {
			buffer := newReorderBuffer()
			var received []uint16
			deliver := func(packet *rtp.Packet) { received = append(received, packet.SequenceNumber) }
			push := func(offset uint16) {
				buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: scenario.start + offset}}, deliver)
			}
			push(0)
			push(2)
			push(4)
			buffer.gapSince = time.Now().Add(-time.Second)
			if scenario.heal {
				push(1)
			} else {
				push(5)
			}
			push(6)
			push(3)
			push(5)
			want := []uint16{scenario.start}
			if scenario.heal {
				want = append(want, scenario.start+1)
			}
			for offset := uint16(2); offset <= 6; offset++ {
				want = append(want, scenario.start+offset)
			}
			if !reflect.DeepEqual(received, want) {
				test.Fatalf("fresh gap skipped using previous deadline: got %v, want %v", received, want)
			}
			if len(buffer.pkts) != 0 || !buffer.gapSince.IsZero() {
				test.Fatal("completed delivery retained a gap")
			}
		})
	}
}

func TestRTPReorderFreshGapPreservesCarrierMessage(test *testing.T) {
	buffer := newReorderBuffer()
	var frame vp8FrameState
	var received [][]byte
	assembler := newReassembler(2, func(data []byte) { received = append(received, data) })
	deliver := func(packet *rtp.Packet) {
		if fragment, valid := decodeVP8Frame(frame.process(packet)); valid {
			assembler.ingest(fragment)
		}
	}
	pushKeepalive := func(sequence uint16) {
		payloader := &codecs.VP8Payloader{}
		buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: sequence, Timestamp: uint32(sequence), Marker: true}, Payload: payloader.Payload(600, vp8Keepalive)[0]}, deliver)
	}
	payload := bytes.Repeat([]byte{0x53}, 2000)
	fragments, err := encodeFragments(1, 1, payload)
	if err != nil {
		test.Fatal(err)
	}
	payloader := &codecs.VP8Payloader{}
	packets := payloader.Payload(600, encodeVP8DataFrame(fragments[0]))
	if len(packets) != 4 {
		test.Fatal("fixture requires four RTP packets")
	}
	pushData := func(index int) {
		buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: uint16(103 + index), Timestamp: 103, Marker: index == len(packets)-1}, Payload: packets[index]}, deliver)
	}
	pushKeepalive(100)
	pushKeepalive(102)
	pushData(1)
	buffer.gapSince = time.Now().Add(-time.Second)
	pushKeepalive(101)
	pushData(2)
	pushData(0)
	pushData(3)
	if len(received) != 1 || !bytes.Equal(received[0], payload) {
		test.Fatal("fully received RTP packets failed byte-exact carrier delivery")
	}
}

func TestRTPReorderDoesNotExtendUnchangedGap(test *testing.T) {
	buffer := newReorderBuffer()
	var received []uint16
	deliver := func(packet *rtp.Packet) { received = append(received, packet.SequenceNumber) }
	push := func(sequence uint16) {
		buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: sequence}}, deliver)
	}
	push(100)
	push(102)
	deadlineStart := buffer.gapSince
	push(103)
	push(103)
	push(104)
	if !buffer.gapSince.Equal(deadlineStart) {
		test.Fatal("later packets or duplicates extended the same gap deadline")
	}
	buffer.gapSince = time.Now().Add(-time.Second)
	push(105)
	if !reflect.DeepEqual(received, []uint16{100, 102, 103, 104, 105}) || !buffer.gapSince.IsZero() {
		test.Fatal("expired gap prevented later packet delivery")
	}
	push(101)
	if len(received) != 5 {
		test.Fatal("late packet delivered after its gap was skipped")
	}
}
