package main

import (
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"encoding/pem"
	"io"
	"math"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

type receipt struct {
	Version    int    `json:"version"`
	Status     string `json:"status"`
	Stage      string `json:"stage"`
	Reason     string `json:"reason"`
	Object     string `json:"object"`
	Comparison string `json:"comparison"`
}

func failed(stage, reason, object, comparison string) receipt {
	return receipt{1, "FAIL", stage, reason, object, comparison}
}

func validate(raw, canaryRaw []byte) receipt {
	configuration, expiry, err := familysession.Configuration(raw, true)
	if err != nil || !expiry.After(time.Now()) {
		return failed("configuration", "rejected", "gateway_profile", "not_evaluated")
	}
	var credentials familysession.Credentials
	if json.Unmarshal(raw, &credentials) != nil {
		return failed("configuration", "malformed", "gateway_profile", "not_evaluated")
	}
	block, remaining := pem.Decode(canaryRaw)
	if block == nil || len(remaining) != 0 {
		return failed("device_parse", "malformed", "device_certificate", "not_evaluated")
	}
	canary, err := x509.ParseCertificate(block.Bytes)
	if err != nil {
		return failed("device_parse", "malformed", "device_certificate", "not_evaluated")
	}
	chains, err := canary.Verify(x509.VerifyOptions{Roots: configuration.ClientCAs, KeyUsages: []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth}})
	if err != nil {
		return failed("device_chain", "rejected", "device_certificate", "not_evaluated")
	}
	state := tls.ConnectionState{Version: tls.VersionTLS13, NegotiatedProtocol: familysession.Protocol, PeerCertificates: []*x509.Certificate{canary}, VerifiedChains: chains}
	if configuration.VerifyConnection(state) != nil {
		return failed("device_admission", "rejected", "device_certificate", "signed_claim_or_revocation")
	}
	gateway, err := x509.ParseCertificate(configuration.Certificates[0].Certificate[0])
	if err != nil {
		return failed("gateway_parse", "malformed", "gateway_certificate", "not_evaluated")
	}
	gatewayChains, err := gateway.Verify(x509.VerifyOptions{Roots: configuration.RootCAs, DNSName: "gateway.family-connect.test", KeyUsages: []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth}})
	if err != nil {
		return failed("gateway_chain", "rejected", "gateway_certificate", "not_evaluated")
	}
	client, _, err := familysession.Configuration(raw, false)
	if err != nil || client.VerifyConnection(tls.ConnectionState{Version: tls.VersionTLS13, NegotiatedProtocol: familysession.Protocol, PeerCertificates: []*x509.Certificate{gateway}, VerifiedChains: gatewayChains}) != nil {
		return failed("gateway_binding", "rejected", "gateway_certificate", "signed_claim_or_revocation")
	}
	revision := 0
	for _, claim := range canary.Subject.OrganizationalUnit {
		if strings.HasPrefix(claim, "revision=") {
			revision, err = strconv.Atoi(strings.TrimPrefix(claim, "revision="))
		}
	}
	if err != nil || revision < credentials.MinimumRevision || revision == math.MaxInt {
		return failed("revision_negative", "successor_unavailable", "device_certificate", "above_signed_revision")
	}
	crlBlock, _ := pem.Decode([]byte(credentials.Revocations))
	crl, err := x509.ParseRevocationList(crlBlock.Bytes)
	if err != nil || crl.Number == nil || !crl.Number.IsInt64() || crl.Number.Int64() == math.MaxInt64 {
		return failed("crl_negative", "successor_unavailable", "crl", "above_signed_sequence")
	}
	for _, mutation := range []string{"family", "revision", "crl"} {
		changed := credentials
		object, comparison := "device_certificate", "wrong_family"
		switch mutation {
		case "family":
			changed.Family = strings.Repeat("0", 32)
			if changed.Family == credentials.Family {
				changed.Family = strings.Repeat("1", 32)
			}
		case "revision":
			changed.MinimumRevision = revision + 1
			comparison = "above_signed_revision"
		case "crl":
			changed.MinimumCRL = crl.Number.Int64() + 1
			object, comparison = "crl", "above_signed_sequence"
		}
		encoded, _ := json.Marshal(changed)
		altered, _, failure := familysession.Configuration(encoded, true)
		if failure == nil && altered.VerifyConnection(state) == nil {
			return failed(mutation+"_negative", "unexpected_acceptance", object, comparison)
		}
	}
	return receipt{1, "PASS", "complete", "validated", "authority", "positive_and_negatives"}
}

func readBounded(path string, limit int64) ([]byte, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()
	return io.ReadAll(io.LimitReader(file, limit+1))
}

func run(arguments []string) receipt {
	if len(arguments) != 2 {
		return failed("input", "arguments", "operator", "not_evaluated")
	}
	profile, err := readBounded(arguments[0], 48<<10)
	if err != nil || len(profile) > 48<<10 {
		return failed("input", "unreadable_or_oversized", "gateway_profile", "not_evaluated")
	}
	defer clear(profile)
	certificate, err := readBounded(arguments[1], 16<<10)
	if err != nil || len(certificate) > 16<<10 {
		return failed("input", "unreadable_or_oversized", "device_certificate", "not_evaluated")
	}
	return validate(profile, certificate)
}

func main() {
	result := run(os.Args[1:])
	if json.NewEncoder(os.Stdout).Encode(result) != nil || result.Status != "PASS" {
		os.Exit(1)
	}
}
