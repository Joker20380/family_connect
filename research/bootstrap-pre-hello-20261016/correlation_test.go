package bootstrap

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"time"

	serverbootstrap "fixture.invalid/gateway/bootstrap"
	serverfamily "fixture.invalid/gateway/familysession"
	brokerapi "fixture.invalid/gateway/roombroker"
	servertrace "fixture.invalid/gateway/sessiontrace"
	"github.com/Joker20380/family_connect/carrier/nativeexport"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/Joker20380/family_connect/carrier/startupdiag"
)

func correlationAwait[Value any](test *testing.T, ctx context.Context, channel <-chan Value) Value {
	test.Helper()
	select {
	case value := <-channel:
		return value
	case <-ctx.Done():
		test.Fatal("fixture synchronization deadline")
	}
	var empty Value
	return empty
}

type correlationProvider struct{}

func (correlationProvider) CreateRoom(context.Context) (brokerapi.Room, error) {
	return brokerapi.Room{ID: "local-only", JoinURL: "https://telemost.yandex.ru/j/local-fixture"}, nil
}

type correlationGateway struct {
	activate chan struct{}
	active   chan error
	release  chan struct{}
	trace    *servertrace.Recorder
}

func (gateway *correlationGateway) Close() error { return nil }
func (gateway *correlationGateway) Run(ctx context.Context, active func() error) error {
	select {
	case <-gateway.activate:
		gateway.active <- active()
	case <-ctx.Done():
		return ctx.Err()
	}
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-gateway.release:
		return nil
	}
}

type correlationStarter struct{ created chan *correlationGateway }

func (starter correlationStarter) Start(ctx, ready context.Context, room brokerapi.Room, id string, identity brokerapi.Identity) (brokerapi.Gateway, error) {
	gateway := &correlationGateway{activate: make(chan struct{}), active: make(chan error, 1), release: make(chan struct{}), trace: servertrace.From(ctx)}
	starter.created <- gateway
	return gateway, nil
}
func correlationBroker(test *testing.T, capture bool) (*brokerapi.Broker, <-chan *correlationGateway) {
	test.Helper()
	starter := correlationStarter{make(chan *correlationGateway, 16)}
	broker, err := brokerapi.New(correlationProvider{}, starter, brokerapi.DefaultLimits(), nil)
	if err != nil {
		test.Fatal(err)
	}
	if capture {
		if err = broker.CaptureOwnership(512, time.Now().Add(time.Minute)); err != nil {
			test.Fatal(err)
		}
	}
	test.Cleanup(func() { broker.Close() })
	return broker, starter.created
}
func correlationEvent(test *testing.T, ctx context.Context, broker *brokerapi.Broker, action, tag string) brokerapi.OwnershipEvent {
	test.Helper()
	ticker := time.NewTicker(time.Millisecond)
	defer ticker.Stop()
	for {
		for _, event := range broker.OwnershipSnapshot().Events {
			if event.Action == action && (tag == "" || event.Exchange == tag || action == "release" && event.HolderExchange == tag) {
				return event
			}
		}
		select {
		case <-ticker.C:
		case <-ctx.Done():
			test.Fatalf("missing %s event", action)
		}
	}
}

type correlationResult struct {
	descriptor roombroker.Descriptor
	err        error
}

