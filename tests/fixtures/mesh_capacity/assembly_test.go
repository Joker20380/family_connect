package telemost

import (
	"bytes"
	"context"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/reliablestream"
	"github.com/pion/rtp/codecs"
)

func TestCapacityFramedWindowRecovery(test *testing.T) {
	for _, windows := range [][2]int{{8, 16}, {8, 32}, {16, 32}, {32, 32}} {
		config := reliablestream.DefaultConfig()
		config.SendWindow, config.ReceiveWindow = windows[0], windows[1]
		ctx, cancel := context.WithTimeout(context.Background(), 12*time.Second)
		leftEndpoint, rightEndpoint := framedReliablePair()
		leftEndpoint.dropUntil = 2
		left, err := reliablestream.New(ctx, leftEndpoint, config)
		if err != nil {
			test.Fatal(err)
		}
		right, err := reliablestream.New(ctx, rightEndpoint, config)
		if err != nil {
			test.Fatal(err)
		}
		completed := make(chan error, 1)
		go func() {
			for index := 0; index < 64; index++ {
				if err := left.SendContext(ctx, bytes.Repeat([]byte{byte(index)}, 16384)); err != nil {
					completed <- err
					return
				}
			}
			completed <- nil
		}()
		for index := 0; index < 64; index++ {
			data, err := right.Recv(ctx)
			if err != nil || !bytes.Equal(data, bytes.Repeat([]byte{byte(index)}, 16384)) {
				left.Close()
				right.Close()
				cancel()
				test.Fatal(windows, index, err)
			}
		}
		if err := <-completed; err != nil {
			test.Fatal(err)
		}
		left.Close()
		right.Close()
		cancel()
		test.Logf("windows=%v exact=64/64 dropped_RTP=%d assembly=%+v", windows, leftEndpoint.droppedRTP, rightEndpoint.assembler.delivery().Assembly)
	}
}

func TestCapacityPacketization(test *testing.T) {
	for _, size := range []int{64, 128, 1024, 16320, 16384, 16448} {
		fragments, err := encodeFragments(1, 1, make([]byte, size))
		if err != nil {
			test.Fatal(err)
		}
		packets := 0
		payloader := &codecs.VP8Payloader{}
		for _, fragment := range fragments {
			packets += len(payloader.Payload(1100, encodeVP8DataFrame(fragment)))
		}
		if len(fragments) != (size+8191)/8192 {
			test.Fatal("fragment count")
		}
		test.Logf("carrier_bytes=%d fragments=%d VP8_frames=%d RTP_packets_mtu1100=%d", size, len(fragments), len(fragments), packets)
	}
}

func TestCapacityAssemblyOverlap(test *testing.T) {
	for _, interleave := range []bool{false, true} {
		completed := 0
		payload := bytes.Repeat([]byte{73}, 16448)
		assembler := newReassembler(999, func(data []byte) {
			if !bytes.Equal(data, payload) {
				test.Fatal("corruption")
			}
			completed++
		})
		messages := make([][][]byte, 32)
		for index := range messages {
			messages[index], _ = encodeFragments(1, uint32(index+1), payload)
		}
		if interleave {
			for fragment := 0; fragment < 3; fragment++ {
				for _, message := range messages {
					assembler.ingest(message[fragment])
				}
			}
		} else {
			for _, message := range messages {
				for _, fragment := range message {
					assembler.ingest(fragment)
				}
			}
		}
		metrics := assembler.delivery().Assembly
		if !interleave && (completed != 32 || metrics.Capacity != 0) {
			test.Fatal("ordered capacity", completed, metrics)
		}
		if interleave && metrics.Capacity == 0 {
			test.Fatal("overlap did not expose capacity")
		}
		test.Logf("interleave=%v completed=%d assembly=%+v", interleave, completed, metrics)
	}
}
