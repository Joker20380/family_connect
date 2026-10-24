package desktopauto

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/url"
	"os"
	"reflect"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

type fixture struct {
	controller             *Controller
	now                    atomic.Int64
	guard                  atomic.Bool
	active                 atomic.Int32
	releases               atomic.Int32
	configured             []Candidate
	failures               map[Candidate]error
	attempts               []Candidate
	remembered             []Candidate
	deadlines              []time.Duration
	configureFailure       error
	configureDelay         time.Duration
	configureCalls         int
	closeFailure           bool
	closeFailureWhenActive bool
	releaseFailure         bool
	offline                bool
	openUntilDeadline      bool
	cancelCandidate        Candidate
	cancelRemember         bool
	blocked                chan struct{}
	jitter                 time.Duration
	peak                   int32
}

func newFixture(test *testing.T) *fixture {
	test.Helper()
	host := &fixture{configured: []Candidate{AWG, TCP}, failures: make(map[Candidate]error)}
	controller, failure := New(host, 25*time.Second)
	if failure != nil {
		test.Fatal(failure)
	}
	host.controller = controller
	return host
}

func (host *fixture) Now() time.Duration                 { return time.Duration(host.now.Load()) }
func (host *fixture) advance(duration time.Duration)     { host.now.Add(int64(duration)) }
func (host *fixture) Jitter(time.Duration) time.Duration { return host.jitter }
func (host *fixture) NetworkAvailable() bool             { return !host.offline }
func (host *fixture) Configure(ctx context.Context, deadline time.Duration) ([]Candidate, error) {
	host.configureCalls++
	host.guard.Store(true)
	host.advance(host.configureDelay)
	return append([]Candidate(nil), host.configured...), host.configureFailure
}
func (host *fixture) Pause(ctx context.Context, duration time.Duration) error {
	if ctx.Err() != nil {
		return ctx.Err()
	}
	host.advance(duration)
	return nil
}
func (host *fixture) Open(ctx context.Context, candidate Candidate, deadline time.Duration) error {
	host.attempts = append(host.attempts, candidate)
	host.deadlines = append(host.deadlines, deadline)
	active := host.active.Add(1)
	host.peak = max(host.peak, active)
	if !host.guard.Load() || active != 1 {
		return Rejected{Category: Internal}
	}
	if _, exists := ctx.Deadline(); !exists {
		return errors.New("missing attempt deadline")
	}
	if host.blocked != nil {
		close(host.blocked)
		<-ctx.Done()
		return ctx.Err()
	}
	if host.cancelCandidate == candidate {
		_ = host.controller.Interrupt(host.controller.Snapshot().Generation, Cancelled)
	}
	if host.openUntilDeadline {
		host.advance(deadline - host.Now())
		return nil
	}
	return host.failures[candidate]
}
func (host *fixture) CloseCandidate(ctx context.Context) error {
	if host.closeFailure || (host.closeFailureWhenActive && host.active.Load() != 0) {
		return errors.New("synthetic close failure")
	}
	host.active.Store(0)
	return nil
}
func (host *fixture) Release(ctx context.Context) error {
	if host.releaseFailure {
		return errors.New("synthetic release failure")
	}
	host.releases.Add(1)
	host.guard.Store(false)
	return nil
}
func (host *fixture) Remember(candidate Candidate) error {
	host.remembered = append(host.remembered, candidate)
	if host.cancelRemember {
		return host.controller.Interrupt(host.controller.Snapshot().Generation, Cancelled)
	}
	return nil
}
func (host *fixture) connect(test *testing.T) {
	test.Helper()
	if failure := host.controller.Connect(context.Background(), 1, AWG, ""); failure != nil {
		test.Fatal(failure)
	}
}
func count(snapshot Snapshot, name string) int {
	result := 0
	for _, event := range snapshot.Events {
		if event.Name == name {
			result++
		}
	}
	return result
}
func requireState(test *testing.T, host *fixture, state State) Snapshot {
	test.Helper()
	snapshot := host.controller.Snapshot()
	if snapshot.State != state {
		test.Fatalf("got %s, want %s: %+v", snapshot.State, state, snapshot.Events)
	}
	return snapshot
}

