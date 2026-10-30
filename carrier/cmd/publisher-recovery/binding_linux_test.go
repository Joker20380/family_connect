package main

import (
	"crypto/ed25519"
	"crypto/rand"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/json"
	"encoding/pem"
	"math/big"
	"os"
	"path/filepath"
	"syscall"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

func bindingFixture(t *testing.T) (familysession.Credentials, configuration, time.Time) {
	t.Helper()
	now := time.Now().UTC().Truncate(time.Second)
	public, signer, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	authorityTemplate := &x509.Certificate{SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: "synthetic recovery authority"},
		NotBefore: now.Add(-24 * time.Hour), NotAfter: now.Add(48 * time.Hour), IsCA: true, BasicConstraintsValid: true,
		KeyUsage: x509.KeyUsageCertSign | x509.KeyUsageCRLSign, SubjectKeyId: []byte{1, 2, 3, 4}}
	authorityRaw, err := x509.CreateCertificate(rand.Reader, authorityTemplate, authorityTemplate, public, signer)
	if err != nil {
		t.Fatal(err)
	}
	authority, err := x509.ParseCertificate(authorityRaw)
	if err != nil {
		t.Fatal(err)
	}
	leafPublic, leafKey, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	family, gateway := "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
	leafTemplate := &x509.Certificate{SerialNumber: big.NewInt(2), Subject: pkix.Name{SerialNumber: gateway,
		OrganizationalUnit: []string{"family=" + family, "role=gateway", "protocol=" + familysession.Protocol, "revision=1"}},
		NotBefore: now.Add(-5 * time.Hour), NotAfter: now.Add(-time.Hour), KeyUsage: x509.KeyUsageDigitalSignature}
	leaf, err := x509.CreateCertificate(rand.Reader, leafTemplate, authority, leafPublic, signer)
	if err != nil {
		t.Fatal(err)
	}
	crl, err := x509.CreateRevocationList(rand.Reader, &x509.RevocationList{Number: big.NewInt(7), ThisUpdate: now.Add(-5 * time.Hour), NextUpdate: now.Add(-time.Hour)}, authority, signer)
	if err != nil {
		t.Fatal(err)
	}
	key, err := x509.MarshalPKCS8PrivateKey(leafKey)
	if err != nil {
		t.Fatal(err)
	}
	profile := familysession.Credentials{Authority: string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: authorityRaw})),
		Certificate: string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: leaf})), PrivateKey: string(pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: key})),
		Revocations: string(pem.EncodeToMemory(&pem.Block{Type: "X509 CRL", Bytes: crl})), Family: family, Gateway: gateway, MinimumRevision: 1, MinimumCRL: 7}
	raw, err := json.Marshal(profile)
	if err != nil {
		t.Fatal(err)
	}
	return profile, configuration{Family: family, Gateway: gateway, ProfileSHA256: digest(raw), AuthoritySHA256: digest([]byte(profile.Authority))}, now
}

func TestExpiredBindingIsNotCurrentMaterial(t *testing.T) {
	profile, config, now := bindingFixture(t)
	raw, _ := json.Marshal(profile)
	if err := historicalBinding(raw, config, now); err != nil {
		t.Fatal(err)
	}
	if _, _, err := familysession.Configuration(raw, true); err == nil {
		t.Fatal("expired profile became current")
	}
	if digest(raw) != config.ProfileSHA256 || profile.MinimumCRL != 7 {
		t.Fatal("profile changed")
	}
}

