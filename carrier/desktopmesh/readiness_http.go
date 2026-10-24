package desktopmesh

import (
	"bytes"
	"context"
	"crypto/tls"
	"crypto/x509"
	"errors"
	"io"
	"net"
	"net/http"
	"net/url"
	"sync"

	"github.com/Joker20380/family_connect/carrier/underlay"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

const readinessOrigin = "https://185.251.89.19:8443"

type ReadinessHTTPS struct {
	client *http.Client
	origin string
}

func NewReadinessHTTPS(network *underlay.Network) (*ReadinessHTTPS, error) {
	if network == nil {
		return nil, ErrConfiguration
	}
	client := network.HTTPClient()
	client.CheckRedirect = func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }
	return &ReadinessHTTPS{client: client, origin: readinessOrigin}, nil
}

func readinessPath(path string) bool {
	switch path {
	case "/friends/restricted-readiness", "/friends/restricted-readiness/challenge", "/friends/restricted-readiness/ack-challenge", "/friends/restricted-readiness/ack":
		return true
	default:
		return false
	}
}

func readinessStatus(path string, status int) error {
	if status == http.StatusOK {
		return nil
	}
	if path == "/friends/restricted-readiness/challenge" {
		switch {
		case status == 401 || status == 403:
			return &ReadinessFailure{Code: "CHALLENGE_UNAUTHORIZED", Authorization: true}
		case status == 429 || status >= 500 && status <= 599:
			return &ReadinessFailure{Code: "CHALLENGE_TEMPORARY_SERVER_FAILURE", Availability: true}
		default:
			return &ReadinessFailure{Code: "CHALLENGE_INCOMPATIBLE_RESPONSE"}
		}
	}
	switch {
	case status == 401 || status == 403:
		return &ReadinessFailure{Code: "AUTHORIZATION_REJECTED", Authorization: true}
	case status == 429 || status >= 500 && status <= 599:
		return &ReadinessFailure{Code: "FETCH_TEMPORARY_SERVER_FAILURE", Availability: true}
	default:
		return &ReadinessFailure{Code: "FETCH_INCOMPATIBLE_RESPONSE"}
	}
}

func readinessNetworkFailure(path string, err error) error {
	if errors.Is(err, underlay.ErrDenied) {
		return &ReadinessFailure{Code: "UNDERLAY_PROTECTION_REJECTED"}
	}
	for {
		wrapped, valid := err.(*url.Error)
		if !valid {
			break
		}
		err = wrapped.Err
	}
	var certificate *tls.CertificateVerificationError
	var authority x509.UnknownAuthorityError
	var hostname x509.HostnameError
	var invalid x509.CertificateInvalidError
	var record tls.RecordHeaderError
	var alert tls.AlertError
	var operation *net.OpError
	if errors.As(err, &certificate) || errors.As(err, &authority) || errors.As(err, &hostname) || errors.As(err, &invalid) ||
		errors.As(err, &record) || errors.As(err, &alert) || (errors.As(err, &operation) && operation.Net == "tls") {
		return &ReadinessFailure{Code: "TLS_TRUST_REJECTED"}
	}
	var network net.Error
	available := errors.As(err, &network)
	code := "FETCH_NETWORK_FAILURE"
	if path == "/friends/restricted-readiness/challenge" {
		code = "CHALLENGE_TEMPORARY_SERVER_FAILURE"
		if available && network.Timeout() {
			code = "CHALLENGE_TIMEOUT"
		}
	}
	return &ReadinessFailure{Code: code, Availability: available, Network: available}
}

func (transport *ReadinessHTTPS) Post(ctx context.Context, path string, body []byte, probe string) ([]byte, error) {
	if !readinessPath(path) || !validProbeID(probe) || len(body) == 0 || len(body) > 8192 {
		return nil, ErrConfiguration
	}
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}
	request, err := http.NewRequestWithContext(ctx, http.MethodPost, transport.origin+path, bytes.NewReader(body))
	if err != nil {
		return nil, ErrConfiguration
	}
	request.Header.Set("Content-Type", "application/json")
	request.Header.Set("X-FC-Probe-ID", probe)
	response, err := transport.client.Do(request)
	if err != nil {
		if ctx.Err() != nil {
			return nil, ctx.Err()
		}
		return nil, readinessNetworkFailure(path, err)
	}
	defer response.Body.Close()
	if err := readinessStatus(path, response.StatusCode); err != nil {
		return nil, err
	}
	limit := 16384
	if path == "/friends/restricted-readiness" {
		limit = wholedevice.MaxReadiness
	}
	raw, err := io.ReadAll(io.LimitReader(response.Body, int64(limit)+1))
	if ctx.Err() != nil {
		clear(raw)
		return nil, ctx.Err()
	}
	if err != nil {
		clear(raw)
		return nil, readinessNetworkFailure(path, err)
	}
	var value map[string]any
	if strictReadinessJSON(raw, limit, &value) != nil || value == nil {
		clear(raw)
		code := "FETCH_INCOMPATIBLE_RESPONSE"
		if path == "/friends/restricted-readiness/challenge" {
			code = "CHALLENGE_INCOMPATIBLE_RESPONSE"
		}
		return nil, &ReadinessFailure{Code: code}
	}
	return raw, nil
}

type ReadinessRoute struct {
	mu       sync.Mutex
	https    ReadinessTransport
	relay    ReadinessTransport
	selected bool
}

func NewReadinessRoute(https, relay ReadinessTransport) (*ReadinessRoute, error) {
	if https == nil {
		return nil, ErrConfiguration
	}
	return &ReadinessRoute{https: https, relay: relay}, nil
}

func (route *ReadinessRoute) Post(ctx context.Context, path string, body []byte, probe string) ([]byte, error) {
	if !readinessPath(path) || !validProbeID(probe) || len(body) == 0 || len(body) > 8192 {
		return nil, ErrConfiguration
	}
	route.mu.Lock()
	defer route.mu.Unlock()
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}
	if route.selected {
		return route.relay.Post(ctx, path, body, probe)
	}
	raw, err := route.https.Post(ctx, path, body, probe)
	var failure *ReadinessFailure
	challenge := path == "/friends/restricted-readiness/challenge" || path == "/friends/restricted-readiness/ack-challenge"
	if ctx.Err() == nil && challenge && route.relay != nil && errors.As(err, &failure) && failure.Network && !failure.Authorization {
		clear(raw)
		route.selected = true
		return route.relay.Post(ctx, path, body, probe)
	}
	if ctx.Err() != nil {
		clear(raw)
		return nil, ctx.Err()
	}
	return raw, err
}