func TestOrderMatchesAcceptedPreferenceAndRestrictedLast(test *testing.T) {
	for _, sample := range []struct {
		configured      []Candidate
		preferred, hint Candidate
		want            []Candidate
	}{
		{[]Candidate{AWG, TCP}, AWG, TCP, []Candidate{TCP, AWG, Restricted}},
		{[]Candidate{WG, AWG, TCP, AWG}, TCP, "unknown", []Candidate{TCP, WG, AWG, Restricted}},
		{nil, AWG, TCP, []Candidate{Restricted}},
		{[]Candidate{TCP}, AWG, Restricted, []Candidate{TCP, Restricted}},
	} {
		got, failure := Order(sample.configured, sample.preferred, sample.hint)
		if failure != nil || !reflect.DeepEqual(got, sample.want) {
			test.Fatalf("order %v %v, want %v", got, failure, sample.want)
		}
	}
	for _, invalid := range [][]Candidate{{Restricted}, {"shell"}, make([]Candidate, 33)} {
		if _, failure := Order(invalid, "", ""); failure == nil {
			test.Fatal("invalid configured capability accepted")
		}
	}
}

func TestActualHostReadinessAndNoHealthyMigration(test *testing.T) {
	host := newFixture(test)
	host.failures[AWG] = io.EOF
	host.connect(test)
	snapshot := requireState(test, host, Connected)
	if snapshot.Selected != TCP || !snapshot.DesiredConnected || !host.guard.Load() || host.peak != 1 || host.releases.Load() != 0 {
		test.Fatal(snapshot)
	}
	delete(host.failures, AWG)
	host.advance(24 * time.Hour)
	if failure := host.controller.Connect(context.Background(), 2, AWG, ""); !errors.Is(failure, ErrBusy) {
		test.Fatal(failure)
	}
	if !reflect.DeepEqual(host.attempts, []Candidate{AWG, TCP}) || !reflect.DeepEqual(host.remembered, []Candidate{TCP}) {
		test.Fatal(host.attempts, host.remembered)
	}
}

func TestRestrictedOnlyAndFallbackNeverRememberMesh(test *testing.T) {
	for _, restrictedOnly := range []bool{false, true} {
		host := newFixture(test)
		if restrictedOnly {
			host.configured = nil
		}
		host.failures[AWG], host.failures[TCP] = Rejected{Category: Network}, Rejected{Category: TransportUnavailable}
		host.connect(test)
		if snapshot := requireState(test, host, Connected); snapshot.Selected != Restricted {
			test.Fatal(snapshot)
		}
		if len(host.remembered) != 0 || host.peak != 1 {
			test.Fatal(host.remembered, host.peak)
		}
		if restrictedOnly && !reflect.DeepEqual(host.attempts, []Candidate{Restricted}) {
			test.Fatal(host.attempts)
		}
	}
}

func TestTrustAndUnknownErrorsStopFallbackAndKeepGuard(test *testing.T) {
	for _, failure := range []error{Rejected{Category: Auth}, Rejected{Category: Configuration}, Rejected{Category: Internal},
		fmt.Errorf("wrapped: %w", &Rejected{Category: Auth}), errors.New("PRIVATE-TOKEN-NEVER-EXPORT")} {
		test.Run(failure.Error(), func(test *testing.T) {
			host := newFixture(test)
			host.failures[AWG] = failure
			host.connect(test)
			snapshot := requireState(test, host, Failed)
			if !reflect.DeepEqual(host.attempts, []Candidate{AWG}) || !host.guard.Load() || host.active.Load() != 0 || snapshot.DesiredConnected {
				test.Fatal(snapshot, host.attempts)
			}
			for repeat := 0; repeat < 1000; repeat++ {
				_ = host.controller.Retry(1)
				_ = host.controller.Lost(1, Network)
			}
			if len(host.attempts) != 1 {
				test.Fatal("terminal error retried")
			}
			raw, _ := json.Marshal(snapshot)
			if strings.Contains(string(raw), "PRIVATE-TOKEN") {
				test.Fatal("raw error exported")
			}
		})
	}
}

