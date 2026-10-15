package bootstrap

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/roombroker"
)

func TestExchangeReasonDoesNotExposeRawErrors(test *testing.T) {
	for _, entry := range []struct {
		err  error
		want string
	}{
		{roombroker.Code("device_busy"), "device_busy"},
		{fmt.Errorf("private wrapper: %w", roombroker.Code("unauthorized")), "unauthorized"},
		{context.Canceled, "context_cancelled"},
		{fmt.Errorf("private: %w", context.DeadlineExceeded), "context_deadline"},
		{errors.New("device_busy"), "unknown"},
		{roombroker.Code("https://private.example/?token=secret"), "unknown"},
		{errors.New("certificate private profile bytes"), "unknown"},
		{nil, "unknown"},
	} {
		if got := exchangeReason(entry.err); got != entry.want {
			test.Fatalf("got %q, want %q", got, entry.want)
		}
		encoded, err := json.Marshal(ExchangeFailure{Stage: "challenge", Reason: exchangeReason(entry.err)})
		if err != nil || len(encoded) > 96 || strings.Contains(string(encoded), "private") || strings.Contains(string(encoded), "secret") {
			test.Fatal("unbounded or private diagnostic")
		}
	}
}

func TestObservedChallengeRejectionsKeepWireAndAdmissionClosed(test *testing.T) {
	for _, reason := range []string{"device_busy", "outstanding_limit", "unauthorized", "closed"} {
		test.Run(reason, func(test *testing.T) {
			ctx := bounded(test)
			var calls atomic.Int32
			limits := roombroker.DefaultLimits()
			if reason == "outstanding_limit" {
				limits.Outstanding = 1
			}
			broker, _ := testBroker(test, &calls, nil, "", limits)
			authorize := roombroker.Authorize(allow)
			if reason == "device_busy" || reason == "outstanding_limit" {
				if _, err := broker.Challenge(ctx, allow); err != nil {
					test.Fatal(err)
				}
			}
			if reason == "outstanding_limit" {
				authorize = func(ctx context.Context) (roombroker.Identity, error) {
					identity, err := allow(ctx)
					identity.Device = strings.Repeat("a", 32)
					return identity, err
				}
			}
			if reason == "unauthorized" {
				authorize = func(context.Context) (roombroker.Identity, error) {
					return roombroker.Identity{}, errors.New("private authorization detail")
				}
			}
			if reason == "closed" {
				broker.Close()
			}
			client, server := pair()
			var reports []ExchangeFailure
			err := exchange(ctx, server, broker, authorize, func(report ExchangeFailure) { reports = append(reports, report) })
			var code roombroker.Code
			if !errors.As(err, &code) || string(code) != reason || calls.Load() != 0 {
				test.Fatal("admission or original error changed", err)
			}
			if len(reports) != 1 || reports[0] != (ExchangeFailure{Stage: "challenge", Reason: reason}) {
				test.Fatal("missing or duplicate safe rejection", reports)
			}
			raw, err := client.Recv(ctx)
			if err != nil || string(raw) != `{"type":"ERROR"}` {
				test.Fatal("reason exposed over wire or unexpected message")
			}
			if _, err := client.Recv(ctx); err == nil {
				test.Fatal("rejected exchange left open")
			}
			if reason == "device_busy" {
				if _, err := broker.Challenge(ctx, allow); err != roombroker.Code("device_busy") {
					test.Fatal("diagnosis cancelled the original setup", err)
				}
			}
		})
	}
}

func TestObservedMalformedRequestReportsReceiveStage(test *testing.T) {
	ctx := bounded(test)
	var calls atomic.Int32
	broker, _ := testBroker(test, &calls, nil, "")
	client, server := pair()
	reports := make(chan ExchangeFailure, 1)
	done := make(chan error, 1)
	go func() {
		done <- exchange(ctx, server, broker, allow, func(report ExchangeFailure) { reports <- report })
	}()
	if _, err := client.Recv(ctx); err != nil {
		test.Fatal(err)
	}
	if err := client.SendContext(ctx, []byte(`{"type":"DATA","secret":"not-for-logs"}`)); err != nil {
		test.Fatal(err)
	}
	if err := <-done; err != roombroker.Code("bootstrap_protocol_rejected") {
		test.Fatal("malformed request accepted", err)
	}
	if report := <-reports; report != (ExchangeFailure{Stage: "request_receive", Reason: "bootstrap_protocol_rejected"}) {
		test.Fatal("wrong diagnostic", report)
	}
	if calls.Load() != 0 {
		test.Fatal("provider called before valid request")
	}
}

