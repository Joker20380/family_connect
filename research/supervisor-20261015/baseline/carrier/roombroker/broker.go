package roombroker

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"errors"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"sync"
	"time"
)

type State string

const (
	Authorized     State = "AUTHORIZED"
	Creating       State = "CREATING"
	Created        State = "CREATED"
	GatewayJoining State = "GATEWAY_JOINING"
	Ready          State = "READY"
	ClientIssued   State = "CLIENT_ISSUED"
	Active         State = "ACTIVE"
	Closed         State = "CLOSED"
	Failed         State = "FAILED"
	Expired        State = "EXPIRED"
	Cancelled      State = "CANCELLED"
)

type Identity struct {
	Family, Device string
	PublicKey      [32]byte
}
type Authorize func(context.Context) (Identity, error)

type Descriptor struct {
	Transport string    `json:"transport"`
	SetupID   string    `json:"setup_id"`
	JoinURL   string    `json:"join_url"`
	ExpiresAt time.Time `json:"expires_at"`
}

func (Descriptor) String() string   { return "[ephemeral descriptor redacted]" }
func (Descriptor) GoString() string { return "[ephemeral descriptor redacted]" }

type Gateway interface {
	Run(context.Context, func() error) error
	Close() error
}

type GatewayStarter interface {
	Start(lifetime, ready context.Context, room Room, setupID string, identity Identity) (Gateway, error)
}

type Limits struct {
	Create, Ready, Unused, Lifetime, Recheck time.Duration
	Outstanding                              int
}

func DefaultLimits() Limits {
	return Limits{CreationTimeout, 45 * time.Second, 60 * time.Second, 10 * time.Minute, time.Second, 32}
}

type setup struct {
	exchange    string
	created     time.Time
	id          string
	identity    Identity
	authorize   Authorize
	state       State
	ctx         context.Context
	cancel      context.CancelFunc
	deadline    time.Time
	started     bool
	claimed     bool
	done        chan struct{}
	lease       *leaseLifetime
	renewal     uint64
	lastLease   LeaseReceipt
	lastRequest LeaseReceipt
}

type Broker struct {
	ownership *ownershipCapture
	traceSink func(sessiontrace.Event) bool
	mu        sync.Mutex
	publishMu sync.Mutex
	provider  RoomProvider
	gateway   GatewayStarter
	limits    Limits
	setups    map[string]*setup
	closed    bool
	workers   sync.WaitGroup
	event     func(State, Code)
	pending   []func()
	newLease  func(time.Duration) *leaseLifetime
}

func New(provider RoomProvider, gateway GatewayStarter, limits Limits, event func(State, Code), traces ...func(sessiontrace.Event) bool) (*Broker, error) {
	if provider == nil || gateway == nil || limits.Create <= 0 || limits.Create > CreationTimeout ||
		limits.Ready <= 0 || limits.Ready > time.Minute || limits.Unused <= 0 || limits.Unused > 2*time.Minute ||
		limits.Lifetime <= 0 || limits.Lifetime > time.Hour || limits.Recheck <= 0 || limits.Recheck > time.Second ||
		limits.Outstanding < 1 || limits.Outstanding > 32 {
		return nil, Code("invalid_limits")
	}
	if event == nil {
		event = func(State, Code) {}
	}
	broker := &Broker{provider: provider, gateway: gateway, limits: limits, setups: make(map[string]*setup), event: event, newLease: newLeaseLifetime}
	if len(traces) > 0 {
		broker.traceSink = traces[0]
	}
	return broker, nil
}

func authorized(ctx context.Context, authorize Authorize) (Identity, error) {
	if authorize == nil {
		return Identity{}, Code("unauthorized")
	}
	identity, err := authorize(ctx)
	if err != nil || len(identity.Family) != 32 || len(identity.Device) != 32 || ctx.Err() != nil {
		return Identity{}, Code("unauthorized")
	}
	return identity, nil
}

