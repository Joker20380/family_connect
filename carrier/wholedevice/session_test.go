package wholedevice

import (
	"context"
	"encoding/binary"
	"io"
	"net"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/reliablestream"
)

type testStream struct{ net.Conn }

type failingPlane struct {
	testPlane
	failure error
}

func (plane *failingPlane) Wait() error { <-plane.done; return plane.failure }

func TestTerminalReasonSurvivesClose(test *testing.T) {
	plane := &failingPlane{testPlane: testPlane{done: make(chan struct{})}, failure: reliablestream.ErrExhausted}
	session := Attach(context.Background(), plane, nil)
	plane.Close()
	select {
	case <-session.ctx.Done():
	case <-time.After(time.Second):
		test.Fatal("failure not propagated")
	}
	if session.Snapshot()["terminal_reason"] != "RELIABLE_EXHAUSTED" {
		test.Fatal("terminal lost")
	}
	session.Close()
	if session.Snapshot()["terminal_reason"] != "RELIABLE_EXHAUSTED" {
		test.Fatal("cleanup overwrote failure")
	}
}

func (stream testStream) CloseWrite() error { return nil }
func (stream testStream) Reset() error      { return stream.Close() }

type testPlane struct {
	done    chan struct{}
	once    sync.Once
	calls   atomic.Int32
	queries atomic.Int32
}

func (plane *testPlane) Wait() error  { <-plane.done; return ErrClosed }
func (plane *testPlane) Close() error { plane.once.Do(func() { close(plane.done) }); return nil }
func (plane *testPlane) Open(ctx context.Context, host string, port uint16) (Stream, error) {
	plane.calls.Add(1)
	client, server := net.Pipe()
	go func() {
		defer server.Close()
		stop := context.AfterFunc(ctx, func() { server.Close() })
		defer stop()
		io.Copy(server, server)
	}()
	return testStream{client}, nil
}
func (plane *testPlane) QueryDNS(ctx context.Context, query []byte) ([]byte, error) {
	plane.queries.Add(1)
	answer := append([]byte{}, query...)
	answer[2] |= 0x80
	return answer, nil
}

func TestConcurrentTCPIsolationAndStop(test *testing.T) {
	plane := &testPlane{done: make(chan struct{})}
	session := Attach(context.Background(), plane, nil)
	defer session.Close()
	var workers sync.WaitGroup
	for index := 0; index < 8; index++ {
		workers.Add(1)
		go func(value byte) {
			defer workers.Done()
			app, engine := net.Pipe()
			defer app.Close()
			go session.Handle(engine, "tcp", "93.184.216.34", 443)
			app.SetDeadline(time.Now().Add(3 * time.Second))
			payload := []byte{value, value, 0, value}
			if _, err := app.Write(payload); err != nil {
				test.Error(err)
				return
			}
			response := make([]byte, 4)
			if _, err := io.ReadFull(app, response); err != nil || string(response) != string(payload) {
				test.Error("cross-flow", err)
			}
		}(byte(index))
	}
	workers.Wait()
	session.Close()
	if plane.calls.Load() != 8 || session.Counters.Active.Load() != 0 {
		test.Fatal("cleanup", plane.calls.Load(), session.Snapshot())
	}
	if session.Allow("tcp", "93.184.216.34", 443) {
		test.Fatal("stale session accepted")
	}
}

func TestFamilyDNSAndNoFallback(test *testing.T) {
	for _, protocol := range []string{"udp", "tcp"} {
		plane := &testPlane{done: make(chan struct{})}
		session := Attach(context.Background(), plane, nil)
		app, engine := net.Pipe()
		go session.Handle(engine, protocol, "10.79.0.1", 53)
		query := make([]byte, 12)
		query[0] = 42
		if protocol == "tcp" {
			query = append([]byte{0, 12}, query...)
		}
		app.SetDeadline(time.Now().Add(time.Second))
		if _, err := app.Write(query); err != nil {
			test.Fatal(err)
		}
		answer := make([]byte, len(query))
		if _, err := io.ReadFull(app, answer); err != nil {
			test.Fatal(err)
		}
		if protocol == "tcp" {
			if binary.BigEndian.Uint16(answer[:2]) != 12 {
				test.Fatal("framing")
			}
			answer = answer[2:]
		}
		if answer[2]&0x80 == 0 || plane.queries.Load() != 1 || plane.calls.Load() != 0 {
			test.Fatal("DNS routing")
		}
		app.Close()
		session.Close()
	}
}

func TestUnsupportedTrafficAndSessionFailure(test *testing.T) {
	plane := &testPlane{done: make(chan struct{})}
	session := Attach(context.Background(), plane, nil)
	defer session.Close()
	for _, input := range []struct {
		protocol, host string
		port           uint16
	}{{"udp", "1.1.1.1", 443}, {"tcp", "2606:4700::1111", 443}, {"udp", "::1", 53}, {"icmp", "1.1.1.1", 0}} {
		if session.Allow(input.protocol, input.host, input.port) {
			test.Fatal("unsupported traffic allowed")
		}
	}
	app, engine := net.Pipe()
	defer app.Close()
	go session.Handle(engine, "tcp", "1.1.1.1", 443)
	app.SetDeadline(time.Now().Add(time.Second))
	app.Write([]byte{1})
	buffer := make([]byte, 1)
	io.ReadFull(app, buffer)
	plane.Close()
	if _, err := app.Read(buffer); err == nil {
		test.Fatal("session failure did not close app flow")
	}
	session.Close()
	if session.Counters.Active.Load() != 0 {
		test.Fatal("zombie flow")
	}
}

func TestFlowLimitAndParentCancellation(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	plane := &testPlane{done: make(chan struct{})}
	session := Attach(ctx, plane, nil)
	defer session.Close()
	var applications []net.Conn
	for index := 0; index < 32; index++ {
		app, engine := net.Pipe()
		applications = append(applications, app)
		go session.Handle(engine, "tcp", "1.1.1.1", 443)
		app.SetDeadline(time.Now().Add(3 * time.Second))
		if _, err := app.Write([]byte{42}); err != nil {
			test.Fatal(err)
		}
		var answer [1]byte
		if _, err := io.ReadFull(app, answer[:]); err != nil {
			test.Fatal(err)
		}
	}
	app, engine := net.Pipe()
	go session.Handle(engine, "tcp", "1.1.1.1", 443)
	app.SetDeadline(time.Now().Add(time.Second))
	if _, err := app.Write([]byte{42}); err == nil {
		test.Fatal("flow limit")
	}
	app.Close()
	if plane.calls.Load() != 32 {
		test.Fatal("extra outbound")
	}
	cancel()
	session.Close()
	for _, app := range applications {
		app.Close()
	}
	if session.Counters.Active.Load() != 0 || session.Counters.Peak.Load() != 32 {
		test.Fatal("unbounded cleanup", session.Snapshot())
	}
	if _, err := Open(context.Background(), "unused", "unused", nil, func(string) {}); err == nil {
		test.Fatal("unprotected bootstrap")
	}
}
