package desktopauto

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"errors"
	"io"
	"net"
	"sync"
	"time"
)

type State string
type Failure string
type Candidate string

const (
	Disconnected         State     = "DISCONNECTED"
	Connecting           State     = "CONNECTING"
	Connected            State     = "CONNECTED"
	Restoring            State     = "RESTORING"
	Failed               State     = "FAILED"
	Disconnecting        State     = "DISCONNECTING"
	Cancelled            Failure   = "CANCELLED"
	Auth                 Failure   = "AUTH"
	Configuration        Failure   = "CONFIGURATION"
	Network              Failure   = "NETWORK"
	TransportUnavailable Failure   = "TRANSPORT_UNAVAILABLE"
	BootstrapUnavailable Failure   = "BOOTSTRAP_UNAVAILABLE"
	Internal             Failure   = "INTERNAL"
	WG                   Candidate = "wg"
	AWG                  Candidate = "awg"
	TCP                  Candidate = "tcp"
	Restricted           Candidate = "restricted"
	NormalTimeout                  = 20 * time.Second
	RestrictedTimeout              = 200 * time.Second
	ConnectTimeout                 = 300 * time.Second
	ConfigureTimeout               = 30 * time.Second
	RecoveryBackoff                = 30 * time.Second
	MaxRecoveryBackoff             = 120 * time.Second
	RecoveryCooldown               = 300 * time.Second
	StableTraffic                  = 120 * time.Second
	MaxEvents                      = 128
)

var (
	ErrBusy    = errors.New("automatic operation already running")
	ErrStale   = errors.New("stale automatic generation")
	ErrInvalid = errors.New("invalid automatic operation")
)

type Rejected struct {
	Category           Failure
	TemporaryBootstrap bool
}

func (rejected Rejected) Error() string { return string(rejected.Category) }

type Event struct {
	Name      string    `json:"event"`
	Candidate Candidate `json:"candidate,omitempty"`
	Category  Failure   `json:"category,omitempty"`
	State     State     `json:"state"`
	ElapsedMS int64     `json:"elapsed_ms"`
}

type Snapshot struct {
	Generation       uint64    `json:"generation"`
	State            State     `json:"state"`
	Selected         Candidate `json:"selected,omitempty"`
	DesiredConnected bool      `json:"desired_connected"`
	FirstReason      Failure   `json:"first_reason,omitempty"`
	RetryAtMS        int64     `json:"retry_at_ms"`
	Events           []Event   `json:"events"`
	EventsDropped    uint64    `json:"events_dropped"`
}

type Host interface {
	Now() time.Duration
	Jitter(time.Duration) time.Duration
	NetworkAvailable() bool
	Configure(context.Context, time.Duration) ([]Candidate, error)
	Pause(context.Context, time.Duration) error
	Open(context.Context, Candidate, time.Duration) error
	CloseCandidate(context.Context) error
	Release(context.Context) error
	Remember(Candidate) error
}

type Controller struct {
	host                Host
	cleanupTimeout      time.Duration
	operation           sync.Mutex
	mu                  sync.Mutex
	view                Snapshot
	interrupted         Failure
	cancel              context.CancelFunc
	ctx                 context.Context
	state               State
	selected            Candidate
	generation          uint64
	requested           bool
	started             time.Duration
	candidates          []Candidate
	restorations        int
	failedSeries        int
	bootstrapRecoveries int
	retryAt             time.Duration
	retryReason         Failure
	healthySince        time.Duration
	events              []Event
	dropped             uint64
	firstReason         Failure
}

func New(host Host, cleanupTimeout time.Duration) (*Controller, error) {
	if host == nil || cleanupTimeout <= 0 || cleanupTimeout > time.Minute {
		return nil, ErrInvalid
	}
	return &Controller{host: host, cleanupTimeout: cleanupTimeout, state: Disconnected,
		view: Snapshot{State: Disconnected}, healthySince: -1}, nil
}

func Order(configured []Candidate, preferred, lastGood Candidate) ([]Candidate, error) {
	if len(configured) > 32 {
		return nil, Rejected{Category: Configuration}
	}
	allowed := make(map[Candidate]bool, 3)
	for _, candidate := range configured {
		if candidate != WG && candidate != AWG && candidate != TCP {
			return nil, Rejected{Category: Configuration}
		}
		allowed[candidate] = true
	}
	ordered := make([]Candidate, 0, 4)
	for _, candidate := range append([]Candidate{lastGood, preferred}, configured...) {
		if allowed[candidate] {
			ordered = append(ordered, candidate)
			delete(allowed, candidate)
		}
	}
	return append(ordered, Restricted), nil
}

func (controller *Controller) Snapshot() Snapshot {
	controller.mu.Lock()
	defer controller.mu.Unlock()
	result := controller.view
	result.Events = append([]Event(nil), result.Events...)
	return result
}

