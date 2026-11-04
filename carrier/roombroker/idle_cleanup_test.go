package roombroker

import (
	"context"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/reliablestream"
)

type idleOwnerEndpoint struct {
	packets
	blocked *atomic.Bool
}

func (point idleOwnerEndpoint) SendContext(ctx context.Context, data []byte) error {
	if point.blocked.Load() {
		return nil
	}
	return point.packets.SendContext(ctx, data)
}

type idleOwnerGateway struct {
	stream  *reliablestream.Stream
	closing chan struct{}
	release chan struct{}
}

func (gateway *idleOwnerGateway) Run(ctx context.Context, _ func() error) error {
	_, err := gateway.stream.Recv(ctx)
	return err
}

func (gateway *idleOwnerGateway) Close() error {
	close(gateway.closing)
	<-gateway.release
	return gateway.stream.Close()
}

func TestIdleMediaLossWaitsForOwnerCleanupBeforeReacquisition(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	forward, reverse := make(chan []byte, 32), make(chan []byte, 32)
	var blocked atomic.Bool
	clientEndpoint := idleOwnerEndpoint{packets{reverse, forward, make(chan struct{}), new(sync.Once)}, &blocked}
	serverEndpoint := idleOwnerEndpoint{packets{forward, reverse, make(chan struct{}), new(sync.Once)}, &blocked}
	config := reliablestream.DefaultConfig()
	config.RTO, config.MaxAge = 20*time.Millisecond, 500*time.Millisecond
	client, err := reliablestream.New(ctx, clientEndpoint, config)
	if err != nil {
		test.Fatal(err)
	}
	defer client.Close()
	server, err := reliablestream.New(ctx, serverEndpoint, config)
	if err != nil {
		test.Fatal(err)
	}
	defer server.Close()
	if err := server.SendContext(ctx, []byte("last response before quiet session")); err != nil {
		test.Fatal(err)
	}
	if _, err := client.Recv(ctx); err != nil {
		test.Fatal(err)
	}
	for server.Stats().SendDepth != 0 || server.Stats().ACKReceived == 0 || client.Stats().ACKReceived == 0 {
		select {
		case <-time.After(time.Millisecond):
		case <-ctx.Done():
			test.Fatal("last response was not acknowledged")
		}
	}
	broker := observedBroker(test)
	gateway := &idleOwnerGateway{server, make(chan struct{}), make(chan struct{})}
	release := sync.OnceFunc(func() { close(gateway.release) })
	defer release()
	broker.gateway = gatewayFunc(func(context.Context, context.Context, Room, string, Identity) (Gateway, error) { return gateway, nil })
	previous := observedActive(test, broker, ctx, allow)
	waiting := WithExchange(ctx, strings.Repeat("a", 64))
	type acquired struct {
		id  string
		err error
	}
	ready := make(chan acquired, 1)
	go func() { id, err := broker.ChallengeAfterCleanup(waiting, allow); ready <- acquired{id, err} }()
	observedEvent(test, broker, "wait", exchangeTag(waiting))
	if _, err := broker.Challenge(ctx, allow); err != Code("device_busy") {
		test.Fatal("waiter preempted healthy owner", err)
	}
	blocked.Store(true)
	select {
	case <-gateway.closing:
	case <-ctx.Done():
		test.Fatal("idle loss left broker owner active until parent expiry")
	}
	if ctx.Err() != nil || server.Stats().Terminal != "recovery_exhausted" {
		test.Fatal("idle loss did not initiate cleanup")
	}
	select {
	case <-ready:
		test.Fatal("new owner admitted before gateway cleanup finished")
	default:
	}
	if _, err := broker.Challenge(ctx, allow); err != Code("device_busy") {
		test.Fatal("cleaning owner released prematurely", err)
	}
	release()
	select {
	case next := <-ready:
		if next.err != nil || next.id == previous || next.id == "" {
			test.Fatal("next owner not acquired after cleanup", next.err)
		}
	case <-ctx.Done():
		test.Fatal("cleanup did not unblock authenticated reacquisition")
	}
	if err := broker.Cancel(ctx, previous, allow); err != Code("stale_or_unbound_setup") {
		test.Fatal("old owner could cancel a replacement", err)
	}
	if _, err := broker.Challenge(ctx, allow); err != Code("device_busy") {
		test.Fatal("stale cleanup released replacement", err)
	}
}
