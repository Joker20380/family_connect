package bootstrap

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/startupdiag"
)

func reproAwait[Value any](test *testing.T, ctx context.Context, channel <-chan Value) Value {
	test.Helper()
	select {
	case value := <-channel:
		return value
	case <-ctx.Done():
		test.Fatalf("synchronization deadline: %T", ctx.Err())
	}
	var empty Value
	return empty
}

func reproLog(test *testing.T, kind string, value any) {
	test.Helper()
	raw, err := json.Marshal(value)
	if err != nil {
		test.Fatal(err)
	}
	test.Logf("REPRO %s %s", kind, raw)
}

func reproError(ctx context.Context, err error) map[string]any {
	var timed interface{ Timeout() bool }
	hasTimeout := errors.As(err, &timed)
	return map[string]any{"go_type": fmt.Sprintf("%T", err), "context_deadline": errors.Is(err, context.DeadlineExceeded), "context_canceled": errors.Is(err, context.Canceled), "os_deadline": errors.Is(err, os.ErrDeadlineExceeded), "eof": errors.Is(err, io.EOF), "unexpected_eof": errors.Is(err, io.ErrUnexpectedEOF), "closed_pipe": errors.Is(err, io.ErrClosedPipe), "timeout_implemented": hasTimeout, "timeout": hasTimeout && timed.Timeout(), "ctx_err_type": fmt.Sprintf("%T", ctx.Err()), "ctx_deadline": errors.Is(ctx.Err(), context.DeadlineExceeded), "ctx_canceled": errors.Is(ctx.Err(), context.Canceled), "context_cause_type": fmt.Sprintf("%T", context.Cause(ctx)), "cause_deadline": errors.Is(context.Cause(ctx), context.DeadlineExceeded), "cause_canceled": errors.Is(context.Cause(ctx), context.Canceled)}
}

type reproEndpoint struct {
	familysession.PacketEndpoint
	helloSent     atomic.Int32
	helloReceived atomic.Int32
	first         atomic.Bool
	result        chan map[string]any
}

func (endpoint *reproEndpoint) SendContext(ctx context.Context, raw []byte) error {
	err := endpoint.PacketEndpoint.SendContext(ctx, raw)
	var input message
	if json.Unmarshal(raw, &input) == nil && input.Type == "HELLO" && err == nil {
		endpoint.helloSent.Add(1)
	}
	return err
}

func (endpoint *reproEndpoint) Recv(ctx context.Context) ([]byte, error) {
	raw, err := endpoint.PacketEndpoint.Recv(ctx)
	if endpoint.first.CompareAndSwap(false, true) {
		observation := reproError(ctx, err)
		var input message
		if json.Unmarshal(raw, &input) == nil && input.Type == "HELLO" {
			endpoint.helloReceived.Add(1)
			observation["hello"] = true
		}
		endpoint.result <- observation
	}
	return raw, err
}

type reproGateway struct {
	activate chan struct{}
	active   chan error
	closing  chan struct{}
	release  chan struct{}
	once     sync.Once
}

func (gateway *reproGateway) Run(ctx context.Context, active func() error) error {
	select {
	case <-gateway.activate:
		err := active()
		gateway.active <- err
		if err != nil {
			return err
		}
	case <-ctx.Done():
		return ctx.Err()
	}
	<-ctx.Done()
	return ctx.Err()
}

func (gateway *reproGateway) Close() error   { close(gateway.closing); <-gateway.release; return nil }
func (gateway *reproGateway) permitCleanup() { gateway.once.Do(func() { close(gateway.release) }) }

func reproBroker(test *testing.T) (*roombroker.Broker, <-chan *reproGateway) {
	test.Helper()
	created := make(chan *reproGateway, 8)
	var mutex sync.Mutex
	var gateways []*reproGateway
	broker, err := roombroker.New(providerFunc(func(context.Context) (roombroker.Room, error) {
		return roombroker.Room{ID: "synthetic-local-room", JoinURL: "https://telemost.yandex.ru/j/characterization-only"}, nil
	}), starterFunc(func(context.Context, context.Context, roombroker.Room, string, roombroker.Identity) (roombroker.Gateway, error) {
		gateway := &reproGateway{make(chan struct{}), make(chan error, 1), make(chan struct{}), make(chan struct{}), sync.Once{}}
		mutex.Lock()
		gateways = append(gateways, gateway)
		mutex.Unlock()
		created <- gateway
		return gateway, nil
	}), roombroker.DefaultLimits(), nil)
	if err != nil {
		test.Fatal(err)
	}
	if err := broker.CaptureOwnership(512, time.Now().Add(time.Minute)); err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() {
		mutex.Lock()
		for _, gateway := range gateways {
			gateway.permitCleanup()
		}
		mutex.Unlock()
		broker.Close()
		reproLog(test, "cleanup", map[string]any{"broker_close_returned": true, "gateways": len(gateways)})
	})
	return broker, created
}

