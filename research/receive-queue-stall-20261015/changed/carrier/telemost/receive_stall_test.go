package telemost

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"runtime"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/reliablestream"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

type stallEndpoint struct {
	session    *Session
	peer       *stallEndpoint
	mu         sync.Mutex
	gate       chan struct{}
	entered    chan struct{}
	lastACK    []byte
	received   atomic.Int64
	activeSend atomic.Int64
	activeRecv atomic.Int64
	closeGate  chan struct{}
	closing    chan struct{}
	closeOnce  sync.Once
}

func (point *stallEndpoint) SendContext(ctx context.Context, payload []byte) error {
	point.activeSend.Add(1)
	defer point.activeSend.Add(-1)
	point.mu.Lock()
	gate := point.gate
	if gate != nil && point.entered != nil {
		close(point.entered)
		point.entered = nil
	}
	if len(payload) >= 64 && payload[4] == 3 {
		point.lastACK = append([]byte(nil), payload...)
	}
	point.mu.Unlock()
	if gate != nil {
		select {
		case <-gate:
		case <-ctx.Done():
			return ctx.Err()
		case <-point.session.closeCh:
			return ErrClosed
		}
	}
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-point.session.closeCh:
		return ErrClosed
	default:
	}
	point.peer.session.deliver(append([]byte(nil), payload...))
	return nil
}

func (point *stallEndpoint) Recv(ctx context.Context) ([]byte, error) {
	point.activeRecv.Add(1)
	defer point.activeRecv.Add(-1)
	payload, err := point.session.Recv(ctx)
	if err == nil {
		point.received.Add(1)
	}
	return payload, err
}

func (point *stallEndpoint) Close() error {
	point.closeOnce.Do(func() {
		if point.closing != nil {
			close(point.closing)
		}
		if point.closeGate != nil {
			<-point.closeGate
		}
	})
	return point.session.Close()
}

func waitStall(t *testing.T, label string, predicate func() bool) bool {
	t.Helper()
	deadline := time.NewTimer(400 * time.Millisecond)
	defer deadline.Stop()
	for !predicate() {
		select {
		case <-deadline.C:
			t.Log("gate timeout", label)
			return false
		default:
			runtime.Gosched()
		}
	}
	return true
}

func stallPair(t *testing.T) (*stallEndpoint, *stallEndpoint, *reliablestream.Stream, *reliablestream.Stream) {
	t.Helper()
	points := make([]*stallEndpoint, 2)
	for index := range points {
		session, err := New(context.Background(), Config{RoomURL: "local-fixture-no-provider", Trace: sessiontrace.New(strings.Repeat(fmt.Sprint(index+1), 64), nil)})
		if err != nil {
			t.Fatal(err)
		}
		if cap(session.recvQueue) != 16 || cap(session.sendQueue) != 256 {
			t.Fatal("production capacity changed")
		}
		points[index] = &stallEndpoint{session: session}
	}
	points[0].peer, points[1].peer = points[1], points[0]
	left, err := reliablestream.New(context.Background(), points[0], reliablestream.DefaultConfig())
	if err != nil {
		t.Fatal(err)
	}
	right, err := reliablestream.New(context.Background(), points[1], reliablestream.DefaultConfig())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { left.Close(); right.Close() })
	return points[0], points[1], left, right
}

func exchangeStall(t *testing.T, sender, receiver *reliablestream.Stream, payload []byte) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	sent := make(chan error, 1)
	go func() { sent <- sender.SendContext(ctx, payload) }()
	received, err := receiver.Recv(ctx)
	if err != nil || !bytes.Equal(received, payload) {
		t.Fatalf("byte exact delivery: %v length=%d want=%d", err, len(received), len(payload))
	}
	if err := <-sent; err != nil {
		t.Fatal(err)
	}
}

