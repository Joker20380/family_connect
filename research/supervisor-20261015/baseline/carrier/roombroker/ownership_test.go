package roombroker

import (
	"context"
	"encoding/json"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func observedBroker(test *testing.T) *Broker {
	test.Helper()
	broker := makeBroker(test, providerFunc(fresh), gatewayFunc(func(context.Context, context.Context, Room, string, Identity) (Gateway, error) {
		return &fakeGateway{run: waiting}, nil
	}), shortLimits())
	if err := broker.CaptureOwnership(512, time.Now().Add(time.Minute)); err != nil {
		test.Fatal(err)
	}
	return broker
}

func observedActive(test *testing.T, broker *Broker, ctx context.Context, authorize Authorize) string {
	test.Helper()
	identifier, err := broker.Challenge(ctx, authorize)
	if err != nil {
		test.Fatal(err)
	}
	if _, err := broker.Create(ctx, identifier, authorize); err != nil {
		test.Fatal(err)
	}
	if err := broker.Claim(ctx, identifier, authorize); err != nil {
		test.Fatal(err)
	}
	broker.mu.Lock()
	current := broker.setups[identifier]
	broker.mu.Unlock()
	if err := broker.activate(current); err != nil {
		test.Fatal(err)
	}
	return identifier
}

func observedEvent(test *testing.T, broker *Broker, action, exchange string) OwnershipEvent {
	test.Helper()
	deadline := time.Now().Add(time.Second)
	for time.Now().Before(deadline) {
		for _, event := range broker.OwnershipSnapshot().Events {
			if event.Action == action && event.Exchange == exchange {
				return event
			}
		}
		time.Sleep(time.Millisecond)
	}
	test.Fatalf("missing %s for exchange", action)
	return OwnershipEvent{}
}

func TestOwnershipActualHolderNotNearestActive(test *testing.T) {
	broker := observedBroker(test)
	holderContext := WithExchange(context.Background(), strings.Repeat("1", 64))
	holder := observedActive(test, broker, holderContext, allow)
	other := func(context.Context) (Identity, error) {
		identity := testIdentity
		identity.Device = strings.Repeat("c", 32)
		return identity, nil
	}
	unrelated := observedActive(test, broker, WithExchange(context.Background(), strings.Repeat("2", 64)), other)
	if holder == unrelated {
		test.Fatal("duplicate generation")
	}
	waiting, cancel := context.WithCancel(WithExchange(context.Background(), strings.Repeat("3", 64)))
	done := make(chan error, 1)
	go func() { _, err := broker.ChallengeAfterCleanup(waiting, allow); done <- err }()
	event := observedEvent(test, broker, "wait", exchangeTag(waiting))
	tag, _ := sessiontrace.Tag(holder)
	if event.Generation != tag || event.HolderExchange != exchangeTag(holderContext) || event.State != Active || event.SameIdentity != "true" || !event.Present {
		test.Fatalf("wrong holder: %+v", event)
	}
	cancel()
	if err := <-done; err != context.Canceled {
		test.Fatal(err)
	}
	end := observedEvent(test, broker, "wait_end", exchangeTag(waiting))
	if !end.Present || end.State != Active || end.Reason != "context_cancelled" {
		test.Fatal("waiter released active owner", end)
	}
	if _, err := broker.Challenge(context.Background(), allow); err != Code("device_busy") {
		test.Fatal(err)
	}
	encoded, _ := json.Marshal(broker.OwnershipSnapshot())
	for _, secret := range []string{testIdentity.Family, testIdentity.Device, holder, unrelated, "JoinURL", "PublicKey"} {
		if strings.Contains(string(encoded), secret) {
			test.Fatal("private data in capture")
		}
	}
}

func TestOwnershipWaitDeadlineAndReleaseGeneration(test *testing.T) {
	broker := observedBroker(test)
	ctx := WithExchange(context.Background(), strings.Repeat("4", 64))
	old := observedActive(test, broker, ctx, allow)
	waiting, cancel := context.WithTimeout(WithExchange(ctx, strings.Repeat("5", 64)), 20*time.Millisecond)
	defer cancel()
	if _, err := broker.ChallengeAfterCleanup(waiting, allow); err != context.DeadlineExceeded {
		test.Fatal(err)
	}
	end := observedEvent(test, broker, "wait_end", exchangeTag(waiting))
	if end.Reason != "context_deadline" || !end.Present || end.State != Active {
		test.Fatal(end)
	}
	if err := broker.Cancel(ctx, old, allow); err != nil {
		test.Fatal(err)
	}
	waitEmpty(test, broker)
	newID, err := broker.Challenge(ctx, allow)
	if err != nil || newID == old {
		test.Fatal("new generation missing", err)
	}
	for count := 0; count < 2; count++ {
		if err := broker.Cancel(ctx, old, allow); err != Code("stale_or_unbound_setup") {
			test.Fatal("old cleanup accepted", err)
		}
	}
	if _, err := broker.Challenge(ctx, allow); err != Code("device_busy") {
		test.Fatal("old cleanup released new holder", err)
	}
	released := false
	oldTag, _ := sessiontrace.Tag(old)
	for _, event := range broker.OwnershipSnapshot().Events {
		if event.Generation == oldTag && event.Action == "release" {
			released = true
			if event.Present || !terminal(event.State) || event.Reason != "worker_finished" {
				test.Fatal(event)
			}
		}
	}
	if !released {
		test.Fatal("release not captured")
	}
}

func TestOwnershipPendingSetupAndPreAcquisitionFailure(test *testing.T) {
	broker := observedBroker(test)
	ctx := WithExchange(context.Background(), strings.Repeat("6", 64))
	identifier, err := broker.Challenge(ctx, allow)
	if err != nil {
		test.Fatal(err)
	}
	if _, err := broker.ChallengeAfterCleanup(ctx, allow); err != Code("device_busy") {
		test.Fatal("pending setup should not wait", err)
	}
	if _, err := broker.ChallengeAfterCleanup(ctx, deny); err != Code("unauthorized") {
		test.Fatal(err)
	}
	if _, err := broker.Challenge(ctx, allow); err != Code("device_busy") {
		test.Fatal("unacquired error released owner")
	}
	if err := broker.Cancel(ctx, identifier, allow); err != nil {
		test.Fatal(err)
	}
	waitEmpty(test, broker)
	event := observedEvent(test, broker, "release", "")
	if event.Reason != "monitor_unstarted" || event.Present || event.Started {
		test.Fatal(event)
	}
}

func TestOwnershipCaptureBoundAndSnapshotIsolation(test *testing.T) {
	broker := observedBroker(test)
	ctx := WithExchange(context.Background(), strings.Repeat("7", 64))
	for count := 0; count < 600; count++ {
		broker.ExchangeEvent(ctx, "authenticated", "ok")
	}
	snapshot := broker.OwnershipSnapshot()
	if len(snapshot.Events) != 512 || !snapshot.Limited {
		test.Fatal("unbounded capture")
	}
	snapshot.Events[0].Reason = "mutated"
	if broker.OwnershipSnapshot().Events[0].Reason != "ok" {
		test.Fatal("snapshot aliases live memory")
	}
}

type ownershipClosingGateway struct {
	entered chan struct{}
	finish  chan struct{}
}

func (gateway *ownershipClosingGateway) Run(ctx context.Context, _ func() error) error {
	<-ctx.Done()
	return ctx.Err()
}

func (gateway *ownershipClosingGateway) Close() error {
	close(gateway.entered)
	<-gateway.finish
	return nil
}

func TestOwnershipTerminalHeldUntilGatewayClose(test *testing.T) {
	broker := observedBroker(test)
	gateway := &ownershipClosingGateway{entered: make(chan struct{}), finish: make(chan struct{})}
	broker.gateway = gatewayFunc(func(context.Context, context.Context, Room, string, Identity) (Gateway, error) { return gateway, nil })
	ctx := WithExchange(context.Background(), strings.Repeat("8", 64))
	identifier := observedActive(test, broker, ctx, allow)
	if err := broker.Cancel(ctx, identifier, allow); err != nil {
		test.Fatal(err)
	}
	<-gateway.entered
	defer close(gateway.finish)
	waiting, cancel := context.WithTimeout(WithExchange(ctx, strings.Repeat("9", 64)), 20*time.Millisecond)
	defer cancel()
	if _, err := broker.ChallengeAfterCleanup(waiting, allow); err != context.DeadlineExceeded {
		test.Fatal(err)
	}
	event := observedEvent(test, broker, "wait", exchangeTag(waiting))
	if !terminal(event.State) || !event.Started || !event.Present || event.SameIdentity != "true" {
		test.Fatal("terminal holder not distinguished", event)
	}
	for _, event := range broker.OwnershipSnapshot().Events {
		if event.Action == "release" {
			test.Fatal("slot released before actual gateway close")
		}
	}
}

func TestOwnershipProviderErrorAndTimeoutRelease(test *testing.T) {
	for _, timeout := range []bool{false, true} {
		test.Run(map[bool]string{false: "error", true: "timeout"}[timeout], func(test *testing.T) {
			broker := observedBroker(test)
			broker.limits.Create = 10 * time.Millisecond
			broker.provider = providerFunc(func(ctx context.Context) (Room, error) {
				if timeout {
					<-ctx.Done()
					return Room{}, ctx.Err()
				}
				return Room{}, Code("provider_failure")
			})
			identifier, err := broker.Challenge(context.Background(), allow)
			if err != nil {
				test.Fatal(err)
			}
			if _, err := broker.Create(context.Background(), identifier, allow); err == nil {
				test.Fatal("provider failure lost")
			}
			waitEmpty(test, broker)
			event := observedEvent(test, broker, "release", "")
			if event.State != Failed || event.Present || !event.Started {
				test.Fatal(event)
			}
			if _, err := broker.Challenge(context.Background(), allow); err != nil {
				test.Fatal("slot leaked after provider failure", err)
			}
		})
	}
}