func TestHistoricalBindingRejectsChanges(t *testing.T) {
	for _, field := range []string{"predecessor", "authority", "family", "gateway", "future", "certificate", "crl", "floor", "key"} {
		t.Run(field, func(t *testing.T) {
			profile, config, now := bindingFixture(t)
			switch field {
			case "predecessor":
				config.ProfileSHA256 = "bad"
			case "authority":
				config.AuthoritySHA256 = "bad"
			case "family":
				config.Family = "cccccccccccccccccccccccccccccccc"
			case "gateway":
				config.Gateway = "cccccccccccccccccccccccccccccccc"
			case "future":
				now = now.Add(-6 * time.Hour)
			case "certificate":
				profile.Certificate = profile.Authority
			case "crl":
				profile.Revocations = profile.Authority
			case "floor":
				profile.MinimumCRL++
			case "key":
				profile.PrivateKey = "invalid"
			}
			raw, _ := json.Marshal(profile)
			if field == "certificate" || field == "crl" || field == "floor" || field == "key" {
				config.ProfileSHA256 = digest(raw)
			}
			if err := historicalBinding(raw, config, now); err == nil {
				t.Fatal("invalid binding accepted")
			}
		})
	}
}

func TestInvalidAuthoritySignatureRejected(t *testing.T) {
	profile, config, now := bindingFixture(t)
	block, _ := pem.Decode([]byte(profile.Authority))
	block.Bytes[len(block.Bytes)-1] ^= 1
	profile.Authority = string(pem.EncodeToMemory(block))
	raw, _ := json.Marshal(profile)
	config.ProfileSHA256 = digest(raw)
	config.AuthoritySHA256 = digest([]byte(profile.Authority))
	if err := historicalBinding(raw, config, now); err == nil {
		t.Fatal("invalid authority signature")
	}
}

func TestExactPublisherContractAndCanonicalBoundary(t *testing.T) {
	if os.Geteuid() != 0 {
		t.Skip("isolated root fixture required")
	}
	root, err := os.MkdirTemp("/var/lib", "publisher-recovery-test-")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(root)
	os.Chmod(root, 0750)
	os.Chown(root, 0, 41003)
	profile, config, now := bindingFixture(t)
	raw, _ := json.Marshal(profile)
	config.Profile = filepath.Join(root, "profile.json")
	os.WriteFile(config.Profile, raw, 0640)
	os.Chown(config.Profile, 0, 41003)
	publisher := filepath.Join(root, "publisher")
	os.Mkdir(publisher, 0700)
	config.Target = filepath.Join(publisher, "directory.json")
	executable := filepath.Join(root, "accepted-publisher")
	os.WriteFile(executable, []byte("synthetic accepted publisher"), 0600)
	contract := []any{[]any{executable, digest([]byte("synthetic accepted publisher")), map[string]any{"uid": 0, "gid": 0, "mode": 0600}}}
	encoded, _ := json.Marshal(contract)
	config.PublisherContractSHA256 = digest(encoded)
	info, _ := os.Stat(publisher)
	metadata := info.Sys().(*syscall.Stat_t)
	locator := map[string]any{"profile": config.Profile, "directory": map[string]any{"path": config.Target, "publisher_contract": contract,
		"publisher_parent": map[string]any{"path": publisher, "uid": metadata.Uid, "gid": metadata.Gid, "mode": metadata.Mode & 07777, "device": metadata.Dev, "inode": metadata.Ino}}}
	encoded, _ = json.Marshal(locator)
	config.Locator = filepath.Join(root, "locator.json")
	os.WriteFile(config.Locator, encoded, 0640)
	config.LocatorSHA256 = digest(encoded)
	if err = validateBinding(config, now); err != nil {
		t.Fatal(err)
	}
	bad := config
	bad.PublisherContractSHA256 = "bad"
	if err = validateBinding(bad, now); err == nil {
		t.Fatal("wrong contract hash")
	}
	bad = config
	bad.Target = filepath.Join(root, "caller-selected")
	if err = validateBinding(bad, now); err == nil {
		t.Fatal("wrong target")
	}
	os.WriteFile(executable, []byte("changed publisher"), 0600)
	if err = validateBinding(config, now); err == nil {
		t.Fatal("changed writer accepted")
	}
	current, _ := os.ReadFile(config.Profile)
	if string(current) != string(raw) {
		t.Fatal("profile changed")
	}
}
