package roombroker

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
)

const renewalTimeout = 15 * time.Second

type leaseMessage struct {
	Type      string        `json:"type"`
	Lease     LeaseReceipt  `json:"lease"`
	Remaining time.Duration `json:"remaining_ns,omitempty"`
}

func leaseReader(stream io.Reader) *json.Decoder {
	decoder := json.NewDecoder(io.LimitReader(stream, 4096))
	decoder.DisallowUnknownFields()
	return decoder
}

func (binding *leaseBinding) snapshot(ctx context.Context, authorize Authorize, securityDeadline time.Time) (LeaseReceipt, error) {
	identity, err := authorized(ctx, authorize)
	if err != nil {
		return LeaseReceipt{}, err
	}
	broker, current := binding.broker, binding.current
	broker.mu.Lock()
	defer broker.unlock()
	if broker.closed || broker.setups[current.id] != current || current.state != Active || current.ctx.Err() != nil || ctx.Err() != nil || identity != current.identity ||
		!current.lease.now().Before(securityDeadline) || !current.lease.now().Before(current.lease.deadline()) {
		return LeaseReceipt{}, Code("stale_or_unbound_setup")
	}
	return LeaseReceipt{current.id, current.renewal, current.lease.deadline()}, nil
}

func (binding *leaseBinding) handler(authorize Authorize, securityDeadline time.Time) func(context.Context, *tcpforward.MuxStream) {
	return binding.dynamicHandler(func(ctx context.Context, use func(Identity, time.Time) error) error {
		identity, err := authorized(ctx, authorize)
		if err != nil {
			return err
		}
		return use(identity, securityDeadline)
	})
}

func (binding *leaseBinding) dynamicHandler(access authorizationAccess) func(context.Context, *tcpforward.MuxStream) {
	return func(parent context.Context, stream *tcpforward.MuxStream) {
		ctx, cancel := context.WithTimeout(parent, renewalTimeout)
		defer cancel()
		stop := context.AfterFunc(ctx, func() { stream.Reset() })
		defer stop()
		encoder, decoder := json.NewEncoder(stream), leaseReader(stream)
		deny := func() {
			if encoder.Encode(leaseMessage{Type: "denied"}) == nil {
				var done leaseMessage
				_ = decoder.Decode(&done)
			}
		}
		var current LeaseReceipt
		var securityDeadline time.Time
		snapshot := func() error {
			return access(ctx, func(identity Identity, deadline time.Time) error {
				var err error
				current, err = binding.snapshot(ctx, func(context.Context) (Identity, error) { return identity, nil }, deadline)
				securityDeadline = deadline
				return err
			})
		}
		err := snapshot()
		if err != nil {
			deny()
			return
		}
		remaining := current.ExpiresAt.Sub(binding.current.lease.now())
		if bound := securityDeadline.Sub(binding.current.lease.now()); bound < remaining {
			remaining = bound
		}
		leaseTrace(parent, "offer", current)
		if encoder.Encode(leaseMessage{Type: "offer", Lease: current, Remaining: remaining}) != nil {
			return
		}
		var request leaseMessage
		if decoder.Decode(&request) != nil {
			return
		}
		if request.Type == "renew" {
			leaseTrace(parent, "request", request.Lease)
			var accepted LeaseReceipt
			err := access(ctx, func(identity Identity, deadline time.Time) error {
				var err error
				accepted, err = binding.renew(ctx, request.Lease, func(context.Context) (Identity, error) { return identity, nil }, deadline)
				securityDeadline = deadline
				return err
			})
			kind := "accepted"
			if err == Code("renewal_limited") {
				kind, accepted = "limited", current
			} else if err != nil {
				deny()
				return
			}
			current = accepted
			if kind == "accepted" {
				leaseTrace(parent, "accepted", current)
			}
			remaining := min(current.ExpiresAt.Sub(binding.current.lease.now()), securityDeadline.Sub(binding.current.lease.now()))
			if encoder.Encode(leaseMessage{Type: kind, Lease: current, Remaining: remaining}) != nil {
				return
			}
			if decoder.Decode(&request) != nil {
				return
			}
		}
		if request.Type != "applied" || request.Lease.SetupID != current.SetupID || request.Lease.Sequence != current.Sequence || !request.Lease.ExpiresAt.Equal(current.ExpiresAt) {
			return
		}
		if err := snapshot(); err != nil {
			deny()
			return
		}
		leaseTrace(parent, "applied", current)
		if encoder.Encode(leaseMessage{Type: "confirmed", Lease: current}) != nil {
			return
		}
		var done leaseMessage
		_ = decoder.Decode(&done)
	}
}

