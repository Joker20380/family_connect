package telemost

import (
	"bytes"
	"testing"
	"time"

	"github.com/pion/rtp"
	"github.com/pion/rtp/codecs"
)

func TestSavedHead597PartialFrameRetainsAssembly(test *testing.T) {
	payload := bytes.Repeat([]byte{0x53}, 16384+44)
	fragments, err := encodeFragments(752154365, 4260144682, payload)
	if err != nil || len(fragments) != 3 {
		test.Fatal("three-fragment fixture", err)
	}
	buffer := newReorderBuffer()
	var frame vp8FrameState
	var received [][]byte
	assembler := newReassembler(2467868236, func(data []byte) { received = append(received, bytes.Clone(data)) })
	deliver := func(packet *rtp.Packet) {
		if fragment, valid := decodeVP8Frame(frame.process(packet)); valid {
			assembler.ingest(fragment)
		}
	}
	var late *rtp.Packet
	sequence := uint16(5973)
	payloader := &codecs.VP8Payloader{}
	for fragmentIndex, fragment := range fragments {
		packets := payloader.Payload(1200, encodeVP8DataFrame(fragment))
		for packetIndex, data := range packets {
			packet := &rtp.Packet{Header: rtp.Header{SequenceNumber: sequence, Timestamp: 7460673 + uint32(fragmentIndex)*2970, Marker: packetIndex == len(packets)-1}, Payload: data}
			sequence++
			if packet.SequenceNumber == 5981 {
				late = packet
				continue
			}
			buffer.push(packet, deliver)
		}
	}
	if late == nil || sequence != 5988 || len(received) != 0 || len(buffer.pkts) == 0 {
		test.Fatal("fixture does not match observed RTP/frame boundaries")
	}
	buffer.gapSince = time.Now().Add(-101 * time.Millisecond)
	keepalive := payloader.Payload(1200, vp8Keepalive)[0]
	buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: sequence, Timestamp: 7469583, Marker: true}, Payload: keepalive}, deliver)
	buffer.push(late, deliver)
	key := [2]uint32{752154365, 4260144682}
	builder := assembler.builds[key]
	if builder == nil || builder.diagnostic.Mask != 5 || len(received) != 0 {
		test.Fatal("expected incomplete carrier mask 101, not delivery")
	}
	if len(buffer.pkts) != 0 || frame.frameValid {
		test.Fatal("gap did not drain or incomplete frame escaped")
	}
	test.Logf("observed_retry2_late_rtp=5981 rejected_after_gap=true fragment_mask=%03b pending=%d remaining_ms=%d", builder.diagnostic.Mask, len(assembler.builds), time.Until(builder.deadline).Milliseconds())
	for index := uint32(1); index < maxPendingMessages; index++ {
		partial, encodeErr := encodeFragments(752154365, index, payload)
		if encodeErr != nil {
			test.Fatal(encodeErr)
		}
		assembler.ingest(partial[0])
	}
	retry, err := encodeFragments(752154365, 4260144700, payload)
	if err != nil {
		test.Fatal(err)
	}
	for _, fragment := range retry {
		assembler.ingest(fragment)
	}
	if len(received) != 0 || assembler.metrics.Capacity != 3 || len(assembler.builds) != 16 {
		test.Fatal("expected complete fresh attempt rejected by full partial-assembly pool")
	}
	test.Log("model_not_claim_of_later_physical_attempt: intact_retry_capacity_drops=3 pending=16 output=0")
	assembler.now = func() time.Time { return time.Now().Add(11 * time.Second) }
	for _, fragment := range retry {
		assembler.ingest(fragment)
	}
	if len(received) != 1 || !bytes.Equal(received[0], payload) {
		test.Fatal("capacity expiry did not restore byte-exact delivery")
	}
}

func TestSavedGapWithoutArrivalDoesNotRelease(test *testing.T) {
	buffer := newReorderBuffer()
	delivered := 0
	deliver := func(*rtp.Packet) { delivered++ }
	buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: 100}}, deliver)
	buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: 102}}, deliver)
	time.Sleep(150 * time.Millisecond)
	if delivered != 1 || len(buffer.pkts) != 1 {
		test.Fatal("accepted source no longer has arrival-driven gap")
	}
	buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: 103}}, deliver)
	if delivered != 3 || len(buffer.pkts) != 0 {
		test.Fatal("arrival did not release expired gap")
	}
}
