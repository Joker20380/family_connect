package bridge

import (
	"bytes"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"errors"
	"io"
	"net"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
)

type ImportMaterial struct {
	Version   int    `json:"version"`
	Profile   []byte `json:"profile"`
	Directory []byte `json:"directory"`
	Resolver  string `json:"resolver"`
}

func ValidateMaterial(raw []byte) error {
	rejected := errors.New("material rejected")
	if len(raw) == 0 || len(raw) > 96<<10 {
		return rejected
	}
	if uniqueJSON(json.NewDecoder(bytes.NewReader(raw)), 0) != nil {
		return rejected
	}
	var fields map[string]json.RawMessage
	if json.Unmarshal(raw, &fields) != nil || len(fields) != 4 {
		return rejected
	}
	for _, name := range []string{"version", "profile", "directory", "resolver"} {
		if _, present := fields[name]; !present {
			return rejected
		}
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	var material ImportMaterial
	if decoder.Decode(&material) != nil || decoder.Decode(new(any)) != io.EOF {
		return rejected
	}
	defer clear(material.Profile)
	defer clear(material.Directory)
	if material.Version != 1 || len(material.Profile) > 48<<10 || len(material.Directory) > bootstrap.MaxDirectory {
		return rejected
	}
	if uniqueJSON(json.NewDecoder(bytes.NewReader(material.Profile)), 0) != nil {
		return rejected
	}
	host, port, err := net.SplitHostPort(material.Resolver)
	if err != nil || net.ParseIP(host).To4() == nil || port != "53" {
		return rejected
	}
	config, _, err := familysession.Configuration(material.Profile, true)
	if err != nil {
		return rejected
	}
	certificate, err := x509.ParseCertificate(config.Certificates[0].Certificate[0])
	if err != nil {
		return rejected
	}
	chains, err := certificate.Verify(x509.VerifyOptions{Roots: config.RootCAs, CurrentTime: time.Now(), KeyUsages: []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth}})
	if err != nil {
		return rejected
	}
	if config.VerifyConnection(tls.ConnectionState{Version: tls.VersionTLS13, NegotiatedProtocol: familysession.Protocol,
		PeerCertificates: []*x509.Certificate{certificate}, VerifiedChains: chains}) != nil {
		return rejected
	}
	var credentials familysession.Credentials
	if json.Unmarshal(material.Profile, &credentials) != nil {
		return rejected
	}
	if _, err := bootstrap.ParseDirectory(material.Directory, credentials.Family, credentials.Gateway, time.Now()); err != nil {
		return rejected
	}
	return nil
}

func uniqueJSON(decoder *json.Decoder, depth int) error {
	if depth > 16 {
		return errors.New("depth")
	}
	token, err := decoder.Token()
	if err != nil {
		return err
	}
	if token == json.Delim('{') {
		keys := map[string]bool{}
		for decoder.More() {
			key, err := decoder.Token()
			name, ok := key.(string)
			if err != nil || !ok || keys[name] {
				return errors.New("key")
			}
			keys[name] = true
			if err := uniqueJSON(decoder, depth+1); err != nil {
				return err
			}
		}
		_, err = decoder.Token()
	} else if token == json.Delim('[') {
		for decoder.More() {
			if err := uniqueJSON(decoder, depth+1); err != nil {
				return err
			}
		}
		_, err = decoder.Token()
	}
	return err
}
