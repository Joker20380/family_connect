package restrictedchat

import (
	"context"
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
	"errors"
	"fmt"
	"math/big"
	"net/url"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/restrictedowner"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

func signedConfig(test *testing.T, now time.Time, revoked bool) Config {
	test.Helper()
	anchor, rootPrivate, _ := ed25519.GenerateKey(rand.Reader)
	issuerPublic, issuerPrivate, _ := ed25519.GenerateKey(rand.Reader)
	devicePublic, devicePrivate, _ := ed25519.GenerateKey(rand.Reader)
	exchange, _ := ecdh.X25519().GenerateKey(rand.Reader)
	identity := append(exchange.Bytes(), devicePrivate.Seed()...)
	public := append(exchange.PublicKey().Bytes(), devicePublic...)
	hash := sha256.Sum256(public)
	reference := hex.EncodeToString(hash[:16])
	family, gateway := strings.Repeat("a", 32), strings.Repeat("b", 32)
	issuer := &x509.Certificate{SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: "synthetic chat issuer"},
		NotBefore: now.Add(-time.Minute), NotAfter: now.Add(time.Hour), IsCA: true, BasicConstraintsValid: true,
		KeyUsage: x509.KeyUsageCertSign | x509.KeyUsageCRLSign, SubjectKeyId: []byte{1, 2, 3}}
	issuerRaw, err := x509.CreateCertificate(rand.Reader, issuer, issuer, issuerPublic, issuerPrivate)
	if err != nil {
		test.Fatal(err)
	}
	issuer, err = x509.ParseCertificate(issuerRaw)
	if err != nil {
		test.Fatal(err)
	}
	uri, _ := url.Parse("urn:family-connect:identity:" + hex.EncodeToString(public))
	leaf := &x509.Certificate{SerialNumber: big.NewInt(2), Subject: pkix.Name{SerialNumber: reference,
		OrganizationalUnit: []string{"protocol=" + familysession.Protocol, "family=" + family, "role=device", "revision=1"}},
		NotBefore: now.Add(-time.Second), NotAfter: now.Add(time.Hour), ExtKeyUsage: []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth}, URIs: []*url.URL{uri}}
	leafRaw, err := x509.CreateCertificate(rand.Reader, leaf, issuer, devicePublic, issuerPrivate)
	if err != nil {
		test.Fatal(err)
	}
	crl := &x509.RevocationList{Number: big.NewInt(1), ThisUpdate: now.Add(-time.Second), NextUpdate: now.Add(30 * time.Minute)}
	if revoked {
		crl.RevokedCertificateEntries = []x509.RevocationListEntry{{SerialNumber: leaf.SerialNumber, RevocationTime: now.Add(-time.Second)}}
	}
	crlRaw, err := x509.CreateRevocationList(rand.Reader, crl, issuer, issuerPrivate)
	if err != nil {
		test.Fatal(err)
	}
	delegation, _ := json.Marshal(map[string]any{"version": 1, "sequence": 1, "family": family, "gateway": gateway,
		"authority": string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: issuerRaw})),
		"issued_at": now.Add(-time.Minute).Unix(), "expires_at": now.Add(time.Hour).Unix(), "minimum_revision": 1})
	signature := ed25519.Sign(rootPrivate, append([]byte("family-connect/restricted-issuer/v1\x00"), delegation...))
	directory := bootstrap.Directory{Version: 1, Family: family, IssuedAt: now, ExpiresAt: now.Add(30 * time.Minute),
		Seeds: []bootstrap.Seed{{Transport: "telemost-webrtc", JoinURL: "https://telemost.yandex.ru/j/test-only", Gateway: gateway}}}
	raw, err := json.Marshal(map[string]any{"version": 1, "device": reference, "challenge": base64.StdEncoding.EncodeToString(make([]byte, 32)),
		"issued_at": now.Unix(), "expires_at": now.Add(30 * time.Minute).Unix(), "revision": 1, "minimum_crl": 1,
		"issuer":      map[string]string{"payload": base64.StdEncoding.EncodeToString(delegation), "signature": base64.StdEncoding.EncodeToString(signature)},
		"certificate": string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: leafRaw})),
		"revocations": string(pem.EncodeToMemory(&pem.Block{Type: "X509 CRL", Bytes: crlRaw})), "directory": directory})
	if err != nil {
		test.Fatal(err)
	}
	return Config{Readiness: raw, Identity: identity, Anchor: anchor, Resolver: "1.1.1.1:53"}
}