func blockStall(t *testing.T, point *stallEndpoint, stream *reliablestream.Stream) (func(), chan error) {
	t.Helper()
	gate, entered := make(chan struct{}), make(chan struct{})
	point.mu.Lock()
	point.gate = gate
	point.entered = entered
	point.mu.Unlock()
	sent := make(chan error, 1)
	go func() { sent <- stream.SendContext(context.Background(), []byte("outbound-gated")) }()
	select {
	case <-entered:
	case <-time.After(time.Second):
		t.Fatal("transmit did not enter SendContext")
	}
	var once sync.Once
	unblock := func() { once.Do(func() { close(gate) }) }
	t.Cleanup(unblock)
	return unblock, sent
}

func TestReceiveStallControlAndSlowConsumer(t *testing.T) {
	_, _, left, right := stallPair(t)
	exchangeStall(t, left, right, []byte("left-control"))
	exchangeStall(t, right, left, []byte("right-control"))
	baseline := left.Stats().DataReceived
	for index := 0; index < 8; index++ {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		err := right.SendContext(ctx, []byte{byte(index)})
		cancel()
		if err != nil {
			t.Fatal(err)
		}
	}
	if !waitStall(t, "slow upper consumer still accepts bounded DATA", func() bool { return left.Stats().DataReceived == baseline+8 }) {
		t.Fatal("upper consumer blocked incoming")
	}
	for index := 0; index < 8; index++ {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		payload, err := left.Recv(ctx)
		cancel()
		if err != nil || !bytes.Equal(payload, []byte{byte(index)}) {
			t.Fatal("slow consumer lost order", err)
		}
	}
	exchangeStall(t, left, right, []byte("after-drain"))
}

func TestReceiveStallProgress(t *testing.T) {
	point, _, left, right := stallPair(t)
	exchangeStall(t, left, right, []byte("warm"))
	_, sent := blockStall(t, point, left)
	baseline := left.Stats().DataReceived
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	if err := right.SendContext(ctx, []byte("inbound-during-block")); err != nil {
		t.Fatal(err)
	}
	if !waitStall(t, "DATA processing while transmit blocked", func() bool { return left.Stats().DataReceived > baseline }) {
		t.Fatalf("PROGRESS_DEFECT: transmit blocked; real Recv returns=%d recvQueue=%d DataReceived=%d", point.received.Load(), len(point.session.recvQueue), left.Stats().DataReceived)
	}
	payload, err := left.Recv(ctx)
	if err != nil || string(payload) != "inbound-during-block" {
		t.Fatal("inbound progress", err)
	}
	left.Close()
	select {
	case err := <-sent:
		if err == nil {
			t.Fatal("blocked send accepted on cancel")
		}
	case <-time.After(time.Second):
		t.Fatal("blocked send worker leaked")
	}
}

func TestReceiveStallBoundedBurst(t *testing.T) {
	for _, count := range []int{8, 20, 40} {
		t.Run(fmt.Sprint(count), func(t *testing.T) {
			point, peer, left, right := stallPair(t)
			exchangeStall(t, left, right, []byte("warm"))
			if !waitStall(t, "ACK captured", func() bool { peer.mu.Lock(); defer peer.mu.Unlock(); return len(peer.lastACK) > 0 }) {
				t.Fatal("missing ACK")
			}
			peer.mu.Lock()
			packet := append([]byte(nil), peer.lastACK...)
			peer.mu.Unlock()
			_, _ = blockStall(t, point, left)
			baseline := left.Stats().ACKReceived
			for index := 0; index < count; index++ {
				point.session.deliver(packet)
				deadline := time.Now().Add(5 * time.Millisecond)
				for left.Stats().ACKReceived < baseline+uint64(index+1) && time.Now().Before(deadline) {
					runtime.Gosched()
				}
			}
			raw, _ := json.Marshal(point.session.cfg.Trace.Snapshot())
			t.Logf("burst=%d received=%d ACKReceived=%d recvQueue=%d closed=%v", count, point.received.Load(), left.Stats().ACKReceived, len(point.session.recvQueue), point.session.closed.Load())
			if point.session.closed.Load() || strings.Contains(string(raw), "RECEIVE_QUEUE_FULL") {
				t.Fatal("bounded control replay overflowed despite active consumer")
			}
			if !waitStall(t, "all bounded ACKs processed", func() bool { return left.Stats().ACKReceived >= baseline+uint64(count) }) {
				t.Fatal("ACK progress stopped by transmit")
			}
		})
	}
}