func (broker *Broker) Challenge(ctx context.Context, authorize Authorize) (string, error) {
	identity, err := authorized(ctx, authorize)
	if err != nil {
		return "", err
	}
	var nonce [32]byte
	if _, err := rand.Read(nonce[:]); err != nil {
		return "", Code("entropy_unavailable")
	}
	broker.mu.Lock()
	defer broker.unlock()
	if broker.closed {
		broker.ownershipLocked(ctx, nil, nil, "reject", "closed")
		return "", Code("closed")
	}
	if len(broker.setups) >= broker.limits.Outstanding {
		broker.ownershipLocked(ctx, nil, nil, "reject", "outstanding_limit")
		return "", Code("outstanding_limit")
	}
	for _, current := range broker.setups {
		if current.identity == identity {
			broker.ownershipLocked(ctx, current, &identity, "busy", "device_busy")
			return "", Code("device_busy")
		}
	}
	lease := broker.newLease(broker.limits.Lifetime)
	lifetime, cancel := context.Context(lease), lease.cancel
	trace := sessiontrace.New(hex.EncodeToString(nonce[:]), broker.traceSink)
	broker.pending = append(broker.pending, func() { sessiontrace.StartDiagnosticControl(lifetime, trace, "gateway") })
	lifetime = sessiontrace.With(lifetime, trace)
	leaseDeadline := lease.deadline()
	broker.pending = append(broker.pending, func() {
		trace.Record(sessiontrace.Event{Stage: "AUTHORIZED", State: "ESTABLISHED", Reason: "NONE", LeaseDeadlineMS: leaseDeadline.UnixMilli()})
	})
	current := &setup{id: hex.EncodeToString(nonce[:]), identity: identity, authorize: authorize, state: Authorized,
		ctx: lifetime, cancel: cancel, deadline: time.Now().Add(broker.limits.Unused), done: make(chan struct{}), lease: lease}
	current.ctx = context.WithValue(current.ctx, leaseKey{}, &leaseBinding{broker: broker, current: current})
	broker.setups[current.id] = current
	current.exchange, current.created = exchangeTag(ctx), time.Now()
	broker.ownershipLocked(ctx, current, &identity, "grant", "acquired")
	broker.workers.Add(1)
	go broker.monitor(current)
	return current.id, nil
}

func (broker *Broker) ChallengeAfterCleanup(ctx context.Context, authorize Authorize) (string, error) {
	if err := ctx.Err(); err != nil {
		return "", err
	}
	identity, err := authorized(ctx, authorize)
	if err != nil {
		if interrupted := ctx.Err(); interrupted != nil {
			return "", interrupted
		}
		return "", err
	}
	check := func(ctx context.Context) (Identity, error) {
		current, err := authorized(ctx, authorize)
		if err != nil || current != identity {
			return Identity{}, Code("unauthorized")
		}
		return current, nil
	}
	for {
		if err := ctx.Err(); err != nil {
			return "", err
		}
		id, err := broker.Challenge(ctx, check)
		if err != Code("device_busy") {
			if err != nil && ctx.Err() != nil {
				return "", ctx.Err()
			}
			return id, err
		}
		broker.mu.Lock()
		var pending *setup
		for _, current := range broker.setups {
			if current.identity == identity {
				pending = current
				break
			}
		}
		waitable := pending == nil || pending.state == Active || pending.started && terminal(pending.state)
		if pending != nil && waitable {
			broker.ownershipLocked(ctx, pending, &identity, "wait", "device_busy")
		}
		broker.unlock()
		if !waitable {
			return "", err
		}
		if pending == nil {
			continue
		}
		err = waitForCleanup(ctx, pending.done, broker.limits.Recheck, check)
		broker.mu.Lock()
		broker.ownershipLocked(ctx, pending, &identity, "wait_end", ownershipReason(err))
		broker.unlock()
		if err != nil {
			return "", err
		}
	}
}

func waitForCleanup(ctx context.Context, done <-chan struct{}, interval time.Duration, authorize Authorize) error {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()
	for {
		select {
		case <-done:
			return nil
		case <-ctx.Done():
			return ctx.Err()
		case <-ticker.C:
			if _, err := authorize(ctx); err != nil {
				if interrupted := ctx.Err(); interrupted != nil {
					return interrupted
				}
				return err
			}
		}
	}
}

