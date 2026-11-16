package familysession

import (
	"bytes"
	"context"
	"net"
	"sync"
	"testing"
	"time"
)

type batchWriteBarrier struct {
	net.Conn
	entered chan struct{}
	release chan struct{}
	once    sync.Once
}

func (barrier *batchWriteBarrier) Write(payload []byte) (int, error) {
	barrier.once.Do(func() { close(barrier.entered) })
	<-barrier.release
	return barrier.Conn.Write(payload)
}

func TestBatchRegistersAndClearsSecurityBound(test *testing.T) {
	for _, cancelled := range []bool{false, true} {
		name := "success"
		if cancelled {
			name = "cancelled"
		}
		test.Run(name, func(test *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			clientProfile, serverProfile := profiles(test)
			client, server := connect(test, ctx, clientProfile, serverProfile)
			barrier := &batchWriteBarrier{Conn: client.stream.Conn, entered: make(chan struct{}), release: make(chan struct{})}
			client.stream.Conn = barrier
			var release sync.Once
			unblock := func() { release.Do(func() { close(barrier.release) }) }
			test.Cleanup(unblock)
			writeContext, stopWrite := context.WithTimeout(ctx, 3*time.Second)
			defer stopWrite()
			deadline, _ := writeContext.Deadline()
			done := make(chan error, 1)
			go func() { done <- client.SendBatchContext(writeContext, [][]byte{[]byte("bounded batch")}) }()
			select {
			case <-barrier.entered:
			case <-ctx.Done():
				test.Fatal("batch did not reach TLS write")
			}
			client.securityMu.Lock()
			bound := client.writeBound
			client.securityMu.Unlock()
			if !bound.Equal(deadline) {
				test.Fatal("batch context bound is not registered for credential renewal")
			}
			if cancelled {
				stopWrite()
				select {
				case <-client.Done():
				case <-ctx.Done():
					test.Fatal("cancelled batch did not stop its session")
				}
			}
			unblock()
			if !cancelled {
				payload, err := server.Recv(ctx)
				if err != nil || string(payload) != "bounded batch" {
					test.Fatal("batch receive failed", err)
				}
			}
			select {
			case err := <-done:
				if (err != nil) != cancelled {
					test.Fatal("unexpected batch write outcome", err)
				}
			case <-ctx.Done():
				test.Fatal("batch write did not finish")
			}
			client.securityMu.Lock()
			cleared := client.writeBound.IsZero()
			client.securityMu.Unlock()
			if !cleared {
				test.Fatal("completed batch retained its context bound")
			}
		})
	}
}

func TestBatchLegacyReceiveAndBoundary(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	clientProfile, serverProfile := profiles(test)
	client, server := connect(test, ctx, clientProfile, serverProfile)
	payloads := [][]byte{[]byte("one"), nil, bytes.Repeat([]byte{7}, MaxBatchPlaintext-3*BatchMessageHeaderSize-3)}
	done := make(chan error, 1)
	go func() { done <- client.SendBatchContext(ctx, payloads) }()
	for _, expected := range payloads {
		received, err := server.Recv(ctx)
		if err != nil || !bytes.Equal(received, expected) {
			test.Fatalf("receive %d: %v", len(received), err)
		}
	}
	if err := <-done; err != nil {
		test.Fatal(err)
	}
	go func() { done <- client.SendContext(ctx, []byte("legacy-after-batch")) }()
	received, err := server.Recv(ctx)
	if err != nil || string(received) != "legacy-after-batch" {
		test.Fatal(err)
	}
	if err := <-done; err != nil {
		test.Fatal(err)
	}
	if client.sendSequence != 4 || server.recvSequence != 4 {
		test.Fatal("sequence mismatch")
	}
}

func TestBatchRejectionBeforeWrite(test *testing.T) {
	for _, kind := range []string{"empty", "count", "bytes", "sequence", "expired", "cancelled"} {
		test.Run(kind, func(test *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			clientProfile, serverProfile := profiles(test)
			client, _ := connect(test, ctx, clientProfile, serverProfile)
			payloads := [][]byte{[]byte("never sent")}
			sendContext := ctx
			switch kind {
			case "empty":
				payloads = nil
			case "count":
				payloads = make([][]byte, MaxBatchMessages+1)
			case "bytes":
				payloads = [][]byte{make([]byte, MaxBatchPlaintext)}
			case "sequence":
				client.sendSequence = ^uint64(0) - 1
				payloads = [][]byte{nil, nil}
			case "expired":
				client.expiry = time.Now().Add(-time.Second)
			case "cancelled":
				var stop context.CancelFunc
				sendContext, stop = context.WithCancel(ctx)
				stop()
			}
			sequence := client.sendSequence
			if err := client.SendBatchContext(sendContext, payloads); err != ErrRejected {
				test.Fatalf("unexpected %v", err)
			}
			if client.sendSequence != sequence {
				test.Fatal("invalid batch consumed sequence")
			}
		})
	}
}