type delayedCleanupGateway struct {
	claimed   chan struct{}
	active    chan error
	release   chan struct{}
	closed    chan struct{}
	closeOnce sync.Once
}

func (gateway *delayedCleanupGateway) Run(ctx context.Context, activate func() error) error {
	select {
	case <-gateway.claimed:
	case <-ctx.Done():
		return ctx.Err()
	}
	err := activate()
	gateway.active <- err
	if err != nil {
		return err
	}
	select {
	case <-gateway.release:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func (gateway *delayedCleanupGateway) Close() error {
	gateway.closeOnce.Do(func() { close(gateway.closed) })
	return nil
}

func TestActiveGatewayBlocksNewExchangeUntilServerCleanup(test *testing.T) {
	ctx := bounded(test)
	back := &delayedCleanupGateway{claimed: make(chan struct{}), active: make(chan error, 1), release: make(chan struct{}), closed: make(chan struct{})}
	var calls atomic.Int32
	limits := roombroker.DefaultLimits()
	limits.Recheck = time.Millisecond
	broker, err := roombroker.New(providerFunc(func(context.Context) (roombroker.Room, error) {
		calls.Add(1)
		return roombroker.Room{ID: "test", JoinURL: "https://telemost.yandex.ru/j/dedicated-test"}, nil
	}), starterFunc(func(context.Context, context.Context, roombroker.Room, string, roombroker.Identity) (roombroker.Gateway, error) {
		return back, nil
	}), limits, nil)
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(broker.Close)
	id, err := broker.Challenge(ctx, allow)
	if err != nil {
		test.Fatal(err)
	}
	if _, err := broker.Create(ctx, id, allow); err != nil {
		test.Fatal(err)
	}
	if err := broker.Claim(ctx, id, allow); err != nil {
		test.Fatal(err)
	}
	close(back.claimed)
	select {
	case err := <-back.active:
		if err != nil {
			test.Fatal(err)
		}
	case <-ctx.Done():
		test.Fatal("old session never became active")
	}
	test.Run("deadline", func(test *testing.T) {
		waiting, cancel := context.WithTimeout(ctx, 20*time.Millisecond)
		defer cancel()
		if _, err := broker.ChallengeAfterCleanup(waiting, allow); err != context.DeadlineExceeded {
			test.Fatal("wait escaped caller deadline", err)
		}
	})
	for _, changedIdentity := range []bool{false, true} {
		test.Run(fmt.Sprintf("authorization_changed_%t", changedIdentity), func(test *testing.T) {
			var checks atomic.Int32
			authorize := func(ctx context.Context) (roombroker.Identity, error) {
				identity, err := allow(ctx)
				if checks.Add(1) > 2 {
					if !changedIdentity {
						return roombroker.Identity{}, errors.New("revoked")
					}
					identity.Device = strings.Repeat("a", 32)
				}
				return identity, err
			}
			if _, err := broker.ChallengeAfterCleanup(ctx, authorize); err != roombroker.Code("unauthorized") || checks.Load() < 3 {
				test.Fatal("changed authorization survived wait", err)
			}
		})
	}
	test.Run("cancelled", func(test *testing.T) {
		waiting, cancel := context.WithCancel(ctx)
		var checks atomic.Int32
		authorize := func(ctx context.Context) (roombroker.Identity, error) {
			if checks.Add(1) > 2 {
				cancel()
			}
			return allow(ctx)
		}
		defer cancel()
		if _, err := broker.ChallengeAfterCleanup(waiting, authorize); err != context.Canceled || checks.Load() < 3 {
			test.Fatal("cancelled wait admitted a setup", err)
		}
	})
	client, server := pair()
	defer client.Close()
	done := make(chan error, 1)
	go func() { done <- Exchange(ctx, server, broker, allow) }()
	probe, stop := context.WithTimeout(ctx, 20*time.Millisecond)
	_, receiveErr := client.Recv(probe)
	stop()
	if receiveErr != context.DeadlineExceeded {
		test.Fatal("new exchange rejected or admitted before old cleanup", receiveErr)
	}
	select {
	case <-back.closed:
		test.Fatal("rejected exchange killed old session")
	default:
	}
	close(back.release)
	raw, err := client.Recv(ctx)
	var hello message
	if err != nil || json.Unmarshal(raw, &hello) != nil || hello.Type != "HELLO" || hello.SetupID == id || calls.Load() != 1 {
		test.Fatal("fresh challenge missing after cleanup", err)
	}
	if err := client.Close(); err != nil {
		test.Fatal(err)
	}
	if err := <-done; err != roombroker.Code("bootstrap_protocol_rejected") {
		test.Fatal("unexpected exchange outcome after test client close", err)
	}
}