func (broker *Broker) monitor(current *setup) {
	defer broker.workers.Done()
	ticker := time.NewTicker(broker.limits.Recheck)
	defer ticker.Stop()
	for {
		select {
		case <-current.done:
			return
		case <-current.ctx.Done():
			broker.mu.Lock()
			if !terminal(current.state) {
				current.state = Cancelled
				code := Code("cancelled")
				if current.ctx.Err() == context.DeadlineExceeded {
					current.state = Expired
					code = "lifetime_expired"
				}
				broker.emit(current, current.state, code)
			}
			started := current.started
			if !started {
				delete(broker.setups, current.id)
				close(current.done)
				broker.ownershipLocked(current.ctx, current, nil, "release", "monitor_unstarted")
			}
			broker.unlock()
			return
		case <-ticker.C:
			identity, err := authorized(current.ctx, current.authorize)
			broker.mu.Lock()
			stale := current.state != Active && time.Now().After(current.deadline)
			broker.unlock()
			if err != nil || identity != current.identity {
				broker.terminate(current, Failed, "authorization_changed")
			} else if stale {
				broker.terminate(current, Expired, "unused_expired")
			}
		}
	}
}

func (broker *Broker) terminate(current *setup, state State, code Code) {
	broker.mu.Lock()
	if !terminal(current.state) {
		current.state = state
		broker.emit(current, state, code)
	}
	current.cancel()
	broker.unlock()
}

func terminal(state State) bool {
	return state == Closed || state == Failed || state == Expired || state == Cancelled
}

func (broker *Broker) lookup(ctx context.Context, id string, identity Identity) (*setup, error) {
	current := broker.setups[id]
	if ctx.Err() != nil || current == nil || current.identity != identity || current.ctx.Err() != nil || terminal(current.state) ||
		(current.state != Active && !time.Now().Before(current.deadline)) {
		return nil, Code("stale_or_unbound_setup")
	}
	return current, nil
}

func (broker *Broker) Create(ctx context.Context, id string, authorize Authorize) (Descriptor, error) {
	identity, err := authorized(ctx, authorize)
	if err != nil {
		return Descriptor{}, err
	}
	broker.mu.Lock()
	current, err := broker.lookup(ctx, id, identity)
	if err != nil {
		broker.unlock()
		return Descriptor{}, err
	}
	if current.state != Authorized {
		broker.unlock()
		return Descriptor{}, Code("setup_replayed")
	}
	current.started = true
	current.state = Creating
	broker.emit(current, Creating, "")
	current.deadline = time.Now().Add(broker.limits.Create + broker.limits.Ready + broker.limits.Unused)
	broker.workers.Add(1)
	broker.unlock()
	stop := context.AfterFunc(ctx, current.cancel)
	defer stop()
	owned := true
	defer func() {
		if owned {
			broker.finish(current)
		}
	}()
	creation, cancel := context.WithTimeout(current.ctx, broker.limits.Create)
	room, err := broker.provider.CreateRoom(creation)
	creationErr := creation.Err()
	cancel()
	if err != nil || creationErr != nil {
		code := Code("provider_failure")
		var safe Code
		if errors.As(err, &safe) {
			code = safe
		}
		if creationErr == context.DeadlineExceeded {
			code = "provider_timeout"
		}
		if creationErr == context.Canceled {
			code = "provider_cancelled"
		}
		broker.terminate(current, Failed, code)
		return Descriptor{}, code
	}
	if room.ID == "" || !ValidJoinURL(room.JoinURL) {
		broker.terminate(current, Failed, "provider_response")
		return Descriptor{}, Code("provider_response")
	}
	broker.transition(current, Created)
	broker.transition(current, GatewayJoining)
	ready, cancel := context.WithTimeout(current.ctx, broker.limits.Ready)
	gateway, err := broker.gateway.Start(current.ctx, ready, room, id, current.identity)
	readyErr := ready.Err()
	cancel()
	if err != nil || readyErr != nil || gateway == nil {
		if gateway != nil {
			_ = gateway.Close()
		}
		code := Code("gateway_failed")
		if readyErr == context.DeadlineExceeded {
			code = "gateway_ready_timeout"
		}
		broker.terminate(current, Failed, code)
		return Descriptor{}, code
	}
	identity, err = authorized(ctx, authorize)
	if err != nil || identity != current.identity || current.ctx.Err() != nil {
		_ = gateway.Close()
		broker.terminate(current, Failed, "authorization_changed")
		return Descriptor{}, Code("authorization_changed")
	}
	broker.mu.Lock()
	if terminal(current.state) {
		broker.unlock()
		_ = gateway.Close()
		return Descriptor{}, Code("cancelled")
	}
	current.state = Ready
	broker.emit(current, Ready, "")
	current.deadline = time.Now().Add(broker.limits.Unused)
	descriptor := Descriptor{"telemost-webrtc", id, room.JoinURL, current.deadline}
	current.state = ClientIssued
	broker.emit(current, ClientIssued, "")
	broker.unlock()
	owned = false
	go func() {
		defer broker.finish(current)
		defer func() {
			broker.mu.Lock()
			broker.ownershipLocked(current.ctx, current, nil, "gateway_close_begin", "worker_cleanup")
			broker.unlock()
			_ = gateway.Close()
			broker.mu.Lock()
			broker.ownershipLocked(current.ctx, current, nil, "gateway_close_end", "worker_cleanup")
			broker.unlock()
		}()
		err := gateway.Run(current.ctx, func() error { return broker.activate(current) })
		broker.mu.Lock()
		broker.ownershipLocked(current.ctx, current, nil, "gateway_run_end", ownershipReason(err))
		broker.unlock()
		if err != nil {
			broker.terminate(current, Failed, "gateway_session_failed")
		} else {
			broker.terminate(current, Closed, "")
		}
	}()
	return descriptor, nil
}

