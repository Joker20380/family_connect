//go:build go1.25

package roombroker

import (
	"context"
	"testing"
	"testing/synctest"
	"time"
)

func TestLeaseSchedulerBoundedRenewal(test *testing.T) {
	for _, mode := range []string{"two_renewals", "lost_response", "timeout", "revoked", "cancel_during_renewal", "initial_loss", "security_limit"} {
		test.Run(mode, func(test *testing.T) {
			synctest.Test(test, func(test *testing.T) {
				fixture, binding, request, acquired := renewalFixture(test)
				ctx, cancel := context.WithCancel(context.Background())
				defer cancel()
				calls, closed := 0, 0
				done := make(chan struct{})
				go func() {
					defer close(done)
					maintainLease(ctx, func(ctx context.Context, known LeaseReceipt, renew bool) (LeaseReceipt, time.Time, error) {
						if !renew && mode == "initial_loss" {
							return LeaseReceipt{}, time.Time{}, context.DeadlineExceeded
						}
						if renew {
							calls++
							if time.Since(acquired) < 8*time.Minute {
								test.Error("renewal too early")
							}
							if mode == "revoked" {
								return LeaseReceipt{}, time.Time{}, Code("unauthorized")
							}
							if mode == "timeout" || mode == "cancel_during_renewal" {
								bounded, cancel := context.WithTimeout(ctx, renewalTimeout)
								defer cancel()
								<-bounded.Done()
								return LeaseReceipt{}, time.Time{}, bounded.Err()
							}
						}
						if renew && mode == "security_limit" {
							return known, known.ExpiresAt, nil
						}
						current, err := binding.snapshot(ctx, allow, acquired.Add(time.Hour))
						if err != nil {
							return LeaseReceipt{}, time.Time{}, err
						}
						if renew && current.Sequence == known.Sequence {
							current.Sequence++
							current, err = binding.renew(ctx, current, allow, acquired.Add(time.Hour))
							if mode == "lost_response" && calls == 1 {
								return LeaseReceipt{}, time.Time{}, context.DeadlineExceeded
							}
						}
						return current, current.ExpiresAt, err
					}, func() { closed++; _ = fixture.broker.Cancel(context.Background(), request.SetupID, allow) })
				}()
				switch mode {
				case "two_renewals", "lost_response":
					time.Sleep(22 * time.Minute)
					synctest.Wait()
					if binding.current.renewal != 2 || closed != 0 || fixture.lifetime.Err() != nil {
						test.Fatal("scheduler did not preserve two lease boundaries")
					}
					if calls != 2 && mode == "two_renewals" || calls != 3 && mode == "lost_response" {
						test.Fatal("unbounded or missing attempts")
					}
					cancel()
				case "cancel_during_renewal":
					time.Sleep(8*time.Minute + time.Second)
					cancel()
					_ = fixture.broker.Cancel(context.Background(), request.SetupID, allow)
				case "timeout", "revoked", "initial_loss", "security_limit":
					time.Sleep(10 * time.Minute)
					synctest.Wait()
					if fixture.lifetime.Err() == nil {
						test.Fatal("failure extended existing permission")
					}
					if mode == "timeout" && (calls != 3 || closed != 1) {
						test.Fatal("timeout retry bound")
					}
					if mode == "revoked" && (calls != 1 || closed != 1) {
						test.Fatal("authorization failure retried")
					}
					if mode == "initial_loss" && closed != 0 {
						test.Fatal("transient offer loss closed an authorized carrier early")
					}
					if mode == "security_limit" && (closed != 1 || calls != 1) {
						test.Fatal("nonextendable security deadline caused renewal polling")
					}
				}
				<-done
			})
		})
	}
}
