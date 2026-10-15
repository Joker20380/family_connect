package bootstrap

import (
	"context"
	"crypto/ed25519"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"fmt"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

type seedTestTimer struct {
	clock    *seedTestClock
	at       time.Time
	callback func()
	stopped  bool
}

type seedTestClient struct{ familysession.PacketEndpoint }

func (client seedTestClient) Close() error { return nil }

func TestOverlappingSeedsKeepSingleAuthenticatedOwner(test *testing.T) {
	path := gatewayProfile(test)
	raw := fixture(test, "valid")
	var credentials familysession.Credentials
	if json.Unmarshal(raw, &credentials) != nil {
		test.Fatal("disposable profile invalid")
	}
	pairing, err := tls.X509KeyPair([]byte(credentials.Certificate), []byte(credentials.PrivateKey))
	if err != nil {
		test.Fatal(err)
	}
	certificate, err := x509.ParseCertificate(pairing.Certificate[0])
	if err != nil {
		test.Fatal(err)
	}
	identity := roombroker.Identity{Family: credentials.Family, Device: certificate.Subject.SerialNumber}
	copy(identity.PublicKey[:], certificate.PublicKey.(ed25519.PublicKey))
	authorize := func(context.Context) (roombroker.Identity, error) { return identity, nil }
	clock := &seedTestClock{now: time.Now().UTC(), armed: make(chan struct{}, 1)}
	publications, clients := make(chan Directory, 2), make(chan *pipe, 2)
	retired := make(chan struct{}, 1)
	observed := make(chan SeedFailure, 2)
	var creations, admissions, dedicated atomic.Int32
	broker, _ := testBroker(test, &dedicated, nil, "")
	manager := &SeedManager{RotateAfter: 30 * time.Minute, now: clock.read, lifetime: clock.lifetime, after: clock.after,
		Observe: func(value SeedFailure) { observed <- value },
		Event: func(event string) {
			if event == "bootstrap_previous_seed_retired" {
				retired <- struct{}{}
			}
		},
		Publish: func(directory Directory) error { publications <- directory; return nil }}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	done := make(chan error, 1)
	go func() {
		done <- manager.Run(ctx, providerFunc(func(context.Context) (roombroker.Room, error) {
			index := creations.Add(1)
			return roombroker.Room{ID: fmt.Sprint(index), JoinURL: fmt.Sprintf("https://telemost.yandex.ru/j/auth-overlap-%d", index)}, nil
		}), func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
			client, server := pair()
			clients <- client
			return server, nil
		}, credentials.Family, credentials.Gateway, time.Hour, func(ctx context.Context, endpoint familysession.PacketEndpoint) {
			OpenServer(ctx, endpoint, path, broker, func(event string) {
				if event == "bootstrap_family_auth" {
					admissions.Add(1)
				}
			})
		})
	}()
	first := seedWait(test, publications)
	oldClient := seedWait(test, clients)
	seedWait(test, clock.armed)
	clock.advance(30 * time.Minute)
	seedWait(test, publications)
	newClient := seedWait(test, clients)
	if _, err := ParseDirectory(encode(first), credentials.Family, credentials.Gateway, clock.read()); err != nil {
		test.Fatal(err)
	}
	descriptor, err := recoverCarrier(bounded(test), seedTestClient{oldClient}, raw, func(string) {})
	if err != nil || descriptor.SetupID == "" || dedicated.Load() != 1 || admissions.Load() != 1 {
		test.Fatal("old generation authenticated startup failed", err)
	}
	if _, err := broker.Challenge(bounded(test), authorize); err != roombroker.Code("device_busy") {
		test.Fatal("overlap added independent admission owner", err)
	}
	if err := broker.Cancel(bounded(test), descriptor.SetupID, authorize); err != nil {
		test.Fatal(err)
	}
	second, err := recoverCarrier(bounded(test), seedTestClient{newClient}, raw, func(string) {})
	if err != nil || second.SetupID == descriptor.SetupID || dedicated.Load() != 2 || admissions.Load() != 2 {
		test.Fatal("new generation failed after prior owner cleanup", err)
	}
	clock.advance(30 * time.Minute)
	seedWait(test, oldClient.done)
	seedWait(test, retired)
	select {
	case <-observed:
		test.Fatal("retired generation classified as process fatal")
	default:
	}
	if _, err := ParseDirectory(encode(first), credentials.Family, credentials.Gateway, clock.read()); err == nil {
		test.Fatal("old generation accepted outside overlap")
	}
	if _, err := broker.Challenge(bounded(test), authorize); err != roombroker.Code("device_busy") {
		test.Fatal("old seed cleanup released new dedicated owner", err)
	}
	cancel()
	seedWait(test, done)
}

