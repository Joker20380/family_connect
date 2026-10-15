package bootstrap

import (
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"math/big"
	"net/url"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

func reproProfiles(test *testing.T) ([]byte, []byte) {
	test.Helper()
	now := time.Now()
	_, authorityKey, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		test.Fatal(err)
	}
	rootTemplate := &x509.Certificate{SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: "disposable characterization CA"}, NotBefore: now.Add(-time.Hour), NotAfter: now.Add(time.Hour), IsCA: true, BasicConstraintsValid: true, KeyUsage: x509.KeyUsageCertSign | x509.KeyUsageCRLSign}
	rootDER, err := x509.CreateCertificate(rand.Reader, rootTemplate, rootTemplate, authorityKey.Public(), authorityKey)
	if err != nil {
		test.Fatal(err)
	}
	root, err := x509.ParseCertificate(rootDER)
	if err != nil {
		test.Fatal(err)
	}
	crlDER, err := x509.CreateRevocationList(rand.Reader, &x509.RevocationList{Number: big.NewInt(2), ThisUpdate: now.Add(-time.Minute), NextUpdate: now.Add(time.Hour)}, root, authorityKey)
	if err != nil {
		test.Fatal(err)
	}
	create := func(role string, serial int64) familysession.Credentials {
		public, key, err := ed25519.GenerateKey(rand.Reader)
		if err != nil {
			test.Fatal(err)
		}
		identity := make([]byte, 64)
		if _, err := rand.Read(identity[:32]); err != nil {
			test.Fatal(err)
		}
		copy(identity[32:], public)
		reference := sha256.Sum256(identity)
		uri, err := url.Parse("urn:family-connect:identity:" + hex.EncodeToString(identity))
		if err != nil {
			test.Fatal(err)
		}
		usage := x509.ExtKeyUsageClientAuth
		if role == "gateway" {
			usage = x509.ExtKeyUsageServerAuth
		}
		template := &x509.Certificate{SerialNumber: big.NewInt(serial), Subject: pkix.Name{SerialNumber: hex.EncodeToString(reference[:16]), OrganizationalUnit: []string{"protocol=" + familysession.Protocol, "family=" + strings.Repeat("a", 32), "role=" + role, "revision=1"}}, NotBefore: now.Add(-time.Minute), NotAfter: now.Add(time.Hour), ExtKeyUsage: []x509.ExtKeyUsage{usage}, DNSNames: []string{"gateway.family-connect.test"}, URIs: []*url.URL{uri}}
		der, err := x509.CreateCertificate(rand.Reader, template, root, public, authorityKey)
		if err != nil {
			test.Fatal(err)
		}
		privateDER, err := x509.MarshalPKCS8PrivateKey(key)
		if err != nil {
			test.Fatal(err)
		}
		return familysession.Credentials{Certificate: string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})), PrivateKey: string(pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: privateDER})), Authority: string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: rootDER})), Revocations: string(pem.EncodeToMemory(&pem.Block{Type: "X509 CRL", Bytes: crlDER})), Family: strings.Repeat("a", 32), Gateway: hex.EncodeToString(reference[:16]), MinimumRevision: 1, MinimumCRL: 2}
	}
	client, server := create("device", 2), create("gateway", 3)
	client.Gateway = server.Gateway
	clientRaw, err := json.Marshal(client)
	if err != nil {
		test.Fatal(err)
	}
	serverRaw, err := json.Marshal(server)
	if err != nil {
		test.Fatal(err)
	}
	return clientRaw, serverRaw
}

func reproFamily(test *testing.T, ctx context.Context) (*familysession.Session, *familysession.Session, []byte) {
	test.Helper()
	clientRaw, serverRaw := reproProfiles(test)
	clientPacket, serverPacket := pair()
	test.Cleanup(func() { clientPacket.Close(); serverPacket.Close(); clear(clientRaw); clear(serverRaw) })
	type opened struct {
		session *familysession.Session
		err     error
	}
	ready := make(chan opened, 1)
	go func() {
		session, err := familysession.Open(ctx, serverPacket, serverRaw, true)
		ready <- opened{session, err}
	}()
	client, clientErr := familysession.Open(ctx, clientPacket, clientRaw, false)
	server := reproAwait(test, ctx, ready)
	if client != nil {
		test.Cleanup(func() { client.Close() })
	}
	if server.session != nil {
		test.Cleanup(func() { server.session.Close() })
	}
	if clientErr != nil || server.err != nil {
		test.Fatalf("Family open: client=%T server=%T", clientErr, server.err)
	}
	return client, server.session, serverRaw
}