func (broker *Broker) transition(current *setup, state State) {
	broker.mu.Lock()
	defer broker.unlock()
	if !terminal(current.state) {
		current.state = state
		broker.emit(current, state, "")
	}
}

func (broker *Broker) Claim(ctx context.Context, id string, authorize Authorize) error {
	identity, err := authorized(ctx, authorize)
	if err != nil {
		return err
	}
	broker.mu.Lock()
	defer broker.unlock()
	current, err := broker.lookup(ctx, id, identity)
	if err != nil {
		return err
	}
	if current.state != ClientIssued || current.claimed {
		return Code("descriptor_replayed")
	}
	current.claimed = true
	broker.ownershipLocked(ctx, current, nil, "claim", "descriptor_claimed")
	return nil
}

func (broker *Broker) activate(current *setup) error {
	identity, err := authorized(current.ctx, current.authorize)
	broker.mu.Lock()
	defer broker.unlock()
	if err != nil || identity != current.identity || current.ctx.Err() != nil || current.state != ClientIssued || !current.claimed ||
		!time.Now().Before(current.deadline) {
		return Code("stale_or_unbound_setup")
	}
	current.state = Active
	broker.emit(current, Active, "")
	return nil
}

func (broker *Broker) Cancel(ctx context.Context, id string, authorize Authorize) error {
	identity, err := authorized(ctx, authorize)
	if err != nil {
		return err
	}
	broker.mu.Lock()
	current, err := broker.lookup(ctx, id, identity)
	broker.unlock()
	if err != nil {
		return err
	}
	broker.terminate(current, Cancelled, "cancelled")
	return nil
}

func (broker *Broker) finish(current *setup) {
	sessiontrace.From(current.ctx).Add("CLEANUP", "COMPLETED", "NONE")
	current.cancel()
	broker.mu.Lock()
	if broker.setups[current.id] == current {
		delete(broker.setups, current.id)
		close(current.done)
	}
	broker.ownershipLocked(current.ctx, current, nil, "release", "worker_finished")
	broker.unlock()
	broker.workers.Done()
}

func (broker *Broker) Close() {
	broker.mu.Lock()
	broker.closed = true
	for _, current := range broker.setups {
		trace := sessiontrace.From(current.ctx)
		broker.pending = append(broker.pending, func() { trace.Add("LOCAL_CLOSE", "STARTED", "NONE") })
		current.cancel()
	}
	broker.unlock()
	broker.workers.Wait()
}
