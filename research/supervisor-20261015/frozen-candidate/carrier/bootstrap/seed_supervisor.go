package bootstrap

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/telemost"
)

const MaxSeedRecoveryAttempts = 3

type SeedRecovery struct {
	Schema          int                           `json:"schema"`
	UTC             time.Time                     `json:"utc"`
	State           string                        `json:"state"`
	RoomHash        string                        `json:"room_hash"`
	OldGeneration   uint64                        `json:"old_generation"`
	NewGeneration   uint64                        `json:"new_generation"`
	Attempt         int                           `json:"attempt"`
	BackoffMS       int64                         `json:"backoff_ms"`
	FirstStage      string                        `json:"first_stage"`
	FirstSource     string                        `json:"first_source"`
	FirstSignaling  telemost.SignalingReadFailure `json:"first_signaling"`
	Outcome         string                        `json:"outcome"`
	EndpointReady   bool                          `json:"endpoint_ready"`
	SubscriberReady bool                          `json:"subscriber_ready"`
	PublisherReady  bool                          `json:"publisher_ready"`
	SamplesWritten  uint64                        `json:"media_samples_written"`
	RTPReceived     uint64                        `json:"rtp_received"`
}

type seedGeneration struct {
	id      uint64
	ctx     context.Context
	cancel  context.CancelFunc
	carrier familysession.PacketEndpoint
	once    sync.Once
}

func newSeedGeneration(parent context.Context, id uint64) *seedGeneration {
	ctx, cancel := context.WithCancel(parent)
	return &seedGeneration{id: id, ctx: ctx, cancel: cancel}
}

func (generation *seedGeneration) close() {
	generation.once.Do(func() {
		generation.cancel()
		if generation.carrier != nil {
			generation.carrier.Close()
		}
	})
}

func (manager *SeedManager) swapGeneration(previous, next *seedGeneration) bool {
	manager.mu.Lock()
	defer manager.mu.Unlock()
	if manager.current != previous {
		return false
	}
	manager.current = next
	manager.acceptanceGeneration(next)
	return true
}

type seedConnectFailure struct {
	cause     error
	source    string
	signaling telemost.SignalingReadFailure
}

func (failure *seedConnectFailure) Error() string { return "seed_join_failed" }
func (failure *seedConnectFailure) Unwrap() error { return failure.cause }

func recoverableSeed(failure SeedFailure) bool {
	return failure.Stage == "SEED_READ" && failure.ParentError == nil && failure.CloseSource == "SIGNAL_READ" && failure.SignalingRead.Kind == "WS_CLOSE" && failure.SignalingRead.CloseCode == 1011 && failure.SignalingRead.ContextState == "ACTIVE" && !failure.SignalingRead.CarrierClosed
}

func seedReadFailure(stage string, cause error, parent context.Context, carrier familysession.PacketEndpoint) SeedFailure {
	failure := SeedFailure{Stage: stage, Cause: cause, ParentError: parent.Err()}
	if stage == "SEED_READ" {
		if observed, ok := carrier.(interface{ SeedCloseSource() string }); ok {
			failure.CloseSource = observed.SeedCloseSource()
		}
		if observed, ok := carrier.(interface {
			SeedSignalingReadFailure() telemost.SignalingReadFailure
		}); ok {
			failure.SignalingRead = observed.SeedSignalingReadFailure()
		}
	}
	return failure
}

func (manager *SeedManager) supervise(parent context.Context, room roombroker.Room, initial *seedGeneration, connect SeedConnector, exchange func(context.Context, familysession.PacketEndpoint)) error {
	current := initial
	defer func() { current.close(); manager.swapGeneration(current, nil) }()
	attempts := 0
	for {
		var first SeedFailure
		err := serveCarrier(current.ctx, current.carrier, exchange, func(stage string, cause error) {
			if first.Stage == "" {
				first = seedReadFailure(stage, cause, parent, current.carrier)
			}
		})
		if !recoverableSeed(first) || parent.Err() != nil {
			if manager.Observe != nil && first.Stage != "" {
				manager.Observe(first)
			}
			if attempts > 0 && parent.Err() == context.Canceled {
				return nil
			}
			return err
		}
		next, recoveryErr := manager.recoverSeed(parent, room, current, connect, first, &attempts)
		if recoveryErr != nil {
			if manager.Observe != nil && parent.Err() == nil {
				manager.Observe(first)
			}
			if parent.Err() == context.Canceled {
				return nil
			}
			return recoveryErr
		}
		current = next
	}
}

