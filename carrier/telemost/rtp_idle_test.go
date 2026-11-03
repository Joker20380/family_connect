package telemost

import (
	"bytes"
	"context"
	"os"
	"testing"
	"time"

	"github.com/pion/interceptor"
	"github.com/pion/rtp"
	"github.com/pion/rtp/codecs"
	"github.com/pion/webrtc/v4"
)

type idleRTPReader struct {
	ctx      context.Context
	packets  chan []byte
	deadline time.Time
}

func (reader *idleRTPReader) SetReadDeadline(deadline time.Time) error {
	reader.deadline = deadline
	return nil
}

func (reader *idleRTPReader) Read(buffer []byte) (int, interceptor.Attributes, error) {
	var expired <-chan time.Time
	if !reader.deadline.IsZero() {
		timer := time.NewTimer(time.Until(reader.deadline))
		defer timer.Stop()
		expired = timer.C
	}
	select {
	case raw := <-reader.packets:
		return copy(buffer, raw), nil, nil
	case <-expired:
		return 0, nil, os.ErrDeadlineExceeded
	case <-reader.ctx.Done():
		return 0, nil, reader.ctx.Err()
	}
}

func TestVP8IdleGapReleasesFinalCarrierFrame(test *testing.T) {
	for _, first := range []uint16{100, 65534} {
		test.Run(map[uint16]string{100: "ordinary", 65534: "sequence-wrap"}[first], func(test *testing.T) {
			ctx, cancel := context.WithCancel(context.Background())
			session, err := New(ctx, Config{RoomURL: "local-test"})
			if err != nil {
				cancel()
				test.Fatal(err)
			}
			test.Cleanup(func() { cancel(); session.Close() })
			reader := &idleRTPReader{ctx: ctx, packets: make(chan []byte, 2)}
			push := func(sequence uint16, frame []byte) {
				payloader := &codecs.VP8Payloader{}
				payloads := payloader.Payload(1200, frame)
				if len(payloads) != 1 {
					test.Fatal("fixture requires one complete RTP packet")
				}
				raw, err := (&rtp.Packet{Header: rtp.Header{Version: 2, SequenceNumber: sequence,
					Timestamp: uint32(sequence), Marker: true}, Payload: payloads[0]}).Marshal()
				if err != nil {
					test.Fatal(err)
				}
				reader.packets <- raw
			}
			terminal := []byte("final carrier message after a missing RTP packet")
			fragments, err := encodeFragments(session.senderID+1, 1, terminal)
			if err != nil || len(fragments) != 1 {
				test.Fatal("invalid terminal fixture", err)
			}
			push(first, vp8Keepalive)
			push(first+2, encodeVP8DataFrame(fragments[0]))
			session.startWorker(func() { session.readVP8Track(reader) })
			bounded, stop := context.WithTimeout(ctx, 2*time.Second)
			defer stop()
			received, err := session.Recv(bounded)
			if err != nil || !bytes.Equal(received, terminal) {
				test.Fatalf("idle RTP gap stranded the final frame: %v", err)
			}
		})
	}
}

func TestRTPIdleExpiryPreservesNextGapDeadline(test *testing.T) {
	buffer := newReorderBuffer()
	var received []uint16
	deliver := func(packet *rtp.Packet) { received = append(received, packet.SequenceNumber) }
	push := func(sequence uint16) {
		buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: sequence}}, deliver)
	}
	push(100)
	push(102)
	push(104)
	deadline := buffer.deadline()
	buffer.expire(deadline.Add(-time.Nanosecond), deliver)
	if len(received) != 1 {
		test.Fatal("live gap skipped before its deadline")
	}
	buffer.expire(deadline, deliver)
	if len(received) != 2 || received[1] != 102 || !buffer.deadline().Equal(deadline.Add(reorderGapTimeout)) {
		test.Fatal("idle expiry consumed the next gap's recovery budget")
	}
	buffer.expire(deadline, deliver)
	if len(received) != 2 {
		test.Fatal("next gap expired using the previous deadline")
	}
	push(103)
	if len(received) != 4 || received[2] != 103 || received[3] != 104 || !buffer.deadline().IsZero() || len(buffer.pkts) != 0 {
		test.Fatal("recovered gap retained packets or a read deadline")
	}
}

func TestLocalVP8IdleGapDeadline(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	receiver := testSession(test)
	sender, err := webrtc.NewPeerConnection(webrtc.Configuration{})
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() { sender.Close() })
	remote, err := webrtc.NewPeerConnection(webrtc.Configuration{})
	if err != nil {
		test.Fatal(err)
	}
	receiver.pcSub.Store(remote)
	remote.OnTrack(receiver.onSubscriberTrack)
	track, err := webrtc.NewTrackLocalStaticRTP(webrtc.RTPCodecCapability{MimeType: webrtc.MimeTypeVP8}, "idle-gap", "test")
	if err != nil {
		test.Fatal(err)
	}
	if _, err := sender.AddTrack(track); err != nil {
		test.Fatal(err)
	}
	connected := make(chan struct{}, 1)
	sender.OnConnectionStateChange(func(state webrtc.PeerConnectionState) {
		if state == webrtc.PeerConnectionStateConnected {
			select {
			case connected <- struct{}{}:
			default:
			}
		}
	})
	for index, peer := range []*webrtc.PeerConnection{sender, remote} {
		var description webrtc.SessionDescription
		if index == 0 {
			description, err = peer.CreateOffer(nil)
		} else {
			description, err = peer.CreateAnswer(nil)
		}
		if err != nil {
			test.Fatal(err)
		}
		gathered := webrtc.GatheringCompletePromise(peer)
		if err := peer.SetLocalDescription(description); err != nil {
			test.Fatal(err)
		}
		select {
		case <-gathered:
		case <-ctx.Done():
			test.Fatal(ctx.Err())
		}
		other := []*webrtc.PeerConnection{remote, sender}[index]
		if err := other.SetRemoteDescription(*peer.LocalDescription()); err != nil {
			test.Fatal(err)
		}
	}
	select {
	case <-connected:
	case <-ctx.Done():
		test.Fatal(ctx.Err())
	}
	for _, sequence := range []uint16{100, 102} {
		payload := []byte("last complete frame without a following RTP packet")
		fragments, err := encodeFragments(receiver.senderID+1, uint32(sequence), payload)
		if err != nil || len(fragments) != 1 {
			test.Fatal("invalid frame fixture", err)
		}
		payloader := &codecs.VP8Payloader{}
		packets := payloader.Payload(1200, encodeVP8DataFrame(fragments[0]))
		if len(packets) != 1 {
			test.Fatal("fixture requires a single RTP packet")
		}
		if err := track.WriteRTP(&rtp.Packet{Header: rtp.Header{Version: 2, SequenceNumber: sequence,
			Timestamp: uint32(sequence) * 3000, Marker: true}, Payload: packets[0]}); err != nil {
			test.Fatal(err)
		}
		bounded, stop := context.WithTimeout(ctx, 2*time.Second)
		received, err := receiver.Recv(bounded)
		stop()
		if err != nil || !bytes.Equal(received, payload) {
			test.Fatalf("real Pion RTP read deadline failed at sequence %d: %v", sequence, err)
		}
	}
}
