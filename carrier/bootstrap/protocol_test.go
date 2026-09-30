package bootstrap

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/roombroker"
)

type pipe struct {
	in, out chan []byte
	done    chan struct{}
	once    *sync.Once
}

func pair() (*pipe, *pipe) {
	forward, reverse, done := make(chan []byte, 32), make(chan []byte, 32), make(chan struct{})
	once := &sync.Once{}
	return &pipe{reverse, forward, done, once}, &pipe{forward, reverse, done, once}
}
func (endpoint *pipe) SendContext(ctx context.Context, raw []byte) error {
	select {
	case endpoint.out <- bytes.Clone(raw):
		return nil
	case <-endpoint.done:
		return errors.New("closed")
	case <-ctx.Done():
		return ctx.Err()
	}
}
func (endpoint *pipe) Recv(ctx context.Context) ([]byte, error) {
	select {
	case raw := <-endpoint.in:
		return raw, nil
	default:
	}
	select {
	case raw := <-endpoint.in:
		return raw, nil
	case <-endpoint.done:
		return nil, errors.New("closed")
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}
func (endpoint *pipe) Close() error { endpoint.once.Do(func() { close(endpoint.done) }); return nil }

type providerFunc func(context.Context) (roombroker.Room, error)

func (function providerFunc) CreateRoom(ctx context.Context) (roombroker.Room, error) {
	return function(ctx)
}

type starterFunc func(context.Context, context.Context, roombroker.Room, string, roombroker.Identity) (roombroker.Gateway, error)

func (function starterFunc) Start(ctx, ready context.Context, room roombroker.Room, id string, identity roombroker.Identity) (roombroker.Gateway, error) {
	return function(ctx, ready, room, id, identity)
}

type gateway struct {
	closed chan struct{}
	once   sync.Once
}

func (gateway *gateway) Close() error { gateway.once.Do(func() { close(gateway.closed) }); return nil }
func (gateway *gateway) Run(ctx context.Context, _ func() error) error {
	<-ctx.Done()
	return ctx.Err()
}

func allow(context.Context) (roombroker.Identity, error) {
	return roombroker.Identity{Family: testFamily, Device: testGateway}, nil
}
func testBroker(test *testing.T, calls *atomic.Int32, ready <-chan struct{}, failure string, overrides ...roombroker.Limits) (*roombroker.Broker, *gateway) {
	back := &gateway{closed: make(chan struct{})}
	limits := roombroker.DefaultLimits()
	limits.Recheck = time.Millisecond
	if len(overrides) > 0 {
		limits = overrides[0]
	}
	broker, err := roombroker.New(providerFunc(func(ctx context.Context) (roombroker.Room, error) {
		calls.Add(1)
		if failure == "provider" {
			return roombroker.Room{}, errors.New("private provider error")
		}
		return roombroker.Room{ID: "test", JoinURL: "https://telemost.yandex.ru/j/dedicated-test"}, nil
	}), starterFunc(func(ctx, bound context.Context, room roombroker.Room, id string, identity roombroker.Identity) (roombroker.Gateway, error) {
		if failure == "ready" {
			return nil, errors.New("not ready")
		}
		if ready != nil {
			select {
			case <-ready:
			case <-bound.Done():
				return nil, bound.Err()
			}
		}
		return back, nil
	}), limits, nil)
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(broker.Close)
	return broker, back
}

func TestGlobalOutstandingBound(test *testing.T) {
	ctx := bounded(test)
	var calls atomic.Int32
	broker, _ := testBroker(test, &calls, nil, "")
	for index := 0; index < 32; index++ {
		identity := roombroker.Identity{Family: testFamily, Device: fmt.Sprintf("%032x", index)}
		if _, err := broker.Challenge(ctx, func(context.Context) (roombroker.Identity, error) { return identity, nil }); err != nil {
			test.Fatal(err)
		}
	}
	client, server := pair()
	defer client.Close()
	if err := Exchange(ctx, server, broker, allow); err == nil || calls.Load() != 0 {
		test.Fatal("global bound")
	}
}

func TestUnusedHandoffCleanupAfterDedicatedJoinOrAuthFailure(test *testing.T) {
	for _, reason := range []string{"join_failed", "family_auth_failed", "client_crash_after_descriptor"} {
		test.Run(reason, func(test *testing.T) {
			ctx := bounded(test)
			var calls atomic.Int32
			limits := roombroker.DefaultLimits()
			limits.Recheck = time.Millisecond
			limits.Unused = 80 * time.Millisecond
			broker, back := testBroker(test, &calls, nil, "", limits)
			client, server := pair()
			done := make(chan error, 1)
			go func() { done <- Exchange(ctx, server, broker, allow) }()
			if _, err := requestTransport(ctx, client); err != nil {
				test.Fatal(err)
			}
			if err := <-done; err != nil {
				test.Fatal(err)
			}
			select {
			case <-back.closed:
			case <-ctx.Done():
				test.Fatal("unused setup leak")
			}
		})
	}
}

func TestExpiredDescriptorBeforeHandoff(test *testing.T) {
	ctx := bounded(test)
	client, server := pair()
	defer client.Close()
	done := make(chan struct{})
	go func() {
		defer close(done)
		defer server.Close()
		id := fmt.Sprintf("%064x", 1)
		_ = send(ctx, server, message{Type: "HELLO", SetupID: id})
		_, _ = receive(ctx, server, "REQUEST_TRANSPORT", id)
		_ = send(ctx, server, message{Type: "TRANSPORT_READY", SetupID: id, Descriptor: &roombroker.Descriptor{Transport: "telemost-webrtc", SetupID: id, JoinURL: "https://telemost.yandex.ru/j/test-only", ExpiresAt: time.Now().Add(-time.Second)}})
	}()
	if _, err := requestTransport(ctx, client); err == nil {
		test.Fatal("expired descriptor accepted")
	}
	<-done
}

func TestLateByeCannotReviveExpiredSetup(test *testing.T) {
	ctx := bounded(test)
	var calls atomic.Int32
	limits := roombroker.DefaultLimits()
	limits.Unused = 30 * time.Millisecond
	limits.Recheck = time.Millisecond
	broker, back := testBroker(test, &calls, nil, "", limits)
	client, server := pair()
	done := make(chan error, 1)
	go func() { done <- Exchange(ctx, server, broker, allow) }()
	raw, err := client.Recv(ctx)
	if err != nil {
		test.Fatal(err)
	}
	var hello message
	_ = json.Unmarshal(raw, &hello)
	_ = send(ctx, client, message{Type: "REQUEST_TRANSPORT", SetupID: hello.SetupID})
	if _, err := receive(ctx, client, "TRANSPORT_READY", hello.SetupID); err != nil {
		test.Fatal(err)
	}
	select {
	case <-back.closed:
	case <-ctx.Done():
		test.Fatal("expiry cleanup failed")
	}
	_ = send(ctx, client, message{Type: "BYE", SetupID: hello.SetupID})
	if err := <-done; err == nil {
		test.Fatal("expired setup handed off")
	}
}

func TestDescriptorExpiryDuringBye(test *testing.T) {
	ctx := bounded(test)
	client, server := pair()
	defer client.Close()
	done := make(chan struct{})
	go func() {
		defer close(done)
		defer server.Close()
		id := fmt.Sprintf("%064x", 1)
		_ = send(ctx, server, message{Type: "HELLO", SetupID: id})
		_, _ = receive(ctx, server, "REQUEST_TRANSPORT", id)
		expires := time.Now().Add(50 * time.Millisecond)
		_ = send(ctx, server, message{Type: "TRANSPORT_READY", SetupID: id, Descriptor: &roombroker.Descriptor{Transport: "telemost-webrtc", SetupID: id, JoinURL: "https://telemost.yandex.ru/j/test-only", ExpiresAt: expires}})
		_, _ = receive(ctx, server, "BYE", id)
		time.Sleep(time.Until(expires) + time.Millisecond)
		_ = send(ctx, server, message{Type: "BYE", SetupID: id})
	}()
	if _, err := requestTransport(ctx, client); err == nil {
		test.Fatal("expiry during BYE accepted")
	}
	<-done
}

func bounded(test *testing.T) context.Context {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	test.Cleanup(cancel)
	return ctx
}

func TestExchangeReadyHandoffAndOutstanding(test *testing.T) {
	ctx := bounded(test)
	var calls atomic.Int32
	ready := make(chan struct{})
	broker, back := testBroker(test, &calls, ready, "")
	client, server := pair()
	done := make(chan error, 1)
	go func() { done <- Exchange(ctx, server, broker, allow) }()
	result := make(chan roombroker.Descriptor, 1)
	failed := make(chan error, 1)
	go func() { descriptor, err := requestTransport(ctx, client); result <- descriptor; failed <- err }()
	select {
	case <-result:
		test.Fatal("descriptor before READY")
	case <-time.After(20 * time.Millisecond):
	}
	close(ready)
	descriptor := <-result
	if err := <-failed; err != nil {
		test.Fatal(err)
	}
	if err := <-done; err != nil {
		test.Fatal(err)
	}
	if calls.Load() != 1 || descriptor.SetupID == "" {
		test.Fatal("not broker descriptor")
	}
	if _, err := broker.Challenge(ctx, allow); err == nil {
		test.Fatal("outstanding limit")
	}
	if _, err := broker.Create(ctx, descriptor.SetupID, allow); err == nil {
		test.Fatal("replayed create")
	}
	if err := broker.Cancel(ctx, descriptor.SetupID, allow); err != nil {
		test.Fatal(err)
	}
	select {
	case <-back.closed:
	case <-ctx.Done():
		test.Fatal("gateway leak")
	}
}

func TestExchangeRejectsDataReplayAndDisconnect(test *testing.T) {
	for _, kind := range []string{"TCP_OPEN", "DNS_QUERY", "DATA", "OPEN", "raw_mux", "proxy", "oversized", "stale", "disconnect", "duplicate", "after_descriptor"} {
		test.Run(kind, func(test *testing.T) {
			ctx := bounded(test)
			var calls atomic.Int32
			broker, back := testBroker(test, &calls, nil, "")
			client, server := pair()
			done := make(chan error, 1)
			go func() { done <- Exchange(ctx, server, broker, allow) }()
			raw, err := client.Recv(ctx)
			if err != nil {
				test.Fatal(err)
			}
			var hello message
			_ = json.Unmarshal(raw, &hello)
			switch kind {
			case "raw_mux":
				_ = client.SendContext(ctx, []byte{2, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0})
			case "proxy":
				_ = client.SendContext(ctx, []byte("CONNECT example.org:443 HTTP/1.1\r\n\r\n"))
			case "oversized":
				_ = client.SendContext(ctx, bytes.Repeat([]byte(" "), 257))
			case "disconnect":
				client.Close()
			case "stale":
				_ = send(ctx, client, message{Type: "REQUEST_TRANSPORT", SetupID: testFamily})
			case "duplicate", "after_descriptor":
				_ = send(ctx, client, message{Type: "REQUEST_TRANSPORT", SetupID: hello.SetupID})
				if _, err := receive(ctx, client, "TRANSPORT_READY", hello.SetupID); err != nil {
					test.Fatal(err)
				}
				if kind == "duplicate" {
					_ = send(ctx, client, message{Type: "REQUEST_TRANSPORT", SetupID: hello.SetupID})
				} else {
					client.Close()
				}
			default:
				_ = send(ctx, client, message{Type: kind, SetupID: hello.SetupID})
			}
			if err := <-done; err == nil {
				test.Fatal("invalid flow accepted")
			}
			if calls.Load() > 1 {
				test.Fatal("unbounded creation")
			}
			if kind != "duplicate" && kind != "after_descriptor" && calls.Load() != 0 {
				test.Fatal("unauthorized create")
			}
			if calls.Load() == 1 {
				select {
				case <-back.closed:
				case <-ctx.Done():
					test.Fatal("setup leaked")
				}
			}
			if _, err := broker.Create(ctx, hello.SetupID, allow); err == nil {
				test.Fatal("reconnect old id accepted")
			}
		})
	}
}

func TestExchangeFailureAndCancellation(test *testing.T) {
	for _, failure := range []string{"provider", "ready", "cancel"} {
		test.Run(failure, func(test *testing.T) {
			ctx, cancel := context.WithCancel(bounded(test))
			defer cancel()
			var calls atomic.Int32
			var ready chan struct{}
			if failure == "cancel" {
				ready = make(chan struct{})
			}
			broker, _ := testBroker(test, &calls, ready, failure)
			client, server := pair()
			done := make(chan error, 1)
			go func() { done <- Exchange(ctx, server, broker, allow) }()
			if failure == "cancel" {
				time.AfterFunc(20*time.Millisecond, cancel)
			}
			if _, err := requestTransport(ctx, client); err == nil {
				test.Fatal("failure accepted")
			}
			if err := <-done; err == nil {
				test.Fatal("server accepted")
			}
		})
	}
}
