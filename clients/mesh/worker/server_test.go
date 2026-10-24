package worker

import (
	"context"
	"errors"
	"io"
	"net"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/desktopmesh"
	"github.com/Joker20380/family_connect/carrier/startupdiag"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

type fakePacket struct{ count atomic.Int32 }

func (packet *fakePacket) Close() error { packet.count.Add(1); return nil }

type fakePlatform struct{ packet *fakePacket }

func (fakePlatform) Protect(net.Interface, int) bool { return false }
func (fakePlatform) Probe(context.Context) bool      { return true }
func (platform fakePlatform) Attach(context.Context, *wholedevice.Session) (io.Closer, error) {
	return platform.packet, nil
}

type fakeConnection struct {
	ctx    context.Context
	mu     sync.Mutex
	packet io.Closer
	state  string
	once   sync.Once
}

func (connection *fakeConnection) Activate(attach func(context.Context, *wholedevice.Session) (io.Closer, error)) error {
	packet, err := attach(connection.ctx, nil)
	connection.mu.Lock()
	defer connection.mu.Unlock()
	if err != nil || connection.ctx.Err() != nil {
		if packet != nil {
			packet.Close()
		}
		return desktopmesh.ErrClosed
	}
	connection.packet, connection.state = packet, "CONNECTED"
	return nil
}
func (connection *fakeConnection) State() string {
	connection.mu.Lock()
	defer connection.mu.Unlock()
	return connection.state
}
func (connection *fakeConnection) Snapshot() map[string]any {
	return map[string]any{"state": connection.State()}
}
func (*fakeConnection) HealthSample(time.Duration) *desktopmesh.HealthSample { return nil }
func (connection *fakeConnection) Close() error {
	connection.once.Do(func() {
		connection.mu.Lock()
		defer connection.mu.Unlock()
		connection.state = "DISCONNECTED"
		if connection.packet != nil {
			connection.packet.Close()
		}
	})
	return nil
}

func testServer() (*Server, *fakePacket) {
	packet := &fakePacket{}
	server := New(context.Background(), fakePlatform{packet})
	server.underlying = func(int) (*net.Interface, error) {
		return &net.Interface{Index: 2, Name: "test-underlay", Flags: net.FlagUp}, nil
	}
	server.dial = func(ctx context.Context, config desktopmesh.Config, protect func(int) bool, event func(string)) (connection, *startupdiag.Result, error) {
		for index := 0; index < 100; index++ {
			event("bootstrap_ready")
		}
		return &fakeConnection{ctx: ctx, state: "TRANSPORT_READY"}, nil, nil
	}
	return server, packet
}

func startRequest() Request {
	return Request{Schema: Schema, ID: 1, Action: "start", Start: &Start{Attempt: 1, BudgetMS: 1000, Profile: "P1", Resolver: "1.1.1.1:53", UnderlyingIndex: 2, Readiness: []byte("{}"), Identity: make([]byte, 64), Anchor: make([]byte, 32)}}
}

func waitState(test *testing.T, server *Server, state string, id *uint64) Reply {
	test.Helper()
	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		*id++
		reply := server.Handle(Request{Schema: Schema, ID: *id, Action: "status"})
		if reply.State == state {
			return reply
		}
		time.Sleep(time.Millisecond)
	}
	test.Fatal("state timeout", state)
	return Reply{}
}

func TestConnectedRequiresRoutingAcknowledgement(test *testing.T) {
	server, packet := testServer()
	defer server.Close()
	id := uint64(1)
	if reply := server.Handle(startRequest()); !reply.OK || reply.State != "CONNECTING" {
		test.Fatal(reply)
	}
	reply := waitState(test, server, "PACKET_READY", &id)
	if reply.Interface != InterfaceName || reply.MTU != MTU || reply.Snapshot["events_dropped"] != uint64(68) {
		test.Fatal(reply)
	}
	if len(reply.Snapshot["events"].([]string)) != 32 {
		test.Fatal("event bound")
	}
	id++
	if reply := server.Handle(Request{Schema: Schema, ID: id, Action: "routed"}); !reply.OK {
		test.Fatal(reply)
	}
	waitState(test, server, "CONNECTED", &id)
	id++
	if reply := server.Handle(Request{Schema: Schema, ID: id, Action: "routed"}); reply.OK {
		test.Fatal("duplicate route acknowledgement")
	}
	id++
	server.Handle(Request{Schema: Schema, ID: id, Action: "stop"})
	server.Close()
	waitState(test, server, "DISCONNECTED", &id)
	if packet.count.Load() != 1 {
		test.Fatal("packet cleanup count", packet.count.Load())
	}
}

func TestCancelBeforeRoutingDoesNotBecomeConnected(test *testing.T) {
	server, packet := testServer()
	defer server.Close()
	server.Handle(startRequest())
	id := uint64(1)
	waitState(test, server, "PACKET_READY", &id)
	id++
	server.Handle(Request{Schema: Schema, ID: id, Action: "stop"})
	server.Close()
	id++
	if reply := server.Handle(Request{Schema: Schema, ID: id, Action: "routed"}); reply.OK || reply.State != "DISCONNECTED" {
		test.Fatal(reply)
	}
	if packet.count.Load() != 1 {
		test.Fatal("cancel did not close packet")
	}
}

func TestStartRejectsWeakOrExperimentalConfiguration(test *testing.T) {
	for _, mutate := range []func(*Start){func(start *Start) { start.Profile = "P2" }, func(start *Start) { start.BudgetMS = 200001 }, func(start *Start) { start.Identity = make([]byte, 96) }, func(start *Start) { start.Resolver = "example.com:53" }, func(start *Start) { start.UnderlyingIndex = 0 }} {
		server, _ := testServer()
		request := startRequest()
		mutate(request.Start)
		if reply := server.Handle(request); reply.OK {
			test.Fatal("invalid startup accepted")
		}
		server.Close()
	}
	server, _ := testServer()
	defer server.Close()
	server.underlying = func(int) (*net.Interface, error) { return nil, errors.New("private description") }
	if reply := server.Handle(startRequest()); reply.OK || reply.Error != "UNDERLAY_UNAVAILABLE" {
		test.Fatal(reply)
	}
}

func TestReplayAndSecondStartCannotReplaceSession(test *testing.T) {
	server, _ := testServer()
	defer server.Close()
	server.Handle(startRequest())
	if reply := server.Handle(Request{Schema: Schema, ID: 1, Action: "stop"}); reply.OK {
		test.Fatal("replay accepted")
	}
	request := startRequest()
	request.ID = 2
	if reply := server.Handle(request); reply.OK {
		test.Fatal("multiple concurrent sessions")
	}
}
