package familysession

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"errors"
	"math/big"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"
)

type endpoint struct {
	incoming  chan []byte
	outgoing  chan []byte
	closed    chan struct{}
	once      sync.Once
	transform func([]byte) []byte
}

func (point *endpoint) SendContext(ctx context.Context, payload []byte) error {
	copyPayload := bytes.Clone(payload)
	if point.transform != nil {
		copyPayload = point.transform(copyPayload)
	}
	select {
	case point.outgoing <- copyPayload:
		return nil
	case <-point.closed:
		return errors.New("closed")
	case <-ctx.Done():
		return ctx.Err()
	}
}

func (point *endpoint) Recv(ctx context.Context) ([]byte, error) {
	select {
	case payload := <-point.incoming:
		return payload, nil
	case <-point.closed:
		return nil, errors.New("closed")
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}

func (point *endpoint) Close() error { point.once.Do(func() { close(point.closed) }); return nil }

func pair() (*endpoint, *endpoint) {
	forward, reverse := make(chan []byte, 16), make(chan []byte, 16)
	return &endpoint{incoming: reverse, outgoing: forward, closed: make(chan struct{})}, &endpoint{incoming: forward, outgoing: reverse, closed: make(chan struct{})}
}

func profiles(t *testing.T) (Credentials, Credentials) {
	return profilesWithExpiry(t, time.Now().Add(time.Hour))
}

func profilesWithExpiry(t *testing.T, expiry time.Time) (Credentials, Credentials) {
	t.Helper()
	now := time.Now()
	_, authorityKey, _ := ed25519.GenerateKey(rand.Reader)
	rootTemplate := &x509.Certificate{SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: "test CA"}, NotBefore: now.Add(-time.Hour), NotAfter: now.Add(time.Hour), IsCA: true, BasicConstraintsValid: true, KeyUsage: x509.KeyUsageCertSign | x509.KeyUsageCRLSign}
	rootDER, err := x509.CreateCertificate(rand.Reader, rootTemplate, rootTemplate, authorityKey.Public(), authorityKey)
	if err != nil {
		t.Fatal(err)
	}
	root, _ := x509.ParseCertificate(rootDER)
	crlDER, err := x509.CreateRevocationList(rand.Reader, &x509.RevocationList{Number: big.NewInt(2), ThisUpdate: now.Add(-time.Minute), NextUpdate: now.Add(time.Hour)}, root, authorityKey)
	if err != nil {
		t.Fatal(err)
	}
	create := func(role string, serial int64) Credentials {
		public, key, _ := ed25519.GenerateKey(rand.Reader)
		identity := make([]byte, 64)
		rand.Read(identity[:32])
		copy(identity[32:], public)
		reference := sha256.Sum256(identity)
		uri, _ := url.Parse("urn:family-connect:identity:" + hex.EncodeToString(identity))
		usage := x509.ExtKeyUsageClientAuth
		if role == "gateway" {
			usage = x509.ExtKeyUsageServerAuth
		}
		template := &x509.Certificate{SerialNumber: big.NewInt(serial), Subject: pkix.Name{SerialNumber: hex.EncodeToString(reference[:16]), OrganizationalUnit: []string{"protocol=" + Protocol, "family=" + strings.Repeat("a", 32), "role=" + role, "revision=1"}}, NotBefore: now.Add(-time.Minute), NotAfter: expiry, ExtKeyUsage: []x509.ExtKeyUsage{usage}, DNSNames: []string{"gateway.family-connect.test"}, URIs: []*url.URL{uri}}
		der, err := x509.CreateCertificate(rand.Reader, template, root, public, authorityKey)
		if err != nil {
			t.Fatal(err)
		}
		privateDER, _ := x509.MarshalPKCS8PrivateKey(key)
		return Credentials{Certificate: string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})), PrivateKey: string(pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: privateDER})), Authority: string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: rootDER})), Revocations: string(pem.EncodeToMemory(&pem.Block{Type: "X509 CRL", Bytes: crlDER})), Family: strings.Repeat("a", 32), Gateway: hex.EncodeToString(reference[:16]), MinimumRevision: 1, MinimumCRL: 2}
	}
	client, server := create("device", 2), create("gateway", 3)
	client.Gateway = server.Gateway
	return client, server
}

func encoded(credentials Credentials) []byte { raw, _ := json.Marshal(credentials); return raw }

