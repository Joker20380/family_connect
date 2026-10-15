package bootstrap

import (
	"context"
	"os"
	"path/filepath"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/restrictedowner"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

type handoffSession struct {
	closed atomic.Bool
	close  func()
}

func (session *handoffSession) Failed() bool { return session.closed.Load() }
func (session *handoffSession) Close() {
	if session.closed.CompareAndSwap(false, true) {
		session.close()
	}
}

func TestHandoffRealBroker(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
	defer cancel()
	client, server, raw := reproFamily(test, ctx)
	profile := filepath.Join(test.TempDir(), "synthetic-gateway.json")
	if err := os.WriteFile(profile, raw, 0600); err != nil {
		test.Fatal(err)
	}
	authorize := roombroker.SessionAuthorizer(profile, server.ConnectionState())
	broker, created := reproBroker(test)
	var coordinator restrictedowner.Coordinator
	var old *reproGateway
	var holder string
	var openCount atomic.Int32
	localCleanup := make(chan struct{})
	chat, err := coordinator.AcquireChat(time.Now().Add(time.Minute), [32]byte{1}, func(context.Context) (restrictedowner.Session, func(), error) {
		openCount.Add(1)
		holder, old = reproActive(test, ctx, broker, created, authorize)
		return &handoffSession{close: func() {
			if err := broker.Cancel(ctx, holder, authorize); err != nil {
				panic(err)
			}
		}}, func() { close(localCleanup) }, nil
	}, func() {})
	if err != nil {
		test.Fatal(err)
	}
	defer chat.Release()
	if _, err := chat.Session(ctx); err != nil {
		test.Fatal(err)
	}
	prior := len(broker.OwnershipSnapshot().Events)
	vpn, err := coordinator.ReserveVPN(ctx)
	if err != nil {
		test.Fatal(err)
	}
	defer vpn.Release()
	if err := vpn.Wait(ctx); err != nil {
		test.Fatal(err)
	}
	select {
	case <-localCleanup:
	default:
		test.Fatal("local cleanup not joined")
	}
	reproAwait(test, ctx, old.closing)
	incoming := &reproEndpoint{PacketEndpoint: client, result: make(chan map[string]any, 1)}
	outgoing := &reproEndpoint{PacketEndpoint: server, result: make(chan map[string]any, 1)}
	serverDone, clientDone := make(chan error, 1), make(chan error, 1)
	go func() { serverDone <- Exchange(ctx, outgoing, broker, authorize) }()
	go func() { _, err := requestTransport(ctx, incoming); clientDone <- err }()
	reproOwnership(test, ctx, broker, prior, func(event roombroker.OwnershipEvent) bool { return event.Action == "wait" })
	if outgoing.helloSent.Load() != 0 {
		test.Fatal("server guard bypassed")
	}
	old.permitCleanup()
	if err := reproAwait(test, ctx, clientDone); err != nil {
		test.Fatal(err)
	}
	if err := reproAwait(test, ctx, serverDone); err != nil {
		test.Fatal(err)
	}
	newGateway := reproAwait(test, ctx, created)
	newGateway.permitCleanup()
	var release, grant int
	for _, event := range broker.OwnershipSnapshot().Events {
		if event.Sequence <= prior {
			continue
		}
		if event.Action == "release" && release == 0 {
			release = event.Sequence
		}
		if event.Action == "grant" && grant == 0 {
			grant = event.Sequence
		}
	}
	if release == 0 || grant <= release || outgoing.helloSent.Load() != 1 || incoming.helloReceived.Load() != 1 {
		test.Fatalf("release/grant/HELLO order: %d %d", release, grant)
	}
	active := &handoffSession{close: func() {}}
	if err := vpn.Publish(active, [32]byte{1}); err != nil {
		test.Fatal(err)
	}
	borrowed, err := coordinator.AcquireChat(time.Now().Add(time.Minute), [32]byte{1}, func(context.Context) (restrictedowner.Session, func(), error) {
		panic("borrow attempted independent create")
	}, func() {})
	if err != nil || borrowed.State() != 2 {
		test.Fatal("borrowing failed")
	}
	borrowed.Release()
	borrowed.Release()
	if active.Failed() || openCount.Load() != 1 {
		test.Fatal("borrow affected transport")
	}
	vpn.Release()
	active.Close()
	reproLog(test, "handoff", map[string]any{"local_cleanup_joined": true, "server_cleanup_is_separate": true, "old_release_sequence": release, "new_grant_sequence": grant, "hello_received": incoming.helloReceived.Load(), "borrowed": true, "independent_chat_opens": openCount.Load()})
}
