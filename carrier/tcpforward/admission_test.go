package tcpforward

import (
	"context"
	"io"
	"testing"
	"time"
)

func awaitAdmission(test *testing.T, mux *Mux, count int) {
	test.Helper()
	deadline := time.Now().Add(2 * time.Second)
	for time.Now().Before(deadline) {
		if mux.Stats().AdmissionWaiting == count {
			return
		}
		time.Sleep(time.Millisecond)
	}
	test.Fatalf("admission waiting: wanted=%d got=%d", count, mux.Stats().AdmissionWaiting)
}

func TestAdmissionFIFOAndCancellation(test *testing.T) {
	port := muxFixture(test, muxEcho)
	ctx, client, _ := muxPair(test, port, 1, 1)
	client.config.WaitForSlot = true
	held := muxOpen(test, ctx, client, port)
	type result struct {
		stream *MuxStream
		err    error
	}
	first, second := make(chan result, 1), make(chan result, 1)
	go func() {
		stream, err := client.OpenTCP(ctx, OpenRequest{Host: "127.0.0.1", Port: port})
		first <- result{stream, err}
	}()
	awaitAdmission(test, client, 1)
	secondCtx, cancel := context.WithCancel(ctx)
	go func() {
		stream, err := client.OpenTCP(secondCtx, OpenRequest{Host: "127.0.0.1", Port: port})
		second <- result{stream, err}
	}()
	awaitAdmission(test, client, 2)
	if err := exactMux(held, []byte("held flow survives and closes")); err != nil {
		test.Fatal(err)
	}
	opened := <-first
	if opened.err != nil {
		test.Fatal(opened.err)
	}
	defer opened.stream.Reset()
	awaitAdmission(test, client, 1)
	select {
	case <-second:
		test.Fatal("second waiter bypassed first")
	default:
	}
	cancel()
	if next := <-second; next.err != ErrReset {
		test.Fatal("cancelled waiter", next.err)
	}
	awaitAdmission(test, client, 0)
	if client.Stats().AdmissionWaits != 2 || client.Stats().AdmissionCancelled != 1 {
		test.Fatal(client.Stats())
	}
	if err := exactMux(opened.stream, []byte("admitted FIFO body")); err != nil {
		test.Fatal(err)
	}
}

func TestAdmissionQueueBoundAndShutdown(test *testing.T) {
	port := muxFixture(test, muxEcho)
	ctx, client, _ := muxPair(test, port, 1, 1)
	client.config.WaitForSlot = true
	muxOpen(test, ctx, client, port)
	results := make(chan error, MuxMaxPendingOpens)
	for index := 0; index < MuxMaxPendingOpens; index++ {
		go func() { _, err := client.OpenTCP(ctx, OpenRequest{Host: "127.0.0.1", Port: port}); results <- err }()
		awaitAdmission(test, client, index+1)
	}
	if _, err := client.OpenTCP(ctx, OpenRequest{Host: "127.0.0.1", Port: port}); err != ErrStreamLimit {
		test.Fatal(err)
	}
	if client.Stats().AdmissionRejected != 1 || client.Stats().Opened != 1 {
		test.Fatal(client.Stats())
	}
	client.Close()
	for index := 0; index < MuxMaxPendingOpens; index++ {
		if err := <-results; err != ErrReset {
			test.Fatal(err)
		}
	}
	awaitAdmission(test, client, 0)
	if client.Stats().AdmissionCancelled != MuxMaxPendingOpens {
		test.Fatal(client.Stats())
	}
}

func TestAdmissionDeadlineAndImmediateCounter(test *testing.T) {
	port := muxFixture(test, muxEcho)
	ctx, client, _ := muxPair(test, port, 1, 1)
	muxOpen(test, ctx, client, port)
	if _, err := client.OpenTCP(ctx, OpenRequest{Host: "127.0.0.1", Port: port}); err != ErrStreamLimit {
		test.Fatal(err)
	}
	if client.Stats().AdmissionRejected != 1 || client.Stats().OpenErrors != 0 {
		test.Fatal(client.Stats())
	}
	deadline := make(chan time.Time, 1)
	deadline <- time.Now()
	client.mu.Lock()
	client.config.WaitForSlot = true
	err := client.admitLocked(ctx, false, deadline)
	client.mu.Unlock()
	if err != ErrReset || client.Stats().AdmissionTimeouts != 1 || client.Stats().AdmissionWaiting != 0 {
		test.Fatal(err, client.Stats())
	}
}

func TestAdmissionLeaseReserveAndUnconfiguredPeer(test *testing.T) {
	for _, configured := range []bool{true, false} {
		test.Run(map[bool]string{true: "reserved", false: "unconfigured"}[configured], func(test *testing.T) {
			port := muxFixture(test, muxEcho)
			ctx, client, server := muxPair(test, port, 4, 4)
			if configured {
				server.mu.Lock()
				server.config.LeaseRenewal = func(ctx context.Context, stream *MuxStream) { stream.Write([]byte{42}); io.Copy(io.Discard, stream) }
				server.mu.Unlock()
			}
			var flows []*MuxStream
			for index := 0; index < 4; index++ {
				flows = append(flows, muxOpen(test, ctx, client, port))
			}
			lease, err := client.OpenTCP(ctx, OpenRequest{Host: LeaseRenewalHost, Port: 1})
			if !configured {
				if err == nil {
					lease.Reset()
					test.Fatal("unconfigured control bypassed capacity/policy")
				}
				return
			}
			if err != nil {
				test.Fatal(err)
			}
			defer lease.Reset()
			var response [1]byte
			if _, err := io.ReadFull(lease, response[:]); err != nil || response[0] != 42 {
				test.Fatal(err)
			}
			if _, err := client.OpenTCP(ctx, OpenRequest{Host: LeaseRenewalHost, Port: 1}); err != ErrStreamLimit {
				test.Fatal("unbounded control reserve", err)
			}
			if client.Stats().LeaseRejected != 1 || server.Stats().ActiveSockets != 4 || server.Stats().ActiveStreams != 5 {
				test.Fatal(client.Stats(), server.Stats())
			}
			for _, stream := range flows {
				if err := exactMux(stream, []byte("sibling remains usable")); err != nil {
					test.Fatal(err)
				}
			}
		})
	}
}
