package telemost

import (
	"bytes"
	"encoding/binary"
	"strings"
	"testing"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/pion/rtp"
)

func TestForensicsObserverPreservesRTPBytes(test *testing.T) {
	fragment := make([]byte, fragmentHeaderLen+3)
	binary.BigEndian.PutUint32(fragment, 7)
	binary.BigEndian.PutUint32(fragment[4:], 11)
	binary.BigEndian.PutUint32(fragment[12:], 1)
	payload := append([]byte{0x90, 0x80, 0x80, 0x7b}, encodeVP8DataFrame(fragment)...)
	packet := &rtp.Packet{Header: rtp.Header{Version: 2, Marker: true, PayloadType: 96, SequenceNumber: 65535, Timestamp: 12345, SSRC: 77}, Payload: payload}
	before, err := packet.Marshal()
	if err != nil {
		test.Fatal(err)
	}
	for _, direction := range []string{"tx", "rx"} {
		for _, correlationOnly := range []bool{false, true} {
			observer := rtpBoundary{trace: sessiontrace.New(strings.Repeat("a", 64), nil), stage: "rtp_received", direction: direction, correlationOnly: correlationOnly}
			observer.packet(&packet.Header, packet.Payload, "ok")
			after, err := packet.Marshal()
			if err != nil || !bytes.Equal(before, after) {
				test.Fatal("forensic observer changed RTP bytes", direction, correlationOnly, err)
			}
		}
	}
}
