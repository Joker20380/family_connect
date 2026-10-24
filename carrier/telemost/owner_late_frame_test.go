package telemost

import (
	"bytes"
	"fmt"
	"testing"
	"time"

	"github.com/pion/rtp"
	"github.com/pion/rtp/codecs"
)

func TestOwnerCompleteLateFrames(test *testing.T) {
	for _, delay := range []time.Duration{358, 381, 474, 483, 540} {
		for _, start := range []uint16{337, 65534} {
			test.Run(fmt.Sprintf("%dms-start%d", delay, start), func(test *testing.T) {
				buffer := newReorderBuffer()
				var frame vp8FrameState
				var received [][]byte
				assembler := newReassembler(2, func(data []byte) { received = append(received, bytes.Clone(data)) })
				deliver := func(packet *rtp.Packet) {
					if fragment, valid := decodeVP8Frame(frame.process(packet)); valid {
						assembler.ingest(fragment)
					}
				}
				keepalive := func(sequence uint16) {
					payloader := &codecs.VP8Payloader{}
					buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: sequence, Timestamp: uint32(sequence), Marker: true}, Payload: payloader.Payload(800, vp8Keepalive)[0]}, deliver)
				}
				payload := bytes.Repeat([]byte{0x53}, 2000)
				fragments, err := encodeFragments(7, 85, payload)
				if err != nil {
					test.Fatal(err)
				}
				payloader := &codecs.VP8Payloader{}
				packets := payloader.Payload(800, encodeVP8DataFrame(fragments[0]))
				if len(packets) != 3 {
					test.Fatal("fixture must have three packets")
				}
				push := func(index int) {
					buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: start + 1 + uint16(index), Timestamp: 894003, Marker: index == 2}, Payload: packets[index]}, deliver)
				}
				keepalive(start)
				push(2)
				buffer.gapSince = time.Now().Add(-delay * time.Millisecond)
				keepalive(start + 4)
				push(0)
				push(1)
				push(1)
				if len(received) != 1 || !bytes.Equal(received[0], payload) {
					test.Fatal("all three packets arrived but complete carrier message was lost")
				}
				if len(buffer.pkts) != 0 || !buffer.gapSince.IsZero() {
					test.Fatal("completed frame retained state")
				}
			})
		}
	}
}

func TestOwnerGapBoundAndMemory(test *testing.T) {
	buffer := newReorderBuffer()
	var count int
	deliver := func(*rtp.Packet) { count++ }
	push := func(sequence uint16) { buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: sequence}}, deliver) }
	push(100)
	push(102)
	buffer.gapSince = time.Now().Add(-800 * time.Millisecond)
	push(103)
	if count != 3 || len(buffer.pkts) != 0 {
		test.Fatal("permanent loss stalled past bounded deadline")
	}
	for sequence := uint16(105); sequence < 30000; sequence += 2 {
		push(sequence)
		if len(buffer.pkts) > reorderWindow || len(buffer.free) > reorderWindow+1 {
			test.Fatal("reorder memory bound exceeded")
		}
	}
	buffer.gapSince = time.Now().Add(-800 * time.Millisecond)
	push(30000)
	if len(buffer.pkts) >= reorderWindow {
		test.Fatal("expired gap prevented progress")
	}
}

func TestOwnerWindowPressureDrainsCompleteFrames(test *testing.T) {
	for _, start := range []uint16{100, 65500} {
		test.Run(fmt.Sprintf("start%d", start), func(test *testing.T) {
			buffer := newReorderBuffer()
			var frame vp8FrameState
			var received [][]byte
			assembler := newReassembler(2, func(data []byte) { received = append(received, bytes.Clone(data)) })
			deliver := func(packet *rtp.Packet) {
				if fragment, valid := decodeVP8Frame(frame.process(packet)); valid {
					assembler.ingest(fragment)
				}
			}
			keepalive := func(offset uint16) {
				payloader := &codecs.VP8Payloader{}
				sequence := start + offset
				buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: sequence, Timestamp: uint32(sequence), Marker: true}, Payload: payloader.Payload(800, vp8Keepalive)[0]}, deliver)
			}
			keepalive(0)
			payload := bytes.Repeat([]byte{0x5a}, 2000)
			fragments, err := encodeFragments(7, 222, payload)
			if err != nil {
				test.Fatal(err)
			}
			payloader := &codecs.VP8Payloader{}
			packets := payloader.Payload(800, encodeVP8DataFrame(fragments[0]))
			if len(packets) != 3 {
				test.Fatal("fixture must have three packets")
			}
			for index, payload := range packets {
				buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: start + 2 + uint16(index), Timestamp: 2723523, Marker: index == 2}, Payload: payload}, deliver)
			}
			for offset := uint16(5); offset <= 256; offset++ {
				keepalive(offset)
			}
			if len(buffer.pkts) != 255 {
				test.Fatal("fixture failed to fill bounded pending range")
			}
			keepalive(257)
			keepalive(1)
			if len(received) != 1 || !bytes.Equal(received[0], payload) {
				test.Fatal("window pressure discarded an already complete queued frame")
			}
			if len(buffer.pkts) != 0 || !buffer.gapSince.IsZero() || len(buffer.free) > reorderWindow+1 {
				test.Fatal("pressure drain leaked or exceeded bounded state")
			}
		})
	}
}
