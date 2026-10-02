package wholedevice

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
	"fmt"
	"math/big"
	"net/url"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
)

func deliveryFixture(test *testing.T) (ReadinessDelivery, []byte, []byte, []byte, time.Time) {
	test.Helper()
	now := time.Now().UTC().Truncate(time.Second)
	root, rootPrivate, _ := ed25519.GenerateKey(rand.Reader)
	issuerPublic, issuerPrivate, _ := ed25519.GenerateKey(rand.Reader)
	publicSigning, privateSigning, _ := ed25519.GenerateKey(rand.Reader)
	exchange, _ := ecdh.X25519().GenerateKey(rand.Reader)
	identity := append(exchange.Bytes(), privateSigning.Seed()...)
	public := append(exchange.PublicKey().Bytes(), publicSigning...)
	ref := sha256.Sum256(public)
	family, gateway := strings.Repeat("a", 32), strings.Repeat("b", 32)
	template := &x509.Certificate{SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: "test delegated issuer"}, NotBefore: now.Add(-time.Minute), NotAfter: now.Add(time.Hour), IsCA: true, BasicConstraintsValid: true, KeyUsage: x509.KeyUsageCertSign | x509.KeyUsageCRLSign, SubjectKeyId: []byte{1, 2, 3}}
	caBytes, err := x509.CreateCertificate(rand.Reader, template, template, issuerPublic, issuerPrivate)
	if err != nil {
		test.Fatal(err)
	}
	ca, err := x509.ParseCertificate(caBytes)
	if err != nil {
		test.Fatal(err)
	}
	uri, _ := url.Parse("urn:family-connect:identity:" + hex.EncodeToString(public))
	leaf := &x509.Certificate{SerialNumber: big.NewInt(2), Subject: pkix.Name{SerialNumber: hex.EncodeToString(ref[:16]), OrganizationalUnit: []string{"protocol=" + familysession.Protocol, "family=" + family, "role=device", "revision=1"}}, NotBefore: now.Add(-time.Second), NotAfter: now.Add(time.Hour), ExtKeyUsage: []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth}, URIs: []*url.URL{uri}}
	leafBytes, err := x509.CreateCertificate(rand.Reader, leaf, ca, publicSigning, issuerPrivate)
	if err != nil {
		test.Fatal(err)
	}
	crlBytes, err := x509.CreateRevocationList(rand.Reader, &x509.RevocationList{Number: big.NewInt(1), ThisUpdate: now.Add(-time.Second), NextUpdate: now.Add(30 * time.Minute)}, ca, issuerPrivate)
	if err != nil {
		test.Fatal(err)
	}
	payload, _ := json.Marshal(issuerDelegation{1, 1, family, gateway, string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: caBytes})), now.Add(-time.Minute).Unix(), now.Add(time.Hour).Unix(), 1})
	signature := ed25519.Sign(rootPrivate, append([]byte("family-connect/restricted-issuer/v1\x00"), payload...))
	directory, _ := json.Marshal(bootstrap.Directory{Version: 1, Family: family, IssuedAt: now, ExpiresAt: now.Add(30 * time.Minute), Seeds: []bootstrap.Seed{{Transport: "telemost-webrtc", JoinURL: "https://telemost.yandex.ru/j/test-only", Gateway: gateway}}})
	return ReadinessDelivery{Version: 1, Device: hex.EncodeToString(ref[:16]), Challenge: base64.StdEncoding.EncodeToString(make([]byte, 32)), IssuedAt: now.Unix(), ExpiresAt: now.Add(30 * time.Minute).Unix(), Revision: 1, Issuer: issuerEnvelope{base64.StdEncoding.EncodeToString(payload), base64.StdEncoding.EncodeToString(signature)}, Certificate: string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: leafBytes})), Revocations: string(pem.EncodeToMemory(&pem.Block{Type: "X509 CRL", Bytes: crlBytes})), MinimumCRL: 1, Directory: directory}, public, identity, root, now
}

