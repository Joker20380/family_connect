package main

import (
	"crypto/ed25519"
	"crypto/sha256"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"math/big"
	"net/url"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
	"testing/synctest"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

type fixtureOptions struct {
	revision, floor int
	crl, crlFloor   int64
	mutation        string
}

func fixture(test *testing.T, options fixtureOptions) ([]byte, []byte) {
	test.Helper()
	key := func(label string) ed25519.PrivateKey {
		seed := sha256.Sum256([]byte("synthetic-native-authority-test-" + label))
		return ed25519.NewKeyFromSeed(seed[:])
	}
	now := time.Now()
	issuer := key("issuer")
	ca := &x509.Certificate{SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: "synthetic authority"}, NotBefore: now.Add(-time.Hour), NotAfter: now.Add(time.Hour), IsCA: true, BasicConstraintsValid: true, MaxPathLenZero: true, KeyUsage: x509.KeyUsageCertSign | x509.KeyUsageCRLSign, SubjectKeyId: []byte{1, 2, 3}}
	if options.mutation == "expired_issuer" {
		ca.NotAfter = now
	}
	caDER, err := x509.CreateCertificate(nil, ca, ca, issuer.Public(), issuer)
	if err != nil {
		test.Fatal("fixture authority construction failed")
	}
	authority, err := x509.ParseCertificate(caDER)
	if err != nil {
		test.Fatal("fixture authority parse failed")
	}
	family := strings.Repeat("a", 32)
	if options.mutation == "zero_family" {
		family = strings.Repeat("0", 32)
	}
	leaf := func(role string, revision int, serial int64) (*x509.Certificate, string, string, string) {
		private := key(role)
		public := append(make([]byte, 32), private.Public().(ed25519.PublicKey)...)
		reference := sha256.Sum256(public)
		identifier := hex.EncodeToString(reference[:16])
		identityURI, _ := url.Parse("urn:family-connect:identity:" + hex.EncodeToString(public))
		usage := x509.ExtKeyUsageClientAuth
		if role == "gateway" {
			usage = x509.ExtKeyUsageServerAuth
		}
		certificate := &x509.Certificate{SerialNumber: big.NewInt(serial), Subject: pkix.Name{SerialNumber: identifier, OrganizationalUnit: []string{"protocol=" + familysession.Protocol, "family=" + family, "role=" + role, "revision=" + strconv.Itoa(revision)}}, NotBefore: now.Add(-time.Minute), NotAfter: now.Add(30 * time.Minute), KeyUsage: x509.KeyUsageDigitalSignature, ExtKeyUsage: []x509.ExtKeyUsage{usage}, DNSNames: []string{"gateway.family-connect.test"}, URIs: []*url.URL{identityURI}}
		if options.mutation == "expired_"+role {
			certificate.NotAfter = now.Add(-time.Second)
		}
		der, failure := x509.CreateCertificate(nil, certificate, authority, private.Public(), issuer)
		if failure != nil {
			test.Fatal("fixture leaf construction failed")
		}
		privateDER, failure := x509.MarshalPKCS8PrivateKey(private)
		if failure != nil {
			test.Fatal("fixture key construction failed")
		}
		return certificate, string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})), string(pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: privateDER})), identifier
	}
	device, canary, _, _ := leaf("device", options.revision, 2)
	_, gatewayCertificate, privateKey, gateway := leaf("gateway", options.floor, 3)
	revocations := &x509.RevocationList{Number: big.NewInt(options.crl), ThisUpdate: now.Add(-time.Minute), NextUpdate: now.Add(15 * time.Minute)}
	if options.mutation == "expired_crl" {
		revocations.NextUpdate = now
	}
	if options.mutation == "revoked_device" {
		revocations.RevokedCertificateEntries = []x509.RevocationListEntry{{SerialNumber: device.SerialNumber, RevocationTime: now.Add(-time.Second)}}
	}
	crlDER, err := x509.CreateRevocationList(nil, revocations, authority, issuer)
	if err != nil {
		test.Fatal("fixture CRL construction failed")
	}
	profile := familysession.Credentials{Authority: string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: caDER})), Certificate: gatewayCertificate, PrivateKey: privateKey, Family: family, Gateway: gateway, MinimumRevision: options.floor, MinimumCRL: options.crlFloor, Revocations: string(pem.EncodeToMemory(&pem.Block{Type: "X509 CRL", Bytes: crlDER}))}
	if options.mutation == "wrong_family" {
		profile.Family = strings.Repeat("b", 32)
	}
	if options.mutation == "wrong_gateway" {
		profile.Gateway = strings.Repeat("b", 32)
	}
	raw, err := json.Marshal(profile)
	if err != nil {
		test.Fatal("fixture profile construction failed")
	}
	return raw, []byte(canary)
}

