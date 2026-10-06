package telemost

import (
	"bytes"
	"context"
	"encoding/binary"
	"fmt"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/reliablestream"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/pion/interceptor"
	"github.com/pion/rtp"
	"github.com/pion/rtp/codecs"
	"github.com/pion/webrtc/v4"
)

type lossTrackContext struct{ writer webrtc.TrackLocalWriter }

func (binding lossTrackContext) CodecParameters() []webrtc.RTPCodecParameters {
	return []webrtc.RTPCodecParameters{{RTPCodecCapability: webrtc.RTPCodecCapability{MimeType: webrtc.MimeTypeVP8, ClockRate: 90000}, PayloadType: 96}}
}
func (binding lossTrackContext) HeaderExtensions() []webrtc.RTPHeaderExtensionParameter { return nil }
func (binding lossTrackContext) SSRC() webrtc.SSRC                                      { return 1 }
func (binding lossTrackContext) SSRCRetransmission() webrtc.SSRC                        { return 0 }
func (binding lossTrackContext) SSRCForwardErrorCorrection() webrtc.SSRC                { return 0 }
func (binding lossTrackContext) WriteStream() webrtc.TrackLocalWriter                   { return binding.writer }
func (binding lossTrackContext) ID() string                                             { return "loss-test" }
func (binding lossTrackContext) RTCPReader() interceptor.RTCPReader                     { return nil }

type lossTrackWriter struct{ writer interceptor.RTPWriter }

func (writer lossTrackWriter) WriteRTP(header *rtp.Header, payload []byte) (int, error) {
	return writer.writer.Write(header, payload, nil)
}
func (writer lossTrackWriter) Write(raw []byte) (int, error) {
	packet := &rtp.Packet{}
	if err := packet.Unmarshal(raw); err != nil {
		return 0, err
	}
	return writer.WriteRTP(&packet.Header, packet.Payload)
}

type headAttempt struct {
	message uint32
	point   sessiontrace.Boundary
	packets []*rtp.Packet
}

type headLossEndpoint struct {
	dropACK atomic.Bool
	*Session
	peer         *headLossEndpoint
	sendMu       sync.Mutex
	receiveMu    sync.Mutex
	reorder      *reorderBuffer
	frame        vp8FrameState
	observer     rtpBoundary
	packets      []*rtp.Packet
	attempts     []headAttempt
	head         uint64
	fault        string
	hold         []byte
	late         []*rtp.Packet
	dropDelivery bool
}

func headLossPair(test *testing.T, ctx context.Context, head uint64, fault string) (*headLossEndpoint, *headLossEndpoint) {
	test.Helper()
	points := make([]*headLossEndpoint, 2)
	for index := range points {
		trace := sessiontrace.New(strings.Repeat(fmt.Sprint(index+1), 64), nil)
		session, err := New(sessiontrace.With(ctx, trace), Config{RoomURL: "local-test"})
		if err != nil {
			test.Fatal(err)
		}
		point := &headLossEndpoint{Session: session, reorder: newReorderBuffer(), head: head}
		point.reorder.trace, point.frame.trace = trace, trace
		point.observer = rtpBoundary{trace: trace, stage: "rtp_received", direction: "rx"}
		session.reassembler.onData = func(data []byte) {
			sequence, known := reliablestream.DataSequencePrefix(data, uint32(len(data)))
			if known && sequence == point.head && point.dropDelivery {
				point.dropDelivery = false
				if point.fault == "late_message" {
					point.hold = bytes.Clone(data)
				}
				return
			}
			session.deliver(data)
			if known && sequence == point.head && point.hold != nil {
				session.deliver(point.hold)
				point.hold = nil
			}
		}
		track, err := newVP8Track()
		if err != nil {
			test.Fatal(err)
		}
		session.track = track
		boundary, _ := (&boundaryFactory{trace: trace, writes: &session.rtpWrites}).NewInterceptor("")
		writer := boundary.BindLocalStream(&interceptor.StreamInfo{MimeType: webrtc.MimeTypeVP8}, interceptor.RTPWriterFunc(func(header *rtp.Header, payload []byte, _ interceptor.Attributes) (int, error) {
			point.packets = append(point.packets, (&rtp.Packet{Header: *header, Payload: payload}).Clone())
			return header.MarshalSize() + len(payload), nil
		}))
		if _, err := track.Bind(lossTrackContext{writer: lossTrackWriter{writer}}); err != nil {
			test.Fatal(err)
		}
		session.pubReady.Store(true)
		session.subReady.Store(true)
		points[index] = point
	}
	points[0].peer, points[1].peer = points[1], points[0]
	points[0].fault = fault
	if fault == "logical" || fault == "late_message" {
		points[1].fault, points[1].dropDelivery = fault, true
	}
	return points[0], points[1]
}