func reproOwnership(test *testing.T, ctx context.Context, broker *roombroker.Broker, after int, predicate func(roombroker.OwnershipEvent) bool) roombroker.OwnershipEvent {
	test.Helper()
	ticker := time.NewTicker(time.Millisecond)
	defer ticker.Stop()
	for {
		for _, event := range broker.OwnershipSnapshot().Events {
			if event.Sequence > after && predicate(event) {
				return event
			}
		}
		select {
		case <-ticker.C:
		case <-ctx.Done():
			test.Fatal("expected ownership event absent")
		}
	}
}

func reproActive(test *testing.T, ctx context.Context, broker *roombroker.Broker, created <-chan *reproGateway, authorize roombroker.Authorize) (string, *reproGateway) {
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
	gateway := reproAwait(test, ctx, created)
	close(gateway.activate)
	if err := reproAwait(test, ctx, gateway.active); err != nil {
		test.Fatal(err)
	}
	reproOwnership(test, ctx, broker, 0, func(event roombroker.OwnershipEvent) bool { return event.State == roombroker.Active })
	return identifier, gateway
}

func TestReproAdmission(test *testing.T) {
	for _, scenario := range []string{"A_empty", "B_active_same_deadline", "C_cleanup_before_deadline", "D_other_identity"} {
		test.Run(scenario, func(test *testing.T) {
			parent, finish := context.WithTimeout(context.Background(), 8*time.Second)
			defer finish()
			client, server, raw := reproFamily(test, parent)
			profile := filepath.Join(test.TempDir(), "synthetic-gateway.json")
			if err := os.WriteFile(profile, raw, 0600); err != nil {
				test.Fatal(err)
			}
			authorize := roombroker.SessionAuthorizer(profile, server.ConnectionState())
			broker, created := reproBroker(test)
			holderAuthorize := authorize
			if scenario == "D_other_identity" {
				identity, err := authorize(parent)
				if err != nil {
					test.Fatal(err)
				}
				identity.Device = strings.Repeat("c", 32)
				identity.PublicKey[0] ^= 1
				holderAuthorize = func(context.Context) (roombroker.Identity, error) { return identity, nil }
			}
			var holder string
			var old *reproGateway
			if scenario != "A_empty" {
				holder, old = reproActive(test, parent, broker, created, holderAuthorize)
			}
			prior := len(broker.OwnershipSnapshot().Events)
			attempt := parent
			cancel := func() {}
			if scenario == "B_active_same_deadline" {
				attempt, cancel = context.WithTimeout(parent, 200*time.Millisecond)
			}
			defer cancel()
			attempt = startupdiag.Start(attempt, 1)
			incoming := &reproEndpoint{PacketEndpoint: client, result: make(chan map[string]any, 1)}
			outgoing := &reproEndpoint{PacketEndpoint: server, result: make(chan map[string]any, 1)}
			serverDone, clientDone := make(chan error, 1), make(chan error, 1)
			go func() { serverDone <- Exchange(attempt, outgoing, broker, authorize) }()
			go func() {
				_, err := requestTransport(attempt, incoming)
				startupdiag.Complete(attempt, err)
				clientDone <- err
			}()
			if scenario == "B_active_same_deadline" || scenario == "C_cleanup_before_deadline" {
				reproOwnership(test, parent, broker, prior, func(event roombroker.OwnershipEvent) bool {
					return event.Action == "wait" && event.State == roombroker.Active
				})
				if outgoing.helloSent.Load() != 0 {
					test.Fatal("HELLO sent while same ACTIVE holder owns slot")
				}
				if scenario == "C_cleanup_before_deadline" {
					if err := broker.Cancel(parent, holder, holderAuthorize); err != nil {
						test.Fatal(err)
					}
					reproAwait(test, parent, old.closing)
					if outgoing.helloSent.Load() != 0 {
						test.Fatal("HELLO before gateway cleanup completed")
					}
					for _, event := range broker.OwnershipSnapshot().Events {
						if event.Sequence > prior && event.Action == "release" {
							test.Fatal("slot released before cleanup permission")
						}
					}
					old.permitCleanup()
				}
			}
			clientErr := reproAwait(test, parent, clientDone)
			serverErr := reproAwait(test, parent, serverDone)
			if scenario == "B_active_same_deadline" {
				if clientErr == nil || !errors.Is(serverErr, context.DeadlineExceeded) || outgoing.helloSent.Load() != 0 {
					test.Fatalf("unexpected B outcome: client=%T server=%T", clientErr, serverErr)
				}
				if _, err := broker.Challenge(parent, holderAuthorize); err != roombroker.Code("device_busy") {
					test.Fatal("old holder displaced")
				}
				select {
				case <-old.closing:
					test.Fatal("old holder was closed by waiter")
				default:
				}
				if snapshot := startupdiag.Snapshot(attempt); snapshot.Stage != "HELLO_RECEIVE" || !snapshot.Complete {
					test.Fatal("B did not fail at HELLO_RECEIVE")
				}
			} else {
				if clientErr != nil || serverErr != nil || outgoing.helloSent.Load() != 1 || incoming.helloReceived.Load() != 1 {
					test.Fatalf("successful exchange failed: client=%T server=%T", clientErr, serverErr)
				}
				gateway := reproAwait(test, parent, created)
				close(gateway.activate)
				if err := reproAwait(test, parent, gateway.active); err != nil {
					test.Fatal(err)
				}
			}
			released, granted, hello := 0, 0, 0
			for _, event := range broker.OwnershipSnapshot().Events {
				if event.Sequence > prior {
					if event.Action == "release" {
						released = event.Sequence
					}
					if event.Action == "grant" {
						granted = event.Sequence
					}
					if event.Action == "hello_sent" {
						hello = event.Sequence
					}
					if (scenario == "A_empty" || scenario == "D_other_identity") && event.Action == "wait" {
						test.Fatal("unrelated identity or empty broker caused wait")
					}
					if scenario == "B_active_same_deadline" && event.Action == "wait_end" && (!event.Present || event.State != roombroker.Active) {
						test.Fatal("waiter changed ACTIVE holder")
					}
					reproLog(test, "ownership", map[string]any{"sequence": event.Sequence, "action": event.Action, "state": event.State, "present": event.Present, "reason": event.Reason, "same_identity": event.SameIdentity})
				}
			}
			if scenario == "C_cleanup_before_deadline" && !(released > 0 && released < granted && granted < hello) {
				test.Fatal("cleanup -> grant -> HELLO ordering not established")
			}
			reproLog(test, "admission", map[string]any{"scenario": scenario, "hello_sent": outgoing.helloSent.Load(), "hello_received": incoming.helloReceived.Load(), "server_error": reproError(attempt, serverErr), "recv": reproAwait(test, parent, incoming.result), "startup": startupdiag.Snapshot(attempt)})
		})
	}
}

