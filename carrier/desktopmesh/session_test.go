package desktopmesh

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/restrictedchat"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

func TestDesktopProfilesExcludeExperimentalModes(test *testing.T) {
	for _, name := range []string{"", "auto", "P2", "Q1", "FIXED4M", "p1"} {
		if _, err := Profile(name); err == nil {
			test.Fatal("accepted profile", name)
		}
	}
	for _, name := range []string{"P0", "P1"} {
		profile, err := Profile(name)
		if err != nil || profile.Name() != name {
			test.Fatal(name, err)
		}
		if name == "P1" && (profile.Reliable().SendWindow != 32 || profile.Reliable().ReceiveWindow != 32) {
			test.Fatal("P1 reliable limits differ from accepted106")
		}
	}
}

func TestInvalidMaterialDoesNotTouchUnderlyingNetwork(test *testing.T) {
	config := Config{Readiness: []byte("{}"), Identity: make([]byte, 64), Anchor: make([]byte, 32), Profile: "P1", Budget: time.Second, Attempt: 1, Resolver: "1.1.1.1:53"}
	protected := false
	connection, startup, err := Dial(context.Background(), config, func(int) bool { protected = true; return true }, func(string) {})
	if connection != nil || err == nil || protected || startup == nil {
		test.Fatal("invalid credentials must fail before socket creation")
	}
	if strings.Contains(fmt.Sprintf("%+v %#v %s", config, config, config), string(config.Identity)) {
		test.Fatal("configuration formatting exposed private identity")
	}
	if _, err := json.Marshal(config); err == nil {
		test.Fatal("configuration is not a diagnostic DTO")
	}
}

func TestCancelledDialDoesNotBecomeTimeout(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	config := Config{Readiness: []byte("{}"), Identity: make([]byte, 64), Anchor: make([]byte, 32), Profile: "P0", Budget: time.Second, Attempt: 1}
	connection, _, err := Dial(ctx, config, func(int) bool { test.Fatal("cancelled dial opened socket"); return false }, func(string) {})
	if connection != nil || err != context.Canceled {
		test.Fatal("cancel changed meaning", err)
	}
}

func TestInvalidChatMaterialDoesNotDisplaceExistingOwnership(test *testing.T) {
	var owner restrictedchat.Owner
	existing, err := owner.ReserveVPN(context.Background())
	if err != nil {
		test.Fatal(err)
	}
	defer existing.Release()
	config := Config{Readiness: []byte("{}"), Identity: make([]byte, 64), Anchor: make([]byte, 32), Profile: "P1", Budget: time.Second, Attempt: 1}
	connection, _, err := DialWithOwner(context.Background(), config, func(int) bool { test.Fatal("unauthorized socket"); return false }, func(string) {}, &owner)
	if connection != nil || err == nil {
		test.Fatal("invalid material dialed")
	}
	if replacement, err := owner.ReserveVPN(context.Background()); err == nil || replacement != nil {
		test.Fatal("invalid request removed existing ownership")
	}
}

func TestConnectionCloseReleasesOnlyItsReservation(test *testing.T) {
	connection := testConnection()
	var owner restrictedchat.Owner
	reservation, err := owner.ReserveVPN(connection.ctx)
	if err != nil {
		test.Fatal(err)
	}
	connection.ownership = reservation
	if err := reservation.Publish(connection.session, [32]byte{1}); err != nil {
		test.Fatal(err)
	}
	connection.Close()
	replacement, err := owner.ReserveVPN(context.Background())
	if err != nil {
		test.Fatal("old reservation prevented reconnect", err)
	}
	defer replacement.Release()
	connection.Close()
	if unexpected, err := owner.ReserveVPN(context.Background()); err == nil || unexpected != nil {
		test.Fatal("stale close removed new reservation")
	}
}

type testPlane struct {
	done chan struct{}
	once sync.Once
}

func (plane *testPlane) Open(context.Context, string, uint16) (wholedevice.Stream, error) {
	return nil, ErrClosed
}
func (plane *testPlane) QueryDNS(context.Context, []byte) ([]byte, error) { return nil, ErrClosed }
func (plane *testPlane) Close() error                                     { plane.once.Do(func() { close(plane.done) }); return nil }
func (plane *testPlane) Wait() error                                      { <-plane.done; return io.EOF }

type testPacket struct {
	closed atomic.Int32
	failed atomic.Bool
}

func (packet *testPacket) Failed() bool { return packet.failed.Load() }

func (packet *testPacket) Close() error { packet.closed.Add(1); return nil }

func testConnection() *Connection {
	ctx, cancel := context.WithCancelCause(context.Background())
	return &Connection{ctx: ctx, cancel: cancel, session: wholedevice.Attach(ctx, &testPlane{done: make(chan struct{})}, nil), cleanupDone: make(chan struct{}), selected: "P1"}
}

func TestTransportReadyIsNotConnectedWithoutPlatformPath(test *testing.T) {
	connection := testConnection()
	defer connection.Close()
	if connection.State() != "TRANSPORT_READY" || connection.Snapshot()["tun_ready"] != false {
		test.Fatal("native transport alone claimed connected")
	}
	if err := connection.Activate(func(context.Context, *wholedevice.Session) (io.Closer, error) { return nil, nil }); err == nil {
		test.Fatal("missing platform path accepted")
	}
	packet := &testPacket{}
	if err := connection.Activate(func(context.Context, *wholedevice.Session) (io.Closer, error) { return packet, nil }); err != nil || connection.State() != "CONNECTED" {
		test.Fatal("platform path failed", err)
	}
	if err := connection.Activate(func(context.Context, *wholedevice.Session) (io.Closer, error) {
		test.Fatal("double attach")
		return nil, nil
	}); err == nil {
		test.Fatal("second platform path accepted")
	}
	connection.Close()
	connection.Close()
	if connection.State() != "DISCONNECTED" || packet.closed.Load() != 1 {
		test.Fatal("cleanup not idempotent")
	}
}

func TestCancelDuringPlatformAttachClosesOnlyItsOwnPath(test *testing.T) {
	old := testConnection()
	current := testConnection()
	defer current.Close()
	packet := &testPacket{}
	entered := make(chan struct{})
	done := make(chan error, 1)
	go func() {
		done <- old.Activate(func(ctx context.Context, _ *wholedevice.Session) (io.Closer, error) {
			close(entered)
			<-ctx.Done()
			return packet, nil
		})
	}()
	<-entered
	old.Close()
	if err := <-done; err == nil || packet.closed.Load() != 1 || current.State() != "TRANSPORT_READY" {
		test.Fatal("cancel/old callback affected replacement session", err)
	}
}

func TestPacketFailureCannotRemainConnected(test *testing.T) {
	connection := testConnection()
	defer connection.Close()
	packet := &testPacket{}
	if err := connection.Activate(func(context.Context, *wholedevice.Session) (io.Closer, error) { return packet, nil }); err != nil {
		test.Fatal(err)
	}
	packet.failed.Store(true)
	if connection.State() != "FAILED" || connection.Snapshot()["tun_ready"] != false {
		test.Fatal("dead packet path reported connected")
	}
}