func TestConfigureDenialAndDeadlineCannotStartTransport(test *testing.T) {
	for _, denied := range []bool{true, false} {
		host := newFixture(test)
		if denied {
			host.configureFailure = Rejected{Category: Auth}
		} else {
			host.configureDelay = ConfigureTimeout
		}
		host.connect(test)
		requireState(test, host, Failed)
		if len(host.attempts) != 0 || !host.guard.Load() {
			test.Fatal(host.attempts)
		}
	}
}

func TestOfflineWaitHasNoSpinAndResumesOnNetworkReturn(test *testing.T) {
	host := newFixture(test)
	host.offline = true
	host.connect(test)
	snapshot := requireState(test, host, Restoring)
	if snapshot.RetryAtMS != RecoveryBackoff.Milliseconds() || len(host.attempts) != 0 {
		test.Fatal(snapshot)
	}
	for repeat := 0; repeat < 1000; repeat++ {
		_ = host.controller.Retry(1)
	}
	if host.Now() != 0 || len(host.attempts) != 0 {
		test.Fatal("busy waiting")
	}
	host.offline = false
	host.advance(RecoveryBackoff)
	_ = host.controller.Retry(1)
	requireState(test, host, Connected)
	if !reflect.DeepEqual(host.attempts, []Candidate{AWG}) {
		test.Fatal(host.attempts)
	}
}

func TestOneImmediateRestorationThenBackoffPrefersCurrentNormal(test *testing.T) {
	host := newFixture(test)
	host.failures[AWG] = Rejected{Category: Network}
	host.connect(test)
	delete(host.failures, AWG)
	host.failures[TCP] = Rejected{Category: Network}
	_ = host.controller.Lost(1, Network)
	if requireState(test, host, Connected).Selected != AWG {
		test.Fatal(host.attempts)
	}
	if !reflect.DeepEqual(host.attempts, []Candidate{AWG, TCP, TCP, AWG}) {
		test.Fatal(host.attempts)
	}
	_ = host.controller.Lost(1, Network)
	requireState(test, host, Restoring)
	if len(host.attempts) != 4 || host.active.Load() != 0 || !host.guard.Load() {
		test.Fatal("unbounded immediate recovery")
	}
	host.advance(RecoveryBackoff)
	_ = host.controller.Retry(1)
	requireState(test, host, Connected)
	if host.peak != 1 {
		test.Fatal("overlapping candidates")
	}
}

func TestFailedSeriesAndTemporaryBootstrapCooldown(test *testing.T) {
	for _, bootstrap := range []bool{false, true} {
		host := newFixture(test)
		host.configured = nil
		reason := Rejected{Category: Network}
		delays := []time.Duration{30, 60, 120, 120}
		if bootstrap {
			reason = Rejected{Category: BootstrapUnavailable, TemporaryBootstrap: true}
			delays = []time.Duration{30, 60, 300, 120}
		}
		host.failures[Restricted] = reason
		host.connect(test)
		for _, delay := range delays {
			snapshot := requireState(test, host, Restoring)
			if time.Duration(snapshot.RetryAtMS)*time.Millisecond-host.Now() != delay*time.Second {
				test.Fatal(snapshot, delay, host.Now())
			}
			opens := len(host.attempts)
			host.advance(delay*time.Second - time.Millisecond)
			_ = host.controller.Retry(1)
			if len(host.attempts) != opens {
				test.Fatal("early retry")
			}
			host.advance(time.Millisecond)
			_ = host.controller.Retry(1)
			if len(host.attempts) != opens+1 {
				test.Fatal("retry did not open")
			}
		}
	}
	host := newFixture(test)
	host.configured = nil
	host.failures[Restricted] = Rejected{Category: BootstrapUnavailable}
	host.connect(test)
	requireState(test, host, Failed)
}

func TestJitterClampedAndHealthyStabilityResetsBudget(test *testing.T) {
	host := newFixture(test)
	host.jitter = time.Hour
	host.connect(test)
	_ = host.controller.Lost(1, Network)
	_ = host.controller.Lost(1, Network)
	snapshot := requireState(test, host, Restoring)
	if time.Duration(snapshot.RetryAtMS)*time.Millisecond-host.Now() != 35*time.Second {
		test.Fatal(snapshot)
	}
	host.advance(35 * time.Second)
	_ = host.controller.Retry(1)
	_ = host.controller.Healthy(1, true)
	host.advance(StableTraffic - time.Millisecond)
	_ = host.controller.Healthy(1, true)
	if host.controller.restorations != 1 {
		test.Fatal("stability reset too early")
	}
	_ = host.controller.Healthy(1, false)
	_ = host.controller.Healthy(1, true)
	host.advance(StableTraffic)
	_ = host.controller.Healthy(1, true)
	if host.controller.restorations != 0 || host.controller.failedSeries != 0 {
		test.Fatal("stable traffic did not reset")
	}
	_ = host.controller.Lost(1, Network)
	requireState(test, host, Connected)
}