func reproReadBlocked(test *testing.T, ctx context.Context) {
	test.Helper()
	ticker := time.NewTicker(time.Millisecond)
	defer ticker.Stop()
	buffer := make([]byte, 1<<20)
	for {
		count := runtime.Stack(buffer, true)
		for _, stack := range strings.Split(string(buffer[:count]), "\n\n") {
			if strings.Contains(stack, "familysession.(*Session).Recv(") && strings.Contains(stack, "net.(*pipe).read(") {
				return
			}
		}
		select {
		case <-ticker.C:
		case <-ctx.Done():
			test.Fatal("Family TLS read not observed blocked")
		}
	}
}

func TestReproActualClassification(test *testing.T) {
	for _, scenario := range []string{"deadline", "cancel", "peer_close", "invalid_hello", "successful_hello"} {
		repeats := 1
		if scenario == "deadline" || scenario == "cancel" || scenario == "peer_close" {
			repeats = 12
		}
		for iteration := 0; iteration < repeats; iteration++ {
			test.Run(fmt.Sprintf("%s_%02d", scenario, iteration), func(test *testing.T) {
				parent, finish := context.WithTimeout(context.Background(), 5*time.Second)
				defer finish()
				attempt, cancel := context.WithCancel(parent)
				if scenario == "deadline" {
					cancel()
					attempt, cancel = context.WithTimeout(parent, 200*time.Millisecond)
				}
				defer cancel()
				attempt = startupdiag.Start(attempt, 1)
				client, server, _ := reproFamily(test, attempt)
				endpoint := &reproEndpoint{PacketEndpoint: client, result: make(chan map[string]any, 1)}
				done := make(chan error, 1)
				go func() { _, err := requestTransport(attempt, endpoint); startupdiag.Complete(attempt, err); done <- err }()
				reproReadBlocked(test, parent)
				var exchangeDone chan error
				switch scenario {
				case "cancel":
					cancel()
				case "peer_close":
					server.Close()
				case "invalid_hello":
					if err := server.SendContext(parent, []byte(`{"type":"NOT_HELLO"}`)); err != nil {
						test.Fatal(err)
					}
				case "successful_hello":
					broker, _ := reproBroker(test)
					exchangeDone = make(chan error, 1)
					go func() { exchangeDone <- Exchange(attempt, server, broker, allow) }()
				}
				err := reproAwait(test, parent, done)
				actual := reproAwait(test, parent, endpoint.result)
				snapshot := startupdiag.Snapshot(attempt)
				if scenario == "successful_hello" {
					if err != nil || reproAwait(test, parent, exchangeDone) != nil || snapshot.Status != "SUCCEEDED" {
						test.Fatal("success control failed")
					}
				} else if err == nil || snapshot.Stage != "HELLO_RECEIVE" || !snapshot.Complete {
					test.Fatalf("wrong failure boundary: %T", err)
				}
				if scenario == "invalid_hello" && snapshot.Cause != "PROTOCOL_REJECTED" {
					test.Fatal("invalid HELLO classification changed")
				}
				if actual["os_deadline"] == true || actual["closed_pipe"] == true {
					if snapshot.Cause != "UNKNOWN" {
						test.Fatal("expected characterized missing cause mapping")
					}
				}
				reproLog(test, "classification", map[string]any{"scenario": scenario, "iteration": iteration, "family_read_blocked_observed": true, "actual_recv": actual, "returned_error": reproError(attempt, err), "startup": snapshot})
			})
		}
	}
}
