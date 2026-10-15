package roombroker

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"os"
	"path/filepath"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
)

type controlledLeaseClock struct {
	mu             sync.Mutex
	current, until time.Time
	callback       func()
	stopped        bool
}

func (clock *controlledLeaseClock) Now() time.Time {
	clock.mu.Lock()
	defer clock.mu.Unlock()
	return clock.current
}
func (clock *controlledLeaseClock) After(delay time.Duration, callback func()) leaseTimer {
	clock.mu.Lock()
	defer clock.mu.Unlock()
	clock.until, clock.callback = clock.current.Add(delay), callback
	return clock
}
func (clock *controlledLeaseClock) Stop() bool {
	clock.mu.Lock()
	defer clock.mu.Unlock()
	active := !clock.stopped
	clock.stopped = true
	return active
}
func (clock *controlledLeaseClock) Reset(delay time.Duration) bool {
	clock.mu.Lock()
	defer clock.mu.Unlock()
	active := !clock.stopped
	clock.until, clock.stopped = clock.current.Add(delay), false
	return active
}
func (clock *controlledLeaseClock) Advance(delay time.Duration) {
	clock.mu.Lock()
	clock.current = clock.current.Add(delay)
	var callback func()
	if !clock.stopped && !clock.current.Before(clock.until) {
		callback, clock.stopped = clock.callback, true
	}
	clock.mu.Unlock()
	if callback != nil {
		callback()
	}
}

type leaseMuxFixture struct {
	ctx            context.Context
	broker         *Broker
	clock          *controlledLeaseClock
	client, server *tcpforward.Mux
	secured        *familysession.Session
	id             string
	path           string
	port           int
	accepted       *atomic.Int32
}

func newLeaseMuxFixture(test *testing.T, support bool, securityLifetime ...time.Duration) *leaseMuxFixture {
	test.Helper()
	directory := os.Getenv("FC_FAMILY_TEST_FIXTURES")
	if directory == "" {
		test.Skip("requires disposable ProductStore profiles")
	}
	clientRaw, err := os.ReadFile(filepath.Join(directory, "valid.json"))
	if err != nil {
		test.Fatal(err)
	}
	serverRaw, err := os.ReadFile(filepath.Join(directory, "gateway.json"))
	if err != nil {
		test.Fatal(err)
	}
	path := filepath.Join(test.TempDir(), "gateway.json")
	if err := os.WriteFile(path, serverRaw, 0600); err != nil {
		test.Fatal(err)
	}
	var credentials familysession.Credentials
	if json.Unmarshal(clientRaw, &credentials) != nil {
		test.Fatal("fixture credentials")
	}
	certificate, err := tls.X509KeyPair([]byte(credentials.Certificate), []byte(credentials.PrivateKey))
	if err != nil {
		test.Fatal(err)
	}
	config, _, err := familysession.Configuration(clientRaw, false)
	if err != nil {
		test.Fatal(err)
	}
	identity := Identity{Family: credentials.Family, Device: config.Certificates[0].Leaf.Subject.SerialNumber}
	copy(identity.PublicKey[:], certificate.PrivateKey.(ed25519.PrivateKey).Public().(ed25519.PublicKey))
	authorize := func(context.Context) (Identity, error) { return identity, nil }
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	test.Cleanup(cancel)
	listener, err := net.Listen("tcp4", "127.0.0.1:0")
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() { listener.Close() })
	fixture := &leaseMuxFixture{ctx: ctx, clock: &controlledLeaseClock{current: time.Now()}, path: path, port: listener.Addr().(*net.TCPAddr).Port, accepted: new(atomic.Int32)}
	go func() {
		for {
			connection, err := listener.Accept()
			if err != nil {
				return
			}
			fixture.accepted.Add(1)
			go func() { defer connection.Close(); _, _ = io.Copy(connection, connection) }()
		}
	}()
	incoming, outgoing := make(chan []byte, 256), make(chan []byte, 256)
	stopped, once := make(chan struct{}), new(sync.Once)
	clientPipe, serverPipe := packets{incoming, outgoing, stopped, once}, packets{outgoing, incoming, stopped, once}
	test.Cleanup(func() { clientPipe.Close() })
	ready := make(chan struct{})
	broker, err := New(providerFunc(fresh), gatewayFunc(func(lifetime, _ context.Context, _ Room, identifier string, identity Identity) (Gateway, error) {
		return &fakeGateway{run: func(ctx context.Context, active func() error) error {
			secured, err := familysession.Open(ctx, serverPipe, serverRaw, true)
			if err != nil {
				return err
			}
			defer secured.Close()
			if err := bindGateway(ctx, secured, identifier, identity, active); err != nil {
				return err
			}
			config := tcpforward.MuxConfig{MaxStreams: 32, Policy: tcpforward.Policy{TestOnlyLoopbackPort: fixture.port}}
			if support {
				bound := secured.SecurityDeadline()
				if len(securityLifetime) > 0 {
					bound = fixture.clock.Now().Add(securityLifetime[0])
				}
				config.LeaseRenewal = ctx.Value(leaseKey{}).(*leaseBinding).handler(SessionAuthorizer(path, secured.ConnectionState()), bound)
			}
			mux, err := tcpforward.NewMux(ctx, secured, true, config)
			if err != nil {
				return err
			}
			defer mux.Close()
			fixture.server, fixture.secured = mux, secured
			close(ready)
			return mux.Wait()
		}}, nil
	}), DefaultLimits(), nil)
	if err != nil {
		test.Fatal(err)
	}
	fixture.broker = broker
	broker.newLease = func(duration time.Duration) *leaseLifetime {
		return newLeaseWithClock(duration, fixture.clock.Now, fixture.clock.After)
	}
	test.Cleanup(broker.Close)
	identifier, err := broker.Challenge(ctx, authorize)
	if err != nil {
		test.Fatal(err)
	}
	fixture.id = identifier
	descriptor, err := broker.Create(ctx, identifier, authorize)
	if err != nil {
		test.Fatal(err)
	}
	if err := broker.Claim(ctx, identifier, authorize); err != nil {
		test.Fatal(err)
	}
	secured, err := familysession.Open(ctx, clientPipe, clientRaw, false)
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() { secured.Close() })
	if err := BindClient(ctx, secured, descriptor, clientRaw); err != nil {
		test.Fatal(err)
	}
	client, err := tcpforward.NewMux(ctx, secured, false, tcpforward.MuxConfig{MaxStreams: 32})
	if err != nil {
		test.Fatal(err)
	}
	fixture.client = client
	test.Cleanup(func() { client.Close() })
	select {
	case <-ready:
	case <-ctx.Done():
		test.Fatal("server mux startup")
	}
	return fixture
}