func correlationExchange(test *testing.T, parent, attempt context.Context, broker *brokerapi.Broker, profile string, clientRaw []byte, complete ...bool) <-chan correlationResult {
	test.Helper()
	client, server := pair()
	serverCtx, stop := context.WithCancel(parent)
	done := make(chan struct{})
	go func() {
		defer close(done)
		_ = serverbootstrap.ServeCarrier(serverCtx, server, func(ctx context.Context, endpoint serverfamily.PacketEndpoint) {
			serverbootstrap.OpenServer(ctx, endpoint, profile, broker, func(string) {})
		})
	}()
	test.Cleanup(func() {
		stop()
		client.Close()
		server.Close()
		cleanup, finish := context.WithTimeout(context.Background(), 3*time.Second)
		defer finish()
		correlationAwait(test, cleanup, done)
	})
	result := make(chan correlationResult, 1)
	go func() {
		descriptor, err := recoverCarrier(attempt, client, clientRaw, func(string) {})
		if len(complete) == 0 || complete[0] {
			startupdiag.Complete(attempt, err)
		}
		result <- correlationResult{descriptor, err}
	}()
	return result
}
func correlationTag(test *testing.T, ctx context.Context) string {
	test.Helper()
	snapshot := startupdiag.Snapshot(ctx)
	if len(snapshot.BootstrapExchanges) != 1 {
		test.Fatalf("exchange count %d", len(snapshot.BootstrapExchanges))
	}
	return snapshot.BootstrapExchanges[0].Tag
}
func TestCorrelationLease(test *testing.T) {
	for _, scenario := range []string{"A_empty", "B_active_deadline", "C_release", "D_other_identity", "E_auth_failure", "F_cancel", "H_disabled", "H_limited", "H_expired"} {
		test.Run(scenario, func(test *testing.T) {
			parent, finish := context.WithTimeout(context.Background(), 12*time.Second)
			defer finish()
			clientRaw, serverRaw, otherRaw := correlationProfiles(test)
			defer clear(clientRaw)
			defer clear(serverRaw)
			defer clear(otherRaw)
			profile := filepath.Join(test.TempDir(), "gateway.json")
			if err := os.WriteFile(profile, serverRaw, 0600); err != nil {
				test.Fatal(err)
			}
			capture := scenario != "H_disabled" && scenario != "H_limited" && scenario != "H_expired"
			broker, created := correlationBroker(test, capture)
			if scenario == "H_limited" {
				if err := broker.CaptureOwnership(1, time.Now().Add(time.Minute)); err != nil {
					test.Fatal(err)
				}
			}
			if scenario == "H_expired" {
				until := time.Now().Add(5 * time.Millisecond)
				if err := broker.CaptureOwnership(8, until); err != nil {
					test.Fatal(err)
				}
				time.Sleep(time.Until(until) + time.Millisecond)
			}
			var holderTag, generation string
			var holder *correlationGateway
			if scenario == "B_active_deadline" || scenario == "C_release" || scenario == "D_other_identity" || scenario == "F_cancel" {
				holderAttempt := startupdiag.Start(parent, 1)
				result := correlationAwait(test, parent, correlationExchange(test, parent, holderAttempt, broker, profile, clientRaw))
				if result.err != nil {
					test.Fatalf("holder bootstrap: %T", result.err)
				}
				holder = correlationAwait(test, parent, created)
				close(holder.activate)
				if err := correlationAwait(test, parent, holder.active); err != nil {
					test.Fatal(err)
				}
				holderTag = correlationTag(test, holderAttempt)
				generation, _ = sessiontrace.Tag(result.descriptor.SetupID)
				event := correlationEvent(test, parent, broker, "grant", holderTag)
				if event.Generation != generation || holder.trace.Snapshot().SessionTag != generation {
					test.Fatal("holder dedicated binding")
				}
			}
			attemptBase, cancel := context.WithTimeout(parent, 2*time.Second)
			defer cancel()
			attempt := startupdiag.Start(attemptBase, 2)
			raw := clientRaw
			if scenario == "D_other_identity" {
				raw = otherRaw
			}
			if scenario == "E_auth_failure" {
				raw, _, _ = correlationProfiles(test)
			}
			resultChannel := correlationExchange(test, parent, attempt, broker, profile, raw)
			if scenario == "B_active_deadline" || scenario == "C_release" || scenario == "F_cancel" {
				wait := correlationEvent(test, parent, broker, "wait", "")
				tag := correlationTag(test, attempt)
				early := startupdiag.Snapshot(attempt)
				if early.Complete || early.Status != "RUNNING" || !early.BootstrapExchanges[0].FamilyAuthenticated {
					test.Fatal("early receipt not present before HELLO")
				}
				if wait.Exchange != tag || wait.HolderExchange != holderTag || wait.Generation != generation || wait.SameIdentity != "true" || wait.State != brokerapi.Active {
					test.Fatal("requester/holder binding mismatch")
				}
				if tag == holderTag || tag == generation {
					test.Fatal("exchange and dedicated tags conflated")
				}
				for _, event := range broker.OwnershipSnapshot().Events {
					if event.Exchange == tag && event.Action == "hello_sent" {
						test.Fatal("HELLO while holder owns slot")
					}
				}
				if scenario == "C_release" {
					close(holder.release)
					released := correlationEvent(test, parent, broker, "release", holderTag)
					if released.Generation != generation {
						test.Fatal("wrong released holder")
					}
				}
				if scenario == "F_cancel" {
					cancel()
				}
			}
			result := correlationAwait(test, parent, resultChannel)
			snapshot := startupdiag.Snapshot(attempt)
			tag := correlationTag(test, attempt)
			if scenario == "B_active_deadline" || scenario == "F_cancel" {
				if result.err == nil || snapshot.Stage != "HELLO_RECEIVE" || snapshot.Observation.BootstrapExchangeTag != tag {
					test.Fatalf("missing first pre-HELLO failure: %+v", snapshot)
				}
				first, _ := json.Marshal(snapshot.Observation)
				startupdiag.Stop(attempt, "CLEANUP")
				startupdiag.Cancel(attempt)
				startupdiag.Complete(attempt, context.Canceled)
				after, _ := json.Marshal(startupdiag.Snapshot(attempt).Observation)
				if string(first) != string(after) {
					test.Fatal("cleanup overwrote first observation")
				}
				correlationEvent(test, parent, broker, "wait_end", tag)
				if scenario == "B_active_deadline" {
					stats := nativeexport.Export(attempt, 2)
					if len(nativeexport.Export(attempt, 3)) != 0 {
						test.Fatal("native stats mixed attempts")
					}
					stats["ownership"] = broker.OwnershipSnapshot()
					stats["holder_dedicated_tag"] = generation
					receipt, _ := json.Marshal(stats)
					if path := os.Getenv("CORRELATION_RECEIPT"); path != "" {
						if err := os.WriteFile(path, receipt, 0600); err != nil {
							test.Fatal(err)
						}
					}
					test.Logf("CORRELATION %s", receipt)
				}
			} else if scenario == "E_auth_failure" {
				if result.err == nil || snapshot.BootstrapExchanges[0].FamilyAuthenticated {
					test.Fatal("nonce implied authentication")
				}
				for _, event := range broker.OwnershipSnapshot().Events {
					if event.Exchange == tag && event.Action == "authenticated" {
						test.Fatal("server authenticated bad credentials")
					}
				}
			} else {
				if result.err != nil {
					test.Fatalf("bootstrap failed %T", result.err)
				}
				if !snapshot.BootstrapExchanges[0].FamilyAuthenticated {
					test.Fatal("missing Family auth fact")
				}
				dedicated, _ := sessiontrace.Tag(result.descriptor.SetupID)
				if dedicated == tag {
					test.Fatal("dedicated tag conflated")
				}
				if capture {
					for _, action := range []string{"authenticated", "grant", "hello_sent", "exchange_end"} {
						correlationEvent(test, parent, broker, action, tag)
					}
					if scenario == "C_release" {
						ended := correlationEvent(test, parent, broker, "wait_end", tag)
						granted := correlationEvent(test, parent, broker, "grant", tag)
						if ended.Generation != generation || granted.Generation == generation || granted.Sequence <= ended.Sequence {
							test.Fatal("old holder attributed to new grant")
						}
					}
					if scenario == "D_other_identity" {
						for _, event := range broker.OwnershipSnapshot().Events {
							if event.Exchange == tag && event.Action == "wait" {
								test.Fatal("unrelated identity linked")
							}
						}
					}
				}
				startupdiag.Stop(attempt, "CLEANUP")
				startupdiag.Cancel(attempt)
				if startupdiag.Snapshot(attempt).Status != "SUCCEEDED" {
					test.Fatal("late stop changed success")
				}
			}
			if scenario == "H_limited" && !broker.OwnershipSnapshot().Limited {
				test.Fatal("missing limited flag")
			}
			if scenario == "H_disabled" || scenario == "H_expired" {
				if len(broker.OwnershipSnapshot().Events) != 0 {
					test.Fatal("unexpected capture")
				}
			}
		})
	}
}