func (manager *SeedManager) recoverSeed(parent context.Context, room roombroker.Room, previous *seedGeneration, connect SeedConnector, first SeedFailure, attempts *int) (*seedGeneration, error) {
	digest := sha256.Sum256([]byte(room.ID))
	event := SeedRecovery{Schema: 1, State: "SEED_RECOVERING", RoomHash: hex.EncodeToString(digest[:]), OldGeneration: previous.id, FirstStage: first.Stage, FirstSource: first.CloseSource, FirstSignaling: first.SignalingRead.Sanitized()}
	emit := func(state, outcome string) {
		event.UTC = manager.timeNow().UTC()
		event.State = state
		event.Outcome = outcome
		if manager.Recovery != nil {
			manager.Recovery(event)
		}
	}
	emit("SEED_RECOVERING", "FIRST_CLOSE")
	previous.close()
	if manager.RecoveryCheck == nil {
		emit("SEED_TERMINAL", "SECURITY_UNAVAILABLE")
		return nil, roombroker.Code("seed_closed")
	}
	securityDeadline, err := manager.RecoveryCheck(parent)
	if err != nil || !manager.timeNow().Before(securityDeadline) {
		emit("SEED_TERMINAL", "SECURITY_REJECTED")
		return nil, roombroker.Code("credentials_rejected")
	}
	deadline := minTimeRecovery(time.Now().Add(ConnectTimeout), securityDeadline)
	budget, cancel := context.WithDeadline(parent, deadline)
	defer cancel()
	for *attempts < MaxSeedRecoveryAttempts {
		*attempts++
		event.Attempt = *attempts
		event.NewGeneration = uint64(*attempts) + 1
		backoff := time.Second * time.Duration(1<<(*attempts-1))
		event.BackoffMS = backoff.Milliseconds()
		emit("SEED_RECOVERING", "BACKOFF")
		timer := time.NewTimer(backoff)
		select {
		case <-budget.Done():
			timer.Stop()
			emit("SEED_TERMINAL", "DEADLINE_OR_STOP")
			return nil, budget.Err()
		case <-timer.C:
		}
		securityDeadline, err = manager.RecoveryCheck(budget)
		if err != nil || !manager.timeNow().Before(securityDeadline) {
			emit("SEED_TERMINAL", "SECURITY_REJECTED")
			return nil, roombroker.Code("credentials_rejected")
		}
		next := newSeedGeneration(parent, event.NewGeneration)
		ready, stop := context.WithDeadline(budget, securityDeadline)
		stopLifetime := context.AfterFunc(ready, next.cancel)
		endpoint, connectErr := connect(next.ctx, ready, room)
		next.carrier = endpoint
		readyErr := ready.Err()
		lifetimeDetached := stopLifetime()
		stop()
		if connectErr == nil && readyErr == nil && lifetimeDetached && endpoint != nil && budget.Err() == nil && next.ctx.Err() == nil {
			until, securityErr := manager.RecoveryCheck(budget)
			if securityErr != nil || !manager.timeNow().Before(until) {
				next.close()
				emit("SEED_TERMINAL", "SECURITY_REJECTED")
				return nil, roombroker.Code("credentials_rejected")
			}
			if !manager.swapGeneration(previous, next) {
				next.close()
				emit("SEED_TERMINAL", "STALE_GENERATION")
				return nil, roombroker.Code("seed_closed")
			}
			event.EndpointReady = true
			if observed, ok := endpoint.(*observedSeed); ok {
				if session, ok := observed.PacketEndpoint.(*telemost.Session); ok {
					stats := session.Stats()
					event.SubscriberReady = stats.SubscriberState == "connected"
					event.PublisherReady = stats.PublisherState == "connected"
					event.SamplesWritten = stats.Media.SamplesWritten
					event.RTPReceived = stats.Media.RTPReceived
				}
			}
			emit("SEED_ACTIVE", "RECOVERED")
			return next, nil
		}
		next.close()
		var failed *seedConnectFailure
		if !errors.As(connectErr, &failed) || !recoverableSeed(SeedFailure{Stage: "SEED_READ", CloseSource: failed.source, SignalingRead: failed.signaling, ParentError: budget.Err()}) {
			emit("SEED_TERMINAL", "CONNECT_REJECTED")
			return nil, roombroker.Code("seed_not_ready")
		}
		emit("SEED_RECOVERING", "CONNECT_WS1011")
	}
	emit("SEED_TERMINAL", "ATTEMPTS_EXHAUSTED")
	return nil, roombroker.Code("seed_closed")
}

func minTimeRecovery(first, second time.Time) time.Time {
	if second.Before(first) {
		return second
	}
	return first
}
