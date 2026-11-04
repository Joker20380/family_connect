package reliablestream

import (
	"context"
	"errors"
	"sync/atomic"
	"testing"
	"time"
)

func idleEngine(test *testing.T, window int) (*engine, *engine, time.Time) {
	test.Helper()
	states := connectedEngines()
	sender, peer := states[0], states[1]
	sender.config.SendWindow = window
	now := sender.started
	packet, err := sender.send([]byte("fully acknowledged before media loss"), now)
	if err != nil {
		test.Fatal(err)
	}
	if _, err = peer.input(packet, now); err != nil {
		test.Fatal(err)
	}
	_, ack := peer.consume()
	if _, err = sender.input(ack, now); err != nil || len(sender.sent) != 0 {
		test.Fatal("window not drained", err)
	}
	return sender, peer, now
}

func TestIdleACKStarvationExpiresWithoutPendingData(test *testing.T) {
	for _, window := range []int{8, 32} {
		sender, _, now := idleEngine(test, window)
		if _, err := sender.tick(now.Add(sender.config.MaxAge - time.Nanosecond)); err != nil {
			test.Fatal("idle deadline shortened", err)
		}
		if _, err := sender.tick(now.Add(sender.config.MaxAge)); !errors.Is(err, ErrExhausted) {
			test.Fatal("dead idle carrier still owns its session", err)
		}
		failure := sender.failureTrace
		if failure.Reason != "RELIABLE_IDLE_TIMEOUT" || failure.CloseSource != "RELIABLE_EXHAUSTION" ||
			failure.ReliablePending != 0 || failure.ReliableAgeMS != 0 || failure.ReliableRetries != 0 ||
			failure.ReliableACKAgeMS != uint64(sender.config.MaxAge/time.Millisecond) {
			test.Fatal("idle loss misreported as pending DATA exhaustion", failure)
		}
	}
}

func TestIdleACKRefreshPreservesLiveQuietPeer(test *testing.T) {
	sender, peer, now := idleEngine(test, 32)
	for interval := 0; interval < 20; interval++ {
		now = now.Add(sender.config.MaxAge - sender.config.RTO)
		if _, err := sender.tick(now); err != nil {
			test.Fatal("recoverable interruption terminated the session", err)
		}
		if _, err := sender.input(peer.ack(), now); err != nil {
			test.Fatal(err)
		}
	}
	if sender.failureTrace.Reason != "" || sender.stats.Retransmissions != 0 {
		test.Fatal("quiet peer required application traffic or retries")
	}
	if _, err := sender.send([]byte("resume after quiet periods"), now); err != nil {
		test.Fatal(err)
	}
}

func TestIdleStaleACKCannotExtendDeadline(test *testing.T) {
	for _, foreign := range []bool{false, true} {
		sender, peer, now := idleEngine(test, 8)
		packet := peer.ack()
		if foreign {
			packet.source = epoch{3}
		} else {
			packet.ack--
		}
		if _, err := sender.input(packet, now.Add(sender.config.MaxAge-time.Millisecond)); err != nil {
			test.Fatal(err)
		}
		if _, err := sender.tick(now.Add(sender.config.MaxAge)); !errors.Is(err, ErrExhausted) {
			test.Fatal("stale or foreign ACK kept dead session alive", err)
		}
	}
}

func TestIdleDeadlineStartsAtNegotiationWithoutFirstACK(test *testing.T) {
	config := DefaultConfig()
	started := time.Unix(100, 0)
	state := newEngine(config, epoch{1}, started)
	peer := newEngine(config, epoch{2}, started)
	negotiated := started.Add(config.MaxAge - time.Millisecond)
	if _, err := state.input(peer.opening(state.local), negotiated); err != nil {
		test.Fatal(err)
	}
	if _, err := state.tick(negotiated.Add(config.MaxAge - time.Nanosecond)); err != nil {
		test.Fatal("late negotiation inherited the handshake age", err)
	}
	if _, err := state.input(peer.opening(state.local), negotiated.Add(config.MaxAge-time.Millisecond)); err != nil {
		test.Fatal(err)
	}
	if _, err := state.tick(negotiated.Add(config.MaxAge)); !errors.Is(err, ErrExhausted) || state.failureTrace.Reason != "RELIABLE_IDLE_TIMEOUT" {
		test.Fatal("missing first ACK or repeated OPEN bypassed idle expiry", err)
	}
}

func TestIdleMediaLossClosesBothStreamsWithoutRemoteReset(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 4*time.Second)
	defer cancel()
	leftEndpoint, rightEndpoint := endpoints()
	var blocked atomic.Bool
	leftEndpoint.drop = func([]byte) bool { return blocked.Load() }
	rightEndpoint.drop = leftEndpoint.drop
	config := DefaultConfig()
	config.RTO, config.MaxAge = 20*time.Millisecond, 200*time.Millisecond
	left, err := New(ctx, leftEndpoint, config)
	if err != nil {
		test.Fatal(err)
	}
	defer left.Close()
	right, err := New(ctx, rightEndpoint, config)
	if err != nil {
		test.Fatal(err)
	}
	defer right.Close()
	if err := left.SendContext(ctx, []byte("warmup")); err != nil {
		test.Fatal(err)
	}
	if _, err := right.Recv(ctx); err != nil {
		test.Fatal(err)
	}
	for left.Stats().SendDepth != 0 || left.Stats().ACKReceived == 0 || right.Stats().ACKReceived == 0 {
		select {
		case <-time.After(time.Millisecond):
		case <-ctx.Done():
			test.Fatal("initial ACK exchange did not settle")
		}
	}
	blocked.Store(true)
	for _, stream := range []*Stream{left, right} {
		if _, err := stream.Recv(ctx); !errors.Is(err, ErrExhausted) {
			test.Fatal("idle blackhole survived until outer cancellation", err)
		}
		stream.Close()
		if stats := stream.Stats(); stats.Terminal != "recovery_exhausted" || stats.BufferedBytes != 0 || stats.Retransmissions != 0 {
			test.Fatal("idle failure did not join and release cleanly", stats.Terminal)
		}
	}
}
