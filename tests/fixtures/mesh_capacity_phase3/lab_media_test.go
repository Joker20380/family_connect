package telemost

import (
	"bytes"
	"context"
	"github.com/pion/interceptor"
	"github.com/pion/rtp"
	"github.com/pion/rtp/codecs"
	"github.com/pion/webrtc/v4/pkg/media"
	"testing"
	"time"
)

func TestLabMediaClock(test *testing.T) {
	for _, policy := range []string{"A", "B"} {
		test.Run(policy, func(test *testing.T) {
			labMedia.policy = policy
			defer func() { labMedia.policy = "" }()
			track, err := newVP8Track()
			if err != nil {
				test.Fatal(err)
			}
			var packets []*rtp.Packet
			writer := interceptor.RTPWriterFunc(func(header *rtp.Header, payload []byte, _ interceptor.Attributes) (int, error) {
				packets = append(packets, (&rtp.Packet{Header: *header, Payload: payload}).Clone())
				return header.MarshalSize() + len(payload), nil
			})
			if _, err = track.Bind(lossTrackContext{writer: lossTrackWriter{writer}}); err != nil {
				test.Fatal(err)
			}
			defer track.Unbind(lossTrackContext{})
			session := &Session{track: track}
			start := time.Now()
			durations := []time.Duration{0, 2 * time.Second, 2*time.Second + 2*time.Millisecond, 2*time.Second + 3333333*time.Nanosecond, 25 * time.Hour, 25*time.Hour + 2*time.Second}
			var first uint32
			for index, elapsed := range durations {
				before := len(packets)
				if err = session.labWriteSampleAt(media.Sample{Data: vp8Keepalive, Duration: vp8FrameDuration}, start.Add(elapsed)); err != nil {
					test.Fatal(err)
				}
				if len(packets) != before+1 {
					test.Fatal("empty timestamp advance emitted RTP")
				}
				stamp := packets[before].Timestamp
				if index == 0 {
					first = stamp
				}
				expected := uint32(index * 2970)
				if policy == "B" {
					expected = uint32(uint64(elapsed) * 90000 / uint64(time.Second))
				}
				actual := stamp - first
				if actual != expected && !(policy == "B" && expected-actual == 1) {
					test.Fatalf("elapsed=%s ticks=%d expected=%d", elapsed, actual, expected)
				}
				if index > 0 && packets[before].SequenceNumber != packets[before-1].SequenceNumber+1 {
					test.Fatal("empty advance consumed sequence")
				}
			}
			test.Logf("policy=%s idle2s delta=%d ticks;25h wrap and fractional ticks verified", policy, packets[1].Timestamp-packets[0].Timestamp)
		})
	}
}

func TestLabMediaKeepaliveBoundaries(test *testing.T) {
	for _, fault := range []string{"none", "reorder", "duplicate", "loss_then_retry", "close_partial"} {
		test.Run(fault, func(test *testing.T) {
			payload := bytes.Repeat([]byte{57}, 16448)
			fragments, _ := encodeFragments(1, 123, payload)
			packetizer := rtp.NewPacketizerWithOptions(1200, &codecs.VP8Payloader{}, rtp.NewFixedSequencer(65530), 90000, rtp.WithTimestamp(0xfffffff0))
			var packets []*rtp.Packet
			for _, fragment := range fragments {
				packets = append(packets, packetizer.Packetize(encodeVP8DataFrame(fragment), 180)...)
				packets = append(packets, packetizer.Packetize(vp8Keepalive, 180000)...)
			}
			var received [][]byte
			assembler := newReassembler(2, func(data []byte) { received = append(received, bytes.Clone(data)) })
			buffer := newReorderBuffer()
			state := vp8FrameState{}
			deliver := func(packet *rtp.Packet) {
				if frame := state.process(packet); frame != nil {
					if fragment, ok := decodeVP8Frame(frame); ok {
						assembler.ingest(fragment)
					}
				}
			}
			if fault == "reorder" {
				packets[2], packets[3] = packets[3], packets[2]
			}
			for index, packet := range packets {
				if fault == "close_partial" && index == 3 {
					break
				}
				if fault == "loss_then_retry" && index == 2 {
					continue
				}
				if fault == "loss_then_retry" && index == 3 {
					buffer.gapSince = time.Now().Add(-time.Second)
				}
				buffer.push(packet, deliver)
				if fault == "duplicate" {
					buffer.push(packet, deliver)
				}
			}
			if fault == "loss_then_retry" {
				for _, fragment := range fragments {
					for _, packet := range packetizer.Packetize(encodeVP8DataFrame(fragment), 180) {
						buffer.push(packet, deliver)
					}
				}
			}
			if fault == "close_partial" {
				if len(received) != 0 || len(state.frameBuf) > maxAssembledFrameSize {
					test.Fatal("partial delivered or unbounded")
				}
				return
			}
			if len(received) != 1 || !bytes.Equal(received[0], payload) {
				test.Fatalf("delivery=%d", len(received))
			}
			test.Logf("%s: 3 fragments, interleaved keepalive, sequence/timestamp wrap, byte exact", fault)
		})
	}
}

func TestLabMediaReliableCandidate(test *testing.T) {
	labMedia.policy = "B"
	defer func() { labMedia.policy = "" }()
	TestPacingBoundPionRSByteExact(test)
}

func TestLabMediaCancel(test *testing.T) {
	labMedia.policy = "B"
	defer func() { labMedia.policy = "" }()
	ctx, cancel := context.WithCancel(context.Background())
	left, right := headLossPair(test, ctx, 0, "none")
	left.startWorker(left.writerLoop)
	right.startWorker(right.writerLoop)
	done := make(chan struct{})
	go func() {
		defer close(done)
		for index := 0; index < 100; index++ {
			if left.SendContext(ctx, bytes.Repeat([]byte{1}, 16384)) != nil {
				return
			}
		}
	}()
	cancel()
	left.Close()
	right.Close()
	select {
	case <-done:
	case <-time.After(time.Second):
		test.Fatal("cancel blocked")
	}
}
