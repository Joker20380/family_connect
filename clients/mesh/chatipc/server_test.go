package chatipc

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/restrictedchat"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
	"github.com/Joker20380/family_connect/desktopbridge/worker"
)

type fakeClient struct {
	closed   atomic.Bool
	peers    chan net.Conn
	requests chan struct{}
	block    bool
	denial   error
}

type testLease = client

type unusedPlatform struct{}

func (unusedPlatform) Protect(net.Interface, int) bool { return false }
func (unusedPlatform) Attach(context.Context, *wholedevice.Session) (io.Closer, error) {
	panic("chat IPC must not attach a TUN")
}
func (unusedPlatform) Probe(context.Context) bool { return false }

func (client *fakeClient) Route() string { return "EXISTING_EXIT" }
func (client *fakeClient) Close() error  { client.closed.Store(true); return nil }
func (client *fakeClient) OpenMailbox(ctx context.Context, duration time.Duration) (net.Conn, error) {
	local, remote := net.Pipe()
	client.peers <- remote
	return local, nil
}
func (client *fakeClient) Request(ctx context.Context, path string, data []byte, duration time.Duration) (restrictedchat.Reply, error) {
	if client.requests != nil {
		client.requests <- struct{}{}
	}
	if client.block {
		<-ctx.Done()
		return restrictedchat.Reply{}, ctx.Err()
	}
	return restrictedchat.Reply{Status: 200, Body: bytes.Clone(data)}, client.denial
}

type harness struct {
	connection net.Conn
	done       chan error
	identifier uint64
	test       *testing.T
}

func launch(test *testing.T, acquire func(*Acquisition) (client, error)) *harness {
	return launchPinned(test, func(material *Acquisition, generation client) (client, error) { return acquire(material) })
}

func launchPinned(test *testing.T, acquire func(*Acquisition, client) (client, error)) *harness {
	test.Helper()
	local, remote := net.Pipe()
	remote.SetDeadline(time.Now().Add(5 * time.Second))
	current := &harness{connection: remote, done: make(chan error, 1), test: test}
	go func() { current.done <- serve(context.Background(), local, acquire) }()
	test.Cleanup(func() {
		remote.Close()
		select {
		case <-current.done:
		case <-time.After(2 * time.Second):
			test.Error("chat lane did not close")
		}
	})
	return current
}

func (current *harness) send(request Request) uint64 {
	current.test.Helper()
	current.identifier++
	request.Schema, request.ID = Schema, current.identifier
	raw, err := json.Marshal(request)
	if err != nil {
		current.test.Fatal(err)
	}
	var header [4]byte
	binary.BigEndian.PutUint32(header[:], uint32(len(raw)))
	if _, err = current.connection.Write(append(header[:], raw...)); err != nil {
		current.test.Fatal(err)
	}
	return request.ID
}

func (current *harness) receive() Reply {
	current.test.Helper()
	var reply Reply
	if err := worker.ReadControlMessage(current.connection, &reply, MaxFrame); err != nil {
		current.test.Fatal(err)
	}
	return reply
}

func (current *harness) call(request Request) Reply {
	current.test.Helper()
	identifier := current.send(request)
	reply := current.receive()
	if reply.ID != identifier {
		current.test.Fatalf("unexpected reply %d for %d", reply.ID, identifier)
	}
	return reply
}

