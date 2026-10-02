package wholedevice

import (
	"bytes"
	"crypto/ecdh"
	"crypto/ed25519"
	"crypto/sha256"
	"crypto/x509"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"errors"
	"io"
	"strconv"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
)

const MaxReadiness = 65536

var ErrBootstrapValidation = errors.New("bootstrap validation failed")

func DeliveryValidationCode(raw, public, anchor []byte, now time.Time) int32 {
	_, _, err := ValidateDelivery(raw, public, anchor, now)
	if err == nil {
		return 0
	}
	if errors.Is(err, ErrBootstrapValidation) {
		return 2
	}
	return 1
}

type issuerEnvelope struct {
	Payload   string `json:"payload"`
	Signature string `json:"signature"`
}

type issuerDelegation struct {
	Version         int    `json:"version"`
	Sequence        int64  `json:"sequence"`
	Family          string `json:"family"`
	Gateway         string `json:"gateway"`
	Authority       string `json:"authority"`
	IssuedAt        int64  `json:"issued_at"`
	ExpiresAt       int64  `json:"expires_at"`
	MinimumRevision int    `json:"minimum_revision"`
}

type ReadinessDelivery struct {
	Version     int             `json:"version"`
	Device      string          `json:"device"`
	Challenge   string          `json:"challenge"`
	IssuedAt    int64           `json:"issued_at"`
	ExpiresAt   int64           `json:"expires_at"`
	Revision    int             `json:"revision"`
	Issuer      issuerEnvelope  `json:"issuer"`
	Certificate string          `json:"certificate"`
	Revocations string          `json:"revocations"`
	MinimumCRL  int64           `json:"minimum_crl"`
	Directory   json.RawMessage `json:"directory"`
}

func (ReadinessDelivery) String() string   { return "[restricted readiness redacted]" }
func (ReadinessDelivery) GoString() string { return "[restricted readiness redacted]" }

