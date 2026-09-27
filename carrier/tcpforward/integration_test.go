package tcpforward

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"io"
	"math/big"
	"net"
	"net/url"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/reliablestream"
)

type lossyEndpoint struct {
	incoming chan []byte
	outgoing chan []byte
	closed   chan struct{}
	once     *sync.Once
	armed    atomic.Bool
	seen     map[uint64]int
}

func (endpoint *lossyEndpoint) Close() error {
	endpoint.once.Do(func() { close(endpoint.closed) })
	return nil
}
func (endpoint *lossyEndpoint) SendContext(ctx context.Context, payload []byte) error {
	repeat := false
	if endpoint.armed.Load() && len(payload) >= reliablestream.HeaderSize && payload[4] == 2 {
		sequence := binary.BigEndian.Uint64(payload[40:])
		endpoint.seen[sequence]++
		if endpoint.seen[sequence] == 1 && sequence%7 == 0 {
			return nil
		}
		repeat = sequence%3 == 0
	}
	for attempt := 0; attempt < 1+boolInt(repeat); attempt++ {
		select {
		case endpoint.outgoing <- bytes.Clone(payload):
		case <-ctx.Done():
			return ctx.Err()
		case <-endpoint.closed:
			return io.ErrClosedPipe
		}
	}
	return nil
}
func boolInt(value bool) int {
	if value {
		return 1
	}
	return 0
}
func (endpoint *lossyEndpoint) Recv(ctx context.Context) ([]byte, error) {
	select {
	case payload := <-endpoint.incoming:
		return payload, nil
	case <-ctx.Done():
		return nil, ctx.Err()
	case <-endpoint.closed:
		return nil, io.ErrClosedPipe
	}
}

func testCredentials(test *testing.T) ([]byte, []byte) {
	test.Helper()
	now := time.Now()
	_, authorityKey, _ := ed25519.GenerateKey(rand.Reader)
	root := &x509.Certificate{SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: "TCP test authority"}, NotBefore: now.Add(-time.Minute), NotAfter: now.Add(time.Hour), IsCA: true, BasicConstraintsValid: true, KeyUsage: x509.KeyUsageCertSign | x509.KeyUsageCRLSign}
	rootDER, err := x509.CreateCertificate(rand.Reader, root, root, authorityKey.Public(), authorityKey)
	if err != nil {
		test.Fatal(err)
	}
	root, err = x509.ParseCertificate(rootDER)
	if err != nil {
		test.Fatal(err)
	}
	crl, err := x509.CreateRevocationList(rand.Reader, &x509.RevocationList{Number: big.NewInt(1), ThisUpdate: now.Add(-time.Minute), NextUpdate: now.Add(time.Hour)}, root, authorityKey)
	if err != nil {
		test.Fatal(err)
	}
	create := func(role string, serial int64) familysession.Credentials {
		public, private, _ := ed25519.GenerateKey(rand.Reader)
		identity := make([]byte, 64)
		rand.Read(identity[:32])
		copy(identity[32:], public)
		reference := sha256.Sum256(identity)
		uri, _ := url.Parse("urn:family-connect:identity:" + hex.EncodeToString(identity))
		usage := x509.ExtKeyUsageClientAuth
		if role == "gateway" {
			usage = x509.ExtKeyUsageServerAuth
		}
		certificate := &x509.Certificate{SerialNumber: big.NewInt(serial), Subject: pkix.Name{SerialNumber: hex.EncodeToString(reference[:16]), OrganizationalUnit: []string{"protocol=" + familysession.Protocol, "family=" + strings.Repeat("a", 32), "role=" + role, "revision=1"}}, NotBefore: now.Add(-time.Minute), NotAfter: now.Add(time.Hour), ExtKeyUsage: []x509.ExtKeyUsage{usage}, DNSNames: []string{"gateway.family-connect.test"}, URIs: []*url.URL{uri}}
		der, err := x509.CreateCertificate(rand.Reader, certificate, root, public, authorityKey)
		if err != nil {
			test.Fatal(err)
		}
		key, _ := x509.MarshalPKCS8PrivateKey(private)
		return familysession.Credentials{Certificate: string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})), PrivateKey: string(pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: key})), Authority: string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: rootDER})), Revocations: string(pem.EncodeToMemory(&pem.Block{Type: "X509 CRL", Bytes: crl})), Family: strings.Repeat("a", 32), Gateway: hex.EncodeToString(reference[:16]), MinimumRevision: 1, MinimumCRL: 1}
	}
	client, server := create("device", 2), create("gateway", 3)
	client.Gateway = server.Gateway
	clientJSON, _ := json.Marshal(client)
	serverJSON, _ := json.Marshal(server)
	return clientJSON, serverJSON
}

