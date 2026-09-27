package reliablestream

import (
	"bytes"
	"context"
	"errors"
	"sync"
	"testing"
	"time"
)

type testEndpoint struct {
	in, out chan []byte
	done    chan struct{}
	once    sync.Once
	drop    func([]byte) bool
}

func (point *testEndpoint) SendContext(ctx context.Context, data []byte) error {
	if point.drop != nil && point.drop(data) {
		return nil
	}
	select {
	case point.out <- bytes.Clone(data):
		return nil
	case <-point.done:
		return ErrClosed
	case <-ctx.Done():
		return ctx.Err()
	}
}

func (point *testEndpoint) Recv(ctx context.Context) ([]byte, error) {
	select {
	case data := <-point.in:
		return data, nil
	case <-point.done:
		return nil, ErrClosed
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}

func (point *testEndpoint) Close() error { point.once.Do(func() { close(point.done) }); return nil }

func endpoints() (*testEndpoint, *testEndpoint) {
	forward, reverse := make(chan []byte, 32), make(chan []byte, 32)
	return &testEndpoint{in: reverse, out: forward, done: make(chan struct{})}, &testEndpoint{in: forward, out: reverse, done: make(chan struct{})}
}

func streamPair(test *testing.T, drop func([]byte) bool) (*Stream, *Stream) {
	test.Helper()
	leftEndpoint, rightEndpoint := endpoints()
	leftEndpoint.drop = drop
	config := DefaultConfig()
	config.RTO = 20 * time.Millisecond
	config.MaxAge = time.Second
	left, err := New(context.Background(), leftEndpoint, config)
	if err != nil {
		test.Fatal(err)
	}
	right, err := New(context.Background(), rightEndpoint, config)
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() { left.Close(); right.Close() })
	return left, right
}

func TestAdapterBackpressureCancellation(test *testing.T) {
	left, right := streamPair(test, nil)
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	for index := 0; index < 8; index++ {
		if err := left.SendContext(ctx, []byte{byte(index)}); err != nil {
			test.Fatal(err)
		}
	}
	blocked := make(chan error, 1)
	go func() { blocked <- left.SendContext(ctx, []byte{8}) }()
	select {
	case <-blocked:
		test.Fatal("ninth frame was not backpressured")
	case <-time.After(40 * time.Millisecond):
	}
	data, err := right.Recv(ctx)
	if err != nil || !bytes.Equal(data, []byte{0}) {
		test.Fatal("ordered read", err)
	}
	select {
	case err := <-blocked:
		if err != nil {
			test.Fatal(err)
		}
	case <-ctx.Done():
		test.Fatal("waiter not resumed")
	}
	left.Close()
	if left.Stats().BufferedBytes != 0 {
		test.Fatal("closed stream retains buffers")
	}
}

func TestAdapterExhaustionAndCancellation(test *testing.T) {
	for _, cancelDuringRetry := range []bool{false, true} {
		test.Run(map[bool]string{true: "cancel", false: "exhaustion"}[cancelDuringRetry], func(test *testing.T) {
			left, right := streamPair(test, func(raw []byte) bool { return raw[4] == dataFrame })
			ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			defer cancel()
			if err := left.SendContext(ctx, []byte{1}); err != nil {
				test.Fatal(err)
			}
			if cancelDuringRetry {
				time.Sleep(45 * time.Millisecond)
				left.Close()
			}
			select {
			case <-left.done:
			case <-ctx.Done():
				test.Fatal("retry worker leaked")
			}
			if !cancelDuringRetry && !errors.Is(left.failure(), ErrExhausted) {
				test.Fatal(left.failure())
			}
			select {
			case <-right.done:
			case <-ctx.Done():
				test.Fatal("remote reset waiter leaked")
			}
			if !errors.Is(right.failure(), ErrReset) {
				test.Fatal(right.failure())
			}
		})
	}
}

func TestCarrierStallAndClose(test *testing.T) {
	point, _ := endpoints()
	for index := 0; index < cap(point.out); index++ {
		point.out <- []byte{1}
	}
	config := DefaultConfig()
	config.RTO = 10 * time.Millisecond
	ctx, cancel := context.WithCancel(context.Background())
	stream, err := New(ctx, point, config)
	if err != nil {
		test.Fatal(err)
	}
	waiter := make(chan error, 1)
	go func() { waiter <- stream.SendContext(ctx, []byte{1}) }()
	cancel()
	stream.Close()
	select {
	case <-waiter:
	case <-time.After(time.Second):
		test.Fatal("stalled carrier leaked waiter")
	}
}

func TestNegotiatedPayload(test *testing.T) {
	leftEndpoint, rightEndpoint := endpoints()
	config := DefaultConfig()
	left, _ := New(context.Background(), leftEndpoint, config)
	defer left.Close()
	config.Payload = 31
	right, _ := New(context.Background(), rightEndpoint, config)
	defer right.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	source := bytes.Repeat([]byte{17}, 256)
	completed := make(chan error, 1)
	go func() { completed <- left.SendContext(ctx, source) }()
	var actual []byte
	for len(actual) < len(source) {
		data, err := right.Recv(ctx)
		if err != nil {
			test.Fatal(err)
		}
		actual = append(actual, data...)
	}
	if err := <-completed; err != nil || !bytes.Equal(source, actual) {
		test.Fatal("negotiation", err)
	}
}
