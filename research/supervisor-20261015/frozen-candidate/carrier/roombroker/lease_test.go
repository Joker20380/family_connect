//go:build go1.25

package roombroker

import (
	"context"
	"errors"
	"strings"
	"testing"
	"testing/synctest"
	"time"
)

func renewalFixture(test *testing.T) (*lifetimeFixture, *leaseBinding, LeaseReceipt, time.Time) {
	test.Helper()
	fixture := newLifetimeFixture(test)
	test.Cleanup(fixture.broker.Close)
	identifier, acquired := fixture.open(test, 0)
	binding := fixture.lifetime.Value(leaseKey{}).(*leaseBinding)
	return fixture, binding, LeaseReceipt{identifier, 1, acquired.Add(10 * time.Minute)}, acquired
}

func TestLeaseTwoRenewalsSameHolder(test *testing.T) {
	synctest.Test(test, func(test *testing.T) {
		fixture, binding, request, acquired := renewalFixture(test)
		for sequence := uint64(1); sequence <= 2; sequence++ {
			time.Sleep(8 * time.Minute)
			request.Sequence = sequence
			accepted, err := binding.renew(context.Background(), request, allow, acquired.Add(time.Hour))
			if err != nil || accepted.Sequence != sequence || accepted.ExpiresAt != time.Now().Add(10*time.Minute) {
				test.Fatalf("renewal: %+v %v", accepted, err)
			}
			binding.current.lease.expire()
			if fixture.lifetime.Err() != nil || fixture.broker.setups[request.SetupID] != binding.current || len(fixture.broker.setups) != 1 {
				test.Fatal("old callback closed renewed holder or slot changed")
			}
			if _, err := fixture.broker.Challenge(context.Background(), allow); err != Code("device_busy") {
				test.Fatal("renewal allocated another slot")
			}
			retry, err := binding.renew(context.Background(), request, allow, acquired.Add(time.Hour))
			if err != nil || retry != accepted {
				test.Fatal("lost response retry must return the original receipt, without extending")
			}
			request.ExpiresAt = accepted.ExpiresAt
		}
		time.Sleep(9 * time.Minute)
		if fixture.lifetime.Err() != nil {
			test.Fatal("old acquisition deadline survived renewal")
		}
		time.Sleep(time.Minute)
		synctest.Wait()
		if !errors.Is(fixture.lifetime.Err(), context.DeadlineExceeded) || len(fixture.broker.setups) != 0 || fixture.gateway.closes.Load() != 1 {
			test.Fatal("final expiry leaked a holder")
		}
	})
}

func TestLeaseSecurityAndReplay(test *testing.T) {
	for _, mode := range []string{"identity", "session", "replay", "expired_security", "revoked", "cancelled", "late", "security_bound"} {
		test.Run(mode, func(test *testing.T) {
			synctest.Test(test, func(test *testing.T) {
				fixture, binding, request, acquired := renewalFixture(test)
				time.Sleep(8 * time.Minute)
				authorize, security := Authorize(allow), acquired.Add(time.Hour)
				switch mode {
				case "identity":
					authorize = func(context.Context) (Identity, error) {
						other := testIdentity
						other.Device = strings.Repeat("d", 32)
						return other, nil
					}
				case "session":
					request.SetupID = strings.Repeat("f", 64)
				case "replay":
					request.Sequence = 0
				case "expired_security":
					security = time.Now()
				case "revoked":
					authorize = deny
				case "cancelled":
					_ = fixture.broker.Cancel(context.Background(), request.SetupID, allow)
				case "late":
					time.Sleep(2 * time.Minute)
				case "security_bound":
					security = time.Now().Add(3 * time.Minute)
				}
				accepted, err := binding.renew(context.Background(), request, authorize, security)
				if mode == "security_bound" {
					if err != nil || !accepted.ExpiresAt.Equal(security) {
						test.Fatal("security deadline was not binding")
					}
					time.Sleep(3 * time.Minute)
					synctest.Wait()
					if fixture.lifetime.Err() == nil {
						test.Fatal("ran beyond security deadline")
					}
					return
				}
				if err == nil {
					test.Fatal("unbound/replayed/unauthorized renewal accepted")
				}
				if !binding.current.lease.deadline().Equal(acquired.Add(10 * time.Minute)) {
					test.Fatal("failed renewal changed deadline")
				}
			})
		})
	}
}

func TestLeaseRenewalCancellationAndExpiryRaces(test *testing.T) {
	for _, mode := range []string{"timeout", "disconnect", "expiry", "server_close"} {
		test.Run(mode, func(test *testing.T) {
			synctest.Test(test, func(test *testing.T) {
				fixture, binding, request, acquired := renewalFixture(test)
				time.Sleep(9 * time.Minute)
				ctx, cancel := context.WithCancel(context.Background())
				defer cancel()
				entered, release := make(chan struct{}), make(chan struct{})
				result := make(chan error, 1)
				go func() {
					_, err := binding.renew(ctx, request, func(context.Context) (Identity, error) { close(entered); <-release; return testIdentity, nil }, acquired.Add(time.Hour))
					result <- err
				}()
				<-entered
				switch mode {
				case "timeout":
					cancel()
				case "disconnect":
					_ = fixture.broker.Cancel(context.Background(), request.SetupID, allow)
				case "expiry":
					time.Sleep(time.Minute)
				case "server_close":
					fixture.broker.Close()
				}
				close(release)
				if err := <-result; err == nil {
					test.Fatal("late authorization resurrected the session")
				}
				if mode == "timeout" {
					time.Sleep(time.Minute)
				}
				synctest.Wait()
				if fixture.lifetime.Err() == nil || len(fixture.broker.setups) != 0 {
					test.Fatal("expiry/cleanup did not release holder")
				}
			})
		})
	}
}

func TestLeasePreviousGenerationCannotAffectReplacement(test *testing.T) {
	synctest.Test(test, func(test *testing.T) {
		fixture, binding, request, acquired := renewalFixture(test)
		_ = fixture.broker.Cancel(context.Background(), request.SetupID, allow)
		synctest.Wait()
		identifier, _ := fixture.open(test, 0)
		if _, err := binding.renew(context.Background(), request, allow, acquired.Add(time.Hour)); err == nil {
			test.Fatal("old session renewed replacement")
		}
		binding.current.lease.expire()
		if fixture.lifetime.Err() != nil || len(fixture.broker.setups) != 1 || fixture.broker.setups[identifier] == nil {
			test.Fatal("old expiry changed new ownership")
		}
	})
}
