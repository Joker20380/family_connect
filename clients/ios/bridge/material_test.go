package bridge

import (
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

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
)

func syntheticMaterial(test *testing.T, fault string) []byte {
	test.Helper()
	now := time.Now()
	_, authorityKey, _ := ed25519.GenerateKey(rand.Reader)
	rootTemplate := &x509.Certificate{SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: "isolated iOS CA"}, NotBefore: now.Add(-time.Hour), NotAfter: now.Add(time.Hour), IsCA: true, BasicConstraintsValid: true, KeyUsage: x509.KeyUsageCertSign | x509.KeyUsageCRLSign}
	rootDER, err := x509.CreateCertificate(rand.Reader, rootTemplate, rootTemplate, authorityKey.Public(), authorityKey)
	if err != nil {
		test.Fatal(err)
	}
	root, _ := x509.ParseCertificate(rootDER)
	crl := &x509.RevocationList{Number: big.NewInt(2), ThisUpdate: now.Add(-time.Minute), NextUpdate: now.Add(time.Hour)}
	if fault == "revoked" {
		crl.RevokedCertificateEntries = []x509.RevocationListEntry{{SerialNumber: big.NewInt(2), RevocationTime: now.Add(-time.Minute)}}
	}
	if fault == "expired-crl" {
		crl.NextUpdate = now.Add(-time.Second)
	}
	crlDER, err := x509.CreateRevocationList(rand.Reader, crl, root, authorityKey)
	if err != nil {
		test.Fatal(err)
	}
	if fault == "bad-crl-signature" {
		crlDER[len(crlDER)-1] ^= 1
	}
	public, key, _ := ed25519.GenerateKey(rand.Reader)
	identity := make([]byte, 64)
	rand.Read(identity[:32])
	copy(identity[32:], public)
	reference := sha256.Sum256(identity)
	uri, _ := url.Parse("urn:family-connect:identity:" + hex.EncodeToString(identity))
	role := "device"
	if fault == "wrong-role" {
		role = "gateway"
	}
	family := strings.Repeat("a", 32)
	template := &x509.Certificate{SerialNumber: big.NewInt(2), Subject: pkix.Name{SerialNumber: hex.EncodeToString(reference[:16]), OrganizationalUnit: []string{"protocol=" + familysession.Protocol, "family=" + family, "role=" + role, "revision=1"}}, NotBefore: now.Add(-time.Minute), NotAfter: now.Add(time.Hour), ExtKeyUsage: []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth}, URIs: []*url.URL{uri}}
	if fault == "expired-certificate" {
		template.NotAfter = now.Add(-time.Second)
	}
	der, err := x509.CreateCertificate(rand.Reader, template, root, public, authorityKey)
	if err != nil {
		test.Fatal(err)
	}
	if fault == "bad-certificate-signature" {
		der[len(der)-1] ^= 1
	}
	privateDER, _ := x509.MarshalPKCS8PrivateKey(key)
	credentials := familysession.Credentials{Certificate: string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})), PrivateKey: string(pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: privateDER})), Authority: string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: rootDER})), Revocations: string(pem.EncodeToMemory(&pem.Block{Type: "X509 CRL", Bytes: crlDER})), Family: family, Gateway: strings.Repeat("b", 32), MinimumRevision: 1, MinimumCRL: 2}
	if fault == "wrong-family" {
		credentials.Family = strings.Repeat("c", 32)
	}
	if fault == "stale-revision" {
		credentials.MinimumRevision = 2
	}
	profile, _ := json.Marshal(credentials)
	if fault == "duplicate-profile" {
		profile = append([]byte(`{"family":"ignored",`), profile[1:]...)
	}
	directory := bootstrap.Directory{Version: 1, Family: family, IssuedAt: now.Add(-time.Minute), ExpiresAt: now.Add(time.Hour), Seeds: []bootstrap.Seed{{Transport: "telemost-webrtc", JoinURL: "https://telemost.yandex.ru/j/12345678901234", Gateway: credentials.Gateway}}}
	if fault == "expired-directory" {
		directory.ExpiresAt = now.Add(-time.Second)
	}
	if fault == "wrong-directory-gateway" {
		directory.Seeds[0].Gateway = strings.Repeat("c", 32)
	}
	directoryData, _ := json.Marshal(directory)
	material := ImportMaterial{Version: 1, Profile: profile, Directory: directoryData, Resolver: "192.0.2.1:53"}
	if fault == "version" {
		material.Version = 2
	}
	if fault == "resolver" {
		material.Resolver = "[2001:db8::1]:53"
	}
	raw, _ := json.Marshal(material)
	if fault == "duplicate" {
		raw = append([]byte(`{"version":99,`), raw[1:]...)
	}
	if fault == "trailing" {
		raw = append(raw, []byte(`{}`)...)
	}
	if fault == "case-alias" {
		raw = []byte(strings.Replace(string(raw), `"version":1`, `"Version":1`, 1))
	}
	if fault == "case-shadow" {
		raw = []byte(strings.Replace(string(raw), `"version":1`, `"version":2,"Version":1`, 1))
	}
	return raw
}

func TestOfflineImportExistingTrustPolicy(test *testing.T) {
	if ValidateMaterial(syntheticMaterial(test, "")) != nil {
		test.Fatal("valid synthetic import rejected")
	}
	for _, fault := range []string{"revoked", "expired-crl", "bad-crl-signature", "expired-certificate", "bad-certificate-signature", "wrong-role", "wrong-family", "stale-revision", "expired-directory", "wrong-directory-gateway", "version", "resolver", "duplicate", "duplicate-profile", "trailing", "case-alias", "case-shadow"} {
		test.Run(fault, func(test *testing.T) {
			if ValidateMaterial(syntheticMaterial(test, fault)) == nil {
				test.Fatal("invalid material accepted")
			}
		})
	}
	for _, raw := range [][]byte{nil, []byte(`{}`), make([]byte, 96<<10+1), []byte(`{"version":1,"unknown":1}`)} {
		if ValidateMaterial(raw) == nil {
			test.Fatal("invalid import accepted")
		}
	}
}
