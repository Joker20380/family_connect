package telemost

import (
	"context"
	"errors"
	"net/http"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/reliablestream"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

type gatedResetEndpoint struct {
	*headLossEndpoint
	reset   chan struct{}
	release chan struct{}
	once    sync.Once
}

func (endpoint *gatedResetEndpoint) SendContext(ctx context.Context, raw []byte) error {
	if len(raw) >= reliablestream.HeaderSize && string(raw[:4]) == "FRS1" && raw[4] == 4 {
		endpoint.once.Do(func() { close(endpoint.reset) })
		select {
		case <-endpoint.release:
		case <-ctx.Done():
			return ctx.Err()
		}
	}
	return endpoint.headLossEndpoint.SendContext(ctx, raw)
}

func TestOwnedCarrierKeepsResetPathAfterCancellation(test *testing.T) {
	for _, mode := range []string{"cancel", "deadline", "explicit-close"} {
		test.Run(mode, func(test *testing.T) {
			parent, cancel := context.WithCancel(context.Background())
			if mode == "deadline" {
				cancel()
				parent, cancel = context.WithTimeout(context.Background(), 500*time.Millisecond)
			}
			defer cancel()
			created := 0
			left, right := headLossPair(test, context.Background(), 1000, "none", func(ctx context.Context, config Config) (*Session, error) {
				created++
				if created == 1 {
					return NewOwned(sessiontrace.With(parent, sessiontrace.From(ctx)), config)
				}
				return New(ctx, config)
			})
			defer left.Close()
			defer right.Close()
			point := &gatedResetEndpoint{headLossEndpoint: left, reset: make(chan struct{}), release: make(chan struct{})}
			release := sync.OnceFunc(func() { close(point.release) })
			defer release()
			sender, err := reliablestream.New(parent, point, reliablestream.DefaultConfig())
			if err != nil {
				test.Fatal(err)
			}
			receiver, err := reliablestream.New(context.Background(), right, reliablestream.DefaultConfig())
			if err != nil {
				test.Fatal(err)
			}
			defer receiver.Close()
			defer func() { release(); sender.Close() }()
			bounded, stop := context.WithTimeout(context.Background(), 2*time.Second)
			defer stop()
			if err := sender.SendContext(bounded, []byte("establish before cancellation")); err != nil {
				test.Fatal(err)
			}
			if _, err := receiver.Recv(bounded); err != nil {
				test.Fatal(err)
			}
			switch mode {
			case "cancel":
				cancel()
			case "explicit-close":
				go sender.Close()
			}
			select {
			case <-point.reset:
			case <-bounded.Done():
				test.Fatal("upper layer did not start bounded RESET delivery")
			}
			if left.ctx.Err() != nil || left.closed.Load() {
				test.Fatal("carrier closed before the upper layer could deliver RESET")
			}
			release()
			if _, err := receiver.Recv(bounded); !errors.Is(err, reliablestream.ErrReset) {
				test.Fatalf("peer retained the previous session: %v", err)
			}
			sender.Close()
			select {
			case <-left.cleanupDone:
			case <-bounded.Done():
				test.Fatal("upper layer left its carrier running")
			}
			if sender.Stats().BufferedBytes != 0 || receiver.Stats().BufferedBytes != 0 {
				test.Fatal("closed session retained reliable data")
			}
		})
	}
}

func TestOwnedCarrierRejectsCancelledCreation(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	carrier, err := NewOwned(ctx, Config{RoomURL: "local-test"})
	if carrier != nil || !errors.Is(err, context.Canceled) {
		test.Fatal("cancelled owner allocated a carrier")
	}
}

func TestOwnedCarrierFailedConnectCloses(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	carrier, err := NewOwned(ctx, Config{RoomURL: "local-test", HTTPClient: &http.Client{Transport: transportFunc(func(request *http.Request) (*http.Response, error) {
		cancel()
		<-request.Context().Done()
		return nil, request.Context().Err()
	})}})
	if err != nil {
		test.Fatal(err)
	}
	defer carrier.Close()
	if err := carrier.Connect(ctx); err == nil {
		test.Fatal("cancelled owner connected")
	}
	select {
	case <-carrier.cleanupDone:
	case <-time.After(time.Second):
		test.Fatal("failed startup retained its owned carrier")
	}
}
