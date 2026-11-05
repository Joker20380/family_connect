package roombroker

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
	"math/big"
	"net/url"
	"os"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
)

type rotationProfiles struct {
	now       time.Time
	authority *x509.Certificate
	key       ed25519.PrivateKey
	client    familysession.Credentials
	server    familysession.Credentials
}

func rotationKey(test *testing.T) ed25519.PrivateKey {
	test.Helper()
	_, key, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		test.Fatal(err)
	}
	return key
}

func rotationCertificate(test *testing.T, template, authority *x509.Certificate, public any, key ed25519.PrivateKey) *x509.Certificate {
	test.Helper()
	raw, err := x509.CreateCertificate(rand.Reader, template, authority, public, key)
	if err != nil {
		test.Fatal(err)
	}
	certificate, err := x509.ParseCertificate(raw)
	if err != nil {
		test.Fatal(err)
	}
	return certificate
}

func (profiles *rotationProfiles) crl(test *testing.T, number int64, deadline time.Time, revoked []x509.RevocationListEntry) string {
	test.Helper()
	raw, err := x509.CreateRevocationList(rand.Reader, &x509.RevocationList{
		Number: big.NewInt(number), ThisUpdate: profiles.now.Add(-time.Minute), NextUpdate: deadline,
		RevokedCertificateEntries: revoked,
	}, profiles.authority, profiles.key)
	if err != nil {
		test.Fatal(err)
	}
	return string(pem.EncodeToMemory(&pem.Block{Type: "X509 CRL", Bytes: raw}))
}

func newRotationProfiles(test *testing.T, leafBound bool) *rotationProfiles {
	test.Helper()
	profiles := &rotationProfiles{now: time.Now().UTC().Truncate(time.Second), key: rotationKey(test)}
	root := &x509.Certificate{SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: "disposable renewal test"},
		NotBefore: profiles.now.Add(-time.Hour), NotAfter: profiles.now.Add(2 * time.Hour), IsCA: true,
		BasicConstraintsValid: true, KeyUsage: x509.KeyUsageCertSign | x509.KeyUsageCRLSign}
	profiles.authority = rotationCertificate(test, root, root, profiles.key.Public(), profiles.key)
	leafDeadline, crlDeadline := profiles.now.Add(40*time.Minute), profiles.now.Add(20*time.Minute)
	if leafBound {
		leafDeadline, crlDeadline = crlDeadline, leafDeadline
	}
	revocations := profiles.crl(test, 1, crlDeadline, nil)
	create := func(role string, serial int64) familysession.Credentials {
		key := rotationKey(test)
		identity := make([]byte, 64)
		if _, err := rand.Read(identity[:32]); err != nil {
			test.Fatal(err)
		}
		copy(identity[32:], key.Public().(ed25519.PublicKey))
		reference := sha256.Sum256(identity)
		identifier := hex.EncodeToString(reference[:16])
		identityURI, err := url.Parse("urn:family-connect:identity:" + hex.EncodeToString(identity))
		if err != nil {
			test.Fatal(err)
		}
		usage := x509.ExtKeyUsageClientAuth
		if role == "gateway" {
			usage = x509.ExtKeyUsageServerAuth
		}
		template := &x509.Certificate{SerialNumber: big.NewInt(serial), Subject: pkix.Name{SerialNumber: identifier,
			OrganizationalUnit: []string{"protocol=" + familysession.Protocol, "family=" + strings.Repeat("a", 32), "role=" + role, "revision=1"}},
			NotBefore: profiles.now.Add(-time.Minute), NotAfter: leafDeadline, ExtKeyUsage: []x509.ExtKeyUsage{usage},
			DNSNames: []string{"gateway.family-connect.test"}, URIs: []*url.URL{identityURI}}
		certificate := rotationCertificate(test, template, profiles.authority, key.Public(), profiles.key)
		privateDER, err := x509.MarshalPKCS8PrivateKey(key)
		if err != nil {
			test.Fatal(err)
		}
		return familysession.Credentials{
			Certificate: string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: certificate.Raw})),
			PrivateKey:  string(pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: privateDER})),
			Authority:   string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: profiles.authority.Raw})),
			Revocations: revocations, Family: strings.Repeat("a", 32), Gateway: identifier, MinimumRevision: 1, MinimumCRL: 1,
		}
	}
	profiles.client, profiles.server = create("device", 2), create("gateway", 3)
	profiles.client.Gateway = profiles.server.Gateway
	return profiles
}

func rotationRaw(test *testing.T, credentials familysession.Credentials) []byte {
	test.Helper()
	raw, err := json.Marshal(credentials)
	if err != nil {
		test.Fatal(err)
	}
	return raw
}