func (fixture *leaseMuxFixture) data(test *testing.T, stream *tcpforward.MuxStream, sequence int) {
	test.Helper()
	payload := []byte(fmt.Sprintf("persistent-connection-sequence-%04d", sequence))
	if _, err := stream.Write(payload); err != nil {
		test.Fatal(err)
	}
	received := make([]byte, len(payload))
	if _, err := io.ReadFull(stream, received); err != nil {
		test.Fatal(err)
	}
	if !bytes.Equal(payload, received) || fixture.accepted.Load() != 1 || fixture.server.Stats().ActiveSockets != 1 {
		test.Fatal("payload mismatch or replacement TCP connection")
	}
	test.Logf("sequence=%d lease_clock=%s same_mux_stream=%p accepted_tcp=1", sequence, fixture.clock.Now().Format(time.RFC3339Nano), stream)
}

func TestLeaseRealFamilyMuxPersistentTCP(test *testing.T) {
	fixture := newLeaseMuxFixture(test, true)
	stream, err := fixture.client.OpenTCP(fixture.ctx, tcpforward.OpenRequest{Host: "127.0.0.1", Port: fixture.port})
	if err != nil {
		test.Fatal(err)
	}
	defer stream.Reset()
	known, _, err := exchangeLease(fixture.ctx, fixture.client, fixture.id, LeaseReceipt{}, false)
	if err != nil {
		test.Fatal(err)
	}
	fixture.data(test, stream, 0)
	fixture.clock.Advance(8 * time.Minute)
	known, _, err = exchangeLease(fixture.ctx, fixture.client, fixture.id, known, true)
	if err != nil || known.Sequence != 1 {
		test.Fatalf("first renewal %v %+v", err, known)
	}
	fixture.clock.Advance(2 * time.Minute)
	fixture.data(test, stream, 1)
	fixture.clock.Advance(6 * time.Minute)
	known, _, err = exchangeLease(fixture.ctx, fixture.client, fixture.id, known, true)
	if err != nil || known.Sequence != 2 {
		test.Fatalf("second renewal %v %+v", err, known)
	}
	fixture.clock.Advance(4 * time.Minute)
	fixture.data(test, stream, 2)
	fixture.clock.Advance(2 * time.Minute)
	fixture.data(test, stream, 3)
	fixture.broker.mu.Lock()
	count := len(fixture.broker.setups)
	fixture.broker.unlock()
	if count != 1 {
		test.Fatal("renewal changed admission ownership")
	}
	fixture.clock.Advance(4 * time.Minute)
	waitEmpty(test, fixture.broker)
	if fixture.server.Stats().ActiveSockets != 0 {
		test.Fatal("expiry leaked TCP socket")
	}
}

func TestLeaseLegacyClientAndServer(test *testing.T) {
	for _, support := range []bool{false, true} {
		test.Run(fmt.Sprint(support), func(test *testing.T) {
			fixture := newLeaseMuxFixture(test, support)
			if !support {
				_, _, err := exchangeLease(fixture.ctx, fixture.client, fixture.id, LeaseReceipt{}, false)
				if failure, ok := err.(*tcpforward.OpenError); !ok || failure.Code != "policy_rejected" {
					test.Fatalf("old server compatibility: %v", err)
				}
			}
			fixture.clock.Advance(10 * time.Minute)
			waitEmpty(test, fixture.broker)
			if fixture.server.Stats().ActiveSockets != 0 {
				test.Fatal("legacy expiry leaked sockets")
			}
		})
	}
}