func (point *headLossEndpoint) receive(packets []*rtp.Packet) {
	point.receiveMu.Lock()
	defer point.receiveMu.Unlock()
	for _, packet := range packets {
		point.observer.packet(&packet.Header, packet.Payload, "ok")
		point.reorder.push(packet, func(ordered *rtp.Packet) {
			if data := point.frame.process(ordered); data != nil {
				if fragment, valid := decodeVP8Frame(data); valid {
					boundary := fragmentBoundary(fragment)
					boundary.Direction, boundary.Stage, boundary.Result = "rx", "vp8_reassembled", "ok"
					point.cfg.Trace.Boundary(boundary)
					point.reassembler.ingest(fragment)
				}
			}
		})
	}
}

func (point *headLossEndpoint) SendContext(ctx context.Context, data []byte) error {
	point.sendMu.Lock()
	defer point.sendMu.Unlock()
	if len(data) >= reliablestream.HeaderSize && data[4] == 3 && point.dropACK.Load() {
		return nil
	}
	sequence, known := reliablestream.DataSequencePrefix(data, uint32(len(data)))
	isHead := known && sequence == point.head
	point.packets = nil
	if err := point.Session.SendContext(ctx, data); err != nil {
		return err
	}
	message := point.msgID.Load()
	for len(point.sendQueue) > 0 {
		frame := <-point.sendQueue
		if isHead && point.fault == "carrier" && len(point.attempts) == 0 {
			continue
		}
		point.writeVP8Sample(frame.data, frame.point)
	}
	packets := point.packets
	if isHead {
		point.attempts = append(point.attempts, headAttempt{message: message, point: sessiontrace.AttemptFrom(ctx), packets: packets})
		if len(point.attempts) == 1 {
			switch point.fault {
			case "frame":
				headTimestamp := packets[0].Timestamp
				for len(packets) > 0 && packets[0].Timestamp == headTimestamp {
					packets = packets[1:]
				}
			case "late_rtp":
				point.late, packets = packets, nil
			}
		}
	}
	if isHead && point.fault == "duplicate" {
		point.peer.dropACK.Store(len(point.attempts) == 1)
	}
	point.peer.receive(packets)
	if isHead && len(point.attempts) == 1 && (point.fault == "frame" || point.fault == "late_rtp") {
		point.peer.receiveMu.Lock()
		point.peer.reorder.gapSince = time.Now().Add(-101 * time.Millisecond)
		point.peer.receiveMu.Unlock()
	}
	if isHead && len(point.attempts) > 1 && point.late != nil {
		point.peer.receive(point.late)
		point.late = nil
	}
	return nil
}

func waitHeadState(test *testing.T, ctx context.Context, condition func() bool) {
	test.Helper()
	for !condition() {
		select {
		case <-ctx.Done():
			test.Fatal("state did not converge", ctx.Err())
		case <-time.After(time.Millisecond):
		}
	}
}