func TestProductionDeliveryToExistingFamilyMaterial(test *testing.T) {
	delivery, public, identity, root, now := deliveryFixture(test)
	raw, _ := json.Marshal(delivery)
	if strings.Contains(fmt.Sprintf("%+v %#v", delivery, delivery), "https") {
		test.Fatal("delivery diagnostics leak seed")
	}
	if _, _, err := ValidateDelivery(raw, public, root, now); err != nil {
		test.Fatal("valid public delivery rejected")
	}
	profile, directory, err := DeliveryMaterial(raw, identity, root, now)
	if err != nil {
		test.Fatal("device identity material rejected")
	}
	defer clear(profile)
	config, _, err := familysession.Configuration(profile, false)
	if err != nil {
		test.Fatal("accepted Family format incompatible")
	}
	certificate, _ := x509.ParseCertificate(config.Certificates[0].Certificate[0])
	if certificate.Subject.SerialNumber != delivery.Device {
		test.Fatal("identity changed")
	}
	if _, err := bootstrap.ParseDirectory(directory, strings.Repeat("a", 32), strings.Repeat("b", 32), now); err != nil {
		test.Fatal("BOOT-1 v1 changed")
	}
	if strings.Contains(string(raw), "PRIVATE KEY") || strings.Contains(string(raw), "private_key") {
		test.Fatal("server supplies a private key")
	}
}

func TestDeliveryResultCodes(test *testing.T) {
	delivery, public, _, root, now := deliveryFixture(test)
	raw, _ := json.Marshal(delivery)
	if DeliveryValidationCode(raw, public, root, now) != 0 {
		test.Fatal("valid delivery")
	}
	delivery.Directory = json.RawMessage(`{}`)
	raw, _ = json.Marshal(delivery)
	if DeliveryValidationCode(raw, public, root, now) != 2 {
		test.Fatal("bootstrap classification")
	}
	delivery.Certificate = "invalid"
	raw, _ = json.Marshal(delivery)
	if DeliveryValidationCode(raw, public, root, now) != 1 {
		test.Fatal("native classification")
	}
}

func TestProductionDeliveryRejectsBindingTrustExpiryBounds(test *testing.T) {
	delivery, public, _, root, now := deliveryFixture(test)
	for name, change := range map[string]func(*ReadinessDelivery){
		"device":    func(value *ReadinessDelivery) { value.Device = strings.Repeat("c", 32) },
		"revision":  func(value *ReadinessDelivery) { value.Revision = 2 },
		"crl_floor": func(value *ReadinessDelivery) { value.MinimumCRL = 2 },
		"expired":   func(value *ReadinessDelivery) { value.ExpiresAt = now.Unix() },
		"future":    func(value *ReadinessDelivery) { value.IssuedAt = now.Add(time.Second).Unix() },
		"signature": func(value *ReadinessDelivery) {
			value.Issuer.Signature = base64.StdEncoding.EncodeToString(make([]byte, 64))
		},
		"directory": func(value *ReadinessDelivery) { value.Directory = json.RawMessage(`{}`) },
		"nonce":     func(value *ReadinessDelivery) { value.Challenge = "not-a-nonce" },
	} {
		test.Run(name, func(test *testing.T) {
			fresh := delivery
			change(&fresh)
			raw, _ := json.Marshal(fresh)
			if _, _, err := ValidateDelivery(raw, public, root, now); err == nil {
				test.Fatal("accepted invalid delivery")
			}
		})
	}
	raw, _ := json.Marshal(delivery)
	for _, invalid := range [][]byte{[]byte(strings.Repeat(" ", MaxReadiness+1)), append(raw, raw...), []byte(`{"version":1,"version":1}`)} {
		if _, _, err := ValidateDelivery(invalid, public, root, now); err == nil {
			test.Fatal("malformed accepted")
		}
	}
	public[0] ^= 1
	if _, _, err := ValidateDelivery(raw, public, root, now); err == nil {
		test.Fatal("wrong device accepted")
	}
}