func authenticatedPair(test *testing.T, ctx context.Context) (*familysession.Session, *familysession.Session) {
	test.Helper()
	clientJSON, serverJSON := testCredentials(test)
	forward, reverse, closed := make(chan []byte, 64), make(chan []byte, 64), make(chan struct{})
	once := &sync.Once{}
	left := &lossyEndpoint{incoming: reverse, outgoing: forward, closed: closed, once: once, seen: make(map[uint64]int)}
	right := &lossyEndpoint{incoming: forward, outgoing: reverse, closed: closed, once: once, seen: make(map[uint64]int)}
	config := reliablestream.DefaultConfig()
	config.RTO = 30 * time.Millisecond
	type readyResult struct {
		session *familysession.Session
		err     error
	}
	ready := make(chan readyResult, 1)
	go func() {
		session, err := familysession.OpenReliable(ctx, right, serverJSON, true, config)
		ready <- readyResult{session, err}
	}()
	client, err := familysession.OpenReliable(ctx, left, clientJSON, false, config)
	if err != nil {
		test.Fatal(err)
	}
	server := <-ready
	if server.err != nil {
		test.Fatal(server.err)
	}
	test.Cleanup(func() { client.Close(); server.session.Close() })
	left.armed.Store(true)
	right.armed.Store(true)
	return client, server.session
}

func TestAuthenticatedReliableTCPNoDuplicateBytes(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	client, server := authenticatedPair(test, ctx)
	if client.ClaimTCP(true) == nil || server.ClaimTCP(false) == nil {
		test.Fatal("role boundary lost")
	}
	var targetBytes bytes.Buffer
	targetDone := make(chan struct{})
	port := startFixture(test, func(connection *net.TCPConn) {
		defer close(targetDone)
		io.Copy(io.MultiWriter(connection, &targetBytes), connection)
		connection.CloseWrite()
	})
	metrics := &Metrics{}
	done := make(chan error, 1)
	go func() { done <- Serve(ctx, server, Policy{TestOnlyLoopbackPort: port}, metrics) }()
	stream, err := OpenTCP(ctx, client, OpenRequest{Host: "127.0.0.1", Port: port})
	if err != nil {
		test.Fatal(err)
	}
	if _, err := OpenTCP(ctx, client, OpenRequest{Host: "127.0.0.1", Port: port}); err == nil {
		test.Fatal("second stream admitted")
	}
	payload := make([]byte, 1<<20)
	rand.Read(payload)
	sent := make(chan error, 1)
	go func() {
		_, err := stream.Write(payload)
		if err == nil {
			err = stream.CloseWrite()
		}
		sent <- err
	}()
	actual, err := io.ReadAll(stream)
	if err != nil || !bytes.Equal(payload, actual) {
		test.Fatal("retransmission leaked duplicate/missing/corrupt TCP bytes", len(actual), err)
	}
	if err := <-sent; err != nil {
		test.Fatal(err)
	}
	if err := stream.Close(); err != nil {
		test.Fatal(err)
	}
	completed(test, done, true)
	<-targetDone
	if !bytes.Equal(targetBytes.Bytes(), payload) {
		test.Fatal("target byte stream mismatch")
	}
	for _, stats := range []reliablestream.Stats{client.ReliabilityStats(), server.ReliabilityStats()} {
		if stats.Retransmissions == 0 || stats.RecoveredGaps == 0 || stats.Duplicates == 0 {
			test.Fatal("faults not exercised", stats)
		}
		test.Logf("gaps=%d recovered=%d retransmissions=%d duplicates_filtered=%d", stats.Gaps, stats.RecoveredGaps, stats.Retransmissions, stats.Duplicates)
	}
	if metrics.Snapshot().ActiveSockets != 0 {
		test.Fatal("socket leak")
	}
}

func TestAuthenticationRequired(test *testing.T) {
	if _, err := OpenTCP(context.Background(), nil, OpenRequest{Host: "example.com", Port: 443}); err == nil {
		test.Fatal("nil auth")
	}
	if err := Serve(context.Background(), &familysession.Session{}, Policy{}, nil); err == nil {
		test.Fatal("unauthenticated gateway")
	}
}

func TestAuthenticatedImmediateResetPreservesOpen(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	client, server := authenticatedPair(test, ctx)
	port := startFixture(test, func(connection *net.TCPConn) { connection.SetLinger(0) })
	done := make(chan error, 1)
	go func() { done <- Serve(ctx, server, Policy{TestOnlyLoopbackPort: port}, nil) }()
	stream, err := OpenTCP(ctx, client, OpenRequest{Host: "127.0.0.1", Port: port})
	if err != nil {
		test.Fatalf("OPEN_OK lost during reset: %v", err)
	}
	_, err = io.ReadAll(stream)
	if err != ErrReset {
		test.Fatalf("RST became EOF: %v", err)
	}
	stream.Close()
	completed(test, done, false)
}