func TestNativeAcquisitionDenialKeepsIPCAlive(test *testing.T) {
	interfaces, err := net.Interfaces()
	if err != nil {
		test.Fatal(err)
	}
	index := 0
	for _, candidate := range interfaces {
		if candidate.Flags&net.FlagUp != 0 && candidate.Flags&net.FlagLoopback == 0 {
			index = candidate.Index
			break
		}
	}
	if index == 0 {
		test.Skip("requires an up non-loopback interface")
	}
	var owner restrictedchat.Owner
	defer owner.Close()
	local, remote := net.Pipe()
	remote.SetDeadline(time.Now().Add(5 * time.Second))
	current := &harness{connection: remote, done: make(chan error, 1), test: test}
	go func() { current.done <- Serve(context.Background(), local, &owner, unusedPlatform{}) }()
	defer func() {
		remote.Close()
		select {
		case <-current.done:
		case <-time.After(2 * time.Second):
			test.Error("native denial leaked IPC server")
		}
	}()
	for range 2 {
		reply := current.call(Request{Action: "acquire", BudgetMS: 1000, Acquire: &Acquisition{
			Readiness: json.RawMessage(`{}`), Identity: make([]byte, 64), Anchor: make([]byte, 32),
			Resolver: "1.1.1.1:53", UnderlyingIndex: index}})
		if reply.OK || reply.Error != "DENIED" {
			test.Fatal("invalid native material did not fail closed", reply.Error)
		}
	}
}

func acquisition() Request {
	return Request{Action: "acquire", BudgetMS: 30000, Acquire: &Acquisition{Readiness: json.RawMessage(`{}`), Identity: make([]byte, 64), Anchor: make([]byte, 32), Resolver: "1.1.1.1:53", UnderlyingIndex: 1}}
}

func TestPinnedLeaseAdmission(test *testing.T) {
	generation := &fakeClient{peers: make(chan net.Conn, 1)}
	operation := &fakeClient{peers: make(chan net.Conn, 1)}
	var calls atomic.Int32
	current := launchPinned(test, func(material *Acquisition, parent client) (client, error) {
		if calls.Add(1) == 1 {
			if parent != nil {
				test.Error("initial generation unexpectedly pinned")
			}
			return generation, nil
		}
		if parent != generation {
			test.Error("operation lost its generation identity")
		}
		return operation, nil
	})
	lease := current.call(acquisition()).Lease
	pinned := acquisition()
	pinned.Generation = lease
	reply := current.call(pinned)
	if !reply.OK || reply.Lease == lease {
		test.Fatal("operation needs a distinct lease")
	}
	current.call(Request{Action: "release", Lease: reply.Lease})
	current.call(Request{Action: "release", Lease: lease})
	if reply = current.call(pinned); reply.OK || calls.Load() != 2 {
		test.Fatal("released pin reached acquire")
	}
	if reply = current.call(Request{Action: "route", Lease: lease}); reply.OK {
		test.Fatal("released generation survived")
	}
	if (Request{Schema: 1, ID: 1, Action: "route", Lease: lease, Generation: lease}).valid() {
		test.Fatal("pin accepted outside acquisition")
	}
}

func TestProtocolShapeAndPrivacy(test *testing.T) {
	valid := []Request{acquisition(), {Action: "route", Lease: 1}, {Action: "release", Lease: 1}, {Action: "open", Lease: 1, BudgetMS: 30000},
		{Action: "request", Lease: 1, BudgetMS: 1, Path: "/friends/chat/challenge", Data: make([]byte, 8192)},
		{Action: "read", Stream: 1, BudgetMS: 1, Size: MaxData}, {Action: "write", Stream: 1, BudgetMS: 1, Data: []byte("private-content")},
		{Action: "finish", Stream: 1, BudgetMS: 1}, {Action: "close", Stream: 1}, {Action: "cancel", Target: 1}}
	for _, request := range valid {
		request.Schema, request.ID = Schema, 2
		if !request.valid() {
			test.Fatalf("valid shape rejected: %s", request.Action)
		}
		request.Target = 99
		if request.valid() {
			test.Fatal("unexpected field accepted")
		}
	}
	for _, path := range []string{"https://example.org", "/friends/chat/register?other=1", "/admin", "/friends/chat/challenge/"} {
		if (Request{Schema: 1, ID: 1, Action: "request", Lease: 1, BudgetMS: 1, Path: path}).valid() {
			test.Fatal("unrestricted path")
		}
	}
	for _, raw := range []string{`{"schema":1,"id":1,"id":2,"action":"route","lease":1}`, `{"schema":1,"id":1,"action":"route","lease":1,"command":"exec"}`, `{"schema":1,"id":1,"action":"route","lease":NaN}`} {
		var header [4]byte
		binary.BigEndian.PutUint32(header[:], uint32(len(raw)))
		if _, err := readRequest(bytes.NewReader(append(header[:], raw...))); err == nil {
			test.Fatal("bad frame accepted")
		}
	}
	if fmt.Sprint(Request{Data: []byte("private-content")}) != "[chat IPC request redacted]" || fmt.Sprint(Reply{Data: []byte("private-content")}) != "[chat IPC reply redacted]" {
		test.Fatal("payload formatting leak")
	}
}