func connect(t *testing.T, ctx context.Context, clientProfile, serverProfile Credentials) (*Session, *Session) {
	t.Helper()
	clientEndpoint, serverEndpoint := pair()
	serverReady := make(chan *Session, 1)
	serverError := make(chan error, 1)
	go func() {
		session, err := Open(ctx, serverEndpoint, encoded(serverProfile), true)
		serverReady <- session
		serverError <- err
	}()
	client, err := Open(ctx, clientEndpoint, encoded(clientProfile), false)
	if err != nil {
		t.Fatal(err)
	}
	server := <-serverReady
	if err := <-serverError; err != nil {
		client.Close()
		t.Fatal(err)
	}
	t.Cleanup(func() { client.Close(); server.Close() })
	return client, server
}

func TestCanonicalMatrixAndCancellation(t *testing.T) {
	clientProfile, serverProfile := profiles(t)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	client, server := connect(t, ctx, clientProfile, serverProfile)
	completed := make(chan error, 1)
	go func() {
		for {
			payload, err := server.Recv(ctx)
			if err == nil {
				err = server.SendContext(ctx, payload)
			}
			if err != nil {
				completed <- err
				return
			}
		}
	}()
	sizes := []int{1, 32, 256, 1024, 4096, 16384, 65536}
	for repeat := 0; repeat < 100; repeat++ {
		sizes = append(sizes, 1024, 16384)
	}
	for _, size := range sizes {
		payload := make([]byte, size)
		rand.Read(payload)
		if err := client.SendContext(ctx, payload); err != nil {
			t.Fatal(err)
		}
		echoed, err := client.Recv(ctx)
		if err != nil || !bytes.Equal(echoed, payload) {
			t.Fatal("exact echo failed", size, err)
		}
	}
	cancel()
	select {
	case <-completed:
	case <-time.After(time.Second):
		t.Fatal("cancellation stuck")
	}
}

func TestAdmissionFailures(t *testing.T) {
	for _, fault := range []string{"wrong-family", "stale-revision", "wrong-gateway", "unknown-authority", "stale-crl", "bad-crl", "bad-key", "role", "expired-certificate"} {
		t.Run(fault, func(t *testing.T) {
			client, server := profiles(t)
			switch fault {
			case "expired-certificate":
				client, server = profilesWithExpiry(t, time.Now().Add(-time.Second))
			case "wrong-family":
				server.Family = strings.Repeat("b", 32)
			case "stale-revision":
				server.MinimumRevision = 2
			case "wrong-gateway":
				client.Gateway = strings.Repeat("0", 32)
			case "unknown-authority":
				other, _ := profiles(t)
				server.Authority = other.Authority
				server.Revocations = other.Revocations
			case "stale-crl":
				server.MinimumCRL = 3
			case "bad-crl":
				server.Revocations = "invalid"
			case "bad-key":
				server.PrivateKey = client.PrivateKey
			case "role":
				client.Certificate = server.Certificate
				client.PrivateKey = server.PrivateKey
			}
			ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
			defer cancel()
			clientEndpoint, serverEndpoint := pair()
			results := make(chan error, 2)
			go func() {
				connection, err := Open(ctx, serverEndpoint, encoded(server), true)
				if connection != nil {
					connection.Close()
				}
				results <- err
			}()
			connection, clientErr := Open(ctx, clientEndpoint, encoded(client), false)
			if connection != nil {
				connection.Close()
			}
			serverErr := <-results
			clientEndpoint.Close()
			serverEndpoint.Close()
			if clientErr == nil && serverErr == nil {
				t.Fatal("unauthorized session accepted")
			}
		})
	}
}

func TestExpiredLeaseAndBounds(t *testing.T) {
	for _, fault := range []string{"expired", "oversized", "repeated-sequence", "cancel-read", "deadline-read"} {
		t.Run(fault, func(t *testing.T) {
			clientProfile, serverProfile := profiles(t)
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			client, server := connect(t, ctx, clientProfile, serverProfile)
			switch fault {
			case "expired":
				client.expiry = time.Now().Add(-time.Second)
				if client.SendContext(ctx, []byte{1}) == nil {
					t.Fatal("expired send")
				}
			case "oversized":
				if client.SendContext(ctx, make([]byte, MaxPayload+1)) == nil {
					t.Fatal("oversized send")
				}
			case "repeated-sequence":
				if err := client.SendContext(ctx, []byte{1}); err != nil {
					t.Fatal(err)
				}
				if _, err := server.Recv(ctx); err != nil {
					t.Fatal(err)
				}
				client.sendSequence = 0
				if err := client.SendContext(ctx, []byte{2}); err != nil {
					t.Fatal(err)
				}
				if _, err := server.Recv(ctx); err == nil {
					t.Fatal("replayed sequence")
				}
			case "cancel-read", "deadline-read":
				request, stop := context.WithTimeout(ctx, 20*time.Millisecond)
				defer stop()
				if fault == "cancel-read" {
					time.AfterFunc(5*time.Millisecond, stop)
				}
				if _, err := client.Recv(request); err == nil {
					t.Fatal("blocked read accepted")
				}
			}
		})
	}
}

