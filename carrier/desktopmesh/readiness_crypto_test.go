package desktopmesh

import (
	"crypto/ecdh"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/base64"
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

func signedReadiness(test *testing.T, revoked bool) ([]byte, []byte, []byte, time.Time) {
	test.Helper()
	now := time.Date(2026, 10, 22, 12, 0, 0, 0, time.UTC)
	anchor, rootPrivate, _ := ed25519.GenerateKey(rand.Reader)
	issuerPublic, issuerPrivate, _ := ed25519.GenerateKey(rand.Reader)
	deviceSigning, _, _ := ed25519.GenerateKey(rand.Reader)
	exchange, _ := ecdh.X25519().GenerateKey(rand.Reader)
	public := append(exchange.PublicKey().Bytes(), deviceSigning...)
	digest := sha256.Sum256(public)
	reference := hex.EncodeToString(digest[:16])
	family, gateway := strings.Repeat("a", 32), strings.Repeat("b", 32)
	template := &x509.Certificate{SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: "desktop synthetic readiness"},
		NotBefore: now.Add(-time.Minute), NotAfter: now.Add(time.Hour), IsCA: true, BasicConstraintsValid: true,
		KeyUsage: x509.KeyUsageCertSign | x509.KeyUsageCRLSign, SubjectKeyId: []byte{1, 2, 3}}
	caBytes, err := x509.CreateCertificate(rand.Reader, template, template, issuerPublic, issuerPrivate)
	if err != nil {
		test.Fatal(err)
	}
	ca, err := x509.ParseCertificate(caBytes)
	if err != nil {
		test.Fatal(err)
	}
	uri, _ := url.Parse("urn:family-connect:identity:" + hex.EncodeToString(public))
	leaf := &x509.Certificate{SerialNumber: big.NewInt(2), Subject: pkix.Name{SerialNumber: reference,
		OrganizationalUnit: []string{"protocol=" + familysession.Protocol, "family=" + family, "role=device", "revision=1"}},
		NotBefore: now.Add(-time.Second), NotAfter: now.Add(time.Hour), ExtKeyUsage: []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth}, URIs: []*url.URL{uri}}
	leafBytes, err := x509.CreateCertificate(rand.Reader, leaf, ca, deviceSigning, issuerPrivate)
	if err != nil {
		test.Fatal(err)
	}
	crl := &x509.RevocationList{Number: big.NewInt(1), ThisUpdate: now.Add(-time.Second), NextUpdate: now.Add(30 * time.Minute)}
	if revoked {
		crl.RevokedCertificateEntries = []x509.RevocationListEntry{{SerialNumber: leaf.SerialNumber, RevocationTime: now.Add(-time.Second)}}
	}
	crlBytes, err := x509.CreateRevocationList(rand.Reader, crl, ca, issuerPrivate)
	if err != nil {
		test.Fatal(err)
	}
	payload, _ := json.Marshal(map[string]any{"version": 1, "sequence": 1, "family": family, "gateway": gateway,
		"authority": string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: caBytes})),
		"issued_at": now.Add(-time.Minute).Unix(), "expires_at": now.Add(time.Hour).Unix(), "minimum_revision": 1})
	signature := ed25519.Sign(rootPrivate, append([]byte("family-connect/restricted-issuer/v1\x00"), payload...))
	directory := bootstrap.Directory{Version: 1, Family: family, IssuedAt: now, ExpiresAt: now.Add(30 * time.Minute),
		Seeds: []bootstrap.Seed{{Transport: "telemost-webrtc", JoinURL: "https://telemost.yandex.ru/j/test-only", Gateway: gateway}}}
	raw, err := json.Marshal(map[string]any{"version": 1, "device": reference, "challenge": base64.StdEncoding.EncodeToString(make([]byte, 32)),
		"issued_at": now.Unix(), "expires_at": now.Add(20 * time.Minute).Unix(), "revision": 1, "minimum_crl": 1,
		"issuer":      map[string]string{"payload": base64.StdEncoding.EncodeToString(payload), "signature": base64.StdEncoding.EncodeToString(signature)},
		"certificate": string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: leafBytes})),
		"revocations": string(pem.EncodeToMemory(&pem.Block{Type: "X509 CRL", Bytes: crlBytes})), "directory": directory})
	if err != nil {
		test.Fatal(err)
	}
	return raw, public, anchor, now
}

func TestReadinessCacheUsesActualFamilyValidation(test *testing.T) {
	for _, revoked := range []bool{false, true} {
		raw, public, anchor, now := signedReadiness(test, revoked)
		storage := &memoryReadiness{}
		cache, err := NewReadinessCache(storage, public, anchor)
		if err != nil {
			test.Fatal(err)
		}
		err = cache.Accept(raw, cacheAttempt(), now)
		if revoked {
			if err != ReadinessInvalid || storage.raw != nil {
				test.Fatal("revoked certificate stored")
			}
			continue
		}
		if err != nil {
			test.Fatal("actual authorized fixture rejected", err)
		}
		cache, _ = NewReadinessCache(storage, public, anchor)
		if ready, code := cache.Usable(now.Add(19 * time.Minute)); ready == nil || code != ReadinessReady {
			test.Fatal("actual cached authorization lost", code)
		}
		if expired, code := cache.Usable(now.Add(20 * time.Minute)); expired != nil || code != ReadinessExpired {
			test.Fatal("actual expired cache accepted", code)
		}
		wrong, _ := NewReadinessCache(storage, public, make([]byte, 32))
		if usable, code := wrong.Usable(now); usable != nil || code != ReadinessInvalid {
			test.Fatal("wrong trust root accepted")
		}
		wrong, _ = NewReadinessCache(storage, make([]byte, 64), anchor)
		if usable, code := wrong.Usable(now); usable != nil || code != ReadinessInvalid {
			test.Fatal("another device's cache accepted")
		}
	}
}
