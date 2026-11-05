package familysession

import (
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
)

func ValidateLocalSuccessor(previous []byte, public Credentials) error {
	if public.PrivateKey != "" {
		return ErrRejected
	}
	var original Credentials
	if json.Unmarshal(previous, &original) != nil {
		return ErrRejected
	}
	config, _, err := MuxConfiguration(previous, true, true)
	if err != nil {
		return ErrRejected
	}
	local, err := x509.ParseCertificate(config.Certificates[0].Certificate[0])
	if err != nil {
		return ErrRejected
	}
	public.PrivateKey = original.PrivateKey
	raw, err := json.Marshal(public)
	if err != nil {
		return ErrRejected
	}
	defer clear(raw)
	if _, _, err = MuxConfiguration(raw, true, true); err != nil {
		return ErrRejected
	}
	connection := tls.ConnectionState{PeerCertificates: []*x509.Certificate{local}}
	before, err := initialRenewalState(previous, connection)
	if err != nil {
		return ErrRejected
	}
	after, err := initialRenewalState(raw, connection)
	if err != nil || !compatibleSuccessor(before, after) || after.verify(local, false) != nil {
		return ErrRejected
	}
	return nil
}