func leaseTrace(ctx context.Context, action string, receipt LeaseReceipt) {
	sessiontrace.From(ctx).Record(sessiontrace.Event{Stage: "GATEWAY_SESSION", State: "ESTABLISHED", Reason: "NONE", LeaseDeadlineMS: receipt.ExpiresAt.UnixMilli(), LeaseAction: action, LeaseSequence: receipt.Sequence})
}

func exchangeLease(parent context.Context, mux *tcpforward.Mux, setupID string, known LeaseReceipt, renew bool) (LeaseReceipt, time.Time, error) {
	started := time.Now()
	ctx, cancel := context.WithTimeout(parent, renewalTimeout)
	defer cancel()
	stream, err := mux.OpenTCP(ctx, tcpforward.OpenRequest{Host: tcpforward.LeaseRenewalHost, Port: 1})
	if err != nil {
		return LeaseReceipt{}, time.Time{}, err
	}
	defer stream.Reset()
	encoder, decoder := json.NewEncoder(stream), leaseReader(stream)
	var response leaseMessage
	if err := decoder.Decode(&response); err != nil {
		return LeaseReceipt{}, time.Time{}, err
	}
	if response.Type == "denied" {
		return LeaseReceipt{}, time.Time{}, Code("unauthorized")
	}
	valid := func(message leaseMessage) bool {
		return message.Lease.SetupID == setupID && message.Remaining > 0 && message.Remaining <= 10*time.Minute &&
			message.Lease.Sequence >= known.Sequence && !message.Lease.ExpiresAt.Before(known.ExpiresAt)
	}
	if response.Type != "offer" || !valid(response) {
		return LeaseReceipt{}, time.Time{}, Code("renewal_protocol")
	}
	if renew && response.Lease.Sequence == known.Sequence {
		request := response.Lease
		request.Sequence++
		leaseTrace(parent, "request", request)
		if err := encoder.Encode(leaseMessage{Type: "renew", Lease: request}); err != nil {
			return LeaseReceipt{}, time.Time{}, err
		}
		if err := decoder.Decode(&response); err != nil {
			return LeaseReceipt{}, time.Time{}, err
		}
		if response.Type == "denied" {
			return LeaseReceipt{}, time.Time{}, Code("unauthorized")
		}
		if !valid(response) || !(response.Type == "accepted" && response.Lease.Sequence == request.Sequence || response.Type == "limited" && response.Lease.Sequence == known.Sequence && response.Lease.ExpiresAt.Equal(known.ExpiresAt)) {
			return LeaseReceipt{}, time.Time{}, Code("renewal_protocol")
		}
	}
	accepted, deadline := response.Lease, started.Add(response.Remaining)
	if err := encoder.Encode(leaseMessage{Type: "applied", Lease: accepted}); err != nil {
		return LeaseReceipt{}, time.Time{}, err
	}
	if err := decoder.Decode(&response); err != nil {
		return LeaseReceipt{}, time.Time{}, err
	}
	if response.Type != "confirmed" || response.Lease.SetupID != accepted.SetupID || response.Lease.Sequence != accepted.Sequence || !response.Lease.ExpiresAt.Equal(accepted.ExpiresAt) {
		if response.Type == "denied" {
			return LeaseReceipt{}, time.Time{}, Code("unauthorized")
		}
		return LeaseReceipt{}, time.Time{}, Code("renewal_protocol")
	}
	_ = encoder.Encode(leaseMessage{Type: "done"})
	leaseTrace(parent, "confirmed", accepted)
	return accepted, deadline, nil
}

