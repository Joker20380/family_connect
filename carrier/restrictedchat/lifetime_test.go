package restrictedchat

import (
	"context"
	"net/http"
	"net/http/httptest"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/restrictedowner"
)

func TestOperationReleaseVersusGenerationLifetime(test *testing.T) {
	for _, retain := range []bool{false, true} {
		name := "operation-only-reproduces-cleanup-race"
		if retain {
			name = "generation-retains-transport"
		}
		test.Run(name, func(test *testing.T) {
			server := httptest.NewTLSServer(http.HandlerFunc(func(response http.ResponseWriter, request *http.Request) {
				response.Write([]byte(`{"ok":true}`))
			}))
			defer server.Close()
			var owner Owner
			cleanupEntered, cleanupContinue, disposed := make(chan struct{}), make(chan struct{}), make(chan struct{})
			unblock := sync.OnceFunc(func() { close(cleanupContinue) })
			defer owner.Close()
			defer unblock()
			_, session, _ := fixture(test, true, tlsDial(server))
			var opens atomic.Int32
			acquire := func() (*Client, error) {
				client, err := owner.acquire(time.Now().Add(time.Minute), [32]byte{1}, func(context.Context) (restrictedowner.Session, func(), error) {
					opens.Add(1)
					return session, func() { close(cleanupEntered); <-cleanupContinue }, nil
				}, func() {})
				if client != nil {
					trustServer(client, server)
				}
				return client, err
			}
			var generation *Client
			if retain {
				var err error
				generation, err = acquire()
				if err != nil {
					test.Fatal(err)
				}
				defer generation.Close()
			}
			first, err := acquire()
			if err != nil {
				test.Fatal(err)
			}
			if reply, err := first.Request(context.Background(), "/friends/chat/challenge", []byte(`{}`), time.Second); err != nil || reply.Status != 200 {
				test.Fatal("first request", err)
			}
			first.Close()
			if !retain {
				select {
				case <-cleanupEntered:
				case <-time.After(3 * time.Second):
					test.Fatal("last operation did not enter cleanup")
				}
				if next, err := acquire(); next != nil || err != ErrUnavailable {
					test.Fatal("old host must fail during held cleanup", err)
				}
				if first.Route() != "UNAVAILABLE" || !session.Failed() || opens.Load() != 1 {
					test.Fatal("wrong before state/open count")
				}
			} else {
				next, err := acquire()
				if err != nil {
					test.Fatal("next operation lost transport", err)
				}
				defer next.Close()
				if reply, err := next.Request(context.Background(), "/friends/chat/register", []byte(`{}`), time.Second); err != nil || reply.Status != 200 {
					test.Fatal("register", err)
				}
				next.Close()
				if generation.Route() != "SERVICE_ONLY" || session.Failed() || opens.Load() != 1 {
					test.Fatal("operation release cancelled generation or reopened transport")
				}
				generation.Close()
				select {
				case <-cleanupEntered:
				case <-time.After(3 * time.Second):
					test.Fatal("generation release did not enter cleanup")
				}
			}
			reservation, err := owner.ReserveVPN(context.Background())
			if err != nil {
				test.Fatal(err)
			}
			defer reservation.Release()
			if err := reservation.Publish(session, [32]byte{1}); err == nil {
				test.Fatal("published before confirmed cleanup")
			}
			go func() { reservation.Wait(context.Background()); close(disposed) }()
			select {
			case <-disposed:
				test.Fatal("drain acknowledged held cleanup")
			default:
			}
			unblock()
			select {
			case <-disposed:
			case <-time.After(3 * time.Second):
				test.Fatal("drain did not finish")
			}
		})
	}
}
