package tcpforward

import (
	"context"
	"errors"
	"testing"
)

func TestCancelledOpenContextCannotEnqueueBeforeResetCallback(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	mux := &Mux{ctx: context.Background(), streams: make(map[uint32]*MuxStream), changed: make(chan struct{})}
	stream := mux.makeStreamLocked(1)
	stream.opened = true
	stream.openContext = ctx
	cancel()
	count, err := stream.Write([]byte("client-commit"))
	if count != 0 || !errors.Is(err, context.Canceled) || stream.sent != 0 {
		test.Fatal("cancelled context admitted a write", count, err)
	}
	if len(stream.send) != 1 || stream.send[0].kind != resetFrame {
		test.Fatal("unsent work survived synchronous cancellation")
	}
}
