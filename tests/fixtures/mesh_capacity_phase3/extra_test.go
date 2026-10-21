package telemost

import (
	"github.com/pion/interceptor"
	"github.com/pion/rtp"
	"github.com/pion/rtp/codecs"
	"github.com/pion/webrtc/v4/pkg/media"
	"testing"
	"time"
)

func TestLabMediaFreshAndReboundTrack(test *testing.T) {
	labMedia.policy = "B"
	defer func() { labMedia.policy = "" }()
	for generation := 0; generation < 2; generation++ {
		track, err := newVP8Track()
		if err != nil {
			test.Fatal(err)
		}
		session := &Session{track: track}
		var packets []*rtp.Packet
		writer := interceptor.RTPWriterFunc(func(header *rtp.Header, payload []byte, _ interceptor.Attributes) (int, error) {
			packets = append(packets, (&rtp.Packet{Header: *header, Payload: payload}).Clone())
			return header.MarshalSize() + len(payload), nil
		})
		binding := lossTrackContext{writer: lossTrackWriter{writer}}
		if _, err = track.Bind(binding); err != nil {
			test.Fatal(err)
		}
		start := time.Now()
		if err = session.labWriteSampleAt(media.Sample{Data: vp8Keepalive}, start); err != nil {
			test.Fatal(err)
		}
		if err = track.Unbind(binding); err != nil {
			test.Fatal(err)
		}
		if _, err = track.Bind(binding); err != nil {
			test.Fatal(err)
		}
		if err = session.labWriteSampleAt(media.Sample{Data: vp8Keepalive}, start.Add(500*time.Millisecond)); err != nil {
			test.Fatal(err)
		}
		if len(packets) != 2 || packets[1].Timestamp-packets[0].Timestamp != 45000 || packets[1].SequenceNumber != packets[0].SequenceNumber+1 {
			test.Fatal("rebind changed clock/sequence")
		}
		var first, last codecs.VP8Packet
		first.Unmarshal(packets[0].Payload)
		last.Unmarshal(packets[1].Payload)
		if first.I != 0 || last.I != 1 || last.PictureID != 1 {
			test.Fatal("empty advance consumed PictureID")
		}
		if err = track.Unbind(binding); err != nil {
			test.Fatal(err)
		}
	}
}

func TestLabMediaPictureWrap(test *testing.T) {
	payloader := &codecs.VP8Payloader{EnablePictureID: true}
	for index := 0; index < 32770; index++ {
		packets := payloader.Payload(1188, vp8Keepalive)
		if len(packets) != 1 {
			test.Fatal("keepalive packetization")
		}
		var descriptor codecs.VP8Packet
		if _, err := descriptor.Unmarshal(packets[0]); err != nil {
			test.Fatal(err)
		}
		expected := uint16(index) & 0x7fff
		if descriptor.S != 1 || descriptor.PID != 0 || (expected == 0 && descriptor.I != 0) || (expected != 0 && (descriptor.I != 1 || descriptor.PictureID != expected)) {
			test.Fatal(index, "PictureID boundary")
		}
	}
}

func TestLabMediaTraceBoundAndCost(test *testing.T) {
	if err := ConfigureLabMedia("A", 0); err != nil {
		test.Fatal(err)
	}
	defer func() {
		labMedia.Lock()
		labMedia.enabled = false
		labMedia.events = nil
		labMedia.policy = ""
		labMedia.Unlock()
	}()
	payload := make([]byte, 1188)
	payload[0] = 0x10
	header := &rtp.Header{Version: 2, Marker: true, Timestamp: 17, SSRC: 1}
	started := time.Now()
	for index := 0; index < 100010; index++ {
		header.SequenceNumber++
		labMediaPacket("tx", header, payload, "ok")
	}
	elapsed := time.Since(started)
	if len(labMedia.events) != 100000 || labMedia.overflow != 10 {
		test.Fatal("trace bound", len(labMedia.events), labMedia.overflow)
	}
	test.Logf("record+hash 100010 x1188B in %.6fs = %.3f Mbit/s under race; overflow10 explicit", elapsed.Seconds(), float64(100010*1188*8)/elapsed.Seconds()/1e6)
}
