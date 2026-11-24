package coldprovision

import (
	"bytes"
	"crypto/ed25519"
	"crypto/tls"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"encoding/pem"
	"errors"
	"io"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

const Protocol = "family-connect-provisioning-v1"
const Domain = "family-connect/provisioning-locator/v1\x00"
const MaxMessage = 65536
const Timeout = 30 * time.Second

var ErrRejected = errors.New("provisioning rejected")
var ErrUnavailable = errors.New("provisioning unavailable")

type Envelope struct {
	Payload   string `json:"payload"`
	Signature string `json:"signature"`
}

type Locator struct {
	Version int      `json:"version"`
	Issuer  Envelope `json:"issuer"`
	Envelope
}

type Address struct {
	Version           int    `json:"version"`
	Purpose           string `json:"purpose"`
	Sequence          int64  `json:"sequence"`
	IssuedAt          int64  `json:"issued_at"`
	ExpiresAt         int64  `json:"expires_at"`
	GatewayID         string `json:"gateway_id"`
	Room              string `json:"room"`
	ServerCertificate string `json:"server_certificate"`
}

type delegation struct {
	Version         int    `json:"version"`
	Sequence        int64  `json:"sequence"`
	Family          string `json:"family"`
	Gateway         string `json:"gateway"`
	Authority       string `json:"authority"`
	MinimumRevision int    `json:"minimum_revision"`
	IssuedAt        int64  `json:"issued_at"`
	ExpiresAt       int64  `json:"expires_at"`
}

func (Address) String() string   { return "[provisioning locator redacted]" }
func (Address) GoString() string { return "[provisioning locator redacted]" }

func strict(raw []byte, target any) error {
	if len(raw) == 0 || len(raw) > MaxMessage {
		return ErrRejected
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	var walk func(int) error
	walk = func(depth int) error {
		if depth > 12 {
			return ErrRejected
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
					return ErrRejected
				}
				seen[name] = true
				if err = walk(depth + 1); err != nil {
					return err
				}
			}
			_, err = decoder.Token()
		case json.Delim('['):
			for decoder.More() {
				if err = walk(depth + 1); err != nil {
					return err
				}
			}
			_, err = decoder.Token()
		}
		return err
	}
	if walk(0) != nil {
		return ErrRejected
	}
	decoder = json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if decoder.Decode(target) != nil || decoder.Decode(new(any)) != io.EOF {
		return ErrRejected
	}
	return nil
}

func certificate(raw string) (*x509.Certificate, error) {
	block, rest := pem.Decode([]byte(raw))
	if block == nil || block.Type != "CERTIFICATE" || len(bytes.TrimSpace(rest)) != 0 {
		return nil, ErrRejected
	}
	return x509.ParseCertificate(block.Bytes)
}

func Verify(raw, anchor []byte, gateway string, now time.Time) (Address, *tls.Config, error) {
	var locator Locator
	var trust delegation
	var address Address
	fail := func() (Address, *tls.Config, error) { return Address{}, nil, ErrRejected }
	if len(raw) > 16384 || len(anchor) != 32 || strict(raw, &locator) != nil || locator.Version != 1 {
		return fail()
	}
	payload, err := base64.StdEncoding.Strict().DecodeString(locator.Issuer.Payload)
	signature, signatureErr := base64.StdEncoding.Strict().DecodeString(locator.Issuer.Signature)
	if err != nil || signatureErr != nil || !ed25519.Verify(anchor, append([]byte("family-connect/restricted-issuer/v1\x00"), payload...), signature) || strict(payload, &trust) != nil {
		return fail()
	}
	authority, err := certificate(trust.Authority)
	if err != nil || !authority.IsCA || authority.CheckSignatureFrom(authority) != nil || trust.Version != 1 || trust.Sequence < 1 || trust.MinimumRevision < 1 || len(trust.Family) != 32 || len(trust.Gateway) != 32 || trust.IssuedAt > now.Unix() || trust.ExpiresAt <= now.Unix() {
		return fail()
	}
	issuer, ok := authority.PublicKey.(ed25519.PublicKey)
	if !ok {
		return fail()
	}
	payload, err = base64.StdEncoding.Strict().DecodeString(locator.Payload)
	signature, signatureErr = base64.StdEncoding.Strict().DecodeString(locator.Signature)
	if err != nil || signatureErr != nil || !ed25519.Verify(issuer, append([]byte(Domain), payload...), signature) || strict(payload, &address) != nil {
		return fail()
	}
	if address.Version != 1 || address.Purpose != Protocol || address.Sequence < 1 || address.GatewayID != gateway || (gateway != "nl-amsterdam-1" && gateway != "nl-amsterdam-2") || !roombroker.ValidJoinURL(address.Room) || address.IssuedAt < trust.IssuedAt || address.IssuedAt > now.Unix() || address.ExpiresAt <= now.Unix() || address.ExpiresAt > trust.ExpiresAt || address.ExpiresAt-address.IssuedAt > int64(bootstrap.MaxAge/time.Second) {
		return fail()
	}
	server, err := certificate(address.ServerCertificate)
	if err != nil || server.IsCA || server.NotAfter.Unix() < address.ExpiresAt {
		return fail()
	}
	roots := x509.NewCertPool()
	roots.AddCert(authority)
	if _, err = server.Verify(x509.VerifyOptions{Roots: roots, CurrentTime: now, DNSName: "gateway.family-connect.test", KeyUsages: []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth}}); err != nil {
		return fail()
	}
	config := &tls.Config{MinVersion: tls.VersionTLS13, MaxVersion: tls.VersionTLS13, RootCAs: roots, ServerName: "gateway.family-connect.test", NextProtos: []string{Protocol}, SessionTicketsDisabled: true}
	config.VerifyConnection = func(state tls.ConnectionState) error {
		if state.DidResume || state.NegotiatedProtocol != Protocol || len(state.PeerCertificates) != 1 || !bytes.Equal(state.PeerCertificates[0].Raw, server.Raw) || !time.Now().Before(time.Unix(address.ExpiresAt, 0)) {
			return ErrRejected
		}
		return nil
	}
	return address, config, nil
}