func (controller *Controller) Interrupt(generation uint64, reason Failure) error {
	if reason != Cancelled && reason != Auth {
		return ErrInvalid
	}
	controller.mu.Lock()
	if generation == 0 || generation != controller.view.Generation {
		controller.mu.Unlock()
		return ErrStale
	}
	controller.interrupted = reason
	controller.view.DesiredConnected = false
	cancel := controller.cancel
	controller.mu.Unlock()
	if cancel != nil {
		cancel()
	}
	return nil
}

func (controller *Controller) check(deadline time.Duration) error {
	controller.mu.Lock()
	reason := controller.interrupted
	controller.mu.Unlock()
	if reason != "" {
		return Rejected{Category: reason}
	}
	if controller.ctx.Err() != nil {
		return Rejected{Category: Cancelled}
	}
	if controller.host.Now() >= deadline {
		return Rejected{Category: Network}
	}
	return nil
}

func classify(failure error) (Failure, bool) {
	var rejected Rejected
	var pointer *Rejected
	matched := errors.As(failure, &rejected)
	if !matched && errors.As(failure, &pointer) && pointer != nil {
		rejected, matched = *pointer, true
	}
	if matched {
		switch rejected.Category {
		case Cancelled, Auth, Configuration, Network, TransportUnavailable, BootstrapUnavailable, Internal:
			return rejected.Category, rejected.Category == BootstrapUnavailable && rejected.TemporaryBootstrap
		}
	}
	if errors.Is(failure, context.Canceled) {
		return Cancelled, false
	}
	var certificateInvalid x509.CertificateInvalidError
	var unknownAuthority x509.UnknownAuthorityError
	var hostnameInvalid x509.HostnameError
	var certificateInvalidPointer *x509.CertificateInvalidError
	var unknownAuthorityPointer *x509.UnknownAuthorityError
	var hostnameInvalidPointer *x509.HostnameError
	var verification *tls.CertificateVerificationError
	if errors.As(failure, &certificateInvalid) || errors.As(failure, &unknownAuthority) || errors.As(failure, &hostnameInvalid) || errors.As(failure, &verification) ||
		errors.As(failure, &certificateInvalidPointer) || errors.As(failure, &unknownAuthorityPointer) || errors.As(failure, &hostnameInvalidPointer) {
		return Auth, false
	}
	var invalidTLS tls.RecordHeaderError
	var invalidTLSPointer *tls.RecordHeaderError
	if errors.As(failure, &invalidTLS) || errors.As(failure, &invalidTLSPointer) {
		return Configuration, false
	}
	var networkError net.Error
	if errors.Is(failure, context.DeadlineExceeded) || errors.Is(failure, io.EOF) || errors.Is(failure, io.ErrUnexpectedEOF) || errors.As(failure, &networkError) {
		return Network, false
	}
	return Internal, false
}

func retryable(reason Failure) bool { return reason == Network || reason == TransportUnavailable }

func (controller *Controller) Connect(ctx context.Context, generation uint64, preferred, lastGood Candidate) error {
	if !controller.operation.TryLock() {
		return ErrBusy
	}
	defer controller.operation.Unlock()
	if generation == 0 || generation <= controller.generation {
		return ErrStale
	}
	if controller.state != Disconnected {
		return ErrBusy
	}
	if ctx == nil {
		return ErrInvalid
	}
	controller.generation = generation
	controller.mu.Lock()
	controller.ctx, controller.cancel = context.WithCancel(ctx)
	controller.interrupted = ""
	controller.view = Snapshot{Generation: generation, State: Connecting, DesiredConnected: true}
	controller.mu.Unlock()
	controller.started = controller.host.Now()
	controller.restorations, controller.failedSeries, controller.bootstrapRecoveries = 0, 0, 0
	controller.retryAt, controller.healthySince = 0, -1
	controller.candidates, controller.events = nil, nil
	controller.dropped, controller.firstReason = 0, ""
	controller.requested, controller.state = true, Connecting
	controller.emit("connect_requested", "", "")
	deadline := controller.started + ConfigureTimeout
	bounded, cancel := context.WithTimeout(controller.ctx, ConfigureTimeout)
	var configured []Candidate
	failure := controller.check(deadline)
	if failure == nil {
		configured, failure = controller.host.Configure(bounded, deadline)
	}
	if failure == nil {
		failure = controller.check(deadline)
	}
	if failure == nil {
		failure = bounded.Err()
	}
	cancel()
	if failure == nil {
		controller.candidates, failure = Order(configured, preferred, lastGood)
	}
	if failure != nil {
		reason, temporary := controller.reason(failure)
		controller.finish(reason, false, temporary)
		return nil
	}
	controller.run(false)
	return nil
}

