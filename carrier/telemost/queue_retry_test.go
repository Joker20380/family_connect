package telemost

import (
	"bytes"
	"context"
	"encoding/json"
	"os"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/localwrite"
	"github.com/Joker20380/family_connect/carrier/reliablestream"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/pion/interceptor"
	"github.com/pion/rtp"
)

type countedQueueEndpoint struct {
	*Session
	attempts atomic.Uint64
}

func (endpoint *countedQueueEndpoint) SendContext(ctx context.Context, data []byte) error {
	point := sessiontrace.AttemptFrom(ctx)
	if point.DataKnown && point.DataSequence == 1 {
		endpoint.attempts.Add(1)
	}
	return endpoint.Session.SendContext(ctx, data)
}

func TestQueueRetryHeldLocalWriter(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 4*time.Second)
	defer cancel()
	if os.Getenv("FC_QUEUE_COMPLETION_EXPECTED") == "1" {
		ctx = localwrite.WithCompletion(ctx)
	}
	left, right := headLossPair(test, ctx, 0, "none")
	defer left.Close()
	defer right.Close()
	var hold atomic.Bool
	release := make(chan struct{})
	var writes atomic.Uint64
	for _, point := range []*headLossEndpoint{left, right} {
		if err := point.track.Unbind(lossTrackContext{}); err != nil {
			test.Fatal(err)
		}
		boundary, _ := (&boundaryFactory{trace: point.cfg.Trace, writes: &point.rtpWrites}).NewInterceptor("")
		writer := boundary.BindLocalStream(&interceptor.StreamInfo{MimeType: "video/VP8"}, interceptor.RTPWriterFunc(func(header *rtp.Header, payload []byte, _ interceptor.Attributes) (int, error) {
			if point == left && hold.Load() {
				select {
				case <-release:
				case <-ctx.Done():
					return 0, ctx.Err()
				}
			}
			if point == left {
				writes.Add(1)
			}
			point.peer.receive([]*rtp.Packet{(&rtp.Packet{Header: *header, Payload: payload}).Clone()})
			return header.MarshalSize() + len(payload), nil
		}))
		if _, err := point.track.Bind(lossTrackContext{writer: lossTrackWriter{writer}}); err != nil {
			test.Fatal(err)
		}
		point.startWorker(point.writerLoop)
	}
	config := reliablestream.DefaultConfig()
	config.SendWindow, config.ReceiveWindow = 32, 32
	config.RTO, config.MaxAge = 30*time.Millisecond, 2*time.Second
	counted := &countedQueueEndpoint{Session: left.Session}
	sender, err := reliablestream.New(ctx, counted, config)
	if err != nil {
		test.Fatal(err)
	}
	defer sender.Close()
	receiver, err := reliablestream.New(ctx, right.Session, config)
	if err != nil {
		test.Fatal(err)
	}
	defer receiver.Close()
	if err := sender.SendContext(ctx, []byte("warmup")); err != nil {
		test.Fatal(err)
	}
	if _, err := receiver.Recv(ctx); err != nil {
		test.Fatal(err)
	}
	time.Sleep(30 * time.Millisecond)
	hold.Store(true)
	initialWrites := writes.Load()
	started := time.Now()
	sent := make(chan error, 1)
	go func() { sent <- sender.SendContext(ctx, bytes.Repeat([]byte{42}, config.Payload)) }()
	time.Sleep(340 * time.Millisecond)
	stats := sender.Stats()
	queued := len(left.sendQueue)
	written := writes.Load() - initialWrites
	attempts := counted.attempts.Load()
	close(release)
	data, receiveErr := receiver.Recv(ctx)
	sendErr := <-sent
	result := map[string]any{"pending_attempts_before_first_write": attempts, "queued_fragments": queued, "new_data_blocks": stats.DataSent, "retries_before_first_local_write": stats.Retransmissions,
		"rtp_writes_before_release": written, "queue_hold_ms": 340, "goodput_before_release": 0, "terminal": stats.Terminal,
		"byte_exact": receiveErr == nil && bytes.Equal(data, bytes.Repeat([]byte{42}, config.Payload)), "send_ok": sendErr == nil,
		"seconds": time.Since(started).Seconds()}
	encoded, _ := json.Marshal(result)
	test.Log(string(encoded))
	if written != 0 {
		test.Fatal("writer hold ineffective")
	}
	if os.Getenv("FC_QUEUE_COMPLETION_EXPECTED") == "1" && (attempts != 1 || stats.Retransmissions != 0 || stats.Terminal != "" || receiveErr != nil || sendErr != nil || !bytes.Equal(data, bytes.Repeat([]byte{42}, config.Payload))) {
		test.Fatal("completion regression")
	}
	if os.Getenv("FC_QUEUE_COMPLETION_EXPECTED") == "0" && (attempts <= 1 || stats.Retransmissions == 0 || stats.Terminal != "recovery_exhausted") {
		test.Fatal("baseline accumulation not reproduced")
	}
}
