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
	id        string
	identity  Identity
	authorize Authorize
	state     State
	ctx       context.Context
	cancel    context.CancelFunc
	deadline  time.Time
	started   bool
	claimed   bool
	done      chan struct{}
}

type Broker struct {
	traceSink func(sessiontrace.Event) bool
	mu        sync.Mutex
	provider  RoomProvider
	gateway   GatewayStarter
	limits    Limits
	setups    map[string]*setup
	closed    bool
	workers   sync.WaitGroup
	event     func(State, Code)
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
	broker := &Broker{provider: provider, gateway: gateway, limits: limits, setups: make(map[string]*setup), event: event}
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
	defer broker.mu.Unlock()
	if broker.closed {
		return "", Code("closed")
	}
	if len(broker.setups) >= broker.limits.Outstanding {
		return "", Code("outstanding_limit")
	}
	for _, current := range broker.setups {
		if current.identity == identity {
			return "", Code("device_busy")
		}
	}
	lifetime, cancel := context.WithTimeout(context.Background(), broker.limits.Lifetime)
	trace := sessiontrace.New(hex.EncodeToString(nonce[:]), broker.traceSink)
	lifetime = sessiontrace.With(lifetime, trace)
	trace.Add("AUTHORIZED", "ESTABLISHED", "NONE")
	current := &setup{id: hex.EncodeToString(nonce[:]), identity: identity, authorize: authorize, state: Authorized,
		ctx: lifetime, cancel: cancel, deadline: time.Now().Add(broker.limits.Unused), done: make(chan struct{})}
	broker.setups[current.id] = current
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
		broker.mu.Unlock()
		if !waitable {
			return "", err
		}
		if pending == nil {
			continue
		}
		if err := waitForCleanup(ctx, pending.done, broker.limits.Recheck, check); err != nil {
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
			}
			broker.mu.Unlock()
			return
		case <-ticker.C:
			identity, err := authorized(current.ctx, current.authorize)
			broker.mu.Lock()
			stale := current.state != Active && time.Now().After(current.deadline)
			broker.mu.Unlock()
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
	broker.mu.Unlock()
}

func terminal(state State) bool {
	return state == Closed || state == Failed || state == Expired || state == Cancelled
}

func (broker *Broker) lookup(ctx context.Context, id string, authorize Authorize) (*setup, error) {
	identity, err := authorized(ctx, authorize)
	if err != nil {
		return nil, err
	}
	current := broker.setups[id]
	if current == nil || current.identity != identity || current.ctx.Err() != nil || terminal(current.state) ||
		(current.state != Active && !time.Now().Before(current.deadline)) {
		return nil, Code("stale_or_unbound_setup")
	}
	return current, nil
}

func (broker *Broker) Create(ctx context.Context, id string, authorize Authorize) (Descriptor, error) {
	broker.mu.Lock()
	current, err := broker.lookup(ctx, id, authorize)
	if err != nil {
		broker.mu.Unlock()
		return Descriptor{}, err
	}
	if current.state != Authorized {
		broker.mu.Unlock()
		return Descriptor{}, Code("setup_replayed")
	}
	current.started = true
	current.state = Creating
	broker.emit(current, Creating, "")
	current.deadline = time.Now().Add(broker.limits.Create + broker.limits.Ready + broker.limits.Unused)
	broker.workers.Add(1)
	broker.mu.Unlock()
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
	identity, err := authorized(ctx, authorize)
	if err != nil || identity != current.identity || current.ctx.Err() != nil {
		_ = gateway.Close()
		broker.terminate(current, Failed, "authorization_changed")
		return Descriptor{}, Code("authorization_changed")
	}
	broker.mu.Lock()
	if terminal(current.state) {
		broker.mu.Unlock()
		_ = gateway.Close()
		return Descriptor{}, Code("cancelled")
	}
	current.state = Ready
	broker.emit(current, Ready, "")
	current.deadline = time.Now().Add(broker.limits.Unused)
	descriptor := Descriptor{"telemost-webrtc", id, room.JoinURL, current.deadline}
	current.state = ClientIssued
	broker.emit(current, ClientIssued, "")
	broker.mu.Unlock()
	owned = false
	go func() {
		defer broker.finish(current)
		defer gateway.Close()
		err := gateway.Run(current.ctx, func() error { return broker.activate(current) })
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
	defer broker.mu.Unlock()
	if !terminal(current.state) {
		current.state = state
		broker.emit(current, state, "")
	}
}

func (broker *Broker) Claim(ctx context.Context, id string, authorize Authorize) error {
	broker.mu.Lock()
	defer broker.mu.Unlock()
	current, err := broker.lookup(ctx, id, authorize)
	if err != nil {
		return err
	}
	if current.state != ClientIssued || current.claimed {
		return Code("descriptor_replayed")
	}
	current.claimed = true
	return nil
}

func (broker *Broker) activate(current *setup) error {
	identity, err := authorized(current.ctx, current.authorize)
	broker.mu.Lock()
	defer broker.mu.Unlock()
	if err != nil || identity != current.identity || current.ctx.Err() != nil || current.state != ClientIssued || !current.claimed ||
		!time.Now().Before(current.deadline) {
		return Code("stale_or_unbound_setup")
	}
	current.state = Active
	broker.emit(current, Active, "")
	return nil
}

func (broker *Broker) Cancel(ctx context.Context, id string, authorize Authorize) error {
	broker.mu.Lock()
	current, err := broker.lookup(ctx, id, authorize)
	broker.mu.Unlock()
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
	delete(broker.setups, current.id)
	close(current.done)
	broker.mu.Unlock()
	broker.workers.Done()
}

func (broker *Broker) Close() {
	broker.mu.Lock()
	broker.closed = true
	for _, current := range broker.setups {
		sessiontrace.From(current.ctx).Add("LOCAL_CLOSE", "STARTED", "NONE")
		current.cancel()
	}
	broker.mu.Unlock()
	broker.workers.Wait()
}