func TestSignedAcquisitionBorrowsExactProfileAndBoundsLeases(test *testing.T) {
	config := signedConfig(test, time.Now().UTC().Truncate(time.Second), false)
	profile, _, err := wholedevice.DeliveryMaterial(config.Readiness, config.Identity, config.Anchor, time.Now())
	if err != nil {
		test.Fatal(err)
	}
	defer clear(profile)
	_, session, _ := fixture(test, true, pipeDial)
	var owner Owner
	vpn, err := owner.ReserveVPN(context.Background())
	if err != nil {
		test.Fatal(err)
	}
	defer vpn.Release()
	defer owner.Close()
	if err := vpn.Publish(session, sha256.Sum256(profile)); err != nil {
		test.Fatal(err)
	}
	protect := func(int) bool { test.Error("borrowed chat opened underlying socket"); return false }
	clients := []*Client{}
	for index := 0; index < MaxLeases; index++ {
		client, err := owner.Acquire(config, protect)
		if err != nil || client.Route() != "EXISTING_EXIT" {
			test.Fatal("valid exact profile not borrowed", err)
		}
		clients = append(clients, client)
	}
	if client, err := owner.Acquire(config, protect); client != nil || err != ErrUnavailable {
		test.Fatal("ninth lease admitted", err)
	}
	other := signedConfig(test, time.Now().UTC().Truncate(time.Second), false)
	clients[0].Close()
	if client, err := owner.Acquire(other, protect); client != nil || err != ErrUnavailable {
		test.Fatal("different identity borrowed existing exit", err)
	}
	replacement, err := owner.Acquire(config, protect)
	if err != nil {
		test.Fatal("closed handle slot not reusable", err)
	}
	replacement.Close()
	owner.Close()
	owner.Close()
	if owner.active != 0 || len(owner.clients) != 0 || session.Failed() {
		test.Fatal("close leaked leases or killed unrelated VPN")
	}
	if client, err := owner.Acquire(config, protect); client != nil || err != ErrUnavailable {
		test.Fatal("closed owner reopened", err)
	}
	if _, err := owner.ReserveVPN(context.Background()); err != ErrUnavailable {
		test.Fatal("closed owner reserved VPN")
	}
	if strings.Contains(fmt.Sprintf("%+v %#v", config, config), "test-only") {
		test.Fatal("configuration diagnostic exposed room")
	}
	if _, err := json.Marshal(config); !errors.Is(err, ErrDenied) {
		test.Fatal("configuration serialized")
	}
}

func TestInvalidExpiredRevokedMaterialNeverOpensUnderlay(test *testing.T) {
	now := time.Now().UTC().Truncate(time.Second)
	valid := signedConfig(test, now, false)
	wrongIdentity := valid
	wrongIdentity.Identity = make([]byte, 64)
	wrongAnchor := valid
	wrongAnchor.Anchor = make([]byte, 32)
	oversized := valid
	oversized.Readiness = make([]byte, wholedevice.MaxReadiness+1)
	for _, config := range []Config{{}, wrongIdentity, wrongAnchor, oversized, signedConfig(test, now, true), signedConfig(test, now.Add(-2*time.Hour), false)} {
		var owner Owner
		client, err := owner.Acquire(config, func(int) bool { test.Error("invalid material touched network"); return false })
		if client != nil || err != ErrDenied || owner.active != 0 {
			test.Fatal("invalid authorization accepted", err)
		}
		owner.Close()
	}
	var owner Owner
	if client, err := owner.Acquire(valid, nil); client != nil || err != ErrDenied {
		test.Fatal("missing underlay protection accepted")
	}
}

func TestServiceOnlyToVPNDrainsStreamsBeforePublication(test *testing.T) {
	var owner Owner
	defer owner.Close()
	_, session, plane := fixture(test, true, pipeDial)
	var disposed atomic.Int32
	client, err := owner.acquire(time.Now().Add(time.Minute), [32]byte{1}, func(context.Context) (restrictedowner.Session, func(), error) { return session, nil, nil }, func() { disposed.Add(1) })
	if err != nil {
		test.Fatal(err)
	}
	connection, err := client.OpenMailbox(context.Background(), 3*time.Second)
	if err != nil {
		test.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	vpn, err := owner.ReserveVPN(ctx)
	if err != nil {
		test.Fatal(err)
	}
	defer vpn.Release()
	if err := vpn.Wait(ctx); err != nil {
		test.Fatal("service-only drain blocked VPN", err)
	}
	if disposed.Load() != 1 || client.Route() != "UNAVAILABLE" {
		test.Fatal("old lease survived ownership handoff")
	}
	select {
	case <-plane.done:
	default:
		test.Fatal("old carrier not closed before handoff")
	}
	if _, err := connection.Read(make([]byte, 1)); err == nil {
		test.Fatal("old stream still live")
	}
	connection.Close()
	client.Close()
	_, replacement, _ := fixture(test, true, pipeDial)
	if err := vpn.Publish(replacement, [32]byte{2}); err != nil {
		test.Fatal("new VPN failed after drain", err)
	}
	old, err := owner.acquire(time.Now().Add(time.Minute), [32]byte{1}, nil, func() {})
	if old != nil || err != ErrUnavailable {
		test.Fatal("old profile crossed session generation", err)
	}
	current, err := owner.acquire(time.Now().Add(time.Minute), [32]byte{2}, nil, func() {})
	if err != nil || current.Route() != "EXISTING_EXIT" {
		test.Fatal("new matching VPN not reusable", err)
	}
	current.Close()
	if replacement.Failed() {
		test.Fatal("chat release closed replacement VPN")
	}
}
