//go:build fc_owner_diagnostic

package sessiontrace

import "testing"

func TestCorrelationBeta68PreservedMediaOnly(test *testing.T) {
	recorder := New("d093f85a58d68a31c3752e32a113c6e97ff76b2d4c0e777051bd534bf2644f8c", nil)
	key := CorrelationKey{Session: recorder.Snapshot().SessionTag, Direction: "client_to_gateway", Sequence: 60, Attempt: 1}
	armed, err := recorder.PrearmCorrelation(key, "rx")
	if err != nil {
		test.Fatal(err)
	}
	key = armed.Key
	descriptor := CorrelationDescriptor{Key: key, Sender: 433208471, Message: 2855051861, Media: []MediaIdentity{{Fragment: 0, Total: 1, Picture: 214, Timestamp: 1671731102, First: 20994, Last: 20994, Packets: 1}}}
	if _, err := recorder.BindCorrelation(descriptor); err != nil {
		test.Fatal(err)
	}
	point := Boundary{Direction: "rx", Stage: "rtp_correlated", Result: "ok", MessageKnown: true, Sender: descriptor.Sender, Message: descriptor.Message, Total: 1, PictureKnown: true, PictureID: 214, FrameKnown: true, Timestamp: 635613, FirstRTP: 220, LastRTP: 220, Packets: 1, DataKnown: true, DataSequence: 60}
	recorder.CorrelationMedia(point)
	point.Stage = "vp8_reassembled"
	recorder.Boundary(point)
	point.Stage = "carrier_message_completed"
	recorder.Boundary(point)
	value := requireReceiverState(test, recorder, key, "CARRIER_COMPLETE")
	if !value.MediaComplete || value.Reliable != nil {
		test.Fatal("media-only replay invented receiver callbacks")
	}
}

func TestCorrelationHopLocalRTP(test *testing.T) {
	for _, mode := range []string{"rewrite", "rtp_only", "wrong_message", "wrong_picture", "invalid_range", "late_original", "mixed_fragments"} {
		test.Run(mode, func(test *testing.T) {
			recorder, key := correlationFixture(test)
			descriptor := correlationDescriptor(key, 11, 2)
			if _, err := recorder.BindCorrelation(descriptor); err != nil {
				test.Fatal(err)
			}
			for fragment := uint32(0); fragment < 2; fragment++ {
				media := descriptor.Media[fragment]
				point := Boundary{Direction: "rx", Stage: "rtp_correlated", Result: "ok", DataKnown: true, DataSequence: key.Sequence, MessageKnown: true, Sender: descriptor.Sender, Message: descriptor.Message, Fragment: fragment, Total: 2, PictureKnown: true, PictureID: media.Picture, FrameKnown: true, Timestamp: 635613 + fragment, FirstRTP: 220, LastRTP: 221, Packets: 2}
				switch mode {
				case "rtp_only":
					point.Timestamp, point.FirstRTP, point.LastRTP, point.Packets = media.Timestamp, media.First, media.Last, media.Packets
					point.Sender++
					point.PictureID++
				case "wrong_message", "late_original":
					point.Message--
				case "wrong_picture":
					point.PictureID++
				case "invalid_range":
					point.Packets = 0
				case "mixed_fragments":
					if fragment == 0 {
						point.Message--
					}
				}
				recorder.CorrelationMedia(point)
				point.Stage = "vp8_reassembled"
				recorder.Boundary(point)
			}
			correlationComplete(recorder, 11, 2)
			if mode != "rewrite" {
				value := requireReceiverState(test, recorder, key, "BOUND")
				if value.MediaComplete {
					test.Fatal("non-selected identity matched")
				}
				return
			}
			value := requireReceiverState(test, recorder, key, "CARRIER_COMPLETE")
			if value.Descriptor.Media[0].Timestamp == value.Candidates[0].Media[0].Timestamp {
				test.Fatal("leg-local evidence overwritten")
			}
			acceptSelected(recorder, 11)
			requireReceiverState(test, recorder, key, "RELIABLE_ACCEPTED")
			stamp := consumeSelected(recorder)
			requireReceiverState(test, recorder, key, "ACK_GENERATED")
			recorder.ReceiverACKSent(StampACK(), 20, 1, true)
			requireReceiverState(test, recorder, key, "ACK_GENERATED")
			recorder.ReceiverACKSent(stamp, 20, 1, true)
			requireReceiverState(test, recorder, key, "COMPLETE")
		})
	}
}
