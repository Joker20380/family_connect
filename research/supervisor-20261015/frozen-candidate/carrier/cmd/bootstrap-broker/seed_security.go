package main

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

func seedRecoverySecurity(path, family, gateway string) func(context.Context) (time.Time, error) {
	return func(ctx context.Context) (time.Time, error) {
		if ctx.Err() != nil {
			return time.Time{}, ctx.Err()
		}
		raw, err := roombroker.LoadCredentials(path)
		if err != nil {
			return time.Time{}, err
		}
		defer clear(raw)
		var credentials familysession.Credentials
		if json.Unmarshal(raw, &credentials) != nil || credentials.Family != family || credentials.Gateway != gateway {
			return time.Time{}, familysession.ErrRejected
		}
		config, deadline, err := familysession.Configuration(raw, false)
		if err != nil || !time.Now().Before(deadline) {
			return time.Time{}, familysession.ErrRejected
		}
		leaf, err := x509.ParseCertificate(config.Certificates[0].Certificate[0])
		if err != nil {
			return time.Time{}, familysession.ErrRejected
		}
		chains, err := leaf.Verify(x509.VerifyOptions{Roots: config.RootCAs, DNSName: config.ServerName, KeyUsages: []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth}})
		if err != nil {
			return time.Time{}, familysession.ErrRejected
		}
		if config.VerifyConnection(tls.ConnectionState{Version: tls.VersionTLS13, NegotiatedProtocol: familysession.Protocol, PeerCertificates: []*x509.Certificate{leaf}, VerifiedChains: chains}) != nil {
			return time.Time{}, familysession.ErrRejected
		}
		return deadline, ctx.Err()
	}
}