func (profiles *rotationProfiles) successor(test *testing.T, revokePredecessor bool) (familysession.Credentials, familysession.Credentials) {
	return profiles.successorUntil(test, revokePredecessor, profiles.now.Add(90*time.Minute), 2, 4, 5)
}

func (profiles *rotationProfiles) successorUntil(test *testing.T, revokePredecessor bool, deadline time.Time, crlNumber, clientSerial, serverSerial int64) (familysession.Credentials, familysession.Credentials) {
	test.Helper()
	var revoked []x509.RevocationListEntry
	if revokePredecessor {
		revoked = []x509.RevocationListEntry{{SerialNumber: big.NewInt(2), RevocationTime: profiles.now.Add(-time.Second)}}
	}
	revocations := profiles.crl(test, crlNumber, deadline, revoked)
	renew := func(credentials familysession.Credentials, serial int64) familysession.Credentials {
		pair, err := tls.X509KeyPair([]byte(credentials.Certificate), []byte(credentials.PrivateKey))
		if err != nil {
			test.Fatal(err)
		}
		template, err := x509.ParseCertificate(pair.Certificate[0])
		if err != nil {
			test.Fatal(err)
		}
		template.SerialNumber, template.NotAfter = big.NewInt(serial), deadline
		certificate := rotationCertificate(test, template, profiles.authority, template.PublicKey, profiles.key)
		credentials.Certificate = string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: certificate.Raw}))
		credentials.Revocations, credentials.MinimumCRL = revocations, 2
		return credentials
	}
	return renew(profiles.client, clientSerial), renew(profiles.server, serverSerial)
}

func replaceRotationProfile(test *testing.T, path string, credentials familysession.Credentials) {
	test.Helper()
	pending := path + ".next"
	if err := os.WriteFile(pending, rotationRaw(test, credentials), 0600); err != nil {
		test.Fatal(err)
	}
	if err := os.Rename(pending, path); err != nil {
		test.Fatal(err)
	}
}

func openRotationPair(test *testing.T, ctx context.Context, clientRaw, serverRaw []byte) (*familysession.Session, *familysession.Session) {
	test.Helper()
	forward, reverse := make(chan []byte, 256), make(chan []byte, 256)
	stopped, once := make(chan struct{}), new(sync.Once)
	clientPipe, serverPipe := packets{reverse, forward, stopped, once}, packets{forward, reverse, stopped, once}
	test.Cleanup(func() { clientPipe.Close() })
	type result struct {
		session *familysession.Session
		err     error
	}
	ready := make(chan result, 1)
	go func() {
		session, err := familysession.Open(ctx, serverPipe, serverRaw, true)
		ready <- result{session, err}
	}()
	client, err := familysession.Open(ctx, clientPipe, clientRaw, false)
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() { client.Close() })
	select {
	case server := <-ready:
		if server.err != nil {
			test.Fatal(server.err)
		}
		test.Cleanup(func() { server.session.Close() })
		return client, server.session
	case <-ctx.Done():
		test.Fatal("successor TLS handshake did not complete")
		return nil, nil
	}
}

func TestLeaseCredentialRotationKeepsStreamAndOriginalDeadline(test *testing.T) {
	for _, bound := range []string{"leaf", "crl"} {
		test.Run(bound, func(test *testing.T) {
			profiles := newRotationProfiles(test, bound == "leaf")
			fixture := newLeaseMuxWithProfiles(test, true, rotationRaw(test, profiles.client), rotationRaw(test, profiles.server))
			originalDeadline := fixture.secured.SecurityDeadline()
			if !originalDeadline.Equal(profiles.now.Add(20 * time.Minute)) {
				test.Fatal("fixture did not isolate the original security bound")
			}
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
			before, err := SessionAuthorizer(fixture.path, fixture.secured.ConnectionState())(fixture.ctx)
			if err != nil {
				test.Fatal(err)
			}
			clientNext, serverNext := profiles.successor(test, false)
			replaceRotationProfile(test, fixture.path, serverNext)
			after, err := SessionAuthorizer(fixture.path, fixture.secured.ConnectionState())(fixture.ctx)
			if err != nil || before != after {
				test.Fatal("same-holder profile renewal changed authorization", err)
			}
			reloaded, err := LoadCredentials(fixture.path)
			if err != nil || !bytes.Equal(reloaded, rotationRaw(test, serverNext)) {
				test.Fatal("atomic successor readback failed", err)
			}
			clientFresh, serverFresh := openRotationPair(test, fixture.ctx, rotationRaw(test, clientNext), reloaded)
			if !clientFresh.SecurityDeadline().After(originalDeadline) || !serverFresh.SecurityDeadline().After(originalDeadline) ||
				bytes.Equal(serverFresh.ConnectionState().PeerCertificates[0].Raw, fixture.secured.ConnectionState().PeerCertificates[0].Raw) {
				test.Fatal("new handshake did not authenticate the successor certificate")
			}
			freshIdentity, err := SessionAuthorizer(fixture.path, serverFresh.ConnectionState())(fixture.ctx)
			if err != nil || freshIdentity != before {
				test.Fatal("successor handshake did not preserve the authorized holder", err)
			}
			for index := 1; index <= 2; index++ {
				fixture.clock.Advance(8 * time.Minute)
				known, _, err = exchangeLease(fixture.ctx, fixture.client, fixture.id, known, true)
				if err != nil || known.Sequence != uint64(index) || known.ExpiresAt.After(originalDeadline) {
					test.Fatal("renewal lost the holder or bypassed the original security bound", err)
				}
				fixture.data(test, stream, index)
			}
			if !known.ExpiresAt.Equal(originalDeadline) || !fixture.secured.SecurityDeadline().Equal(originalDeadline) {
				test.Fatal("profile replacement silently extended the established TLS lifetime")
			}
			fixture.clock.Advance(originalDeadline.Sub(fixture.clock.Now()))
			waitEmpty(test, fixture.broker)
			if fixture.server.Stats().ActiveSockets != 0 {
				test.Fatal("original deadline did not close the persistent socket")
			}
		})
	}
}