func (timer *seedTestTimer) Stop() bool {
	timer.clock.mu.Lock()
	defer timer.clock.mu.Unlock()
	active := !timer.stopped
	timer.stopped = true
	return active
}

type seedTestClock struct {
	mu     sync.Mutex
	now    time.Time
	timers []*seedTestTimer
	armed  chan struct{}
}

func (clock *seedTestClock) read() time.Time {
	clock.mu.Lock()
	defer clock.mu.Unlock()
	return clock.now
}
func (clock *seedTestClock) after(delay time.Duration, callback func()) seedTimer {
	clock.mu.Lock()
	timer := &seedTestTimer{clock: clock, at: clock.now.Add(delay), callback: callback}
	clock.timers = append(clock.timers, timer)
	clock.mu.Unlock()
	if delay == 30*time.Minute {
		clock.armed <- struct{}{}
	}
	return timer
}
func (clock *seedTestClock) advance(delay time.Duration) {
	clock.mu.Lock()
	clock.now = clock.now.Add(delay)
	var callbacks []func()
	for _, timer := range clock.timers {
		if !timer.stopped && !timer.at.After(clock.now) {
			timer.stopped = true
			callbacks = append(callbacks, timer.callback)
		}
	}
	clock.mu.Unlock()
	for _, callback := range callbacks {
		callback()
	}
}

type seedTestDeadline struct {
	context.Context
	deadline time.Time
}

func (ctx seedTestDeadline) Deadline() (time.Time, bool) { return ctx.deadline, true }
func (clock *seedTestClock) lifetime(parent context.Context, ttl time.Duration) (context.Context, context.CancelFunc) {
	expires := clock.read().Add(ttl)
	if bound, ok := parent.Deadline(); ok && bound.Before(expires) {
		expires = bound
	}
	ctx, cancel := context.WithCancel(parent)
	timer := clock.after(expires.Sub(clock.read()), cancel)
	return seedTestDeadline{ctx, expires}, func() { timer.Stop(); cancel() }
}
func seedWait[T any](test *testing.T, channel <-chan T) T {
	test.Helper()
	select {
	case value := <-channel:
		return value
	case <-time.After(5 * time.Second):
		test.Fatal("seed checkpoint timeout")
	}
	var zero T
	return zero
}

func TestFiniteSeedOverlapAndOldCleanup(test *testing.T) {
	clock := &seedTestClock{now: time.Now().UTC(), armed: make(chan struct{}, 1)}
	publications := make(chan Directory, 2)
	clients := make(chan *pipe, 2)
	manager := &SeedManager{RotateAfter: 30 * time.Minute, now: clock.read, after: clock.after, lifetime: clock.lifetime,
		Publish: func(directory Directory) error { publications <- directory; return nil }}
	var creations atomic.Int32
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	done := make(chan error, 1)
	go func() {
		done <- manager.Run(ctx, providerFunc(func(context.Context) (roombroker.Room, error) {
			index := creations.Add(1)
			return roombroker.Room{ID: fmt.Sprint(index), JoinURL: fmt.Sprintf("https://telemost.yandex.ru/j/overlap-%d", index)}, nil
		}), func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
			client, server := pair()
			clients <- client
			return server, nil
		}, testFamily, testGateway, time.Hour, func(ctx context.Context, endpoint familysession.PacketEndpoint) {
			for {
				raw, err := endpoint.Recv(ctx)
				if err != nil {
					return
				}
				if endpoint.SendContext(ctx, raw) != nil {
					return
				}
			}
		})
	}()
	first := seedWait(test, publications)
	oldClient := seedWait(test, clients)
	seedWait(test, clock.armed)
	clock.advance(30 * time.Minute)
	second := seedWait(test, publications)
	newClient := seedWait(test, clients)
	if !first.ExpiresAt.Equal(clock.read().Add(30*time.Minute)) || !second.ExpiresAt.Equal(clock.read().Add(time.Hour)) {
		test.Fatal("deadline silently extended")
	}
	if _, err := ParseDirectory(encode(first), testFamily, testGateway, clock.read()); err != nil {
		test.Fatal("old directory rejected inside overlap")
	}
	oldExchange, err := connectLease(bounded(test), oldClient)
	if err != nil {
		test.Fatal("old seed unavailable inside overlap", err)
	}
	defer oldExchange.Close()
	go readLease(ctx, oldExchange)
	newExchange, err := connectLease(bounded(test), newClient)
	if err != nil {
		test.Fatal("new seed unavailable", err)
	}
	defer newExchange.Close()
	go readLease(ctx, newExchange)
	for _, endpoint := range []*lease{oldExchange, newExchange} {
		if err := endpoint.SendContext(bounded(test), []byte("probe")); err != nil {
			test.Fatal(err)
		}
		raw, err := endpoint.Recv(bounded(test))
		if err != nil || string(raw) != "probe" {
			test.Fatal("seed response missing", err)
		}
	}
	clock.advance(30 * time.Minute)
	seedWait(test, oldClient.done)
	if _, err := ParseDirectory(encode(first), testFamily, testGateway, clock.read()); err == nil {
		test.Fatal("old directory accepted at exclusive expiry")
	}
	if newExchange.SendContext(bounded(test), []byte("after-old-cleanup")) != nil {
		test.Fatal("old cleanup closed new seed")
	}
	raw, err := newExchange.Recv(bounded(test))
	if err != nil || string(raw) != "after-old-cleanup" {
		test.Fatal("new seed lost after old cleanup", err)
	}
	clock.advance(30 * time.Minute)
	seedWait(test, newClient.done)
	seedWait(test, done)
	if creations.Load() != 2 {
		test.Fatal("unbounded seed creation")
	}
	manager.mu.Lock()
	defer manager.mu.Unlock()
	if manager.running || manager.directory != nil {
		test.Fatal("seed leak after expiry")
	}
}

