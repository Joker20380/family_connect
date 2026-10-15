package roombroker

import (
	"context"
	"errors"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

type providerFunc func(context.Context) (Room, error)

func (function providerFunc) CreateRoom(ctx context.Context) (Room, error) { return function(ctx) }

type gatewayFunc func(context.Context, context.Context, Room, string, Identity) (Gateway, error)

func (function gatewayFunc) Start(lifetime, ready context.Context, room Room, id string, identity Identity) (Gateway, error) {
	return function(lifetime, ready, room, id, identity)
}

type fakeGateway struct {
	run    func(context.Context, func() error) error
	closes atomic.Int32
}

func (gateway *fakeGateway) Run(ctx context.Context, active func() error) error {
	return gateway.run(ctx, active)
}
func (gateway *fakeGateway) Close() error { gateway.closes.Add(1); return nil }

var testIdentity = Identity{Family: strings.Repeat("a", 32), Device: strings.Repeat("b", 32)}

func allow(context.Context) (Identity, error) { return testIdentity, nil }
func deny(context.Context) (Identity, error)  { return Identity{}, errors.New("fake-secret") }
func fresh(context.Context) (Room, error) {
	return Room{"new", "https://telemost.yandex.ru/j/new"}, nil
}
func waiting(ctx context.Context, _ func() error) error { <-ctx.Done(); return ctx.Err() }

func makeBroker(t *testing.T, provider RoomProvider, gateway GatewayStarter, limits Limits) *Broker {
	t.Helper()
	broker, err := New(provider, gateway, limits, func(_ State, code Code) {
		if strings.Contains(string(code), "fake-secret") {
			t.Error("secret leak")
		}
	})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(broker.Close)
	return broker
}
func shortLimits() Limits {
	result := DefaultLimits()
	result.Recheck = time.Millisecond
	return result
}
func waitEmpty(t *testing.T, broker *Broker) {
	t.Helper()
	deadline := time.Now().Add(time.Second)
	for time.Now().Before(deadline) {
		broker.mu.Lock()
		count := len(broker.setups)
		broker.mu.Unlock()
		if count == 0 {
			return
		}
		time.Sleep(time.Millisecond)
	}
	t.Fatal("retained setup leaked")
}

func TestGatewayFirstBoundAndReplay(t *testing.T) {
	var calls atomic.Int32
	release, entered := make(chan struct{}), make(chan struct{})
	lease := &fakeGateway{run: waiting}
	broker := makeBroker(t, providerFunc(func(ctx context.Context) (Room, error) { calls.Add(1); return fresh(ctx) }),
		gatewayFunc(func(life, ready context.Context, room Room, id string, identity Identity) (Gateway, error) {
			if room.ID != "new" || id == "" || identity != testIdentity {
				t.Error("gateway descriptor binding")
			}
			close(entered)
			select {
			case <-release:
				return lease, nil
			case <-ready.Done():
				return nil, ready.Err()
			}
		}), shortLimits())
	if _, err := broker.Challenge(context.Background(), nil); err == nil {
		t.Fatal("unauthenticated")
	}
	if _, err := broker.Challenge(context.Background(), deny); err == nil {
		t.Fatal("revoked")
	}
	id, err := broker.Challenge(context.Background(), allow)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := broker.Challenge(context.Background(), allow); err != Code("device_busy") {
		t.Fatal(err)
	}
	wrong := func(context.Context) (Identity, error) {
		identity := testIdentity
		identity.Family = strings.Repeat("c", 32)
		return identity, nil
	}
	if _, err := broker.Create(context.Background(), id, wrong); err == nil {
		t.Fatal("wrong family")
	}
	result := make(chan Descriptor, 1)
	go func() {
		descriptor, err := broker.Create(context.Background(), id, allow)
		if err != nil {
			t.Error(err)
		}
		result <- descriptor
	}()
	<-entered
	select {
	case <-result:
		t.Fatal("descriptor before READY")
	default:
	}
	if _, err := broker.Create(context.Background(), id, allow); err != Code("setup_replayed") {
		t.Fatal(err)
	}
	close(release)
	descriptor := <-result
	if descriptor.JoinURL == "" || descriptor.SetupID != id || calls.Load() != 1 {
		t.Fatal("one fresh setup")
	}
	if err := broker.Claim(context.Background(), id, wrong); err == nil {
		t.Fatal("unbound claim")
	}
	if err := broker.Claim(context.Background(), id, allow); err != nil {
		t.Fatal(err)
	}
	if err := broker.Claim(context.Background(), id, allow); err == nil {
		t.Fatal("replayed claim")
	}
	if err := broker.Cancel(context.Background(), id, allow); err != nil {
		t.Fatal(err)
	}
	waitEmpty(t, broker)
	if lease.closes.Load() != 1 {
		t.Fatal("gateway not closed")
	}
	if _, err := broker.Create(context.Background(), id, allow); err == nil {
		t.Fatal("stale setup")
	}
}

func TestFailuresReleaseResources(t *testing.T) {
	for _, mode := range []string{"provider", "creation_timeout", "gateway", "ready_timeout", "cancel", "revoked", "unused", "completed"} {
		t.Run(mode, func(t *testing.T) {
			limits := shortLimits()
			limits.Create = 20 * time.Millisecond
			limits.Ready = 20 * time.Millisecond
			if mode == "unused" {
				limits.Unused = 20 * time.Millisecond
			}
			var revoked atomic.Bool
			auth := func(ctx context.Context) (Identity, error) {
				if revoked.Load() {
					return deny(ctx)
				}
				return allow(ctx)
			}
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			lease := &fakeGateway{run: waiting}
			if mode == "completed" {
				lease.run = func(context.Context, func() error) error { return nil }
			}
			broker := makeBroker(t, providerFunc(func(ctx context.Context) (Room, error) {
				if mode == "provider" {
					return Room{}, errors.New("fake-secret")
				}
				if mode == "creation_timeout" {
					<-ctx.Done()
					return Room{}, ctx.Err()
				}
				return fresh(ctx)
			}), gatewayFunc(func(life, ready context.Context, _ Room, _ string, _ Identity) (Gateway, error) {
				if mode == "gateway" {
					return nil, errors.New("fake-secret")
				}
				if mode == "ready_timeout" {
					<-ready.Done()
					return nil, ready.Err()
				}
				if mode == "revoked" {
					revoked.Store(true)
				}
				if mode == "cancel" {
					cancel()
				}
				return lease, nil
			}), limits)
			id, err := broker.Challenge(ctx, auth)
			if err != nil {
				t.Fatal(err)
			}
			_, err = broker.Create(ctx, id, auth)
			if mode != "unused" && mode != "completed" && err == nil {
				t.Fatal("failure accepted")
			}
			if err != nil && strings.Contains(err.Error(), "fake-secret") {
				t.Fatal("secret in error")
			}
			waitEmpty(t, broker)
		})
	}
}

func TestActiveExpiryRevocationAndGlobalBound(t *testing.T) {
	activate := make(chan struct{})
	activated := make(chan error, 1)
	var revoked atomic.Bool
	auth := func(ctx context.Context) (Identity, error) {
		if revoked.Load() {
			return deny(ctx)
		}
		return allow(ctx)
	}
	lease := &fakeGateway{run: func(ctx context.Context, active func() error) error {
		select {
		case <-activate:
			activated <- active()
		case <-ctx.Done():
			return ctx.Err()
		}
		<-ctx.Done()
		return ctx.Err()
	}}
	limits := shortLimits()
	limits.Outstanding = 1
	limits.Unused = 30 * time.Millisecond
	broker := makeBroker(t, providerFunc(fresh), gatewayFunc(func(context.Context, context.Context, Room, string, Identity) (Gateway, error) { return lease, nil }), limits)
	id, _ := broker.Challenge(context.Background(), auth)
	other := func(context.Context) (Identity, error) {
		identity := testIdentity
		identity.Device = strings.Repeat("d", 32)
		return identity, nil
	}
	if _, err := broker.Challenge(context.Background(), other); err != Code("outstanding_limit") {
		t.Fatal(err)
	}
	if _, err := broker.Create(context.Background(), id, auth); err != nil {
		t.Fatal(err)
	}
	if err := broker.Claim(context.Background(), id, auth); err != nil {
		t.Fatal(err)
	}
	close(activate)
	if err := <-activated; err != nil {
		t.Fatal(err)
	}
	time.Sleep(45 * time.Millisecond)
	broker.mu.Lock()
	state := broker.setups[id].state
	broker.mu.Unlock()
	if state != Active {
		t.Fatal("active session expired as unused")
	}
	revoked.Store(true)
	waitEmpty(t, broker)
}

func TestConcurrentDuplicateAndChallengeCleanup(t *testing.T) {
	limits := shortLimits()
	limits.Unused = 15 * time.Millisecond
	broker := makeBroker(t, providerFunc(fresh), gatewayFunc(func(context.Context, context.Context, Room, string, Identity) (Gateway, error) {
		return &fakeGateway{run: waiting}, nil
	}), limits)
	var accepted atomic.Int32
	var workers sync.WaitGroup
	for index := 0; index < 20; index++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			if _, err := broker.Challenge(context.Background(), allow); err == nil {
				accepted.Add(1)
			}
		}()
	}
	workers.Wait()
	if accepted.Load() != 1 {
		t.Fatal("duplicate challenges")
	}
	waitEmpty(t, broker)
}