func TestHeadLossBoundPionAttempts(test *testing.T) {
	for _, head := range []uint64{48, 58} {
		for _, fault := range []string{"logical", "carrier", "frame", "duplicate", "late_message", "late_rtp"} {
			test.Run(fmt.Sprintf("DATA%d/%s", head, fault), func(test *testing.T) {
				ctx, cancel := context.WithTimeout(context.Background(), 12*time.Second)
				defer cancel()
				leftEndpoint, rightEndpoint := headLossPair(test, ctx, head, fault)
				config := reliablestream.DefaultConfig()
				left, err := reliablestream.New(sessiontrace.With(ctx, leftEndpoint.cfg.Trace), leftEndpoint, config)
				if err != nil {
					test.Fatal(err)
				}
				defer left.Close()
				right, err := reliablestream.New(sessiontrace.With(ctx, rightEndpoint.cfg.Trace), rightEndpoint, config)
				if err != nil {
					test.Fatal(err)
				}
				defer right.Close()
				for sequence := uint64(0); sequence < head; sequence++ {
					if err := left.SendContext(ctx, []byte{byte(sequence)}); err != nil {
						test.Fatal(err)
					}
					if data, err := right.Recv(ctx); err != nil || !bytes.Equal(data, []byte{byte(sequence)}) {
						test.Fatal("warmup", err)
					}
				}
				waitHeadState(test, ctx, func() bool { return left.Stats().Flow.SendBase == head })
				for index := 0; index < config.SendWindow; index++ {
					if err := left.SendContext(ctx, bytes.Repeat([]byte{byte(index + 1)}, config.Payload)); err != nil {
						test.Fatal(err)
					}
				}
				if fault == "duplicate" {
					waitHeadState(test, ctx, func() bool { return right.Stats().Flow.ReceiveMask == 255 })
				} else {
					waitHeadState(test, ctx, func() bool { return right.Stats().Flow.ReceiveMask == 254 && left.Stats().Flow.ACKMask == 254 })
					if right.Stats().Flow.Buffered != 7 || right.Stats().Flow.ReceiveNext != head {
						test.Fatal("missing head not held")
					}
				}
				for index := 0; index < config.SendWindow; index++ {
					data, err := right.Recv(ctx)
					if err != nil || !bytes.Equal(data, bytes.Repeat([]byte{byte(index + 1)}, config.Payload)) {
						test.Fatal("release/order", index, err)
					}
				}
				waitHeadState(test, ctx, func() bool { return left.Stats().Flow.SendBase == head+8 })
				if err := left.SendContext(ctx, []byte("same-session-progress")); err != nil {
					test.Fatal(err)
				}
				if data, err := right.Recv(ctx); err != nil || string(data) != "same-session-progress" {
					test.Fatal("duplicate delivery/deadlock", err)
				}
				leftEndpoint.sendMu.Lock()
				attempts := append([]headAttempt(nil), leftEndpoint.attempts...)
				leftEndpoint.sendMu.Unlock()
				if len(attempts) != 2 {
					test.Fatalf("expected original + one retry, got %d", len(attempts))
				}
				for index, attempt := range attempts {
					if !attempt.point.AttemptKnown || attempt.point.Attempt != uint32(index) || attempt.point.DataSequence != head {
						test.Fatal("logical/attempt identity lost", attempt.point)
					}
				}
				original, retry := attempts[0], attempts[1]
				if original.message == retry.message || len(retry.packets) < 3 {
					test.Fatal("retry lacks new actual carrier/RTP emission")
				}
				if len(original.packets) > 0 && (original.packets[0].Timestamp == retry.packets[0].Timestamp || !seqLess(original.packets[len(original.packets)-1].SequenceNumber, retry.packets[0].SequenceNumber)) {
					test.Fatal("RTP identity reuse")
				}
				expectedGaps := uint64(1)
				if fault == "duplicate" {
					expectedGaps = 0
				}
				if right.Stats().RecoveredGaps != expectedGaps || left.Stats().Terminal != "" || right.Stats().Terminal != "" || left.Stats().Resets != 0 {
					test.Fatal("recovery required session reset")
				}
				if (fault == "late_message" || fault == "duplicate") && right.Stats().Duplicates == 0 {
					test.Fatal("late original not safely deduplicated")
				}
				test.Logf("same DATA%d attempts0/1 message IDs distinct; bound Pion RTP=%d/%d; ACK/base=%d; no restart", head, len(original.packets), len(retry.packets), left.Stats().Flow.SendBase)
			})
		}
	}
}

