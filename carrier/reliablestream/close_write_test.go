package reliablestream

import (
	"bytes"
	"context"
	"errors"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/localwrite"
)

type queuedClose struct {
	ctx   context.Context
	raw   []byte
	write *localwrite.Write
}

type queuedCloseEndpoint struct {
	*testEndpoint
	queued chan queuedClose
}

func (endpoint *queuedCloseEndpoint) SendContext(ctx context.Context, raw []byte) error {
	packet, err := decode(raw)
	if err != nil || packet.kind != resetFrame {
		return endpoint.testEndpoint.SendContext(ctx, raw)
	}
	write, err := localwrite.Register(ctx, 1)
	if err != nil {
		return err
	}
	endpoint.queued <- queuedClose{ctx: ctx, raw: bytes.Clone(raw), write: write}
	return nil
}

func closingPair(test *testing.T, completion bool) (*Stream, *Stream, *queuedCloseEndpoint) {
	test.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	test.Cleanup(cancel)
	if completion {
		ctx = localwrite.WithCompletion(ctx)
	}
	left, right := endpoints()
	point := &queuedCloseEndpoint{testEndpoint: left, queued: make(chan queuedClose, 1)}
	sender, err := New(ctx, point, DefaultConfig())
	if err != nil {
		test.Fatal(err)
	}
	receiver, err := New(ctx, right, DefaultConfig())
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() { sender.Close(); receiver.Close() })
	if err := sender.SendContext(ctx, []byte("establish epochs")); err != nil {
		test.Fatal(err)
	}
	if _, err := receiver.Recv(ctx); err != nil {
		test.Fatal(err)
	}
	return sender, receiver, point
}

func TestCloseWaitsForQueuedResetWrite(test *testing.T) {
	for _, completion := range []bool{false, true} {
		test.Run(map[bool]string{false: "legacy-data", true: "completed-data"}[completion], func(test *testing.T) {
			sender, receiver, point := closingPair(test, completion)
			closed := make(chan struct{})
			go func() { sender.Close(); close(closed) }()
			queued := <-point.queued
			if queued.write == nil {
				test.Fatal("reset has no local-write completion, so carrier close can discard it")
			}
			select {
			case <-closed:
				test.Fatal("stream closed before queued reset was written")
			default:
			}
			if !queued.write.Begin() {
				test.Fatal("reset expired before its bounded local write")
			}
			err := point.testEndpoint.SendContext(queued.ctx, queued.raw)
			queued.write.Complete(err)
			if err != nil {
				test.Fatal(err)
			}
			ctx, cancel := context.WithTimeout(context.Background(), time.Second)
			defer cancel()
			if _, err := receiver.Recv(ctx); !errors.Is(err, ErrReset) {
				test.Fatalf("remote closure not observed: %v", err)
			}
			select {
			case <-closed:
			case <-ctx.Done():
				test.Fatal("local close did not finish after reset write")
			}
			if sender.Stats().BufferedBytes != 0 || receiver.Stats().BufferedBytes != 0 {
				test.Fatal("closed stream retained data")
			}
		})
	}
}

func TestCloseQueuedResetRemainsBounded(test *testing.T) {
	sender, _, point := closingPair(test, false)
	closed := make(chan struct{})
	go func() { sender.Close(); close(closed) }()
	queued := <-point.queued
	if queued.write == nil {
		test.Fatal("reset has no cancellable local-write completion")
	}
	select {
	case <-closed:
	case <-time.After(time.Second):
		test.Fatal("stalled reset writer blocked local shutdown")
	}
	if queued.ctx.Err() != context.DeadlineExceeded || queued.write.Begin() {
		test.Fatal("expired reset can still start after carrier shutdown")
	}
}
