package desktopmesh

import (
	"context"
	"crypto/sha256"
	"errors"
	"fmt"
	"io"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/restrictedchat"
	"github.com/Joker20380/family_connect/carrier/restrictedowner"
	"github.com/Joker20380/family_connect/carrier/sessiondiag"
	"github.com/Joker20380/family_connect/carrier/sessionprofile"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/Joker20380/family_connect/carrier/startupdiag"
	"github.com/Joker20380/family_connect/carrier/underlay"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

var ErrConfiguration = errors.New("desktop mesh configuration rejected")
var ErrClosed = errors.New("desktop mesh session closed")

type Config struct {
	Readiness []byte
	Identity  []byte
	Anchor    []byte
	Resolver  string
	Profile   string
	Budget    time.Duration
	Attempt   int64
}

func (Config) String() string               { return "[desktop mesh configuration redacted]" }
func (Config) GoString() string             { return "[desktop mesh configuration redacted]" }
func (Config) MarshalJSON() ([]byte, error) { return nil, ErrConfiguration }
func (config Config) Format(output fmt.State, verb rune) {
	fmt.Fprint(output, "[desktop mesh configuration redacted]")
}

func Profile(value string) (sessionprofile.Profile, error) {
	switch value {
	case "P0":
		return sessionprofile.P0, nil
	case "P1":
		return sessionprofile.P1, nil
	default:
		return sessionprofile.P0, ErrConfiguration
	}
}

func (config Config) validate() (sessionprofile.Profile, error) {
	profile, err := Profile(config.Profile)
	if err != nil || len(config.Readiness) == 0 || len(config.Readiness) > wholedevice.MaxReadiness ||
		len(config.Identity) != 64 || len(config.Anchor) != 32 ||
		config.Budget <= 0 || config.Budget > 200*time.Second || config.Attempt <= 0 {
		return sessionprofile.P0, ErrConfiguration
	}
	return profile, nil
}

type Connection struct {
	mu          sync.Mutex
	ctx         context.Context
	cancel      context.CancelCauseFunc
	network     *underlay.Network
	session     *wholedevice.Session
	packet      io.Closer
	closed      bool
	selected    string
	cleanupDone chan struct{}
	ownership   *restrictedowner.VPN
}

func Dial(parent context.Context, config Config, protect func(int) bool, event func(string)) (*Connection, *startupdiag.Result, error) {
	return DialWithOwner(parent, config, protect, event, &restrictedchat.Owner{})
}

func DialWithOwner(parent context.Context, config Config, protect func(int) bool, event func(string), owner *restrictedchat.Owner) (*Connection, *startupdiag.Result, error) {
	profile, err := config.validate()
	if err != nil || parent == nil || owner == nil || protect == nil || event == nil {
		return nil, nil, ErrConfiguration
	}
	ctx, cancel := context.WithCancelCause(parent)
	ctx = sessiontrace.Watch(startupdiag.Start(sessionprofile.With(ctx, profile), config.Attempt))
	connection := &Connection{ctx: ctx, cancel: cancel, selected: config.Profile, cleanupDone: make(chan struct{})}
	timer := time.AfterFunc(config.Budget, func() {
		startupdiag.Stop(ctx, "STARTUP_BUDGET")
		cancel(context.DeadlineExceeded)
	})
	defer timer.Stop()
	fail := func(stage string, failure error) (*Connection, *startupdiag.Result, error) {
		if cause := context.Cause(ctx); cause != nil {
			failure = cause
		}
		startupdiag.Failure(ctx, stage, failure)
		startupdiag.Complete(ctx, failure)
		record := startupdiag.Snapshot(ctx)
		connection.Close()
		return nil, record, failure
	}
	if err := ctx.Err(); err != nil {
		return fail("STARTUP", err)
	}
	material, directory, err := wholedevice.DeliveryMaterial(config.Readiness, config.Identity, config.Anchor, time.Now())
	if err != nil {
		return fail("PROFILE", err)
	}
	defer clear(material)
	connection.ownership, err = owner.ReserveVPN(ctx)
	if err != nil {
		return fail("STARTUP", err)
	}
	if err = connection.ownership.Wait(ctx); err != nil {
		return fail("STARTUP", err)
	}
	connection.network, err = underlay.New(ctx, config.Resolver, protect)
	if err != nil {
		return fail("STARTUP", err)
	}
	connection.session, err = wholedevice.OpenProvisioned(ctx, material, directory, connection.network, event)
	if err != nil {
		return fail("STARTUP", err)
	}
	if !timer.Stop() || ctx.Err() != nil {
		return fail("STARTUP", context.DeadlineExceeded)
	}
	if err = connection.ownership.Publish(connection.session, sha256.Sum256(material)); err != nil {
		return fail("STARTUP", err)
	}
	startupdiag.Complete(ctx, nil)
	return connection, startupdiag.Snapshot(ctx), nil
}

func (connection *Connection) Activate(attach func(context.Context, *wholedevice.Session) (io.Closer, error)) error {
	connection.mu.Lock()
	defer connection.mu.Unlock()
	if connection.closed || connection.ctx.Err() != nil || connection.session == nil || connection.session.Failed() || connection.packet != nil || attach == nil {
		return ErrClosed
	}
	packet, err := attach(connection.ctx, connection.session)
	if err != nil || packet == nil || connection.ctx.Err() != nil || connection.session.Failed() {
		if packet != nil {
			packet.Close()
		}
		if err != nil {
			return err
		}
		return ErrClosed
	}
	connection.packet = packet
	return nil
}

func (connection *Connection) State() string {
	connection.mu.Lock()
	defer connection.mu.Unlock()
	if connection.closed {
		return "DISCONNECTED"
	}
	if connection.ctx.Err() != nil || connection.session == nil || connection.session.Failed() {
		return "FAILED"
	}
	if packet, ok := connection.packet.(interface{ Failed() bool }); ok && packet.Failed() {
		return "FAILED"
	}
	if connection.packet != nil {
		return "CONNECTED"
	}
	return "TRANSPORT_READY"
}

func (connection *Connection) Snapshot() map[string]any {
	connection.mu.Lock()
	defer connection.mu.Unlock()
	ready := connection.packet != nil && !connection.closed && connection.ctx.Err() == nil && connection.session != nil && !connection.session.Failed()
	if packet, ok := connection.packet.(interface{ Failed() bool }); ok && packet.Failed() {
		ready = false
	}
	result := map[string]any{"selected_transport": "telemost", "actual_transport": "restricted", "selected_profile": connection.selected,
		"startup": startupdiag.Snapshot(connection.ctx), "tun_ready": ready}
	if connection.session != nil {
		result["packet"] = connection.session.Snapshot()
	}
	if connection.network != nil {
		result["protect_ok"] = connection.network.Protected.Load()
		result["protect_denied"] = connection.network.Rejected.Load()
		result["underlay_dns"] = connection.network.DNS.Load()
	}
	return result
}

func (connection *Connection) HealthSample(at time.Duration) *HealthSample {
	if connection.State() != "CONNECTED" {
		return nil
	}
	snapshot := connection.Snapshot()
	if snapshot["tun_ready"] != true {
		return nil
	}
	packet, ok := snapshot["packet"].(map[string]any)
	if !ok {
		return nil
	}
	diagnostic, ok := packet["diagnostic"].(sessiondiag.Report)
	if !ok || diagnostic.TerminalReason != "NONE" {
		return nil
	}
	return cloneSample(&HealthSample{Session: diagnostic.SessionTag, Received: diagnostic.ReceivedBytes,
		Sent: diagnostic.SentBytes, At: at, Ready: true})
}

func (connection *Connection) Close() error {
	connection.cancel(context.Canceled)
	connection.mu.Lock()
	if connection.closed {
		connection.mu.Unlock()
		<-connection.cleanupDone
		return nil
	}
	connection.closed = true
	packet, session, network := connection.packet, connection.session, connection.network
	connection.mu.Unlock()
	defer close(connection.cleanupDone)
	if connection.ownership != nil {
		connection.ownership.Drain()
		defer connection.ownership.Release()
	}
	if network != nil {
		network.Close()
	}
	if packet != nil {
		packet.Close()
	}
	if session != nil {
		session.Close()
	}
	return nil
}
