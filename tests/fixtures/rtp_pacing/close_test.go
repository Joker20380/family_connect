package telemost

import (
	"context"
	"github.com/Joker20380/family_connect/carrier/packetpace"
	"github.com/pion/interceptor"
	"github.com/pion/rtp"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func TestPacingSessionCloseFullQueue(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	left, right := headLossPair(test, ctx, 0, "none")
	defer left.Close()
	defer right.Close()
	if err := left.track.Unbind(lossTrackContext{}); err != nil {
		test.Fatal(err)
	}
	pace := packetpace.New(ctx, true)
	left.cfg.PacketPacing = pace
	first := make(chan struct{})
	var once sync.Once
	var writes atomic.Uint64
	observer, _ := (&pacedBoundaryFactory{boundary: &boundaryFactory{trace: left.cfg.Trace, writes: &left.rtpWrites}, pace: pace}).NewInterceptor("")
	writer := observer.BindLocalStream(&interceptor.StreamInfo{SSRC: 1, MimeType: "video/VP8"}, interceptor.RTPWriterFunc(func(header *rtp.Header, payload []byte, _ interceptor.Attributes) (int, error) {
		writes.Add(1)
		once.Do(func() { close(first) })
		return header.MarshalSize() + len(payload), nil
	}))
	if _, err := left.track.Bind(lossTrackContext{writer: lossTrackWriter{writer}}); err != nil {
		test.Fatal(err)
	}
	fragments, _ := encodeFragments(1, 1, make([]byte, 8192))
	for index := 0; index < cap(left.sendQueue); index++ {
		left.sendQueue <- outboundFrame{data: encodeVP8DataFrame(fragments[0])}
	}
	left.startWorker(left.writerLoop)
	select {
	case <-first:
	case <-ctx.Done():
		test.Fatal(ctx.Err())
	}
	closed := make(chan error, 1)
	go func() { closed <- left.Close() }()
	select {
	case err := <-closed:
		if err != nil {
			test.Fatal(err)
		}
	case <-time.After(time.Second):
		test.Fatal("paced close did not join writer")
	}
	if pace.Snapshot().Pending != 0 || writes.Load() >= 7 {
		test.Fatal("late writes or incomplete frame released", writes.Load(), pace.Snapshot())
	}
	if err := left.SendContext(ctx, []byte("late send")); err == nil {
		test.Fatal("send after close")
	}
}