func strictDelivery(raw []byte, target any) error {
	if len(raw) == 0 || len(raw) > MaxReadiness {
		return ErrClosed
	}
	var visit func(*json.Decoder, int) error
	visit = func(decoder *json.Decoder, depth int) error {
		if depth > 16 {
			return ErrClosed
		}
		token, err := decoder.Token()
		if err != nil {
			return err
		}
		switch token {
		case json.Delim('{'):
			seen := map[string]bool{}
			for decoder.More() {
				key, err := decoder.Token()
				name, ok := key.(string)
				if err != nil || !ok || seen[name] {
					return ErrClosed
				}
				seen[name] = true
				if err = visit(decoder, depth+1); err != nil {
					return err
				}
			}
			_, err = decoder.Token()
		case json.Delim('['):
			for decoder.More() {
				if err = visit(decoder, depth+1); err != nil {
					return err
				}
			}
			_, err = decoder.Token()
		}
		return err
	}
	if visit(json.NewDecoder(bytes.NewReader(raw)), 0) != nil {
		return ErrClosed
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if decoder.Decode(target) != nil || decoder.Decode(new(any)) != io.EOF {
		return ErrClosed
	}
	return nil
}

func ValidateDelivery(raw, public, anchor []byte, now time.Time) (ReadinessDelivery, familysession.Credentials, error) {
	var delivery ReadinessDelivery
	var trust issuerDelegation
	fail := func() (ReadinessDelivery, familysession.Credentials, error) {
		return ReadinessDelivery{}, familysession.Credentials{}, ErrClosed
	}
	if len(public) != 64 || len(anchor) != 32 || strictDelivery(raw, &delivery) != nil {
		return fail()
	}
	reference := sha256.Sum256(public)
	nonce, err := base64.StdEncoding.DecodeString(delivery.Challenge)
	if err != nil || len(nonce) != 32 || delivery.Device != hex.EncodeToString(reference[:16]) || delivery.Version != 1 || delivery.Revision < 1 || delivery.MinimumCRL < 1 || delivery.IssuedAt > now.Unix() || delivery.ExpiresAt <= now.Unix() || delivery.ExpiresAt <= delivery.IssuedAt || delivery.ExpiresAt-delivery.IssuedAt > 3600 {
		return fail()
	}
	payload, err := base64.StdEncoding.DecodeString(delivery.Issuer.Payload)
	if err != nil || len(payload) > 8192 {
		return fail()
	}
	signature, err := base64.StdEncoding.DecodeString(delivery.Issuer.Signature)
	if err != nil || !ed25519.Verify(anchor, append([]byte("family-connect/restricted-issuer/v1\x00"), payload...), signature) || strictDelivery(payload, &trust) != nil {
		return fail()
	}
	if trust.Version != 1 || trust.Sequence < 1 || trust.MinimumRevision < 1 || delivery.Revision < trust.MinimumRevision || trust.IssuedAt > delivery.IssuedAt || trust.ExpiresAt < delivery.ExpiresAt {
		return fail()
	}
	authorityBlock, rest := pem.Decode([]byte(trust.Authority))
	if authorityBlock == nil || len(bytes.TrimSpace(rest)) != 0 {
		return fail()
	}
	authority, err := x509.ParseCertificate(authorityBlock.Bytes)
	if err != nil || !authority.IsCA || authority.CheckSignatureFrom(authority) != nil {
		return fail()
	}
	certBlock, rest := pem.Decode([]byte(delivery.Certificate))
	if certBlock == nil || len(bytes.TrimSpace(rest)) != 0 {
		return fail()
	}
	certificate, err := x509.ParseCertificate(certBlock.Bytes)
	if err != nil {
		return fail()
	}
	roots := x509.NewCertPool()
	roots.AddCert(authority)
	if _, err = certificate.Verify(x509.VerifyOptions{Roots: roots, CurrentTime: now, KeyUsages: []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth}}); err != nil {
		return fail()
	}
	signing, ok := certificate.PublicKey.(ed25519.PublicKey)
	if !ok || !bytes.Equal(signing, public[32:]) || certificate.Subject.SerialNumber != delivery.Device || len(certificate.URIs) != 1 || certificate.URIs[0].String() != "urn:family-connect:identity:"+hex.EncodeToString(public) {
		return fail()
	}
	want := map[string]bool{"protocol=" + familysession.Protocol: true, "family=" + trust.Family: true, "role=device": true, "revision=" + strconv.Itoa(delivery.Revision): true}
	if len(certificate.Subject.OrganizationalUnit) != 4 {
		return fail()
	}
	for _, claim := range certificate.Subject.OrganizationalUnit {
		if !want[claim] {
			return fail()
		}
		delete(want, claim)
	}
	crlBlock, rest := pem.Decode([]byte(delivery.Revocations))
	if crlBlock == nil || len(bytes.TrimSpace(rest)) != 0 {
		return fail()
	}
	crl, err := x509.ParseRevocationList(crlBlock.Bytes)
	if err != nil || crl.CheckSignatureFrom(authority) != nil || crl.Number == nil || !crl.Number.IsInt64() || crl.Number.Int64() != delivery.MinimumCRL || now.Before(crl.ThisUpdate) || !now.Before(crl.NextUpdate) || crl.NextUpdate.Sub(crl.ThisUpdate) > time.Hour {
		return fail()
	}
	for _, revoked := range crl.RevokedCertificateEntries {
		if revoked.SerialNumber.Cmp(certificate.SerialNumber) == 0 {
			return fail()
		}
	}
	directory, err := bootstrap.ParseDirectory(delivery.Directory, trust.Family, trust.Gateway, now)
	if err != nil {
		return ReadinessDelivery{}, familysession.Credentials{}, errors.Join(ErrClosed, ErrBootstrapValidation)
	}
	for _, until := range []time.Time{certificate.NotAfter, authority.NotAfter, crl.NextUpdate, directory.ExpiresAt, time.Unix(trust.ExpiresAt, 0)} {
		if time.Unix(delivery.ExpiresAt, 0).After(until) {
			return fail()
		}
	}
	credentials := familysession.Credentials{Certificate: delivery.Certificate, Authority: trust.Authority, Revocations: delivery.Revocations, Family: trust.Family, Gateway: trust.Gateway, MinimumRevision: trust.MinimumRevision, MinimumCRL: delivery.MinimumCRL}
	return delivery, credentials, nil
}

func DeliveryMaterial(raw, identity, anchor []byte, now time.Time) ([]byte, []byte, error) {
	if len(identity) != 64 {
		return nil, nil, ErrClosed
	}
	signing := ed25519.NewKeyFromSeed(identity[32:])
	defer clear(signing)
	exchange, err := ecdh.X25519().NewPrivateKey(identity[:32])
	if err != nil {
		return nil, nil, ErrClosed
	}
	public := append(exchange.PublicKey().Bytes(), signing.Public().(ed25519.PublicKey)...)
	delivery, credentials, err := ValidateDelivery(raw, public, anchor, now)
	if err != nil {
		return nil, nil, err
	}
	der, err := x509.MarshalPKCS8PrivateKey(signing)
	if err != nil {
		return nil, nil, ErrClosed
	}
	defer clear(der)
	encoded := pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: der})
	defer clear(encoded)
	credentials.PrivateKey = string(encoded)
	profile, err := json.Marshal(credentials)
	if err != nil {
		return nil, nil, ErrClosed
	}
	if _, _, err = familysession.Configuration(profile, false); err != nil {
		clear(profile)
		return nil, nil, err
	}
	return profile, delivery.Directory, nil
}
