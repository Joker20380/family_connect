package reliablestream

import (
	"context"
	"errors"
	"sync/atomic"
	"testing"
	"time"
)

func TestCloseRetriesLocallyWrittenLostReset(test *testing.T) {
	for _, losses := range []int32{1, 4} {
		test.Run(map[int32]string{1: "first-reset", 4: "first-four-resets"}[losses], func(test *testing.T) {
			var attempts atomic.Int32
			sender, receiver := streamPair(test, func(raw []byte) bool {
				packet, err := decode(raw)
				return err == nil && packet.kind == resetFrame && attempts.Add(1) <= losses
			})
			ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			defer cancel()
			if err := sender.SendContext(ctx, []byte("establish before close")); err != nil {
				test.Fatal(err)
			}
			if _, err := receiver.Recv(ctx); err != nil {
				test.Fatal(err)
			}
			sender.Close()
			bounded, stop := context.WithTimeout(ctx, 200*time.Millisecond)
			defer stop()
			if _, err := receiver.Recv(bounded); !errors.Is(err, ErrReset) {
				test.Fatalf("peer retained after %d lost local writes: %v", losses, err)
			}
			if attempts.Load() != 5 {
				test.Fatalf("unexpected bounded reset attempts: %d", attempts.Load())
			}
		})
	}
}

func TestCloseWithAllResetsLostIsBounded(test *testing.T) {
	var attempts atomic.Int32
	sender, receiver := streamPair(test, func(raw []byte) bool {
		packet, err := decode(raw)
		if err == nil && packet.kind == resetFrame {
			attempts.Add(1)
			return true
		}
		return false
	})
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	if err := sender.SendContext(ctx, []byte("establish before total loss")); err != nil {
		test.Fatal(err)
	}
	if _, err := receiver.Recv(ctx); err != nil {
		test.Fatal(err)
	}
	started := time.Now()
	sender.Close()
	if elapsed := time.Since(started); elapsed > 900*time.Millisecond {
		test.Fatalf("lost RESET exceeded local close bound: %v", elapsed)
	}
	if attempts.Load() != 5 {
		test.Fatalf("unexpected reset attempts under total loss: %d", attempts.Load())
	}
	if sender.Stats().BufferedBytes != 0 {
		test.Fatal("closed sender retained buffers")
	}
	select {
	case <-receiver.done:
		test.Fatal("total RESET loss must not imply remote closure")
	default:
	}
}