func (controller *Controller) reason(failure error) (Failure, bool) {
	controller.mu.Lock()
	reason := controller.interrupted
	controller.mu.Unlock()
	if reason != "" {
		return reason, false
	}
	return classify(failure)
}

func (controller *Controller) cleanup(release bool) error {
	bounded, cancel := context.WithTimeout(context.Background(), controller.cleanupTimeout)
	defer cancel()
	var failure error
	if release {
		failure = controller.host.Release(bounded)
	} else {
		failure = controller.host.CloseCandidate(bounded)
	}
	if failure == nil {
		failure = bounded.Err()
	}
	return failure
}

func (controller *Controller) run(restoring bool) {
	deadline := controller.started + ConnectTimeout
	last, temporary := TransportUnavailable, false
	for index, candidate := range controller.candidates {
		failure := controller.check(deadline)
		if failure == nil && controller.cleanup(false) != nil {
			controller.finish(Internal, restoring, false)
			return
		}
		if failure == nil {
			failure = controller.check(deadline)
		}
		if failure == nil && !controller.host.NetworkAvailable() {
			failure = Rejected{Category: TransportUnavailable}
		}
		if failure == nil && (index > 0 || restoring) {
			controller.emit("fallback", candidate, last)
			until := min(deadline, controller.host.Now()+min(4*time.Second, time.Second<<index))
			for failure == nil && controller.host.Now() < until {
				failure = controller.check(deadline)
				if failure == nil {
					failure = controller.host.Pause(controller.ctx, min(100*time.Millisecond, until-controller.host.Now()))
				}
			}
		}
		if failure == nil {
			failure = controller.check(deadline)
		}
		if failure == nil {
			controller.emit("candidate_attempted", candidate, "")
			timeout := NormalTimeout
			if candidate == Restricted {
				timeout = RestrictedTimeout
			}
			candidateDeadline := min(deadline, controller.host.Now()+timeout)
			bounded, cancel := context.WithTimeout(controller.ctx, candidateDeadline-controller.host.Now())
			failure = controller.host.Open(bounded, candidate, candidateDeadline)
			if failure == nil {
				failure = controller.check(candidateDeadline)
			}
			if failure == nil {
				failure = bounded.Err()
			}
			cancel()
			if failure == nil && candidate != Restricted {
				failure = controller.host.Remember(candidate)
			}
			if failure == nil {
				failure = controller.check(candidateDeadline)
			}
			if failure == nil {
				controller.mu.Lock()
				if controller.interrupted != "" {
					failure = Rejected{Category: controller.interrupted}
				} else if controller.ctx.Err() != nil {
					failure = Rejected{Category: Cancelled}
				} else {
					controller.selected, controller.state = candidate, Connected
					controller.retryAt, controller.healthySince = 0, -1
					controller.emitLocked("candidate_succeeded", candidate, "")
					controller.emitLocked("time_to_connected", candidate, "")
					if restoring {
						controller.emitLocked("restoration_succeeded", candidate, "")
					}
				}
				controller.mu.Unlock()
				if failure == nil {
					return
				}
			}
		}
		last, temporary = controller.reason(failure)
		controller.emit("candidate_failed", candidate, last)
		if controller.cleanup(false) != nil {
			controller.finish(Internal, restoring, false)
			return
		}
		if last == Cancelled || last == Auth || last == Configuration || last == Internal || controller.host.Now() >= deadline {
			controller.finish(last, restoring, temporary)
			return
		}
	}
	controller.finish(last, restoring, temporary)
}

func (controller *Controller) finish(reason Failure, restoring, temporary bool) {
	if controller.cleanup(false) != nil {
		reason = Internal
	}
	controller.selected = ""
	if reason == Cancelled {
		controller.disconnect()
		return
	}
	bootstrapRetry := reason == BootstrapUnavailable && temporary
	if controller.requested && (retryable(reason) || bootstrapRetry) && len(controller.candidates) > 0 {
		if bootstrapRetry {
			controller.bootstrapRecoveries++
		}
		delay := min(MaxRecoveryBackoff, RecoveryBackoff<<min(controller.failedSeries, 2))
		if bootstrapRetry && controller.bootstrapRecoveries > 2 {
			delay = RecoveryCooldown
			controller.bootstrapRecoveries = 0
		}
		delay += max(0, min(5*time.Second, controller.host.Jitter(5*time.Second)))
		controller.failedSeries = min(2, controller.failedSeries+1)
		controller.retryAt, controller.retryReason = controller.host.Now()+delay, reason
		controller.healthySince, controller.state = -1, Restoring
		controller.emit("restoration_failed", "", reason)
		controller.emit("recovery_wait", "", reason)
		return
	}
	controller.requested, controller.retryAt, controller.state = false, 0, Failed
	name := "connect_failed"
	if restoring {
		name = "restoration_failed"
	}
	controller.emit(name, "", reason)
}

