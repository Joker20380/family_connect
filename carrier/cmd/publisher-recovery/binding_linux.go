package main

import (
	"bytes"
	"crypto/ed25519"
	"crypto/sha256"
	"crypto/tls"
	"crypto/x509"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"errors"
	"io"
	"os"
	"path/filepath"
	"syscall"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

func digest(raw []byte) string {
	hash := sha256.Sum256(raw)
	return hex.EncodeToString(hash[:])
}

func historicalBinding(raw []byte, config configuration, now time.Time) error {
	if digest(raw) != config.ProfileSHA256 {
		return errors.New("recovery_predecessor_hash")
	}
	var profile familysession.Credentials
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if decoder.Decode(&profile) != nil || decoder.Decode(new(any)) != io.EOF {
		return errors.New("recovery_profile_schema")
	}
	if profile.Family != config.Family || profile.Gateway != config.Gateway || len(profile.Family) != 32 || len(profile.Gateway) != 32 || profile.MinimumRevision < 1 || profile.MinimumCRL < 1 {
		return errors.New("recovery_profile_binding")
	}
	if digest([]byte(profile.Authority)) != config.AuthoritySHA256 {
		return errors.New("recovery_authority_identity")
	}
	authorityBlock, rest := pem.Decode([]byte(profile.Authority))
	if authorityBlock == nil || len(rest) != 0 {
		return errors.New("recovery_authority_encoding")
	}
	authority, err := x509.ParseCertificate(authorityBlock.Bytes)
	if err != nil || !authority.IsCA || authority.CheckSignatureFrom(authority) != nil || now.Before(authority.NotBefore) || !now.Before(authority.NotAfter) {
		return errors.New("recovery_authority_signature")
	}
	if _, ok := authority.PublicKey.(ed25519.PublicKey); !ok {
		return errors.New("recovery_authority_key")
	}
	identity, err := tls.X509KeyPair([]byte(profile.Certificate), []byte(profile.PrivateKey))
	if err != nil || len(identity.Certificate) != 1 {
		return errors.New("recovery_leaf_key")
	}
	leaf, err := x509.ParseCertificate(identity.Certificate[0])
	if err != nil || leaf.CheckSignatureFrom(authority) != nil || leaf.Subject.SerialNumber != config.Gateway || now.Before(leaf.NotBefore) {
		return errors.New("recovery_leaf_binding")
	}
	claims := map[string]bool{}
	for _, claim := range leaf.Subject.OrganizationalUnit {
		claims[claim] = true
	}
	if !claims["family="+config.Family] || !claims["role=gateway"] || !claims["protocol="+familysession.Protocol] {
		return errors.New("recovery_leaf_claims")
	}
	crlBlock, rest := pem.Decode([]byte(profile.Revocations))
	if crlBlock == nil || len(rest) != 0 {
		return errors.New("recovery_crl_encoding")
	}
	crl, err := x509.ParseRevocationList(crlBlock.Bytes)
	if err != nil || crl.CheckSignatureFrom(authority) != nil || crl.Number == nil || !crl.Number.IsInt64() || crl.Number.Int64() != profile.MinimumCRL || now.Before(crl.ThisUpdate) {
		return errors.New("recovery_crl_binding")
	}
	if now.Before(leaf.NotAfter) && now.Before(crl.NextUpdate) {
		return errors.New("recovery_not_required")
	}
	for _, entry := range crl.RevokedCertificateEntries {
		if entry.SerialNumber.Cmp(leaf.SerialNumber) == 0 {
			return errors.New("recovery_leaf_revoked")
		}
	}
	return nil
}

func validateBinding(config configuration, now time.Time) error {
	raw, err := roombroker.LoadCredentials(config.Profile)
	if err != nil {
		return errors.New("recovery_profile_boundary")
	}
	defer clear(raw)
	if err = historicalBinding(raw, config, now); err != nil {
		return err
	}
	locatorRaw, err := os.ReadFile(config.Locator)
	if err != nil || digest(locatorRaw) != config.LocatorSHA256 {
		return errors.New("recovery_locator_changed")
	}
	var locator struct {
		Profile   string `json:"profile"`
		Directory struct {
			Path              string            `json:"path"`
			PublisherContract []json.RawMessage `json:"publisher_contract"`
			PublisherParent   struct {
				Path   string `json:"path"`
				UID    uint32 `json:"uid"`
				GID    uint32 `json:"gid"`
				Mode   uint32 `json:"mode"`
				Device uint64 `json:"device"`
				Inode  uint64 `json:"inode"`
			} `json:"publisher_parent"`
		} `json:"directory"`
	}
	if json.Unmarshal(locatorRaw, &locator) != nil || locator.Profile != config.Profile || locator.Directory.Path != config.Target || len(locator.Directory.PublisherContract) == 0 {
		return errors.New("recovery_publisher_contract")
	}
	parent := locator.Directory.PublisherParent
	info, err := os.Lstat(parent.Path)
	if err != nil || !info.IsDir() || parent.Path != filepath.Dir(config.Target) {
		return errors.New("recovery_publisher_parent")
	}
	actual, ok := info.Sys().(*syscall.Stat_t)
	if !ok || actual.Uid != parent.UID || actual.Gid != parent.GID || actual.Mode&07777 != parent.Mode || actual.Dev != parent.Device || actual.Ino != parent.Inode {
		return errors.New("recovery_publisher_parent")
	}
	var contract any
	encoded, err := json.Marshal(locator.Directory.PublisherContract)
	if err != nil || json.Unmarshal(encoded, &contract) != nil {
		return errors.New("recovery_publisher_contract")
	}
	encoded, err = json.Marshal(contract)
	if err != nil || digest(encoded) != config.PublisherContractSHA256 {
		return errors.New("recovery_publisher_contract")
	}
	for _, entry := range locator.Directory.PublisherContract {
		var values []json.RawMessage
		var path, expected string
		var metadata struct {
			UID  uint32 `json:"uid"`
			GID  uint32 `json:"gid"`
			Mode uint32 `json:"mode"`
		}
		if json.Unmarshal(entry, &values) != nil || len(values) != 3 || json.Unmarshal(values[0], &path) != nil || json.Unmarshal(values[1], &expected) != nil || json.Unmarshal(values[2], &metadata) != nil {
			return errors.New("recovery_publisher_contract")
		}
		info, err := os.Lstat(path)
		if err != nil || !info.Mode().IsRegular() || uint32(info.Mode().Perm()) != metadata.Mode {
			return errors.New("recovery_publisher_contract")
		}
		actual, ok := info.Sys().(*syscall.Stat_t)
		if !ok || actual.Nlink != 1 || actual.Uid != metadata.UID || actual.Gid != metadata.GID {
			return errors.New("recovery_publisher_contract")
		}
		content, err := os.ReadFile(path)
		if err != nil || digest(content) != expected {
			return errors.New("recovery_publisher_contract")
		}
	}
	return nil
}