func TestLeaseControlRevalidatesAdmission(test *testing.T) {
	fixture := newLeaseMuxFixture(test, true)
	known, _, err := exchangeLease(fixture.ctx, fixture.client, fixture.id, LeaseReceipt{}, false)
	if err != nil {
		test.Fatal(err)
	}
	fixture.clock.Advance(8 * time.Minute)
	raw, err := os.ReadFile(fixture.path)
	if err != nil {
		test.Fatal(err)
	}
	var credentials familysession.Credentials
	if json.Unmarshal(raw, &credentials) != nil {
		test.Fatal("fixture")
	}
	credentials.MinimumCRL = 99999
	raw, err = json.Marshal(credentials)
	if err != nil {
		test.Fatal(err)
	}
	if err := os.WriteFile(fixture.path, raw, 0600); err != nil {
		test.Fatal(err)
	}
	if _, _, err := exchangeLease(fixture.ctx, fixture.client, fixture.id, known, true); err != Code("unauthorized") {
		test.Fatalf("stale floor admitted: %v", err)
	}
	fixture.broker.mu.Lock()
	sequence := fixture.broker.setups[fixture.id].renewal
	fixture.broker.unlock()
	if sequence != 0 {
		test.Fatal("rejected admission extended lease")
	}
}

func TestLeaseLostResponseReconciliation(test *testing.T) {
	fixture := newLeaseMuxFixture(test, true)
	known, _, err := exchangeLease(fixture.ctx, fixture.client, fixture.id, LeaseReceipt{}, false)
	if err != nil {
		test.Fatal(err)
	}
	fixture.clock.Advance(8 * time.Minute)
	stream, err := fixture.client.OpenTCP(fixture.ctx, tcpforward.OpenRequest{Host: tcpforward.LeaseRenewalHost, Port: 1})
	if err != nil {
		test.Fatal(err)
	}
	decoder := leaseReader(stream)
	var offer leaseMessage
	if err := decoder.Decode(&offer); err != nil {
		test.Fatal(err)
	}
	request := offer.Lease
	request.Sequence++
	if err := json.NewEncoder(stream).Encode(leaseMessage{Type: "renew", Lease: request}); err != nil {
		test.Fatal(err)
	}
	var lost leaseMessage
	if err := decoder.Decode(&lost); err != nil || lost.Type != "accepted" {
		test.Fatal("server did not accept renewal before response loss")
	}
	stream.Reset()
	fixture.clock.Advance(time.Second)
	reconciled, _, err := exchangeLease(fixture.ctx, fixture.client, fixture.id, known, true)
	if err != nil || reconciled.Sequence != 1 || !reconciled.ExpiresAt.Equal(lost.Lease.ExpiresAt) {
		test.Fatalf("response reconciliation extended twice: %v %+v", err, reconciled)
	}
}

func TestLeaseControlStopsAtSecurityLimit(test *testing.T) {
	fixture := newLeaseMuxFixture(test, true, 10*time.Minute)
	known, _, err := exchangeLease(fixture.ctx, fixture.client, fixture.id, LeaseReceipt{}, false)
	if err != nil {
		test.Fatal(err)
	}
	fixture.clock.Advance(8 * time.Minute)
	limited, _, err := exchangeLease(fixture.ctx, fixture.client, fixture.id, known, true)
	if err != nil || limited.Sequence != known.Sequence || !limited.ExpiresAt.Equal(known.ExpiresAt) {
		test.Fatalf("hard limit extended or authorization falsely rejected: %v", err)
	}
	fixture.clock.Advance(2 * time.Minute)
	waitEmpty(test, fixture.broker)
}

func TestLeaseControlRevocationBeforeConfirmation(test *testing.T) {
	fixture := newLeaseMuxFixture(test, true)
	stream, err := fixture.client.OpenTCP(fixture.ctx, tcpforward.OpenRequest{Host: tcpforward.LeaseRenewalHost, Port: 1})
	if err != nil {
		test.Fatal(err)
	}
	defer stream.Reset()
	decoder := leaseReader(stream)
	var offer leaseMessage
	if err := decoder.Decode(&offer); err != nil {
		test.Fatal(err)
	}
	raw, err := os.ReadFile(fixture.path)
	if err != nil {
		test.Fatal(err)
	}
	var credentials familysession.Credentials
	if json.Unmarshal(raw, &credentials) != nil {
		test.Fatal("fixture")
	}
	credentials.MinimumCRL = 99999
	raw, err = json.Marshal(credentials)
	if err != nil {
		test.Fatal(err)
	}
	if err := os.WriteFile(fixture.path, raw, 0600); err != nil {
		test.Fatal(err)
	}
	if err := json.NewEncoder(stream).Encode(leaseMessage{Type: "applied", Lease: offer.Lease}); err != nil {
		test.Fatal(err)
	}
	var reply leaseMessage
	if err := decoder.Decode(&reply); err != nil || reply.Type != "denied" {
		test.Fatalf("revocation disguised as transient confirmation loss: %v %s", err, reply.Type)
	}
}
