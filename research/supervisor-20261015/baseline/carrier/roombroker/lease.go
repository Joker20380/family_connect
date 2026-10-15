package roombroker

import (
	"context"
	"sync"
	"time"
)

type leaseLifetime struct {
	context.Context
	mu    sync.Mutex
	until time.Time
	timer leaseTimer
	stop  context.CancelCauseFunc
	now   func() time.Time
}

type leaseTimer interface {
	Stop() bool
	Reset(time.Duration) bool
}

func newLeaseLifetime(duration time.Duration) *leaseLifetime {
	return newLeaseWithClock(duration, time.Now, func(delay time.Duration, callback func()) leaseTimer { return time.AfterFunc(delay, callback) })
}

func newLeaseWithClock(duration time.Duration, now func() time.Time, after func(time.Duration, func()) leaseTimer) *leaseLifetime {
	parent, stop := context.WithCancelCause(context.Background())
	lease := &leaseLifetime{Context: parent, stop: stop, until: now().Add(duration), now: now}
	lease.timer = after(duration, lease.expire)
	return lease
}

func (lease *leaseLifetime) Err() error {
	if cause := context.Cause(lease.Context); cause != nil {
		return cause
	}
	return nil
}

func (lease *leaseLifetime) deadline() time.Time {
	lease.mu.Lock()
	defer lease.mu.Unlock()
	return lease.until
}

func (lease *leaseLifetime) expire() {
	lease.mu.Lock()
	defer lease.mu.Unlock()
	if !lease.now().Before(lease.until) {
		lease.stop(context.DeadlineExceeded)
	}
}

func (lease *leaseLifetime) extend(until time.Time) bool {
	lease.mu.Lock()
	defer lease.mu.Unlock()
	if lease.Err() != nil || !lease.now().Before(lease.until) || !until.After(lease.until) {
		return false
	}
	lease.until = until
	lease.timer.Reset(until.Sub(lease.now()))
	return true
}

func (lease *leaseLifetime) cancel() {
	lease.mu.Lock()
	defer lease.mu.Unlock()
	lease.timer.Stop()
	lease.stop(context.Canceled)
}

type leaseKey struct{}
type leaseBinding struct {
	broker  *Broker
	current *setup
}

type LeaseReceipt struct {
	SetupID   string    `json:"setup_id"`
	Sequence  uint64    `json:"sequence"`
	ExpiresAt time.Time `json:"expires_at"`
}

func (binding *leaseBinding) renew(ctx context.Context, request LeaseReceipt, authorize Authorize, securityDeadline time.Time) (LeaseReceipt, error) {
	identity, err := authorized(ctx, authorize)
	if err != nil {
		return LeaseReceipt{}, err
	}
	broker, current := binding.broker, binding.current
	broker.mu.Lock()
	defer broker.unlock()
	if broker.closed || broker.setups[current.id] != current || current.state != Active || current.ctx.Err() != nil || ctx.Err() != nil ||
		identity != current.identity || request.SetupID != current.id || !current.lease.now().Before(current.lease.deadline()) || !current.lease.now().Before(securityDeadline) {
		return LeaseReceipt{}, Code("stale_or_unbound_setup")
	}
	if request.Sequence == current.renewal && current.renewal != 0 && request.ExpiresAt.Equal(current.lastRequest.ExpiresAt) {
		return current.lastLease, nil
	}
	if current.renewal == ^uint64(0) || request.Sequence != current.renewal+1 || !request.ExpiresAt.Equal(current.lease.deadline()) {
		return LeaseReceipt{}, Code("renewal_replayed")
	}
	until := current.lease.now().Add(broker.limits.Lifetime)
	if securityDeadline.Before(until) {
		until = securityDeadline
	}
	if !until.After(current.lease.deadline()) {
		return LeaseReceipt{}, Code("renewal_limited")
	}
	if !current.lease.extend(until) {
		return LeaseReceipt{}, Code("renewal_expired")
	}
	current.renewal = request.Sequence
	current.lastRequest = request
	current.lastLease = LeaseReceipt{current.id, current.renewal, until}
	return current.lastLease, nil
}

func (broker *Broker) unlock() {
	pending := broker.pending
	broker.pending = nil
	broker.mu.Unlock()
	if len(pending) == 0 {
		return
	}
	broker.publishMu.Lock()
	defer broker.publishMu.Unlock()
	for _, publish := range pending {
		publish()
	}
}