func TestCancellationDuringEveryOpenAndRememberCannotPublishReady(test *testing.T) {
	for _, candidate := range []Candidate{AWG, TCP, Restricted} {
		host := newFixture(test)
		host.failures[AWG], host.failures[TCP] = Rejected{Category: Network}, Rejected{Category: Network}
		host.cancelCandidate = candidate
		host.connect(test)
		snapshot := requireState(test, host, Disconnected)
		if host.active.Load() != 0 || host.guard.Load() || host.releases.Load() != 1 || count(snapshot, "candidate_succeeded") != 0 {
			test.Fatal(snapshot)
		}
		_ = host.controller.Disconnect(1)
		if host.releases.Load() != 1 {
			test.Fatal("duplicate release")
		}
	}
	host := newFixture(test)
	host.cancelRemember = true
	host.connect(test)
	if count(requireState(test, host, Disconnected), "candidate_succeeded") != 0 {
		test.Fatal("late readiness")
	}
}

func TestCleanupFailureStopsChainAndExplicitDisconnectRetainsGuardOnFailure(test *testing.T) {
	host := newFixture(test)
	host.failures[AWG] = Rejected{Category: Network}
	host.closeFailureWhenActive = true
	host.connect(test)
	requireState(test, host, Failed)
	if !reflect.DeepEqual(host.attempts, []Candidate{AWG}) || !host.guard.Load() {
		test.Fatal(host.attempts)
	}
	host.closeFailureWhenActive = false
	host.releaseFailure = true
	_ = host.controller.Disconnect(1)
	if count(requireState(test, host, Failed), "cleanup_failed") != 1 || !host.guard.Load() {
		test.Fatal("failed cleanup released guard")
	}
	host.releaseFailure = false
	_ = host.controller.Disconnect(1)
	requireState(test, host, Disconnected)
	if host.guard.Load() {
		test.Fatal("successful cleanup retained guard")
	}
}

func TestPerCandidateDeadlinesRejectLateReady(test *testing.T) {
	host := newFixture(test)
	host.openUntilDeadline = true
	host.connect(test)
	snapshot := requireState(test, host, Restoring)
	if count(snapshot, "candidate_succeeded") != 0 || len(host.attempts) != 3 {
		test.Fatal(snapshot)
	}
	if !reflect.DeepEqual(host.deadlines, []time.Duration{20 * time.Second, 42 * time.Second, 246 * time.Second}) {
		test.Fatal(host.deadlines)
	}
	if host.active.Load() != 0 || !host.guard.Load() {
		test.Fatal("late ready retained active path")
	}
}

func TestStaleGenerationCannotCloseOrChangeNewSession(test *testing.T) {
	host := newFixture(test)
	host.connect(test)
	_ = host.controller.Disconnect(1)
	if failure := host.controller.Connect(context.Background(), 2, TCP, TCP); failure != nil {
		test.Fatal(failure)
	}
	for _, failure := range []error{host.controller.Disconnect(1), host.controller.Interrupt(1, Auth), host.controller.Lost(1, Network), host.controller.Retry(1), host.controller.Healthy(1, false)} {
		if !errors.Is(failure, ErrStale) {
			test.Fatal(failure)
		}
	}
	snapshot := requireState(test, host, Connected)
	if snapshot.Selected != TCP || !snapshot.DesiredConnected || host.active.Load() != 1 || host.releases.Load() != 1 {
		test.Fatal(snapshot)
	}
}

