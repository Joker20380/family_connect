package mixed

import (
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/hex"
	"encoding/pem"
	newfamily "github.com/Joker20380/family_connect/carrier/familysession"
	"math/big"
	"net/url"
	"strings"
	"testing"
	"time"
)

func profiles(test *testing.T) (newfamily.Credentials, newfamily.Credentials) {
	return profilesWithExpiry(test, time.Now().Add(time.Hour))
}

func profilesWithExpiry(test *testing.T, expiry time.Time) (newfamily.Credentials, newfamily.Credentials) {
	test.Helper()
	now := time.Now()
	_, authorityKey, _ := ed25519.GenerateKey(rand.Reader)
	rootTemplate := &x509.Certificate{SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: "test CA"}, NotBefore: now.Add(-time.Hour), NotAfter: now.Add(time.Hour), IsCA: true, BasicConstraintsValid: true, KeyUsage: x509.KeyUsageCertSign | x509.KeyUsageCRLSign}
	rootDER, err := x509.CreateCertificate(rand.Reader, rootTemplate, rootTemplate, authorityKey.Public(), authorityKey)
	if err != nil {
		test.Fatal(err)
	}
	root, _ := x509.ParseCertificate(rootDER)
	crlDER, err := x509.CreateRevocationList(rand.Reader, &x509.RevocationList{Number: big.NewInt(2), ThisUpdate: now.Add(-time.Minute), NextUpdate: now.Add(time.Hour)}, root, authorityKey)
	if err != nil {
		test.Fatal(err)
	}
	create := func(role string, serial int64) newfamily.Credentials {
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
		template := &x509.Certificate{SerialNumber: big.NewInt(serial), Subject: pkix.Name{SerialNumber: hex.EncodeToString(reference[:16]), OrganizationalUnit: []string{"protocol=" + newfamily.Protocol, "family=" + strings.Repeat("a", 32), "role=" + role, "revision=1"}}, NotBefore: now.Add(-time.Minute), NotAfter: expiry, ExtKeyUsage: []x509.ExtKeyUsage{usage}, DNSNames: []string{"gateway.family-connect.test"}, URIs: []*url.URL{uri}}
		der, err := x509.CreateCertificate(rand.Reader, template, root, public, authorityKey)
		if err != nil {
			test.Fatal(err)
		}
		privateDER, _ := x509.MarshalPKCS8PrivateKey(key)
		return newfamily.Credentials{Certificate: string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})), PrivateKey: string(pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: privateDER})), Authority: string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: rootDER})), Revocations: string(pem.EncodeToMemory(&pem.Block{Type: "X509 CRL", Bytes: crlDER})), Family: strings.Repeat("a", 32), Gateway: hex.EncodeToString(reference[:16]), MinimumRevision: 1, MinimumCRL: 2}
	}
	client, server := create("device", 2), create("gateway", 3)
	client.Gateway = server.Gateway
	return client, server
}
