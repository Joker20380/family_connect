package telemost

import (
	"testing"

	"github.com/pion/rtp"
	"github.com/pion/rtp/codecs"
)

func TestCapacityActualPionMTU(test *testing.T) {
	for _, size := range []int{384, 448, 16320, 16384, 16448} {
		fragments, err := encodeFragments(1, 1, make([]byte, size))
		if err != nil {
			test.Fatal(err)
		}
		packetizer := rtp.NewPacketizer(1200, 96, 1, &codecs.VP8Payloader{}, rtp.NewFixedSequencer(1), 90000)
		packets, wire := 0, 0
		for _, fragment := range fragments {
			for _, packet := range packetizer.Packetize(encodeVP8DataFrame(fragment), 3000) {
				packets++
				wire += packet.MarshalSize()
			}
		}
		test.Logf("actual_Pion_MTU1200 carrier_bytes=%d fragments=%d RTP_packets=%d RTP_bytes_without_extensions=%d", size, len(fragments), packets, wire)
		if size == 16448 && packets != 15 {
			test.Fatal("actual packetization mismatch")
		}
		if size == 16384 && packets != 14 {
			test.Fatal("actual packetization mismatch")
		}
	}
}