func TestBoundedEventsKeepFirstReasonAndDetachedSnapshots(test *testing.T) {
	host := newFixture(test)
	host.configured = nil
	host.failures[Restricted] = Rejected{Category: Network}
	host.connect(test)
	for repeat := 0; repeat < 200; repeat++ {
		snapshot := host.controller.Snapshot()
		host.advance(time.Duration(snapshot.RetryAtMS)*time.Millisecond - host.Now())
		_ = host.controller.Retry(1)
	}
	snapshot := requireState(test, host, Restoring)
	if len(snapshot.Events) != MaxEvents || snapshot.EventsDropped == 0 || snapshot.FirstReason != Network {
		test.Fatal(snapshot)
	}
	snapshot.Events[0].Name = "modified by caller"
	if host.controller.Snapshot().Events[0].Name == snapshot.Events[0].Name {
		test.Fatal("snapshot aliases internal events")
	}
	_ = host.controller.Disconnect(1)
	host.advance(time.Hour)
	before := len(host.attempts)
	_ = host.controller.Retry(1)
	if len(host.attempts) != before {
		test.Fatal("cancelled backoff reopened")
	}
}

func TestConcurrentSnapshotsCancelAndBusyCalls(test *testing.T) {
	host := newFixture(test)
	host.blocked = make(chan struct{})
	finished := make(chan error, 1)
	go func() { finished <- host.controller.Connect(context.Background(), 1, AWG, "") }()
	select {
	case <-host.blocked:
	case <-time.After(3 * time.Second):
		test.Fatal("open did not start")
	}
	var readers sync.WaitGroup
	for reader := 0; reader < 8; reader++ {
		readers.Add(1)
		go func() {
			defer readers.Done()
			for repeat := 0; repeat < 1000; repeat++ {
				_ = host.controller.Snapshot()
			}
		}()
	}
	if failure := host.controller.Retry(1); !errors.Is(failure, ErrBusy) {
		test.Fatal(failure)
	}
	if failure := host.controller.Connect(context.Background(), 2, TCP, ""); !errors.Is(failure, ErrBusy) {
		test.Fatal(failure)
	}
	if failure := host.controller.Disconnect(1); failure != nil {
		test.Fatal(failure)
	}
	if failure := <-finished; failure != nil {
		test.Fatal(failure)
	}
	readers.Wait()
	snapshot := requireState(test, host, Disconnected)
	if count(snapshot, "candidate_succeeded") != 0 || host.releases.Load() != 1 || host.active.Load() != 0 {
		test.Fatal(snapshot)
	}
}

func TestAlreadyCancelledContextDoesNotConfigureOrOpen(test *testing.T) {
	host := newFixture(test)
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if failure := host.controller.Connect(ctx, 1, AWG, ""); failure != nil {
		test.Fatal(failure)
	}
	requireState(test, host, Disconnected)
	if host.configureCalls != 0 || len(host.attempts) != 0 {
		test.Fatal("cancelled connect touched networking")
	}
}

func TestAuthorizationInterruptCancelsPendingHostWithoutFallback(test *testing.T) {
	host := newFixture(test)
	host.blocked = make(chan struct{})
	finished := make(chan error, 1)
	go func() { finished <- host.controller.Connect(context.Background(), 1, AWG, "") }()
	select {
	case <-host.blocked:
	case <-time.After(3 * time.Second):
		test.Fatal("open did not start")
	}
	if failure := host.controller.Interrupt(1, Auth); failure != nil {
		test.Fatal(failure)
	}
	if host.controller.Snapshot().DesiredConnected {
		test.Fatal("revoked intent retained")
	}
	if failure := <-finished; failure != nil {
		test.Fatal(failure)
	}
	snapshot := requireState(test, host, Failed)
	if snapshot.FirstReason != Auth || snapshot.DesiredConnected || !host.guard.Load() || len(host.attempts) != 1 || host.releases.Load() != 0 {
		test.Fatal(snapshot)
	}
	if failure := host.controller.Disconnect(1); failure != nil {
		test.Fatal(failure)
	}
	requireState(test, host, Disconnected)
}