func (controller *Controller) Lost(generation uint64, reason Failure) error {
	if !controller.operation.TryLock() {
		return ErrBusy
	}
	defer controller.operation.Unlock()
	if generation == 0 || generation != controller.generation {
		return ErrStale
	}
	if controller.state != Connected {
		return nil
	}
	reason, _ = controller.reason(Rejected{Category: reason})
	controller.emit("transport_lost", controller.selected, reason)
	controller.state, controller.started = Restoring, controller.host.Now()
	if !retryable(reason) || controller.restorations >= 1 {
		controller.finish(reason, true, false)
		return nil
	}
	controller.restorations++
	controller.emit("restoration_attempted", controller.selected, reason)
	normal := controller.candidates[:len(controller.candidates)-1]
	controller.candidates, _ = Order(normal, controller.selected, controller.selected)
	controller.run(true)
	return nil
}

func (controller *Controller) Retry(generation uint64) error {
	if !controller.operation.TryLock() {
		return ErrBusy
	}
	defer controller.operation.Unlock()
	if generation == 0 || generation != controller.generation {
		return ErrStale
	}
	if controller.state != Restoring {
		return nil
	}
	if failure := controller.check(time.Duration(1<<63 - 1)); failure != nil {
		reason, _ := controller.reason(failure)
		controller.finish(reason, true, false)
		return nil
	}
	if !controller.requested || controller.retryAt == 0 || controller.host.Now() < controller.retryAt {
		return nil
	}
	controller.retryAt, controller.restorations, controller.started = 0, 1, controller.host.Now()
	controller.emit("restoration_attempted", controller.selected, controller.retryReason)
	controller.run(true)
	return nil
}

func (controller *Controller) Healthy(generation uint64, good bool) error {
	if !controller.operation.TryLock() {
		return ErrBusy
	}
	defer controller.operation.Unlock()
	if generation == 0 || generation != controller.generation {
		return ErrStale
	}
	if controller.state != Connected || !good {
		controller.healthySince = -1
		return nil
	}
	if controller.healthySince < 0 {
		controller.healthySince = controller.host.Now()
	}
	if controller.host.Now()-controller.healthySince >= StableTraffic {
		controller.restorations, controller.failedSeries, controller.bootstrapRecoveries = 0, 0, 0
	}
	return nil
}

func (controller *Controller) Disconnect(generation uint64) error {
	if failure := controller.Interrupt(generation, Cancelled); failure != nil {
		return failure
	}
	controller.operation.Lock()
	defer controller.operation.Unlock()
	if generation != controller.generation {
		return ErrStale
	}
	controller.disconnect()
	return nil
}

func (controller *Controller) disconnect() {
	controller.requested, controller.retryAt = false, 0
	if controller.state == Disconnected {
		return
	}
	controller.state = Disconnecting
	controller.emit("disconnect_requested", controller.selected, Cancelled)
	failure := controller.cleanup(false)
	if failure == nil {
		failure = controller.cleanup(true)
	}
	if failure != nil {
		controller.state = Failed
		controller.emit("cleanup_failed", controller.selected, Internal)
		return
	}
	controller.selected, controller.state = "", Disconnected
	controller.mu.Lock()
	if controller.cancel != nil {
		controller.cancel()
	}
	controller.interrupted = ""
	controller.mu.Unlock()
	controller.emit("disconnected", "", Cancelled)
}

func (controller *Controller) emit(name string, candidate Candidate, reason Failure) {
	controller.mu.Lock()
	defer controller.mu.Unlock()
	controller.emitLocked(name, candidate, reason)
}

func (controller *Controller) emitLocked(name string, candidate Candidate, reason Failure) {
	if reason != "" && controller.firstReason == "" {
		controller.firstReason = reason
	}
	if len(controller.events) == MaxEvents {
		copy(controller.events, controller.events[1:])
		controller.events = controller.events[:MaxEvents-1]
		if controller.dropped < ^uint64(0) {
			controller.dropped++
		}
	}
	controller.events = append(controller.events, Event{Name: name, Candidate: candidate, Category: reason,
		State: controller.state, ElapsedMS: max(0, (controller.host.Now() - controller.started).Milliseconds())})
	controller.view = Snapshot{Generation: controller.generation, State: controller.state, Selected: controller.selected,
		DesiredConnected: controller.requested && controller.interrupted == "" && controller.ctx.Err() == nil,
		FirstReason:      controller.firstReason, RetryAtMS: controller.retryAt.Milliseconds(),
		Events: append([]Event(nil), controller.events...), EventsDropped: controller.dropped}
}