func TestReceiveStallSequentialCleanup(t *testing.T) {
	for _, hold := range []bool{false, true} {
		t.Run(fmt.Sprint(hold), func(t *testing.T) {
			old, _, oldLeft, oldRight := stallPair(t)
			exchangeStall(t, oldLeft, oldRight, []byte("A"))
			if hold {
				old.closeGate = make(chan struct{})
				old.closing = make(chan struct{})
			}
			closed := make(chan struct{})
			go func() { oldLeft.Close(); close(closed) }()
			if hold {
				select {
				case <-old.closing:
				case <-time.After(time.Second):
					t.Fatal("cleanup not reached")
				}
			} else {
				<-closed
			}
			fresh, _, left, right := stallPair(t)
			if old.session.recvQueue == fresh.session.recvQueue {
				t.Fatal("queue inherited")
			}
			exchangeStall(t, left, right, []byte("B-before-old-cleanup"))
			old.session.deliver([]byte("late-A"))
			if hold {
				close(old.closeGate)
				<-closed
			}
			exchangeStall(t, right, left, []byte("B-after-old-cleanup"))
			_, _ = blockStall(t, fresh, left)
			baseline := left.Stats().DataReceived
			ctx, cancel := context.WithTimeout(context.Background(), time.Second)
			defer cancel()
			if err := right.SendContext(ctx, []byte("B-progress")); err != nil {
				t.Fatal(err)
			}
			if !waitStall(t, "B progress", func() bool { return left.Stats().DataReceived > baseline }) {
				t.Fatal("B stalled like fresh session")
			}
		})
	}
}

func TestReceiveStallActualSendQueueCancellation(t *testing.T) {
	session, err := New(context.Background(), Config{RoomURL: "local-fixture-no-provider", Mode: ModeVP8})
	if err != nil {
		t.Fatal(err)
	}
	defer session.Close()
	session.subReady.Store(true)
	session.pubReady.Store(true)
	for index := 0; index < cap(session.sendQueue); index++ {
		if err := session.SendContext(context.Background(), []byte{1}); err != nil {
			t.Fatal(err)
		}
	}
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	go func() { done <- session.SendContext(ctx, []byte{2}) }()
	cancel()
	select {
	case err := <-done:
		if err != context.Canceled {
			t.Fatal(err)
		}
	case <-time.After(time.Second):
		t.Fatal("real SendContext failed cancellation")
	}
	t.Logf("real sendQueue=%d/%d recvQueue=%d/%d", len(session.sendQueue), cap(session.sendQueue), len(session.recvQueue), cap(session.recvQueue))
}

func TestReceiveStallResumeByteExact(t *testing.T) {
	point, _, left, right := stallPair(t)
	exchangeStall(t, left, right, []byte("warm"))
	unblock, sent := blockStall(t, point, left)
	baseline := left.Stats().DataReceived
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	if err := right.SendContext(ctx, []byte("reverse-during-block")); err != nil {
		t.Fatal(err)
	}
	if !waitStall(t, "reverse progress", func() bool { return left.Stats().DataReceived > baseline }) {
		t.Fatal("reverse stalled")
	}
	payload, err := left.Recv(ctx)
	if err != nil || string(payload) != "reverse-during-block" {
		t.Fatal("reverse mismatch", err)
	}
	unblock()
	if err := <-sent; err != nil {
		t.Fatal(err)
	}
	payload, err = right.Recv(ctx)
	if err != nil || string(payload) != "outbound-gated" {
		t.Fatal("gated write mismatch", err)
	}
	for index := 0; index < 32; index++ {
		payload := bytes.Repeat([]byte{byte(index)}, []int{13, 4096, 16384}[index%3])
		exchangeStall(t, left, right, payload)
		exchangeStall(t, right, left, payload)
	}
	left.Close()
	right.Close()
	if point.activeSend.Load() != 0 || point.activeRecv.Load() != 0 {
		t.Fatal("endpoint workers survived Close")
	}
}

