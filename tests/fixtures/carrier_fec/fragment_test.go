package telemost

import (
	"bytes"
	"context"
	"encoding/binary"
	"github.com/Joker20380/family_connect/carrier/reliablestream"
	"math/rand"
	"sync"
	"testing"
	"time"

	"github.com/pion/interceptor"
	"github.com/pion/rtp"
	"github.com/pion/webrtc/v4/pkg/media"
)

func labTestPair(mode string) (*labFragmentCodec, *labFragmentCodec) {
	config := labFragmentConfig{Mode: mode, Epoch: [16]byte{3, 4, 5}}
	left := newLabFragmentCodec(config)
	config.Direction = 1
	return left, newLabFragmentCodec(config)
}
func labBody(size int) []byte {
	body := make([]byte, size)
	for index := range body {
		body[index] = byte(index*71 + index/256)
	}
	return body
}

func TestFragmentSizesPacketization(test *testing.T) {
	for _, mode := range []string{"S", "SF"} {
		test.Run(mode, func(test *testing.T) {
			left, right := labTestPair(mode)
			sizes := []int{0, 1, 32, 64, 1023, 1024, 1025, 8191, 8192, 8193, 16383, 16384, 16448, 65535, 65536}
			for index := 1; index <= 16; index++ {
				sizes = append(sizes, index*4096)
			}
			for index, size := range sizes {
				body := labBody(size)
				parts, err := left.encode(context.Background(), 12, uint32(index+1), body)
				if err != nil {
					test.Fatal(err)
				}
				var output []byte
				for part := len(parts) - 1; part >= 0; part-- {
					if result := right.ingest(parts[part]); result != nil {
						if output != nil {
							test.Fatal("double delivery")
						}
						output = result
					}
					right.ingest(parts[part])
				}
				if output == nil || !bytes.Equal(output, body) {
					test.Fatalf("size=%d exact=false", size)
				}
				if right.snapshot().Held != 0 || right.snapshot().Pending != 0 {
					test.Fatal("retained completed")
				}
			}
			if _, err := left.encode(context.Background(), 1, 99, make([]byte, 65537)); err == nil {
				test.Fatal("oversize accepted")
			}
		})
	}
	for _, mode := range []string{"L", "S", "SF"} {
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
		codec, _ := labTestPair(mode)
		parts, _ := codec.encode(context.Background(), 2, 1, labBody(16448))
		if mode == "L" {
			parts, _ = encodeFragments(2, 1, labBody(16448))
		}
		maximum := 0
		counts := []int{}
		for _, part := range parts {
			before := len(packets)
			if err = track.WriteSample(media.Sample{Data: encodeVP8DataFrame(part), Duration: vp8FrameDuration}); err != nil {
				test.Fatal(err)
			}
			count := len(packets) - before
			counts = append(counts, count)
			if mode != "L" && count != 1 {
				test.Fatal("not independent single RTP")
			}
		}
		for _, packet := range packets {
			maximum = max(maximum, packet.MarshalSize())
			if packet.MarshalSize() > 1200 {
				test.Fatal("MTU")
			}
		}
		track.Unbind(lossTrackContext{})
		test.Logf("PACKETIZATION mode=%s original=16448 parts=%d RTP=%d per_part=%v max_clear_RTP=%d conservative_IPv6_SRTCP16_extension8=%d timestamp_step=2970", mode, len(parts), len(packets), counts, maximum, maximum+48+16+8)
	}
}

func TestFragmentErasureBounds(test *testing.T) {
	for _, size := range []int{1025, 8192, 8193, 16448, 65536} {
		for removed := 0; removed <= 3; removed++ {
			left, right := labTestPair("SF")
			body := labBody(size)
			parts, _ := left.encode(context.Background(), 1, 1, body)
			var output []byte
			for _, part := range parts {
				if int(part[42]) < removed {
					continue
				}
				if result := right.ingest(part); result != nil {
					output = result
				}
			}
			if removed <= 2 && !bytes.Equal(output, body) {
				test.Fatalf("size=%d erased=%d", size, removed)
			}
			if removed == 3 && output != nil {
				test.Fatal("beyond capacity returned")
			}
		}
	}
	for first := 0; first < 10; first++ {
		for second := first; second < 10; second++ {
			left, right := labTestPair("SF")
			body := labBody(8192)
			parts, _ := left.encode(context.Background(), 1, 1, body)
			var output []byte
			for index, part := range parts {
				if index != first && index != second {
					if result := right.ingest(part); result != nil {
						output = result
					}
				}
			}
			if !bytes.Equal(output, body) {
				test.Fatalf("erasures %d/%d", first, second)
			}
		}
	}
	for _, position := range []int{0, 3, 7} {
		left, right := labTestPair("S")
		parts, _ := left.encode(context.Background(), 1, 1, labBody(8192))
		for index, part := range parts {
			if index != position && right.ingest(part) != nil {
				test.Fatal("partial S delivery")
			}
		}
		right.now = func() time.Time { return time.Now().Add(11 * time.Second) }
		right.prune()
		if right.snapshot().Expired != 1 || right.snapshot().Held != 0 {
			test.Fatal("silent expiry")
		}
	}
	left, right := labTestPair("SF")
	parts, _ := left.encode(context.Background(), 1, 1, labBody(16384))
	for _, part := range parts {
		if binary.BigEndian.Uint16(part[40:]) == 1 && right.ingest(part) != nil {
			test.Fatal("absent group completed")
		}
	}
}

