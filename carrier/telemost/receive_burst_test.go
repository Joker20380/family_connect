package telemost

import (
	"bytes"
	"context"
	"testing"
	"time"
)

func TestReceiveBurstFiniteCapacityAndClose(test *testing.T) {
	session, err := New(context.Background(), Config{RoomURL: "bounded-local-fixture"})
	if err != nil {
		test.Fatal(err)
	}
	defer session.Close()
	if cap(session.recvQueue) != 64 || MaxMessageSize != 65536 {
		test.Fatal("memory envelope changed")
	}
	for index := 0; index < 64; index++ {
		session.deliver(bytes.Repeat([]byte{byte(index)}, MaxMessageSize))
	}
	if session.closed.Load() || len(session.recvQueue) != 64 {
		test.Fatal("bounded complete burst rejected")
	}
	session.deliver([]byte("one message beyond capacity"))
	if !session.closed.Load() {
		test.Fatal("overload must remain observable")
	}
	if err := session.Close(); err != nil {
		test.Fatal(err)
	}
	select {
	case <-session.cleanupDone:
	default:
		test.Fatal("cleanup incomplete")
	}
}

func TestReceiveBurstCancelFullQueue(test *testing.T) {
	for _, parentCancel := range []bool{false, true} {
		name := "close"
		if parentCancel {
			name = "parent-cancel"
		}
		test.Run(name, func(test *testing.T) {
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			session, err := New(ctx, Config{RoomURL: "bounded-local-fixture"})
			if err != nil {
				test.Fatal(err)
			}
			defer session.Close()
			for index := 0; index < 64; index++ {
				session.deliver([]byte{byte(index)})
			}
			if session.closed.Load() || len(session.recvQueue) != 64 {
				test.Fatal("full queue prematurely closed")
			}
			if parentCancel {
				cancel()
			} else if err := session.Close(); err != nil {
				test.Fatal(err)
			}
			select {
			case <-session.cleanupDone:
			case <-time.After(time.Second):
				test.Fatal("full-queue cleanup timeout")
			}
			if !session.closed.Load() {
				test.Fatal("close not recorded")
			}
		})
	}
}