func TestAuthorityMatrix(test *testing.T) {
	cases := []struct {
		name, stage string
		options     fixtureOptions
	}{
		{"initial", "complete", fixtureOptions{1, 1, 1, 1, ""}},
		{"renewed", "complete", fixtureOptions{2, 1, 2, 2, ""}},
		{"attempt11", "complete", fixtureOptions{2, 1, 19, 19, ""}},
		{"future_revision", "complete", fixtureOptions{37, 1, 43, 43, ""}},
		{"floor_tracks_revision", "complete", fixtureOptions{37, 37, 43, 43, ""}},
		{"crl_above_floor", "complete", fixtureOptions{1, 1, 19, 18, ""}},
		{"zero_family", "complete", fixtureOptions{1, 1, 1, 1, "zero_family"}},
		{"rollback_below_floor", "device_admission", fixtureOptions{1, 2, 19, 19, ""}},
		{"stale_crl", "configuration", fixtureOptions{2, 1, 18, 19, ""}},
		{"revoked_current_revision", "device_admission", fixtureOptions{2, 1, 19, 19, "revoked_device"}},
		{"expired_issuer", "configuration", fixtureOptions{2, 1, 19, 19, "expired_issuer"}},
		{"expired_device", "device_chain", fixtureOptions{2, 1, 19, 19, "expired_device"}},
		{"expired_gateway", "configuration", fixtureOptions{2, 1, 19, 19, "expired_gateway"}},
		{"expired_crl", "configuration", fixtureOptions{2, 1, 19, 19, "expired_crl"}},
		{"wrong_family", "device_admission", fixtureOptions{2, 1, 19, 19, "wrong_family"}},
		{"wrong_gateway", "gateway_binding", fixtureOptions{2, 1, 19, 19, "wrong_gateway"}},
	}
	for _, entry := range cases {
		test.Run(entry.name, func(test *testing.T) {
			synctest.Test(test, func(test *testing.T) {
				profile, certificate := fixture(test, entry.options)
				result := validate(profile, certificate)
				if result.Stage != entry.stage || (result.Status == "PASS") != (entry.stage == "complete") {
					test.Fatalf("safe receipt: %+v", result)
				}
			})
		})
	}
}

func TestInputAndRedaction(test *testing.T) {
	if result := run(nil); result.Stage != "input" || result.Status != "FAIL" {
		test.Fatal(result)
	}
	result := run([]string{"secret-private-path", "private-device-id"})
	raw, _ := json.Marshal(result)
	if strings.Contains(string(raw), "secret") || strings.Contains(string(raw), "private-device-id") {
		test.Fatal("unsafe receipt")
	}
	synctest.Test(test, func(test *testing.T) {
		profile, certificate := fixture(test, fixtureOptions{2, 1, 19, 19, ""})
		directory := test.TempDir()
		profilePath, certificatePath := filepath.Join(directory, "profile.json"), filepath.Join(directory, "canary.pem")
		if os.WriteFile(profilePath, profile, 0o600) != nil || os.WriteFile(certificatePath, certificate, 0o600) != nil {
			test.Fatal("fixture write failed")
		}
		if result := run([]string{profilePath, certificatePath}); result.Status != "PASS" {
			test.Fatal(result)
		}
		if result := validate(profile, []byte("private invalid certificate")); result.Stage != "device_parse" {
			test.Fatal(result)
		}
		if os.WriteFile(profilePath, make([]byte, (48<<10)+1), 0o600) != nil {
			test.Fatal("fixture write failed")
		}
		if result := run([]string{profilePath, certificatePath}); result.Reason != "unreadable_or_oversized" {
			test.Fatal(result)
		}
	})
}