func TestFragmentInvalidDuplicateBounds(test *testing.T) {
	left, right := labTestPair("SF")
	body := labBody(8192)
	parts, _ := left.encode(context.Background(), 1, 1, body)
	right.ingest(parts[0])
	right.ingest(parts[0])
	if right.snapshot().Pending != 1 || right.snapshot().Duplicates != 1 {
		test.Fatal("duplicate poisoned")
	}
	for _, offset := range []int{0, 4, 5, 6, 7, 8, 24, 28, 32, 36, 40, 42, 43, 44, 46, 48, 52, 64} {
		_, receiver := labTestPair("SF")
		broken := bytes.Clone(parts[0])
		broken[offset] ^= 0xff
		if receiver.ingest(broken) != nil || receiver.snapshot().Held != 0 {
			test.Fatalf("invalid allocated offset=%d", offset)
		}
	}
	for size := 0; size < labHeader; size++ {
		right.ingest(parts[0][:size])
	}
	right.ingest(make([]byte, 100000))
	conflict := bytes.Clone(parts[0])
	conflict[64] ^= 1
	binary.BigEndian.PutUint32(conflict[48:], labPartCRC(conflict))
	right.ingest(conflict)
	if right.snapshot().Conflicts != 1 || right.snapshot().Held != 0 {
		test.Fatal("conflict accepted")
	}
	_, receiver := labTestPair("SF")
	for index, part := range parts {
		if index == 0 {
			part = conflict
		}
		receiver.ingest(part)
	}
	if receiver.snapshot().MessagesCompleted != 0 || receiver.snapshot().CRCFailures == 0 {
		test.Fatal("corrupt reconstruction")
	}
	_, receiver = labTestPair("S")
	for message := uint32(1); message <= 100; message++ {
		sender, _ := labTestPair("S")
		fragments, _ := sender.encode(context.Background(), 1, message, labBody(65536))
		receiver.ingest(fragments[0])
	}
	if receiver.snapshot().Pending != 16 || receiver.snapshot().Held > labHeldLimit || receiver.snapshot().Capacity == 0 {
		test.Fatal("unbounded pending")
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if _, err := left.encode(ctx, 1, 2, body); err == nil {
		test.Fatal("cancel")
	}
	var wait sync.WaitGroup
	for index := 0; index < 4; index++ {
		wait.Add(1)
		go func() {
			defer wait.Done()
			for count := 0; count < 40; count++ {
				receiver.ingest(parts[0])
				receiver.snapshot()
				receiver.prune()
			}
		}()
	}
	receiver.close()
	wait.Wait()
	if receiver.snapshot().Held != 0 || receiver.snapshot().Pending != 0 || !receiver.snapshot().Closed {
		test.Fatal("close retained")
	}
}

func TestFragmentSeededPacketFaults(test *testing.T) {
	for _, seed := range []int64{11, 29, 47} {
		for _, burst := range []bool{false, true} {
			for _, mode := range []string{"L", "S", "SF"} {
				random := rand.New(rand.NewSource(seed))
				left, right := labTestPair(mode)
				completed, missing, rawLoss, packetsCount := 0, 0, 0, 0
				var delivered []byte
				legacy := newReassembler(2, func(payload []byte) { delivered = payload })
				var channelUntil time.Duration
				clock := time.Duration(0)
				for message := uint32(1); message <= 24; message++ {
					body := labBody(16448)
					parts, _ := left.encode(context.Background(), 1, message, body)
					if mode == "L" {
						parts, _ = encodeFragments(1, message, body)
					}
					delivered = nil
					for _, part := range parts {
						packetCount := (len(part) + 17 + 1183) / 1184
						lost := false
						for packet := 0; packet < packetCount; packet++ {
							packetsCount++
							clock += time.Duration(min(1200, len(part)+30)+64) * time.Second / 1048576
							if burst {
								if clock >= channelUntil && random.Float64() < 0.02 {
									channelUntil = clock + 6*time.Millisecond
								}
								if clock < channelUntil {
									lost = true
									rawLoss++
								}
							} else if random.Float64() < 0.015 {
								lost = true
								rawLoss++
							}
						}
						clock += vp8SendInterval
						if !lost {
							if mode == "L" {
								legacy.ingest(part)
							} else if result := right.ingest(part); result != nil {
								delivered = result
							}
						}
					}
					if delivered != nil {
						if !bytes.Equal(delivered, body) {
							test.Fatal("fault corrupt")
						}
						completed++
					} else {
						missing++
					}
					left.now = func() time.Time { return time.Now().Add(time.Duration(message) * 11 * time.Second) }
					right.now = left.now
					legacy.now = left.now
					right.prune()
					legacy.prune()
				}
				test.Logf("FAULT seed=%d burst=%t mode=%s messages=24 completed=%d residual=%d RTP=%d raw_drop=%d recovered=%d modeled_seconds=%.6f", seed, burst, mode, completed, missing, packetsCount, rawLoss, right.snapshot().RecoveredSymbols, clock.Seconds())
			}
		}
	}
}

func TestFragmentBoundPionRS(test *testing.T) {
	for _, mode := range []string{"L", "S", "SF"} {
		for _, fault := range []string{"none", "loss", "slow"} {
			test.Run(mode+"/"+fault, func(test *testing.T) {
				ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
				defer cancel()
				left, right := headLossPair(test, ctx, 0, "none")
				defer left.Close()
				defer right.Close()
				if mode != "L" {
					left.labFragments, right.labFragments = labTestPair(mode)
				}
				for _, point := range []*headLossEndpoint{left, right} {
					if err := point.track.Unbind(lossTrackContext{}); err != nil {
						test.Fatal(err)
					}
					boundary, _ := (&boundaryFactory{trace: point.cfg.Trace, writes: &point.rtpWrites}).NewInterceptor("")
					dropped := false
					writer := boundary.BindLocalStream(&interceptor.StreamInfo{MimeType: "video/VP8"}, interceptor.RTPWriterFunc(func(header *rtp.Header, payload []byte, _ interceptor.Attributes) (int, error) {
						if point == left && fault == "loss" && !dropped && len(payload) > 1000 {
							dropped = true
							return header.MarshalSize() + len(payload), nil
						}
						point.peer.receive([]*rtp.Packet{(&rtp.Packet{Header: *header, Payload: payload}).Clone()})
						return header.MarshalSize() + len(payload), nil
					}))
					if _, err := point.track.Bind(lossTrackContext{writer: lossTrackWriter{writer}}); err != nil {
						test.Fatal(err)
					}
					point.startWorker(point.writerLoop)
				}
				config := reliablestream.DefaultConfig()
				config.SendWindow = 32
				config.ReceiveWindow = 32
				sender, err := reliablestream.New(ctx, left.Session, config)
				if err != nil {
					test.Fatal(err)
				}
				defer sender.Close()
				receiver, err := reliablestream.New(ctx, right.Session, config)
				if err != nil {
					test.Fatal(err)
				}
				defer receiver.Close()
				done := make(chan error, 1)
				go func() {
					for index := 0; index < 12; index++ {
						if err := sender.SendContext(ctx, bytes.Repeat([]byte{byte(index)}, 16384)); err != nil {
							done <- err
							return
						}
					}
					done <- nil
				}()
				for index := 0; index < 12; index++ {
					if fault == "slow" {
						time.Sleep(80 * time.Millisecond)
					}
					body, err := receiver.Recv(ctx)
					if err != nil || !bytes.Equal(body, bytes.Repeat([]byte{byte(index)}, 16384)) {
						test.Fatal(index, err, "byte mismatch")
					}
				}
				if err := <-done; err != nil {
					test.Fatal(err)
				}
				deadline := time.Now().Add(3 * time.Second)
				for sender.Stats().SendDepth != 0 && time.Now().Before(deadline) {
					time.Sleep(5 * time.Millisecond)
				}
				if sender.Stats().Terminal != "" || sender.Stats().SendDepth != 0 {
					test.Fatal("terminal/drain", sender.Stats())
				}
				test.Logf("BOUND mode=%s fault=%s bytes=196608 retries=%d", mode, fault, sender.Stats().Retransmissions)
			})
		}
	}
}
