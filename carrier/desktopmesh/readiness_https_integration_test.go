package desktopmesh

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"errors"
	"io"
	"log"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/underlay"
)

func readinessTestHTTPS(test *testing.T, handler http.Handler, protect func(int) bool, trust bool) (*ReadinessHTTPS, *underlay.Network) {
	test.Helper()
	server := httptest.NewUnstartedServer(handler)
	server.Config.ErrorLog = log.New(io.Discard, "", 0)
	server.StartTLS()
	test.Cleanup(server.Close)
	network, err := underlay.New(context.Background(), "1.1.1.1:53", protect)
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(network.Close)
	transport, err := NewReadinessHTTPS(network)
	if err != nil {
		test.Fatal(err)
	}
	transport.origin = server.URL
	if trust {
		roots := x509.NewCertPool()
		roots.AddCert(server.Certificate())
		transport.client.Transport.(*http.Transport).TLSClientConfig = &tls.Config{RootCAs: roots}
	}
	return transport, network
}

func TestReadinessHTTPSRealProtectedTLSAndNoRedirect(test *testing.T) {
	var protected, requests atomic.Int32
	var redirect atomic.Bool
	transport, network := readinessTestHTTPS(test, http.HandlerFunc(func(output http.ResponseWriter, request *http.Request) {
		requests.Add(1)
		if protected.Load() == 0 || request.Method != "POST" || request.Header.Get("X-FC-Probe-ID") != strings.Repeat("a", 32) || request.URL.RawQuery != "" {
			test.Error("unprotected or incompatible readiness request")
		}
		if redirect.Load() {
			http.Redirect(output, request, "/forbidden-replay", http.StatusTemporaryRedirect)
			return
		}
		io.WriteString(output, `{"version":1}`)
	}), func(int) bool { protected.Add(1); return true }, true)
	path := "/friends/restricted-readiness/challenge"
	if raw, err := transport.Post(context.Background(), path, []byte(`{}`), strings.Repeat("a", 32)); err != nil || string(raw) != `{"version":1}` {
		test.Fatal("protected TLS request failed", err)
	}
	redirect.Store(true)
	_, err := transport.Post(context.Background(), path, []byte(`{}`), strings.Repeat("a", 32))
	var failure *ReadinessFailure
	if !errors.As(err, &failure) || failure.Availability || failure.Authorization || requests.Load() != 2 || network.Protected.Load() != 2 {
		test.Fatal("redirect replay or unprotected request")
	}
}

func TestReadinessHTTPSRealTrustAndProtectionFailuresNeverFallback(test *testing.T) {
	for _, denied := range []bool{false, true} {
		var reached atomic.Int32
		transport, network := readinessTestHTTPS(test, http.HandlerFunc(func(http.ResponseWriter, *http.Request) { reached.Add(1) }),
			func(int) bool { return !denied }, false)
		_, err := transport.Post(context.Background(), "/friends/restricted-readiness/challenge", []byte(`{}`), strings.Repeat("b", 32))
		var failure *ReadinessFailure
		if !errors.As(err, &failure) || failure.Availability || failure.Network || reached.Load() != 0 {
			test.Fatal("trust/protection rejection became availability fallback", err)
		}
		if denied && (failure.Code != "UNDERLAY_PROTECTION_REJECTED" || network.Rejected.Load() != 1) {
			test.Fatal("socket protection failure lost")
		}
		if !denied && failure.Code != "TLS_TRUST_REJECTED" {
			test.Fatal("TLS trust failure lost", failure.Code)
		}
	}
}

func TestReadinessHTTPSCancellationDuringBodyIsNotTimeout(test *testing.T) {
	started, release := make(chan struct{}), make(chan struct{})
	transport, _ := readinessTestHTTPS(test, http.HandlerFunc(func(output http.ResponseWriter, request *http.Request) {
		output.WriteHeader(http.StatusOK)
		io.WriteString(output, `{"pending":`)
		output.(http.Flusher).Flush()
		close(started)
		<-release
	}), func(int) bool { return true }, true)
	defer close(release)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	finished := make(chan error, 1)
	go func() {
		_, err := transport.Post(ctx, "/friends/restricted-readiness/challenge", []byte(`{}`), strings.Repeat("c", 32))
		finished <- err
	}()
	select {
	case <-started:
	case <-time.After(3 * time.Second):
		test.Fatal("local TLS body did not start")
	}
	cancel()
	select {
	case err := <-finished:
		if !errors.Is(err, context.Canceled) || errors.Is(err, context.DeadlineExceeded) {
			test.Fatal("cancellation mislabeled", err)
		}
	case <-time.After(3 * time.Second):
		test.Fatal("body cancellation did not complete")
	}
}
