package telemost

import (
	"bytes"
	"context"
	"fmt"
	"github.com/Joker20380/family_connect/carrier/localwrite"
	"github.com/Joker20380/family_connect/carrier/packetpace"
	"github.com/Joker20380/family_connect/carrier/reliablestream"
	"github.com/pion/interceptor"
	"github.com/pion/rtp"
	"testing"
	"time"
)

func TestLabMediaOFFWindow32(test *testing.T) {
	labMedia.policy = "B"
	defer func() { labMedia.policy = "" }()
	for _, fault := range []string{"none", "loss", "reorder", "slow"} {
		test.Run(fault, func(test *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
			defer cancel()
			ctx = localwrite.WithCompletion(ctx)
			left, right := headLossPair(test, ctx, 0, "none")
			defer left.Close()
			defer right.Close()
			for _, point := range []*headLossEndpoint{left, right} {
				if err := point.track.Unbind(lossTrackContext{}); err != nil {
					test.Fatal(err)
				}
				pace := packetpace.New(ctx, false)
				point.cfg.PacketPacing = pace
				factory := &pacedBoundaryFactory{boundary: &boundaryFactory{trace: point.cfg.Trace, writes: &point.rtpWrites}, pace: pace}
				observer, _ := factory.NewInterceptor("")
				var pending *rtp.Packet
				dropped := false
				writer := observer.BindLocalStream(&interceptor.StreamInfo{SSRC: 1, MimeType: "video/VP8"}, interceptor.RTPWriterFunc(func(header *rtp.Header, payload []byte, _ interceptor.Attributes) (int, error) {
					packet := (&rtp.Packet{Header: *header, Payload: payload}).Clone()
					if point == left && fault == "loss" && len(payload) > 1000 && !dropped {
						dropped = true
						return header.MarshalSize() + len(payload), nil
					}
					if point == left && fault == "reorder" {
						if pending == nil && !header.Marker {
							pending = packet
							return header.MarshalSize() + len(payload), nil
						}
						point.peer.receive([]*rtp.Packet{packet})
						if pending != nil {
							point.peer.receive([]*rtp.Packet{pending})
							pending = nil
						}
					} else {
						point.peer.receive([]*rtp.Packet{packet})
					}
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
			sent := make(chan error, 1)
			go func() {
				for index := 0; index < 64; index++ {
					if err := sender.SendContext(ctx, bytes.Repeat([]byte{byte(index)}, config.Payload)); err != nil {
						sent <- err
						return
					}
				}
				sent <- nil
			}()
			for index := 0; index < 64; index++ {
				if fault == "slow" {
					timer := time.NewTimer(80 * time.Millisecond)
					select {
					case <-ctx.Done():
						timer.Stop()
						test.Fatal(ctx.Err())
					case <-timer.C:
					}
				}
				data, err := receiver.Recv(ctx)
				if err != nil || !bytes.Equal(data, bytes.Repeat([]byte{byte(index)}, config.Payload)) {
					test.Fatal(index, err, "byte mismatch")
				}
			}
			if err := <-sent; err != nil {
				test.Fatal(err)
			}
			test.Log(fmt.Sprintf("fault=%s bytes=%d retries=%d queue=%d", fault, 64*config.Payload, sender.Stats().Retransmissions, len(left.sendQueue)))
		})
	}
}