func TestUnboundWriteSampleIsNotRTPEmission(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	trace := sessiontrace.New(strings.Repeat("a", 64), nil)
	session, err := New(ctx, Config{RoomURL: "local-test", Trace: trace})
	if err != nil {
		test.Fatal(err)
	}
	defer session.Close()
	session.track, err = newVP8Track()
	if err != nil {
		test.Fatal(err)
	}
	session.writeVP8Sample(vp8Keepalive)
	if session.Stats().Media.SamplesWritten != 1 || session.rtpWrites.Load() != 0 {
		test.Fatal("dependency precondition changed")
	}
	points := trace.Snapshot().Boundaries.Events
	if len(points) != 1 || points[0].Stage != "carrier_written" || points[0].Result != "no_rtp" {
		test.Fatal("false emission claim", points)
	}
}

func TestNineFreshBoundMediaIdentitiesForSameDATA(test *testing.T) {
	for _, head := range []uint64{48, 58} {
		test.Run(fmt.Sprint(head), func(test *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
			defer cancel()
			sender, receiver := headLossPair(test, ctx, head, "none")
			defer sender.Close()
			defer receiver.Close()
			data := diagnosticData()
			binary.BigEndian.PutUint64(data[40:], head)
			for attempt := uint32(0); attempt <= 8; attempt++ {
				if err := sender.SendContext(sessiontrace.WithAttempt(ctx, head, attempt), data); err != nil {
					test.Fatal(err)
				}
				received, err := receiver.Recv(ctx)
				if err != nil || !bytes.Equal(received, data) {
					test.Fatal("fresh carrier attempt suppressed", attempt, err)
				}
				current := sender.attempts[attempt]
				count := 0
				for _, point := range sender.cfg.Trace.Snapshot().Boundaries.Events {
					if point.Stage == "rtp_written" && point.Message == current.message && point.MessageKnown {
						if !point.AttemptKnown || point.Attempt != attempt || !point.DataKnown || point.DataSequence != head || point.Total != 3 || !point.FrameKnown || point.Result != "ok" || point.Packets == 0 || uint16(point.LastRTP-point.FirstRTP)+1 != uint16(point.Packets) {
							test.Fatal("incomplete actual RTP boundary", point)
						}
						count++
					}
				}
				if count != 3 {
					test.Fatal("expected three fragment/frame RTP boundaries", attempt, count)
				}
				if attempt > 0 {
					previous := sender.attempts[attempt-1]
					var previousVP8, currentVP8 codecs.VP8Packet
					if _, err := previousVP8.Unmarshal(previous.packets[0].Payload); err != nil {
						test.Fatal(err)
					}
					if _, err := currentVP8.Unmarshal(current.packets[0].Payload); err != nil {
						test.Fatal(err)
					}
					if currentVP8.I != 1 || currentVP8.PictureID != (previousVP8.PictureID+3)&0x7fff {
						test.Fatal("VP8 PictureID did not advance for three new frames", attempt)
					}
					if current.message == previous.message || current.packets[0].Timestamp == previous.packets[0].Timestamp || current.packets[0].SequenceNumber != previous.packets[len(previous.packets)-1].SequenceNumber+1 {
						test.Fatal("lower identity reused", attempt)
					}
				}
			}
		})
	}
}
