package telemost

import (
	"bytes"
	"context"
	"fmt"
	"testing"
	"time"

	"github.com/pion/rtp"
)

func TestMeshBoundRTPAccounting(test *testing.T) {
	for _, size := range []int{384 + 64, 1024 + 64, 16384 + 64} {
		test.Run(fmt.Sprint(size), func(test *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), time.Second)
			defer cancel()
			sender, receiver := headLossPair(test, ctx, 0, "none")
			defer sender.Close()
			defer receiver.Close()
			payload := bytes.Repeat([]byte{19}, size)
			if err := sender.SendContext(ctx, payload); err != nil {
				test.Fatal(err)
			}
			body, err := receiver.Recv(ctx)
			if err != nil || !bytes.Equal(body, payload) {
				test.Fatal("non-exact delivery", err)
			}
			frames := make(map[uint32]bool)
			rtpBytes := 0
			for _, packet := range sender.packets {
				frames[packet.Timestamp] = true
				rtpBytes += packet.MarshalSize()
			}
			if len(frames) != (size+8191)/8192 {
				test.Fatal("fragment/frame accounting changed")
			}
			test.Logf("bound_Pion_no_network carrier_bytes=%d useful_bytes=%d frames=%d packets=%d RTP_bytes=%d excludes_SRTP_UDP_IP_RTCP=true", size, size-64, len(frames), len(sender.packets), rtpBytes)
		})
	}
}

func TestMeshGapDeadlineRequiresArrival(test *testing.T) {
	buffer := newReorderBuffer()
	delivered := 0
	push := func(sequence uint16) {
		buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: sequence}}, func(*rtp.Packet) { delivered++ })
	}
	push(100)
	push(102)
	time.Sleep(150 * time.Millisecond)
	if delivered != 1 || len(buffer.pkts) != 1 {
		test.Fatal("fixture expected an arrival-driven deadline")
	}
	wait := time.Since(buffer.gapSince)
	push(103)
	if delivered != 3 || len(buffer.pkts) != 0 {
		test.Fatal("next arrival must release the expired gap")
	}
	test.Logf("gap_wait_ms=%.3f no_timer_release=true", float64(wait)/float64(time.Millisecond))
}