func TestDuplexAndStreamLifetime(test *testing.T) {
	client := &fakeClient{peers: make(chan net.Conn, 4)}
	current := launch(test, func(*Acquisition) (testLease, error) { return client, nil })
	lease := current.call(acquisition()).Lease
	opened := current.call(Request{Action: "open", Lease: lease, BudgetMS: 30000})
	if !opened.OK || opened.Stream == 0 {
		test.Fatal("open failed")
	}
	peer := <-client.peers
	defer peer.Close()
	for iteration := 0; iteration < 3; iteration++ {
		data := bytes.Repeat([]byte{byte(iteration + 1)}, MaxData)
		readID := current.send(Request{Action: "read", Stream: opened.Stream, BudgetMS: 1000, Size: len(data)})
		writeID := current.send(Request{Action: "write", Stream: opened.Stream, BudgetMS: 1000, Data: data})
		finished := make(chan error, 1)
		go func() {
			buffer := make([]byte, len(data))
			_, err := io.ReadFull(peer, buffer)
			if err == nil && !bytes.Equal(buffer, data) {
				err = errors.New("mailbox byte mismatch")
			}
			if err == nil {
				_, err = peer.Write(buffer)
			}
			finished <- err
		}()
		for count := 0; count < 2; count++ {
			reply := current.receive()
			if !reply.OK || reply.Count != len(data) || (reply.ID != readID && reply.ID != writeID) {
				test.Fatalf("bad duplex reply: %d %s", reply.ID, reply.Error)
			}
			if reply.ID == readID && !bytes.Equal(reply.Data, data) {
				test.Fatal("read data changed")
			}
		}
		if err := <-finished; err != nil {
			test.Fatal(err)
		}
	}
	current.call(Request{Action: "close", Stream: opened.Stream})
	if client.closed.Load() {
		test.Fatal("closing a stream released the lease")
	}
	current.call(Request{Action: "release", Lease: lease})
	if !client.closed.Load() {
		test.Fatal("lease not released")
	}
}

func TestCancelLaneAndJobBound(test *testing.T) {
	client := &fakeClient{requests: make(chan struct{}, MaxJobs), block: true}
	current := launch(test, func(*Acquisition) (testLease, error) { return client, nil })
	lease := current.call(acquisition()).Lease
	var first uint64
	for index := 0; index < MaxJobs; index++ {
		identifier := current.send(Request{Action: "request", Lease: lease, BudgetMS: 30000, Path: "/friends/chat/register"})
		if first == 0 {
			first = identifier
		}
		<-client.requests
	}
	if reply := current.call(Request{Action: "request", Lease: lease, BudgetMS: 30000, Path: "/friends/chat/register"}); reply.OK {
		test.Fatal("unbounded jobs")
	}
	if reply := current.call(Request{Action: "route", Lease: lease}); !reply.OK || reply.Route != "EXISTING_EXIT" {
		test.Fatal("control starved by API jobs")
	}
	cancelID := current.send(Request{Action: "cancel", Target: first})
	seen := make(map[uint64]Reply)
	for index := 0; index < 2; index++ {
		reply := current.receive()
		seen[reply.ID] = reply
	}
	if !seen[cancelID].OK || seen[first].Error != "CANCELLED" {
		test.Fatal("cancel was blocked or mislabeled")
	}
	current.connection.Close()
}

