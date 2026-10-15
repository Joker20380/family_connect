//go:build sameroomfixture

package roombroker

import (
	"context"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/tcpforward"
)

type RejoinFixtureClock struct {
	mu     sync.Mutex
	now    time.Time
	timers []*rejoinFixtureTimer
}
type rejoinFixtureTimer struct {
	clock    *RejoinFixtureClock
	until    time.Time
	callback func()
	stopped  bool
}

func (timer *rejoinFixtureTimer) Stop() bool {
	timer.clock.mu.Lock()
	defer timer.clock.mu.Unlock()
	active := !timer.stopped
	timer.stopped = true
	return active
}
func (timer *rejoinFixtureTimer) Reset(delay time.Duration) bool {
	timer.clock.mu.Lock()
	defer timer.clock.mu.Unlock()
	active := !timer.stopped
	timer.stopped = false
	timer.until = timer.clock.now.Add(delay)
	return active
}
func (clock *RejoinFixtureClock) Now() time.Time {
	clock.mu.Lock()
	defer clock.mu.Unlock()
	return clock.now
}
func (clock *RejoinFixtureClock) after(delay time.Duration, callback func()) leaseTimer {
	clock.mu.Lock()
	defer clock.mu.Unlock()
	timer := &rejoinFixtureTimer{clock: clock, until: clock.now.Add(delay), callback: callback}
	clock.timers = append(clock.timers, timer)
	return timer
}
func (clock *RejoinFixtureClock) Advance(delay time.Duration) {
	clock.mu.Lock()
	clock.now = clock.now.Add(delay)
	var callbacks []func()
	for _, timer := range clock.timers {
		if !timer.stopped && !clock.now.Before(timer.until) {
			timer.stopped = true
			callbacks = append(callbacks, timer.callback)
		}
	}
	clock.mu.Unlock()
	for _, callback := range callbacks {
		callback()
	}
}
func (broker *Broker) InstallRejoinFixtureClock() *RejoinFixtureClock {
	clock := &RejoinFixtureClock{now: time.Now()}
	broker.newLease = func(duration time.Duration) *leaseLifetime {
		return newLeaseWithClock(duration, clock.Now, clock.after)
	}
	return clock
}
func RejoinFixtureLease(ctx context.Context, mux *tcpforward.Mux, id string, known LeaseReceipt, renew bool) (LeaseReceipt, error) {
	receipt, _, err := exchangeLease(ctx, mux, id, known, renew)
	return receipt, err
}
