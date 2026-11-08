package main

import (
	"bytes"
	"context"
	"crypto/tls"
	"crypto/x509"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/Joker20380/family_connect/carrier/coldprovision"
)

type roundTrip func(*http.Request) (*http.Response, error)

func (operation roundTrip) RoundTrip(request *http.Request) (*http.Response, error) {
	return operation(request)
}

func TestAuthorityBackendBoundedRPC(test *testing.T) {
	calls := 0
	body := []byte(`{"accepted":true}`)
	status := http.StatusOK
	backend := authorityBackend(roundTrip(func(request *http.Request) (*http.Response, error) {
		calls++
		if request.Method != "POST" || request.URL.Scheme != "https" || request.URL.Host != "185.251.89.19:8443" ||
			request.Header.Get("X-FC-Probe-ID") != strings.Repeat("a", 32) {
			test.Fatal("authority destination or correlation changed")
		}
		return &http.Response{StatusCode: status, Header: http.Header{"Location": []string{"https://example.invalid/"}},
			Body: io.NopCloser(bytes.NewReader(body)), Request: request}, nil
	}))
	for _, path := range []string{"/tcp", "/dns-query", "/friends/activate", "/friends/restricted-readiness/ack", "https://example.invalid"} {
		if _, err := backend(context.Background(), coldprovision.Request{Path: path, ID: strings.Repeat("a", 32)}); err == nil {
			test.Fatal("unrestricted operation accepted")
		}
	}
	if calls != 0 {
		test.Fatal("rejected requests reached authority")
	}
	for _, path := range []string{coldprovision.Challenge, coldprovision.Fetch} {
		reply, err := backend(context.Background(), coldprovision.Request{Path: path, ID: strings.Repeat("a", 32)})
		if err != nil || reply.Status != 200 || !bytes.Equal(reply.Body, body) {
			test.Fatal("bounded RPC failed")
		}
	}
	status = http.StatusFound
	reply, err := backend(context.Background(), coldprovision.Request{Path: coldprovision.Fetch, ID: strings.Repeat("a", 32)})
	if err != nil || reply.Status != 302 || calls != 3 {
		test.Fatal("redirect followed or changed")
	}
	body = bytes.Repeat([]byte("x"), coldprovision.MaxMessage+1)
	if _, err := backend(context.Background(), coldprovision.Request{Path: coldprovision.Fetch, ID: strings.Repeat("a", 32)}); err == nil {
		test.Fatal("oversized response accepted")
	}
	for _, address := range []string{"http://185.251.89.19:8443", "https://example.invalid", "192.0.2.1:80"} {
		if _, err := entryBackend(address); err == nil {
			test.Fatal("arbitrary upstream accepted")
		}
	}
}

func TestAuthorityBackendVerifiesTLS(test *testing.T) {
	server := httptest.NewTLSServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		_, _ = writer.Write([]byte(`{}`))
	}))
	defer server.Close()
	transport := &http.Transport{Proxy: nil, DialContext: func(ctx context.Context, network, address string) (net.Conn, error) {
		return (&net.Dialer{}).DialContext(ctx, network, server.Listener.Addr().String())
	}}
	defer transport.CloseIdleConnections()
	request := coldprovision.Request{Path: coldprovision.Challenge, ID: strings.Repeat("a", 32)}
	if _, err := authorityBackend(transport)(context.Background(), request); err == nil {
		test.Fatal("untrusted authority accepted")
	}
	roots := x509.NewCertPool()
	roots.AddCert(server.Certificate())
	trusted := transport.Clone()
	trusted.TLSClientConfig = &tls.Config{RootCAs: roots}
	defer trusted.CloseIdleConnections()
	if _, err := authorityBackend(trusted)(context.Background(), request); err == nil {
		test.Fatal("wrong authority hostname accepted")
	}
}