func TestSeedOverlapCancellationAndFailedReplacement(test *testing.T) {
	for _, failReplacement := range []bool{false, true} {
		test.Run(fmt.Sprint(failReplacement), func(test *testing.T) {
			clock := &seedTestClock{now: time.Now().UTC(), armed: make(chan struct{}, 1)}
			published, events := make(chan Directory, 2), make(chan string, 8)
			client, server := pair()
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			manager := &SeedManager{RotateAfter: 30 * time.Minute, now: clock.read, lifetime: clock.lifetime, after: clock.after,
				Publish: func(directory Directory) error { published <- directory; return nil }, Event: func(event string) { events <- event }}
			var creations atomic.Int32
			done := make(chan error, 1)
			go func() {
				done <- manager.Run(ctx, providerFunc(func(context.Context) (roombroker.Room, error) {
					if creations.Add(1) > 1 {
						return roombroker.Room{}, roombroker.Code("provider_unavailable")
					}
					return roombroker.Room{ID: "first", JoinURL: "https://telemost.yandex.ru/j/first"}, nil
				}), func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
					return server, nil
				}, testFamily, testGateway, time.Hour, func(context.Context, familysession.PacketEndpoint) {})
			}()
			first := seedWait(test, published)
			seedWait(test, clock.armed)
			if failReplacement {
				clock.advance(30 * time.Minute)
				for event := seedWait(test, events); event != "bootstrap_seed_rotation_failed"; event = seedWait(test, events) {
				}
				manager.mu.Lock()
				unchanged := manager.directory != nil && manager.directory.IssuedAt.Equal(first.IssuedAt)
				manager.mu.Unlock()
				if !unchanged {
					test.Fatal("failed replacement displaced current directory")
				}
			}
			cancel()
			seedWait(test, done)
			seedWait(test, client.done)
			clock.advance(time.Hour)
			expected := int32(1)
			if failReplacement {
				expected = 2
			}
			if creations.Load() != expected {
				test.Fatal("timer created seed after cancellation")
			}
		})
	}
}

func TestSeedOverlapRejectsInsufficientHeadroom(test *testing.T) {
	manager := &SeedManager{RotateAfter: time.Hour - roombroker.CreationTimeout - ConnectTimeout}
	err := manager.Run(context.Background(), providerFunc(func(context.Context) (roombroker.Room, error) {
		test.Fatal("invalid overlap performed provider I/O")
		return roombroker.Room{}, nil
	}), func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
		test.Fatal("invalid overlap joined carrier")
		return nil, nil
	}, testFamily, testGateway, time.Hour, func(context.Context, familysession.PacketEndpoint) {})
	if err != roombroker.Code("seed_configuration") {
		test.Fatal("insufficient creation/READY margin accepted", err)
	}
}
