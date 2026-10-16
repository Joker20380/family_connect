package tcpforward

import (
	"context"
	"io"
	"sync"
	"sync/atomic"
	"testing"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/reliablestream"
)

func BrowserAdmissionPair(test *testing.T, ctx context.Context, port int, leases *atomic.Int32) (*Mux, *Mux) {
	test.Helper()
	clientJSON, serverJSON := testCredentials(test)
	forward, reverse, closed := make(chan []byte, 64), make(chan []byte, 64), make(chan struct{})
	once := &sync.Once{}
	left := &lossyEndpoint{incoming: reverse, outgoing: forward, closed: closed, once: once, seen: make(map[uint64]int)}
	right := &lossyEndpoint{incoming: forward, outgoing: reverse, closed: closed, once: once, seen: make(map[uint64]int)}
	type result struct {
		session *familysession.Session
		err     error
	}
	ready := make(chan result, 1)
	go func() {
		session, err := familysession.OpenReliable(ctx, right, serverJSON, true, reliablestream.DefaultConfig())
		ready <- result{session, err}
	}()
	clientSession, err := familysession.OpenReliable(ctx, left, clientJSON, false, reliablestream.DefaultConfig())
	if err != nil {
		test.Fatal(err)
	}
	serverResult := <-ready
	if serverResult.err != nil {
		test.Fatal(serverResult.err)
	}
	test.Cleanup(func() { clientSession.Close(); serverResult.session.Close() })
	server, err := NewMux(ctx, serverResult.session, true, MuxConfig{
		MaxStreams: 32, Policy: Policy{TestOnlyLoopbackPort: port},
		LeaseRenewal: func(ctx context.Context, stream *MuxStream) {
			leases.Add(1)
			stream.Write([]byte{42})
			io.Copy(io.Discard, stream)
		},
	})
	if err != nil {
		test.Fatal(err)
	}
	server.mu.Lock()
	server.exchange = func(ctx context.Context, query []byte) ([]byte, error) {
		message, err := validDNS(query, false)
		if err != nil {
			return nil, err
		}
		message.Header.Response = true
		return message.Pack()
	}
	server.mu.Unlock()
	client, err := NewMux(ctx, clientSession, false, MuxConfig{MaxStreams: 32})
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() { client.Close(); server.Close() })
	return client, server
}
