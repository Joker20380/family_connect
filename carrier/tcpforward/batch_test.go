package tcpforward

import (
	"bytes"
	"context"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

type batchRecorder struct{ writes chan [][]byte }

func (point *batchRecorder) SendContext(ctx context.Context, payload []byte) error {
	return point.SendBatchContext(ctx, [][]byte{payload})
}
func (point *batchRecorder) SendBatchContext(ctx context.Context, payloads [][]byte) error {
	select {
	case point.writes <- payloads:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}
func (point *batchRecorder) Recv(ctx context.Context) ([]byte, error) {
	<-ctx.Done()
	return nil, ctx.Err()
}
func (point *batchRecorder) Close() error { return nil }

func TestBatchAuthenticatedLossyMux(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	clientSession, serverSession := authenticatedPair(test, ctx)
	port := muxFixture(test, muxEcho)
	client, err := NewMux(ctx, clientSession, false, MuxConfig{MaxStreams: 4})
	if err != nil {
		test.Fatal(err)
	}
	defer client.Close()
	server, err := NewMux(ctx, serverSession, true, MuxConfig{MaxStreams: 4, Policy: Policy{TestOnlyLoopbackPort: port}})
	if err != nil {
		test.Fatal(err)
	}
	defer server.Close()
	streams := make([]*MuxStream, 3)
	for index := range streams {
		streams[index] = muxOpen(test, ctx, client, port)
	}
	done := make(chan error, len(streams))
	for index, stream := range streams {
		payload := bytes.Repeat([]byte{byte(index)}, 32<<10)
		go func() { done <- exactMux(stream, payload) }()
	}
	for range streams {
		if err := <-done; err != nil {
			test.Fatal(err)
		}
	}
	retransmissions := clientSession.ReliabilityStats().Retransmissions + serverSession.ReliabilityStats().Retransmissions
	if retransmissions == 0 {
		test.Fatal("loss fixture not exercised")
	}
	test.Logf("byte_exact=true loss_and_duplicates=true retransmissions=%d", retransmissions)
}

func queuedBatchMux(ctx context.Context, point *batchRecorder) *Mux {
	ctx, cancel := context.WithCancel(ctx)
	mux := &Mux{ctx: ctx, cancel: cancel, endpoint: point, batchSend: point.SendBatchContext, streams: make(map[uint32]*MuxStream), changed: make(chan struct{})}
	for index := 0; index < 30; index++ {
		id := uint32(1 + index*2)
		stream := mux.makeStreamLocked(id)
		stream.opened = true
		stream.send = []muxFrame{{dataFrame, id, []byte{byte(index)}}}
	}
	for index := 0; index < 24; index++ {
		mux.control = append(mux.control, muxFrame{resetFrame, 99, nil})
	}
	return mux
}

func TestBatchSchedulerOrderBoundsAndImmediate(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	point := &batchRecorder{writes: make(chan [][]byte, 64)}
	expected := queuedBatchMux(ctx, point)
	var wire [][]byte
	for {
		frame, ok := expected.nextLocked()
		if !ok {
			break
		}
		wire = append(wire, frame.encode())
	}
	mux := queuedBatchMux(ctx, point)
	done := make(chan struct{})
	go func() { mux.writeLoop(); close(done) }()
	offset, batches := 0, 0
	for offset < len(wire) {
		select {
		case frames := <-point.writes:
			if len(frames) > familysession.MaxBatchMessages {
				test.Fatal("message bound")
			}
			size := 0
			for _, payload := range frames {
				if offset >= len(wire) || !bytes.Equal(payload, wire[offset]) {
					test.Fatal("scheduler order changed")
				}
				size += familysession.BatchMessageHeaderSize + len(payload)
				offset++
			}
			if size > familysession.MaxBatchPlaintext {
				test.Fatal("byte bound")
			}
			batches++
		case <-ctx.Done():
			test.Fatal("ready frames were delayed")
		}
	}
	cancel()
	<-done
	if batches != 2 {
		test.Fatalf("54 ready frames should use two writes: %d", batches)
	}
}

type batchingPipe struct {
	*packetPipe
	calls atomic.Int32
}

func (point *batchingPipe) SendBatchContext(ctx context.Context, payloads [][]byte) error {
	point.calls.Add(1)
	for _, payload := range payloads {
		if err := point.SendContext(ctx, payload); err != nil {
			return err
		}
	}
	return nil
}

func TestBatchMixedPeerBulkAndSlotRelease(test *testing.T) {
	for _, sides := range []string{"client", "server", "both"} {
		test.Run(sides, func(test *testing.T) {
			port := muxFixture(test, muxEcho)
			ctx, cancel := context.WithTimeout(context.Background(), 12*time.Second)
			defer cancel()
			left, right := pipePair()
			var clientPoint, serverPoint familysession.PacketEndpoint = left, right
			if sides != "server" {
				clientPoint = &batchingPipe{packetPipe: left}
			}
			if sides != "client" {
				serverPoint = &batchingPipe{packetPipe: right}
			}
			client := newMux(ctx, clientPoint, false, MuxConfig{MaxStreams: 1, WaitForSlot: true})
			server := newMux(ctx, serverPoint, true, MuxConfig{MaxStreams: 1, Policy: Policy{TestOnlyLoopbackPort: port}})
			defer client.Close()
			defer server.Close()
			for cycle := 0; cycle < 3; cycle++ {
				stream := muxOpen(test, ctx, client, port)
				if err := exactMux(stream, bytes.Repeat([]byte{byte(cycle)}, 128<<10)); err != nil {
					test.Fatal(err)
				}
			}
			deadline := time.Now().Add(time.Second)
			for client.Stats().ActiveStreams != 0 || server.Stats().ActiveStreams != 0 {
				if time.Now().After(deadline) {
					test.Fatal("completed slots retained")
				}
				time.Sleep(time.Millisecond)
			}
		})
	}
}

func TestBatchCarriedTerminalNotRemovedEarly(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	point := &batchRecorder{writes: make(chan [][]byte)}
	mux := &Mux{ctx: ctx, cancel: cancel, endpoint: point, batchSend: point.SendBatchContext, streams: make(map[uint32]*MuxStream), changed: make(chan struct{})}
	stream := mux.makeStreamLocked(1)
	stream.terminal = ErrReset
	stream.send = []muxFrame{{dataFrame, 1, make([]byte, 16330)}, {resetFrame, 1, nil}}
	done := make(chan struct{})
	go func() { mux.writeLoop(); close(done) }()
	<-point.writes
	mux.mu.Lock()
	retained := mux.streams[1] != nil
	mux.mu.Unlock()
	if !retained {
		test.Fatal("removed before terminal frame sent")
	}
	select {
	case frames := <-point.writes:
		frame, err := decodeMux(frames[0])
		if err != nil || frame.kind != resetFrame {
			test.Fatal("terminal lost")
		}
	case <-ctx.Done():
		test.Fatal("carried terminal not sent")
	}
	cancel()
	<-done
	mux.mu.Lock()
	remaining := len(mux.streams)
	mux.mu.Unlock()
	if remaining != 0 {
		test.Fatal("terminal stream retained")
	}
}
