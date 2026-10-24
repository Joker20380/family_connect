package reliablestream

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/localwrite"
)

type stalledLocalEndpoint struct {
	*testEndpoint
	started chan *localwrite.Write
}

func (endpoint *stalledLocalEndpoint) SendContext(ctx context.Context, data []byte) error {
	packet, err := decode(data)
	if err != nil || packet.kind != dataFrame {
		return endpoint.testEndpoint.SendContext(ctx, data)
	}
	write, err := localwrite.Register(ctx, 2)
	if err != nil {
		return err
	}
	if write.Begin() {
		write.Complete(nil)
		endpoint.started <- write
	}
	return nil
}

func TestLocalCompletionDeadlinesRepeatedGenerations(test *testing.T) {
	var previous *localwrite.Write
	for generation := 0; generation < 3; generation++ {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		left, right := endpoints()
		point := &stalledLocalEndpoint{testEndpoint: left, started: make(chan *localwrite.Write, 1)}
		config := DefaultConfig()
		config.RTO, config.MaxAge = 20*time.Millisecond, 150*time.Millisecond
		sender, err := New(localwrite.WithCompletion(ctx), point, config)
		if err != nil {
			test.Fatal(err)
		}
		receiver, err := New(ctx, right, config)
		if err != nil {
			test.Fatal(err)
		}
		if previous != nil {
			previous.Complete(nil)
		}
		began := time.Now()
		err = sender.SendContext(ctx, []byte("partial local write never completes"))
		if !errors.Is(err, context.DeadlineExceeded) || time.Since(began) > 500*time.Millisecond {
			test.Fatal("local write did not fail within its finite deadline", err)
		}
		if sender.Stats().Retransmissions != 0 {
			test.Fatal("local queue consumed retry budget")
		}
		select {
		case previous = <-point.started:
		case <-ctx.Done():
			test.Fatal("partial write not reached")
		}
		sender.Close()
		receiver.Close()
		cancel()
	}
	previous.Complete(nil)
}