func TestRecoveryTrustFailureAndCancelCannotStartAnotherSeries(test *testing.T) {
	for _, reason := range []Failure{Auth, Configuration, Internal, Cancelled} {
		host := newFixture(test)
		host.configured = nil
		host.connect(test)
		host.failures[Restricted] = Rejected{Category: Network}
		_ = host.controller.Lost(1, Network)
		requireState(test, host, Restoring)
		host.failures[Restricted] = &Rejected{Category: reason}
		host.advance(RecoveryBackoff)
		_ = host.controller.Retry(1)
		state := Failed
		if reason == Cancelled {
			state = Disconnected
		}
		requireState(test, host, state)
		opens := len(host.attempts)
		host.advance(time.Hour)
		_ = host.controller.Retry(1)
		if len(host.attempts) != opens {
			test.Fatal("terminal recovery retried")
		}
	}
}

func TestReferenceParametersAndHostBoundary(test *testing.T) {
	raw, failure := os.ReadFile("../../clients/shared/android106-auto.json")
	if failure != nil {
		test.Fatal(failure)
	}
	var contract struct {
		Schema       int               `json:"schema"`
		Parameters   map[string]int64  `json:"parameters_ms"`
		Bounds       map[string]int    `json:"bounds"`
		Sources      map[string]string `json:"accepted_sources"`
		Requirements []string          `json:"host_requirements"`
		Missing      []string          `json:"not_implemented"`
	}
	if failure := json.Unmarshal(raw, &contract); failure != nil {
		test.Fatal(failure)
	}
	if contract.Schema != 1 || len(contract.Sources) != 6 || len(contract.Requirements) != 8 || len(contract.Missing) != 4 {
		test.Fatal("reference/integration scope changed")
	}
	for name, duration := range map[string]time.Duration{
		"configure": ConfigureTimeout, "normal": NormalTimeout, "restricted": RestrictedTimeout,
		"connect": ConnectTimeout, "recovery_initial": RecoveryBackoff, "recovery_maximum": MaxRecoveryBackoff,
		"bootstrap_cooldown": RecoveryCooldown, "stable_traffic": StableTraffic, "jitter_maximum": 5 * time.Second,
	} {
		if contract.Parameters[name] != duration.Milliseconds() {
			test.Fatal("reference parameter changed", name)
		}
	}
	if contract.Bounds["events"] != MaxEvents || contract.Bounds["immediate_restorations"] != 1 || contract.Bounds["temporary_bootstrap_recoveries"] != 2 {
		test.Fatal("reference budget changed")
	}
	if _, failure := New(nil, time.Second); !errors.Is(failure, ErrInvalid) {
		test.Fatal(failure)
	}
	if _, failure := New(newFixture(test), 0); !errors.Is(failure, ErrInvalid) {
		test.Fatal(failure)
	}
	if _, failure := New(newFixture(test), time.Minute+1); !errors.Is(failure, ErrInvalid) {
		test.Fatal(failure)
	}
}

func TestTLSValidationCannotBecomeNetworkFallbackThroughURLWrapper(test *testing.T) {
	certificate := &x509.Certificate{}
	for _, cause := range []error{
		x509.UnknownAuthorityError{Cert: certificate},
		&x509.UnknownAuthorityError{Cert: certificate},
		x509.HostnameError{Certificate: certificate, Host: "private.test.invalid"},
		&x509.HostnameError{Certificate: certificate, Host: "private.test.invalid"},
		x509.CertificateInvalidError{Cert: certificate, Reason: x509.Expired},
		&x509.CertificateInvalidError{Cert: certificate, Reason: x509.Expired},
		&tls.CertificateVerificationError{Err: errors.New("PRIVATE-VALIDATION-DETAIL")},
		tls.RecordHeaderError{Msg: "PRIVATE-TLS-DETAIL"},
		&tls.RecordHeaderError{Msg: "PRIVATE-TLS-DETAIL"},
	} {
		host := newFixture(test)
		host.failures[AWG] = &url.Error{Op: "Post", URL: "https://private.test.invalid/proof", Err: cause}
		host.connect(test)
		snapshot := requireState(test, host, Failed)
		if snapshot.FirstReason != Auth && snapshot.FirstReason != Configuration {
			test.Fatal("certificate failure became retryable", snapshot.FirstReason)
		}
		if len(host.attempts) != 1 || !host.guard.Load() || snapshot.DesiredConnected {
			test.Fatal("trust failure fell back")
		}
		raw, _ := json.Marshal(snapshot)
		if strings.Contains(string(raw), "private.test") || strings.Contains(string(raw), "PRIVATE-") {
			test.Fatal("validation detail exported")
		}
	}
}
