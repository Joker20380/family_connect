package wholedevice

import (
	"bytes"
	"context"
	"errors"
	"sync/atomic"
	"testing"
	"time"
)

type datagramPlane struct {
	*testPlane
	query func(context.Context, []byte) ([]byte, error)
}

func (plane *datagramPlane) QueryDNS(ctx context.Context, query []byte) ([]byte, error) {
	plane.queries.Add(1)
	return plane.query(ctx, query)
}

func waitDNSIdle(test *testing.T, session *Session) {
	test.Helper()
	deadline := time.Now().Add(time.Second)
	for session.Counters.Active.Load() != 0 && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	if session.Counters.Active.Load() != 0 {
		test.Fatal("DNS worker retained")
	}
}

func TestDNSDatagramOwnsPayloadAndReleasesSlot(test *testing.T) {
	entered := make(chan struct{})
	release := make(chan struct{})
	answer := make(chan []byte, 1)
	plane := &datagramPlane{testPlane: &testPlane{done: make(chan struct{})}, query: func(ctx context.Context, query []byte) ([]byte, error) {
		close(entered)
		select {
		case <-release:
			return query, nil
		case <-ctx.Done():
			return nil, ctx.Err()
		}
	}}
	session := Attach(context.Background(), plane, nil)
	defer session.Close()
	query := bytes.Repeat([]byte{42}, 12)
	session.HandleDNSDatagram(query, "10.79.0.1", 53, func(response []byte) error {
		answer <- bytes.Clone(response)
		return errors.New("packet output failed")
	})
	<-entered
	clear(query)
	close(release)
	select {
	case response := <-answer:
		if !bytes.Equal(response, bytes.Repeat([]byte{42}, 12)) {
			test.Fatal("packet buffer reused while DNS pending")
		}
	case <-time.After(time.Second):
		test.Fatal("no DNS response")
	}
	waitDNSIdle(test, session)
	if len(session.dnsSlots) != 0 || session.Counters.DNS.Load() != 1 || plane.calls.Load() != 0 {
		test.Fatal("DNS lifecycle or fallback")
	}
}

func TestDNSDatagramConcurrencyAndCancellationBound(test *testing.T) {
	entered := make(chan struct{}, 16)
	var responses atomic.Int32
	plane := &datagramPlane{testPlane: &testPlane{done: make(chan struct{})}, query: func(ctx context.Context, query []byte) ([]byte, error) {
		entered <- struct{}{}
		<-ctx.Done()
		return query, nil
	}}
	session := Attach(context.Background(), plane, nil)
	defer session.Close()
	respond := func([]byte) error { responses.Add(1); return nil }
	for index := 0; index < 16; index++ {
		session.HandleDNSDatagram(make([]byte, 12), "10.79.0.1", 53, respond)
	}
	for index := 0; index < 16; index++ {
		select {
		case <-entered:
		case <-time.After(time.Second):
			test.Fatal("DNS did not start")
		}
	}
	session.HandleDNSDatagram(make([]byte, 12), "10.79.0.1", 53, respond)
	if plane.queries.Load() != 16 || session.Counters.Peak.Load() != 16 || session.Counters.LimitDenied.Load() != 1 {
		test.Fatal("DNS concurrency exceeded", session.Snapshot())
	}
	session.Close()
	session.HandleDNSDatagram(make([]byte, 12), "10.79.0.1", 53, respond)
	if responses.Load() != 0 || plane.queries.Load() != 16 || session.Counters.Active.Load() != 0 || len(session.dnsSlots) != 0 || plane.calls.Load() != 0 {
		test.Fatal("stale response, leaked worker or fallback")
	}
}

func TestDNSDatagramFailClosedInputsAndResponses(test *testing.T) {
	plane := &testPlane{done: make(chan struct{})}
	session := Attach(context.Background(), plane, nil)
	defer session.Close()
	var responses atomic.Int32
	respond := func([]byte) error { responses.Add(1); return nil }
	for _, size := range []int{0, 11, 4097} {
		session.HandleDNSDatagram(make([]byte, size), "10.79.0.1", 53, respond)
	}
	session.HandleDNSDatagram(make([]byte, 12), "::1", 53, respond)
	session.HandleDNSDatagram(make([]byte, 12), "example.com", 53, respond)
	session.HandleDNSDatagram(make([]byte, 12), "1.1.1.1", 443, respond)
	session.HandleDNSDatagram(make([]byte, 12), "10.79.0.1", 53, nil)
	if plane.queries.Load() != 0 || responses.Load() != 0 || session.Counters.Active.Load() != 0 || plane.calls.Load() != 0 {
		test.Fatal("invalid datagram accepted")
	}
	for _, failure := range []struct {
		name string
		size int
		err  error
	}{{"short", 11, nil}, {"oversized", 4097, nil}, {"query_error", 12, errors.New("DNS failed")}} {
		test.Run(failure.name, func(test *testing.T) {
			failedPlane := &datagramPlane{testPlane: &testPlane{done: make(chan struct{})}, query: func(context.Context, []byte) ([]byte, error) {
				return make([]byte, failure.size), failure.err
			}}
			failed := Attach(context.Background(), failedPlane, nil)
			defer failed.Close()
			failed.HandleDNSDatagram(make([]byte, 12), "10.79.0.1", 53, respond)
			waitDNSIdle(test, failed)
			if failedPlane.queries.Load() != 1 || responses.Load() != 0 || failedPlane.calls.Load() != 0 {
				test.Fatal("DNS error bypassed or response escaped")
			}
		})
	}
}