func TestTLSRecordReplayRejected(t *testing.T) {
	clientProfile, serverProfile := profiles(t)
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	clientEndpoint, serverEndpoint := pair()
	var saved []byte
	var lock sync.Mutex
	replay := false
	clientEndpoint.transform = func(payload []byte) []byte {
		lock.Lock()
		defer lock.Unlock()
		if replay {
			return bytes.Clone(saved)
		}
		saved = bytes.Clone(payload)
		return payload
	}
	ready := make(chan *Session, 1)
	go func() { connection, _ := Open(ctx, serverEndpoint, encoded(serverProfile), true); ready <- connection }()
	client, err := Open(ctx, clientEndpoint, encoded(clientProfile), false)
	if err != nil {
		t.Fatal(err)
	}
	defer client.Close()
	server := <-ready
	if server == nil {
		t.Fatal("server handshake")
	}
	defer server.Close()
	if err := client.SendContext(ctx, []byte{1, 2, 3}); err != nil {
		t.Fatal(err)
	}
	if _, err := server.Recv(ctx); err != nil {
		t.Fatal(err)
	}
	lock.Lock()
	replay = true
	lock.Unlock()
	client.SendContext(ctx, []byte{4, 5, 6})
	if _, err := server.Recv(ctx); err == nil {
		t.Fatal("replayed TLS ciphertext accepted")
	}
}

func TestProductStoreFixtures(t *testing.T) {
	directory := os.Getenv("FC_FAMILY_TEST_FIXTURES")
	if directory == "" {
		t.Skip("disposable ProductStore fixture integration is opt-in")
	}
	read := func(name string) Credentials {
		raw, err := os.ReadFile(filepath.Join(directory, name+".json"))
		if err != nil {
			t.Fatal("fixture unavailable")
		}
		var value Credentials
		if json.Unmarshal(raw, &value) != nil {
			t.Fatal("fixture invalid")
		}
		return value
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	client, server := connect(t, ctx, read("valid"), read("gateway"))
	client.SendContext(ctx, []byte{0, 1, 2})
	if received, err := server.Recv(ctx); err != nil || !bytes.Equal(received, []byte{0, 1, 2}) {
		t.Fatal("existing identity binding failed")
	}
	for _, name := range []string{"wrong-family", "revoked"} {
		config, _, err := Configuration(encoded(read("gateway")), true)
		if err != nil {
			t.Fatal(err)
		}
		certificate, _ := tls.X509KeyPair([]byte(read(name).Certificate), []byte(read(name).PrivateKey))
		peer, _ := x509.ParseCertificate(certificate.Certificate[0])
		state := tls.ConnectionState{Version: tls.VersionTLS13, NegotiatedProtocol: Protocol, PeerCertificates: []*x509.Certificate{peer}, VerifiedChains: [][]*x509.Certificate{{peer}}}
		if config.VerifyConnection(state) == nil {
			t.Fatal("ProductStore fixture accepted", name)
		}
	}
}

func TestHandshakeProofReplayRejected(t *testing.T) {
	clientProfile, serverProfile := profiles(t)
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	clientEndpoint, serverEndpoint := pair()
	var transcript [][]byte
	var lock sync.Mutex
	clientEndpoint.transform = func(payload []byte) []byte {
		lock.Lock()
		transcript = append(transcript, bytes.Clone(payload))
		lock.Unlock()
		return payload
	}
	ready := make(chan *Session, 1)
	go func() { connection, _ := Open(ctx, serverEndpoint, encoded(serverProfile), true); ready <- connection }()
	client, err := Open(ctx, clientEndpoint, encoded(clientProfile), false)
	if err != nil {
		t.Fatal(err)
	}
	server := <-ready
	if server == nil {
		t.Fatal("initial handshake failed")
	}
	lock.Lock()
	captured := append([][]byte(nil), transcript...)
	lock.Unlock()
	client.Close()
	server.Close()
	if len(captured) < 2 {
		t.Fatal("full client proof not captured")
	}
	attacker, freshEndpoint := pair()
	defer attacker.Close()
	result := make(chan error, 1)
	go func() {
		session, err := Open(ctx, freshEndpoint, encoded(serverProfile), true)
		if session != nil {
			session.Close()
		}
		result <- err
	}()
	for _, record := range captured {
		if err := attacker.SendContext(ctx, record); err != nil {
			t.Fatal(err)
		}
	}
	select {
	case err := <-result:
		if err == nil {
			t.Fatal("old handshake proof accepted for a fresh server transcript")
		}
	case <-ctx.Done():
		t.Fatal("replay was not rejected before the deadline")
	}
}
