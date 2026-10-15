package roombroker

import (
	"context"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

type exchangeKey struct{}

func WithExchange(ctx context.Context, nonce string) context.Context {
	tag, _ := sessiontrace.Tag(nonce)
	return context.WithValue(ctx, exchangeKey{}, tag)
}

func exchangeTag(ctx context.Context) string {
	tag, _ := ctx.Value(exchangeKey{}).(string)
	return tag
}

type OwnershipEvent struct {
	Sequence        int    `json:"sequence"`
	TimestampMS     int64  `json:"timestamp_ms"`
	Exchange        string `json:"exchange,omitempty"`
	HolderExchange  string `json:"holder_exchange,omitempty"`
	Scope           string `json:"scope"`
	Action          string `json:"action"`
	Generation      string `json:"generation,omitempty"`
	State           State  `json:"holder_state,omitempty"`
	Started         bool   `json:"started"`
	Claimed         bool   `json:"claimed"`
	Present         bool   `json:"present"`
	CreatedMS       int64  `json:"created_ms,omitempty"`
	DeadlineMS      int64  `json:"deadline_ms,omitempty"`
	LeaseDeadlineMS int64  `json:"lease_deadline_ms,omitempty"`
	SameIdentity    string `json:"same_identity"`
	Reason          string `json:"reason"`
}

type OwnershipSnapshot struct {
	Schema  string           `json:"schema"`
	Limited bool             `json:"limited"`
	Events  []OwnershipEvent `json:"events"`
}

type ownershipCapture struct {
	until   time.Time
	limit   int
	limited bool
	events  []OwnershipEvent
}

func (broker *Broker) CaptureOwnership(limit int, until time.Time) error {
	broker.mu.Lock()
	defer broker.mu.Unlock()
	if broker.ownership != nil || limit < 1 || limit > 512 || !until.After(time.Now()) || time.Until(until) > 15*time.Minute {
		return Code("invalid_observation")
	}
	broker.ownership = &ownershipCapture{until: until, limit: limit, events: make([]OwnershipEvent, 0, limit)}
	for _, current := range broker.setups {
		broker.ownershipLocked(context.Background(), current, nil, "snapshot", "capture_started")
	}
	return nil
}

func (broker *Broker) OwnershipSnapshot() OwnershipSnapshot {
	broker.mu.Lock()
	defer broker.mu.Unlock()
	result := OwnershipSnapshot{Schema: "admission-ownership-v1", Events: []OwnershipEvent{}}
	if capture := broker.ownership; capture != nil {
		result.Limited = capture.limited
		result.Events = append(result.Events, capture.events...)
	}
	return result
}

func (broker *Broker) ExchangeEvent(ctx context.Context, action, reason string) {
	if !sessiontrace.Allowed(action, "authenticated|hello_sent|descriptor_sent|handoff|exchange_end") ||
		!sessiontrace.Allowed(reason, "ok|context_deadline|context_cancelled|error") {
		return
	}
	broker.mu.Lock()
	defer broker.mu.Unlock()
	broker.ownershipLocked(ctx, nil, nil, action, reason)
}

func (broker *Broker) ownershipLocked(ctx context.Context, current *setup, requester *Identity, action, reason string) {
	capture := broker.ownership
	if capture == nil || !time.Now().Before(capture.until) {
		return
	}
	if len(capture.events) == capture.limit {
		capture.limited = true
		return
	}
	event := OwnershipEvent{Sequence: len(capture.events) + 1, TimestampMS: time.Now().UnixMilli(), Exchange: exchangeTag(ctx), Scope: "broker_identity", Action: action, SameIdentity: "unknown", Reason: reason}
	if reason == "outstanding_limit" {
		event.Scope = "broker_global"
	}
	if current != nil {
		event.Generation, _ = sessiontrace.Tag(current.id)
		event.HolderExchange = current.exchange
		event.State, event.Started, event.Claimed = current.state, current.started, current.claimed
		event.Present = broker.setups[current.id] == current
		event.CreatedMS, event.DeadlineMS = current.created.UnixMilli(), current.deadline.UnixMilli()
		event.LeaseDeadlineMS = current.lease.deadline().UnixMilli()
		if requester != nil {
			event.SameIdentity = "false"
			if *requester == current.identity {
				event.SameIdentity = "true"
			}
		}
	}
	capture.events = append(capture.events, event)
}

func ownershipReason(err error) string {
	if err == context.DeadlineExceeded {
		return "context_deadline"
	}
	if err == context.Canceled {
		return "context_cancelled"
	}
	if err != nil {
		return "error"
	}
	return "cleanup_done"
}
