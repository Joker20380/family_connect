package telemost

import (
	"bytes"
	"encoding/binary"
	"testing"
	"time"

	"github.com/pion/rtp"
	"github.com/pion/rtp/codecs"
)

func TestFragmentRoundTrips(t *testing.T) {
	for _, size := range []int{0, 1, 32, 256, 1024, 4096, 16384, 65536} {
		payload := make([]byte, size)
		for index := range payload {
			payload[index] = byte(index)
		}
		var received [][]byte
		assembler := newReassembler(2, func(data []byte) { received = append(received, data) })
		fragments, err := encodeFragments(1, uint32(size), payload)
		if err != nil {
			t.Fatal(err)
		}
		for index := len(fragments) - 1; index >= 0; index-- {
			assembler.ingest(fragments[index])
		}
		for _, fragment := range fragments {
			assembler.ingest(fragment)
		}
		if len(received) != 1 || !bytes.Equal(received[0], payload) {
			t.Fatalf("size %d: wrong result", size)
		}
	}
}

func TestReassemblyBoundsAndTimeout(t *testing.T) {
	called := false
	assembler := newReassembler(2, func([]byte) { called = true })
	clock := time.Now()
	assembler.now = func() time.Time { return clock }
	for message := 0; message < 1000; message++ {
		fragments, _ := encodeFragments(1, uint32(message), make([]byte, 16384))
		assembler.ingest(fragments[0])
	}
	if len(assembler.builds) != maxPendingMessages {
		t.Fatal("pending bound")
	}
	clock = clock.Add(reassemblyTimeout)
	assembler.prune()
	if len(assembler.builds) != 0 || called {
		t.Fatal("timeout")
	}
	fragments, _ := encodeFragments(1, 0, make([]byte, 16384))
	for _, fragment := range fragments {
		assembler.ingest(fragment)
	}
	if called {
		t.Fatal("expired message resurrected")
	}
}

func TestReassemblyRejectsMalformedAndDuplicates(t *testing.T) {
	assembler := newReassembler(2, func([]byte) { t.Error("unexpected delivery") })
	fragments, _ := encodeFragments(1, 1, make([]byte, 16384))
	assembler.ingest(fragments[0])
	assembler.ingest(fragments[0])
	assembler.ingest(fragments[1])
	oversized := make([]byte, fragmentHeaderLen+maxFragmentPayload+1)
	assembler.ingest(oversized)
	for _, offset := range []int{8, 12, 16} {
		broken := append([]byte(nil), fragments[0]...)
		binary.BigEndian.PutUint32(broken[offset:], ^uint32(0))
		assembler.ingest(broken)
	}
	if _, err := encodeFragments(1, 2, make([]byte, MaxMessageSize+1)); err != ErrMessageTooLarge {
		t.Fatal(err)
	}
	if len(assembler.builds) != 0 {
		t.Fatal("invalid allocation")
	}
}

func TestVP8RTPRoundTripAndLoss(t *testing.T) {
	payload := bytes.Repeat([]byte{0, 255, 1}, 2700)
	fragments, _ := encodeFragments(1, 1, payload)
	encoded := encodeVP8DataFrame(fragments[0])
	payloader := &codecs.VP8Payloader{}
	packets := payloader.Payload(1100, encoded)
	for _, drop := range []int{-1, 2} {
		state := vp8FrameState{}
		var output []byte
		for index, packet := range packets {
			if index == drop {
				continue
			}
			result := state.process(&rtp.Packet{Header: rtp.Header{SequenceNumber: uint16(65533 + index), Timestamp: 123, Marker: index == len(packets)-1}, Payload: packet})
			if result != nil {
				output = result
			}
		}
		if drop >= 0 {
			if output != nil {
				t.Fatal("accepted damaged RTP")
			}
			continue
		}
		decoded, ok := decodeVP8Frame(output)
		if !ok || !bytes.Equal(decoded, fragments[0]) {
			t.Fatal("VP8/RTP mismatch")
		}
	}
	encoded[4] ^= 1
	if _, ok := decodeVP8Frame(encoded); ok {
		t.Fatal("accepted bad VP8 prefix")
	}
}

func TestRTPReorderAndBounds(t *testing.T) {
	buffer := newReorderBuffer()
	var received []uint16
	deliver := func(packet *rtp.Packet) { received = append(received, packet.SequenceNumber) }
	for _, sequence := range []uint16{65534, 0, 65535, 1, 1} {
		buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: sequence}}, deliver)
	}
	if len(received) != 4 {
		t.Fatalf("got %d packets", len(received))
	}
	for sequence := uint16(3); sequence < 1000; sequence++ {
		buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: sequence}}, deliver)
	}
	if len(buffer.pkts) > reorderWindow || len(buffer.free) > reorderWindow+1 {
		t.Fatal("unbounded reorder")
	}
}

func FuzzReassembler(f *testing.F) {
	fragments, _ := encodeFragments(1, 1, []byte{0, 255})
	f.Add(fragments[0])
	f.Fuzz(func(t *testing.T, data []byte) {
		assembler := newReassembler(2, func(payload []byte) {
			if len(payload) > MaxMessageSize {
				t.Fatal("oversized")
			}
		})
		assembler.ingest(data)
	})
}
