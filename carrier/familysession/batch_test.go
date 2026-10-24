package familysession

import (
	"bytes"
	"context"
	"testing"
	"time"
)

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