func TestReceiveStallPersistentBlockBounded(t *testing.T) {
	point, peer, left, right := stallPair(t)
	exchangeStall(t, left, right, []byte("warm"))
	if !waitStall(t, "ACK captured", func() bool { peer.mu.Lock(); defer peer.mu.Unlock(); return len(peer.lastACK) > 0 }) {
		t.Fatal("missing ACK")
	}
	peer.mu.Lock()
	packet := append([]byte(nil), peer.lastACK...)
	peer.mu.Unlock()
	_, sent := blockStall(t, point, left)
	baseline := left.Stats().ACKReceived
	for index := 0; index < 128; index++ {
		point.session.deliver(packet)
		if !waitStall(t, "bounded continuous control", func() bool { return left.Stats().ACKReceived >= baseline+uint64(index+1) }) {
			t.Fatal("incoming starvation")
		}
	}
	select {
	case err := <-sent:
		if err != context.DeadlineExceeded {
			t.Fatalf("expected existing transmit deadline, got %v", err)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("unbounded blocked write")
	}
	left.Close()
	if point.activeSend.Load() != 0 || point.activeRecv.Load() != 0 {
		t.Fatal("endpoint workers survived Close")
	}
	if cap(point.session.recvQueue) != 16 || cap(point.session.sendQueue) != 256 {
		t.Fatal("capacity changed")
	}
}

func TestReceiveStallCoalescedACK(t *testing.T) {
	point, _, left, right := stallPair(t)
	exchangeStall(t, left, right, []byte("warm"))
	unblock, sent := blockStall(t, point, left)
	baseline := left.Stats().DataReceived
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	for index := 0; index < 8; index++ {
		if err := right.SendContext(ctx, []byte{byte(index)}); err != nil {
			t.Fatal(err)
		}
	}
	if !waitStall(t, "whole default window while writer blocked", func() bool { return left.Stats().DataReceived >= baseline+8 }) {
		t.Fatal("window reception stalled")
	}
	for index := 0; index < 8; index++ {
		payload, err := left.Recv(ctx)
		if err != nil || !bytes.Equal(payload, []byte{byte(index)}) {
			t.Fatal("coalescing changed payload order", err)
		}
	}
	unblock()
	if err := <-sent; err != nil {
		t.Fatal(err)
	}
	if !waitStall(t, "latest cumulative ACK frees entire peer window", func() bool { return right.Stats().Flow.Pending == 0 }) {
		t.Fatal("coalesced ACK lost progress")
	}
	payload, err := right.Recv(ctx)
	if err != nil || string(payload) != "outbound-gated" {
		t.Fatal("outbound order", err)
	}
	exchangeStall(t, right, left, []byte("window-reopened"))
}

func TestReceiveStallUnpacedGuardCharacterization(t *testing.T) {
	for _, count := range []int{8, 20, 40} {
		t.Run(fmt.Sprint(count), func(t *testing.T) {
			point, peer, left, right := stallPair(t)
			exchangeStall(t, left, right, []byte("warm"))
			if !waitStall(t, "ACK captured", func() bool { peer.mu.Lock(); defer peer.mu.Unlock(); return len(peer.lastACK) > 0 }) {
				t.Fatal("missing ACK")
			}
			peer.mu.Lock()
			packet := append([]byte(nil), peer.lastACK...)
			peer.mu.Unlock()
			baseline := left.Stats().ACKReceived
			for index := 0; index < count; index++ {
				point.session.deliver(packet)
			}
			if point.session.closed.Load() {
				raw, _ := json.Marshal(point.session.cfg.Trace.Snapshot())
				if !strings.Contains(string(raw), "RECEIVE_QUEUE_FULL") {
					t.Fatal("unexpected close")
				}
				t.Logf("unpaced=%d EXPECTED_BOUNDED_OVERLOAD_GUARD queue=%d", count, len(point.session.recvQueue))
			} else {
				if !waitStall(t, "unpaced accepted control drained", func() bool { return left.Stats().ACKReceived >= baseline+uint64(count) }) {
					t.Fatal("unexpected progress failure")
				}
				t.Logf("unpaced=%d DRAINED", count)
			}
		})
	}
}
