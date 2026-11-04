package familysession

import (
	"context"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/reliablestream"
)

type idleLossEndpoint struct {
	*endpoint
	blocked *atomic.Bool
}

func (point idleLossEndpoint) SendContext(ctx context.Context, data []byte) error {
	if point.blocked.Load() {
		return nil
	}
	return point.endpoint.SendContext(ctx, data)
}

func TestIdleMediaLossReleasesFamilySession(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	clientProfile, serverProfile := profiles(test)
	clientEndpoint, serverEndpoint := pair()
	var blocked atomic.Bool
	config := reliablestream.DefaultConfig()
	config.RTO, config.MaxAge = 20*time.Millisecond, 500*time.Millisecond
	type opened struct {
		session *Session
		err     error
	}
	ready := make(chan opened, 1)
	go func() {
		session, err := OpenReliable(ctx, idleLossEndpoint{serverEndpoint, &blocked}, encoded(serverProfile), true, config)
		ready <- opened{session, err}
	}()
	client, clientErr := OpenReliable(ctx, idleLossEndpoint{clientEndpoint, &blocked}, encoded(clientProfile), false, config)
	server := <-ready
	if client != nil {
		defer client.Close()
	}
	if server.session != nil {
		defer server.session.Close()
	}
	if clientErr != nil || server.err != nil {
		test.Fatal("Family TLS admission failed", clientErr, server.err)
	}
	for client.ReliabilityStats().SendDepth != 0 || server.session.ReliabilityStats().SendDepth != 0 {
		select {
		case <-time.After(time.Millisecond):
		case <-ctx.Done():
			test.Fatal("handshake did not drain")
		}
	}
	blocked.Store(true)
	for _, session := range []*Session{client, server.session} {
		select {
		case <-session.Done():
		case <-ctx.Done():
			test.Fatal("idle media loss did not notify the Family owner")
		}
		if ctx.Err() != nil || session.ReliabilityStats().Terminal != "recovery_exhausted" {
			test.Fatal("cleanup depended on parent deadline")
		}
		session.Close()
		if session.ReliabilityStats().BufferedBytes != 0 {
			test.Fatal("Family cleanup retained ciphertext")
		}
	}
}