func TestLeaseCredentialRevocationBetweenOfferAndRenewal(test *testing.T) {
	profiles := newRotationProfiles(test, true)
	fixture := newLeaseMuxWithProfiles(test, true, rotationRaw(test, profiles.client), rotationRaw(test, profiles.server))
	fixture.clock.Advance(8 * time.Minute)
	stream, err := fixture.client.OpenTCP(fixture.ctx, tcpforward.OpenRequest{Host: tcpforward.LeaseRenewalHost, Port: 1})
	if err != nil {
		test.Fatal(err)
	}
	defer stream.Reset()
	decoder := leaseReader(stream)
	var offer leaseMessage
	if err := decoder.Decode(&offer); err != nil || offer.Type != "offer" {
		test.Fatal("missing held renewal offer", err)
	}
	_, serverNext := profiles.successor(test, true)
	replaceRotationProfile(test, fixture.path, serverNext)
	request := offer.Lease
	request.Sequence++
	if err := json.NewEncoder(stream).Encode(leaseMessage{Type: "renew", Lease: request}); err != nil {
		test.Fatal(err)
	}
	var reply leaseMessage
	if err := decoder.Decode(&reply); err != nil || reply.Type != "denied" {
		test.Fatal("signed CRL rotation failed to fence the held request", err)
	}
	fixture.broker.mu.Lock()
	current := fixture.broker.setups[fixture.id]
	unchanged := current != nil && current.renewal == offer.Lease.Sequence && current.lease.deadline().Equal(offer.Lease.ExpiresAt)
	fixture.broker.unlock()
	if !unchanged {
		test.Fatal("revoked predecessor extended the lease")
	}
	stream.Reset()
	fixture.clock.Advance(offer.Lease.ExpiresAt.Sub(fixture.clock.Now()))
	waitEmpty(test, fixture.broker)
}

func TestLeaseCredentialRotationRejectsUnsafeSuccessor(test *testing.T) {
	for _, fault := range []string{"foreign-authority", "wrong-family", "stale-crl-floor"} {
		test.Run(fault, func(test *testing.T) {
			profiles := newRotationProfiles(test, true)
			fixture := newLeaseMuxWithProfiles(test, true, rotationRaw(test, profiles.client), rotationRaw(test, profiles.server))
			known, _, err := exchangeLease(fixture.ctx, fixture.client, fixture.id, LeaseReceipt{}, false)
			if err != nil {
				test.Fatal(err)
			}
			_, successor := profiles.successor(test, false)
			switch fault {
			case "foreign-authority":
				successor = newRotationProfiles(test, true).server
			case "wrong-family":
				successor.Family = strings.Repeat("b", 32)
			case "stale-crl-floor":
				successor.MinimumCRL++
			}
			replaceRotationProfile(test, fixture.path, successor)
			fixture.clock.Advance(8 * time.Minute)
			if _, _, err := exchangeLease(fixture.ctx, fixture.client, fixture.id, known, true); err != Code("unauthorized") {
				test.Fatal("unsafe successor authorized renewal", err)
			}
			fixture.broker.mu.Lock()
			current := fixture.broker.setups[fixture.id]
			unchanged := current != nil && current.renewal == known.Sequence && current.lease.deadline().Equal(known.ExpiresAt)
			fixture.broker.unlock()
			if !unchanged {
				test.Fatal("rejected successor changed the lease")
			}
		})
	}
}