func MaintainLease(ctx context.Context, mux *tcpforward.Mux, setupID string, closeSession func()) {
	MaintainSession(ctx, mux, setupID, closeSession, nil)
}

type Maintenance func(context.Context) (bool, error)

func MaintainSession(ctx context.Context, mux *tcpforward.Mux, setupID string, closeSession func(), updates <-chan Maintenance) {
	maintainSession(ctx, func(ctx context.Context, known LeaseReceipt, renew bool) (LeaseReceipt, time.Time, error) {
		return exchangeLease(ctx, mux, setupID, known, renew)
	}, closeSession, updates)
}

func maintainLease(ctx context.Context, exchange func(context.Context, LeaseReceipt, bool) (LeaseReceipt, time.Time, error), closeSession func()) {
	maintainSession(ctx, exchange, closeSession, nil)
}

func waitMaintenance(ctx context.Context, until, deadline time.Time, updates <-chan Maintenance) (bool, error) {
	timer := time.NewTimer(max(0, time.Until(until)))
	defer timer.Stop()
	for {
		select {
		case <-ctx.Done():
			return false, ctx.Err()
		case <-timer.C:
			return false, nil
		case update := <-updates:
			bounded, cancel := context.WithDeadline(ctx, deadline)
			changed, err := update(bounded)
			cancel()
			if err != nil || changed {
				return changed, err
			}
		}
	}
}

func maintainSession(ctx context.Context, exchange func(context.Context, LeaseReceipt, bool) (LeaseReceipt, time.Time, error), closeSession func(), updates <-chan Maintenance) {
	known, deadline, err := exchange(ctx, LeaseReceipt{}, false)
	if err != nil {
		var unsupported *tcpforward.OpenError
		if errors.As(err, &unsupported) && unsupported.Code == "policy_rejected" {
			return
		}
		if err == Code("unauthorized") || err == Code("renewal_protocol") {
			closeSession()
		}
		return
	}
	force := false
	for {
		remaining := time.Until(deadline)
		margin := min(2*time.Minute, remaining/5)
		until := time.Now().Add(max(0, remaining-margin))
		if force {
			until = time.Now()
			force = false
		}
		if _, err := waitMaintenance(ctx, until, deadline, updates); err != nil {
			if ctx.Err() == nil {
				closeSession()
			}
			return
		}
		accepted := false
		for attempt := 0; attempt < 3 && time.Now().Before(deadline); attempt++ {
			bounded, cancel := context.WithDeadline(ctx, deadline)
			next, nextDeadline, err := exchange(bounded, known, true)
			cancel()
			if err == nil {
				if !next.ExpiresAt.After(known.ExpiresAt) {
					if nextDeadline.Before(deadline) {
						deadline = nextDeadline
					}
					break
				}
				known, deadline, accepted = next, nextDeadline, true
				break
			}
			if err == Code("unauthorized") || err == Code("renewal_protocol") {
				closeSession()
				return
			}
			if ctx.Err() != nil {
				return
			}
			if attempt < 2 {
				retry := time.NewTimer(min(5*time.Second, max(0, time.Until(deadline))))
				select {
				case <-ctx.Done():
					retry.Stop()
					return
				case <-retry.C:
				}
			}
		}
		if !accepted {
			changed, err := waitMaintenance(ctx, deadline, deadline, updates)
			if err == nil && changed {
				force = true
				continue
			}
			if ctx.Err() == nil {
				closeSession()
			}
			return
		}
	}
}