func TestCorrelationParallelRealExchanges(test *testing.T) {
	parent, finish := context.WithTimeout(context.Background(), 8*time.Second)
	defer finish()
	clientRaw, serverRaw, otherRaw := correlationProfiles(test)
	defer clear(clientRaw)
	defer clear(serverRaw)
	defer clear(otherRaw)
	profile := filepath.Join(test.TempDir(), "gateway.json")
	if err := os.WriteFile(profile, serverRaw, 0600); err != nil {
		test.Fatal(err)
	}
	broker, _ := correlationBroker(test, true)
	attempt := startupdiag.Start(parent, 1)
	first := correlationExchange(test, parent, attempt, broker, profile, clientRaw, false)
	second := correlationExchange(test, parent, attempt, broker, profile, otherRaw, false)
	generations := map[string]bool{}
	for _, pending := range []<-chan correlationResult{first, second} {
		result := correlationAwait(test, parent, pending)
		if result.err != nil {
			test.Fatal(result.err)
		}
		tag, _ := sessiontrace.Tag(result.descriptor.SetupID)
		generations[tag] = true
	}
	startupdiag.Complete(attempt, nil)
	snapshot := startupdiag.Snapshot(attempt)
	if len(snapshot.BootstrapExchanges) != 2 || len(generations) != 2 {
		test.Fatal("real exchanges collapsed")
	}
	tags := map[string]bool{}
	for _, entry := range snapshot.BootstrapExchanges {
		if tags[entry.Tag] || !entry.FamilyAuthenticated {
			test.Fatal("exchange conflated")
		}
		tags[entry.Tag] = true
		event := correlationEvent(test, parent, broker, "grant", entry.Tag)
		if !generations[event.Generation] {
			test.Fatal("unrelated dedicated generation")
		}
		delete(generations, event.Generation)
	}
	if len(generations) != 0 {
		test.Fatal("missing generation")
	}
}
