//go:build go1.25

package roombroker

import (
	"context"
	"errors"
	"testing"
	"testing/synctest"
	"time"
)

type lifetimeFixture struct {
	broker   *Broker
	activate chan struct{}
	active   chan error
	lifetime context.Context
	gateway  *fakeGateway
}

func newLifetimeFixture(t *testing.T) *lifetimeFixture {
	t.Helper()
	fixture := &lifetimeFixture{activate: make(chan struct{}), active: make(chan error, 1)}
	fixture.gateway = &fakeGateway{run: func(ctx context.Context, active func() error) error {
		select {
		case <-fixture.activate:
			fixture.active <- active()
		case <-ctx.Done():
			return ctx.Err()
		}
		<-ctx.Done()
		return ctx.Err()
	}}
	broker, err := New(providerFunc(fresh), gatewayFunc(func(lifetime, ready context.Context, room Room, identifier string, identity Identity) (Gateway, error) {
		fixture.lifetime = lifetime
		return fixture.gateway, nil
	}), DefaultLimits(), nil)
	if err != nil {
		t.Fatal(err)
	}
	fixture.broker = broker
	return fixture
}

func (fixture *lifetimeFixture) open(t *testing.T, challengeAge time.Duration) (string, time.Time) {
	t.Helper()
	challenged := time.Now()
	identifier, err := fixture.broker.Challenge(context.Background(), allow)
	if err != nil {
		t.Fatal(err)
	}
	time.Sleep(challengeAge)
	descriptor, err := fixture.broker.Create(context.Background(), identifier, allow)
	if err != nil {
		t.Fatal(err)
	}
	if descriptor.ExpiresAt.Sub(time.Now()) != DefaultLimits().Unused {
		t.Fatal("descriptor admission deadline differs from unused budget")
	}
	if err := fixture.broker.Claim(context.Background(), identifier, allow); err != nil {
		t.Fatal(err)
	}
	fixture.activate <- struct{}{}
	if err := <-fixture.active; err != nil {
		t.Fatal(err)
	}
	deadline := fixture.lifetime.Value(leaseKey{}).(*leaseBinding).current.lease.deadline()
	if _, fixed := fixture.lifetime.Deadline(); fixed || deadline.Sub(challenged) != DefaultLimits().Lifetime {
		t.Fatal("dedicated lifetime must originate at challenge, not READY or cached directory")
	}
	return identifier, challenged
}

func TestLifetimeFreshAndPartiallySpentChallenge(t *testing.T) {
	for _, age := range []time.Duration{0, 45 * time.Second} {
		t.Run(age.String(), func(t *testing.T) {
			synctest.Test(t, func(t *testing.T) {
				fixture := newLifetimeFixture(t)
				defer fixture.broker.Close()
				_, challenged := fixture.open(t, age)
				deadline := fixture.lifetime.Value(leaseKey{}).(*leaseBinding).current.lease.deadline()
				remaining := time.Until(deadline)
				if remaining != 10*time.Minute-age {
					t.Fatal("lease was silently renewed at READY")
				}
				time.Sleep(remaining - time.Nanosecond)
				if fixture.lifetime.Err() != nil {
					t.Fatal("active setup closed before challenge lifetime")
				}
				time.Sleep(time.Nanosecond)
				synctest.Wait()
				if !errors.Is(fixture.lifetime.Err(), context.DeadlineExceeded) || fixture.gateway.closes.Load() != 1 {
					t.Fatal("active dedicated carrier did not close exactly at security lifetime")
				}
				t.Logf("challenge=%s READY_age=%s remaining_at_READY=%s close_age=%s", challenged.Format(time.RFC3339Nano), age, remaining, time.Since(challenged))
			})
		})
	}
}

func TestLifetimeProcessReopenRejectsPriorDescriptor(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		old := newLifetimeFixture(t)
		identifier, _ := old.open(t, 0)
		old.broker.Close()
		fresh := newLifetimeFixture(t)
		defer fresh.broker.Close()
		if err := fresh.broker.Claim(context.Background(), identifier, allow); err != Code("stale_or_unbound_setup") {
			t.Fatal("process reopen accepted an old descriptor")
		}
		current, _ := fresh.open(t, 0)
		if current == identifier {
			t.Fatal("reopened session reused challenge identity")
		}
	})
}

func TestLifetimeRecoveryGetsFreshChallengeWithoutExtendingOldLease(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		fixture := newLifetimeFixture(t)
		defer fixture.broker.Close()
		oldIdentifier, _ := fixture.open(t, 0)
		oldLifetime := fixture.lifetime
		time.Sleep(9 * time.Minute)
		if err := fixture.broker.Cancel(context.Background(), oldIdentifier, allow); err != nil {
			t.Fatal(err)
		}
		synctest.Wait()
		identifier, challenged := fixture.open(t, 0)
		if identifier == oldIdentifier || !errors.Is(oldLifetime.Err(), context.Canceled) {
			t.Fatal("recovery did not finish the previous setup")
		}
		time.Sleep(2 * time.Minute)
		if fixture.lifetime.Err() != nil || time.Since(challenged) != 2*time.Minute {
			t.Fatal("old challenge deadline leaked into fresh recovery")
		}
		if err := fixture.broker.Claim(context.Background(), oldIdentifier, allow); err != Code("stale_or_unbound_setup") {
			t.Fatal("recovery accepted a prior descriptor")
		}
	})
}