func TestLimitsDeadlineAndDuplicateDirection(test *testing.T) {
	clients := make(chan *fakeClient, 8)
	current := launch(test, func(*Acquisition) (client, error) {
		created := &fakeClient{peers: make(chan net.Conn, 4)}
		clients <- created
		return created, nil
	})
	lease := current.call(acquisition()).Lease
	first := <-clients
	for index := 1; index < restrictedchat.MaxLeases; index++ {
		if !current.call(acquisition()).OK {
			test.Fatal("lease capacity")
		}
	}
	if current.call(acquisition()).OK {
		test.Fatal("unbounded leases")
	}
	var streamID uint64
	for index := 0; index < MaxStreams; index++ {
		reply := current.call(Request{Action: "open", Lease: lease, BudgetMS: 30000})
		if !reply.OK {
			test.Fatal("stream capacity")
		}
		streamID = reply.Stream
		peer := <-first.peers
		defer peer.Close()
	}
	if current.call(Request{Action: "open", Lease: lease, BudgetMS: 30000}).OK {
		test.Fatal("unbounded streams")
	}
	readID := current.send(Request{Action: "read", Stream: streamID, BudgetMS: 100, Size: 1})
	if current.call(Request{Action: "read", Stream: streamID, BudgetMS: 30000, Size: 1}).OK {
		test.Fatal("concurrent same-direction reader")
	}
	reply := current.receive()
	if reply.ID != readID || reply.Error != "DEADLINE" {
		test.Fatalf("deadline mislabeled: %d %s", reply.ID, reply.Error)
	}
	if !current.call(Request{Action: "route", Lease: lease}).OK {
		test.Fatal("timeout killed owner")
	}
}

func TestAuthorizationAndLaneFailure(test *testing.T) {
	for _, denial := range []error{restrictedchat.ErrDenied, restrictedchat.ErrConflict} {
		test.Run(classify(denial), func(test *testing.T) {
			client := &fakeClient{denial: denial}
			current := launch(test, func(*Acquisition) (testLease, error) { return client, nil })
			lease := current.call(acquisition()).Lease
			reply := current.call(Request{Action: "request", Lease: lease, BudgetMS: 30000, Path: "/friends/chat/register"})
			if reply.OK || reply.Error != classify(denial) {
				test.Fatal("terminal error lost")
			}
		})
	}
	owner := &restrictedchat.Owner{}
	reservation, err := owner.ReserveVPN(context.Background())
	if err != nil {
		test.Fatal(err)
	}
	defer reservation.Release()
	local, remote := net.Pipe()
	finished := make(chan struct{})
	go func() {
		defer close(finished)
		Serve(context.Background(), local, owner, unusedPlatform{})
	}()
	remote.Write([]byte{0, 0, 0, 0})
	remote.Close()
	<-finished
	if _, err := owner.ReserveVPN(context.Background()); err == nil {
		test.Fatal("chat failure released VPN")
	}
}

func TestAcquireCancellationDisposesLateResult(test *testing.T) {
	started, finish := make(chan struct{}), make(chan struct{})
	client := &fakeClient{}
	var once sync.Once
	current := launch(test, func(*Acquisition) (testLease, error) {
		once.Do(func() { close(started) })
		<-finish
		return client, nil
	})
	identifier := current.send(acquisition())
	<-started
	current.call(Request{Action: "cancel", Target: identifier})
	close(finish)
	if reply := current.receive(); reply.Error != "CANCELLED" || reply.Lease != 0 {
		test.Fatal("cancelled lease published")
	}
	if !client.closed.Load() {
		test.Fatal("late acquired lease leaked")
	}
}
