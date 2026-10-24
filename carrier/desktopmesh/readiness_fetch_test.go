package desktopmesh

import (
	"bytes"
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"errors"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"time"
)

type readinessPost func(context.Context, string, []byte, string) ([]byte, error)

func (post readinessPost) Post(ctx context.Context, path string, body []byte, probe string) ([]byte, error) {
	return post(ctx, path, body, probe)
}

func testReadinessClient(test *testing.T) *ReadinessClient {
	test.Helper()
	client, err := NewReadinessClient(make([]byte, 64), bytes.Repeat([]byte{1}, 32))
	if err != nil {
		test.Fatal(err)
	}
	client.clock = func() time.Time { return time.Unix(200, 0) }
	test.Cleanup(client.Close)
	return client
}

func TestReadinessProofMatchesPythonAndAndroidGolden(test *testing.T) {
	raw, err := os.ReadFile(filepath.Join("..", "..", "tests", "vectors", "control-v1", "TEST-ONLY-identity.json"))
	if err != nil {
		test.Fatal(err)
	}
	var vector map[string]any
	if json.Unmarshal(raw, &vector) != nil || vector["test_only"] != true {
		test.Fatal("public synthetic vector required")
	}
	identity, _ := base64.StdEncoding.DecodeString(vector["rns_private_b64"].(string))
	wireguard, _ := base64.StdEncoding.DecodeString(vector["wireguard_public_key"].(string))
	client, err := NewReadinessClient(identity, wireguard)
	if err != nil {
		test.Fatal(err)
	}
	defer client.Close()
	actual, err := client.proof(base64.StdEncoding.EncodeToString(make([]byte, 32)))
	if err != nil {
		test.Fatal(err)
	}
	expected, err := os.ReadFile(filepath.Join("..", "..", "tests", "vectors", "control-identity-v1", "identity-binding-proof.json"))
	if err != nil {
		test.Fatal(err)
	}
	var proof, golden map[string]any
	if json.Unmarshal(actual, &proof) != nil || json.Unmarshal(expected, &golden) != nil || !reflect.DeepEqual(proof, golden) {
		test.Fatal("cross-language proof mismatch")
	}
	client.Close()
	if _, err := client.proof(base64.StdEncoding.EncodeToString(make([]byte, 32))); err == nil {
		test.Fatal("closed identity signs proof")
	}
}

func TestReadinessChallengeWireAndStatusesMatch106(test *testing.T) {
	raw, err := os.ReadFile(filepath.Join("..", "..", "tests", "vectors", "friends-readiness-challenge.json"))
	if err != nil {
		test.Fatal(err)
	}
	var vector struct {
		Body string `json:"body"`
	}
	if json.Unmarshal(raw, &vector) != nil {
		test.Fatal("invalid golden")
	}
	var expected map[string]string
	if json.Unmarshal([]byte(vector.Body), &expected) != nil {
		test.Fatal("invalid body golden")
	}
	wireguard, _ := base64.StdEncoding.DecodeString(expected["wireguard_public_key"])
	client, err := NewReadinessClient(make([]byte, 64), wireguard)
	if err != nil {
		test.Fatal(err)
	}
	defer client.Close()
	body, _ := client.challengeBody()
	if string(body) != vector.Body {
		test.Fatal("Android challenge bytes differ")
	}
	for _, status := range []int{401, 403, 429, 500, 503, 400, 404, 302} {
		failure := readinessStatus("/friends/restricted-readiness/challenge", status).(*ReadinessFailure)
		if failure.Authorization != (status == 401 || status == 403) || failure.Availability != (status == 429 || status >= 500) || failure.Network {
			test.Fatal("status classification differs", status)
		}
	}
}

func TestReadinessChallengeInvalidNeverSendsProof(test *testing.T) {
	for _, response := range []string{`{}`, `{"challenge":null}`, `{"challenge":"bad","expires_at":300,"audience":"family-connect/enrollment/v1"}`,
		`{"challenge":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=","expires_at":321,"audience":"family-connect/enrollment/v1"}`,
		`{"challenge":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=","expires_at":200,"audience":"family-connect/enrollment/v1"}`,
		`{"challenge":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=","expires_at":300,"audience":"other"}`} {
		client := testReadinessClient(test)
		calls := 0
		transport := readinessPost(func(_ context.Context, path string, body []byte, probe string) ([]byte, error) {
			calls++
			return []byte(response), nil
		})
		if _, err := client.Fetch(context.Background(), transport, cacheAttempt()); err == nil || calls != 1 {
			test.Fatal("invalid challenge continued")
		}
	}
}

func TestReadinessFetchBoundToOwnNonceAndIdentity(test *testing.T) {
	client := testReadinessClient(test)
	for _, mismatch := range []string{"none", "challenge", "device"} {
		transport := readinessPost(func(_ context.Context, path string, body []byte, probe string) ([]byte, error) {
			if strings.HasSuffix(path, "/challenge") {
				return []byte(`{"challenge":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=","expires_at":300,"audience":"family-connect/enrollment/v1"}`), nil
			}
			raw := bytes.Replace(policyMaterial(test), []byte(`"device":"synthetic"`), []byte(`"device":"`+client.Reference()+`"`), 1)
			if mismatch == "device" {
				raw = bytes.Replace(raw, []byte(client.Reference()), []byte(strings.Repeat("f", 32)), 1)
			}
			if mismatch == "challenge" {
				raw = bytes.Replace(raw, []byte("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="), []byte("different"), 1)
			}
			return raw, nil
		})
		raw, err := client.Fetch(context.Background(), transport, cacheAttempt())
		if (err == nil) != (mismatch == "none") || (err != nil && raw != nil) {
			test.Fatal("response binding mismatch", mismatch)
		}
	}
}

func TestReadinessTransientCacheAuthorizationAndCancellation(test *testing.T) {
	for _, outcome := range []string{"transient", "authorization", "invalid", "cancel"} {
		client := testReadinessClient(test)
		storage := &memoryReadiness{}
		cache := policyCache(test, storage)
		if err := cache.Accept(policyMaterial(test), cacheAttempt(), client.clock()); err != nil {
			test.Fatal(err)
		}
		ctx, cancel := context.WithCancel(context.Background())
		transport := readinessPost(func(context.Context, string, []byte, string) ([]byte, error) {
			if outcome == "cancel" {
				cancel()
			}
			return nil, &ReadinessFailure{Code: "synthetic", Availability: outcome == "transient", Authorization: outcome == "authorization"}
		})
		raw, source, err := ResolveReadiness(ctx, cache, client, transport, cacheAttempt(), true)
		cancel()
		if outcome == "transient" {
			if err != nil || raw == nil || source != ReadinessSaved {
				test.Fatal("valid transient cache not used", err)
			}
		} else if err == nil || raw != nil || source != "" {
			test.Fatal("failure weakened into cache acceptance", outcome)
		}
		if outcome == "authorization" {
			if _, code := cache.Usable(client.clock()); code != ReadinessDenied {
				test.Fatal("authorization denial not durable")
			}
		}
		if outcome == "cancel" && !errors.Is(err, context.Canceled) {
			test.Fatal("cancellation became timeout/fallback")
		}
	}
}

func TestReadinessRelayOnlyBeforeChallengeAndNeverAfterTrustFailure(test *testing.T) {
	for _, failure := range []*ReadinessFailure{{Code: "network", Availability: true, Network: true}, {Code: "TLS_TRUST_REJECTED"}, {Code: "denied", Authorization: true}, {Code: "busy", Availability: true}} {
		directCalls, relayCalls := 0, 0
		direct := readinessPost(func(context.Context, string, []byte, string) ([]byte, error) { directCalls++; return nil, failure })
		relay := readinessPost(func(context.Context, string, []byte, string) ([]byte, error) { relayCalls++; return []byte(`{}`), nil })
		route, _ := NewReadinessRoute(direct, relay)
		_, err := route.Post(context.Background(), "/friends/restricted-readiness/challenge", []byte(`{}`), cacheAttempt().ChallengeID)
		if failure.Network {
			if err != nil || relayCalls != 1 {
				test.Fatal("network challenge did not select relay")
			}
			_, err = route.Post(context.Background(), "/friends/restricted-readiness", []byte(`{}`), cacheAttempt().FetchID)
			if err != nil || relayCalls != 2 || directCalls != 1 {
				test.Fatal("authorized fetch changed route")
			}
		} else if err == nil || relayCalls != 0 {
			test.Fatal("trust/auth/status failure weakened into relay")
		}
		route, _ = NewReadinessRoute(direct, relay)
		before := relayCalls
		_, err = route.Post(context.Background(), "/friends/restricted-readiness", []byte(`{}`), cacheAttempt().FetchID)
		if err == nil || relayCalls != before {
			test.Fatal("fetch replayed on alternate route")
		}
	}
}

type readinessRoundTrip func(*http.Request) (*http.Response, error)

func (transport readinessRoundTrip) RoundTrip(request *http.Request) (*http.Response, error) {
	return transport(request)
}

func TestReadinessHTTPBoundsPathsHeadersAndTrustClassification(test *testing.T) {
	for _, response := range []string{`{"ok":true}`, `{"ok":true,"ok":false}`, strings.Repeat("x", 16385)} {
		calls := 0
		transport := &ReadinessHTTPS{origin: readinessOrigin, client: &http.Client{Transport: readinessRoundTrip(func(request *http.Request) (*http.Response, error) {
			calls++
			if request.Method != "POST" || request.Header.Get("Content-Type") != "application/json" || request.Header.Get("X-FC-Probe-ID") != cacheAttempt().ChallengeID {
				test.Fatal("wire request mismatch")
			}
			return &http.Response{StatusCode: 200, Body: io.NopCloser(strings.NewReader(response)), Header: make(http.Header)}, nil
		})}}
		_, err := transport.Post(context.Background(), "/friends/restricted-readiness/challenge", []byte(`{}`), cacheAttempt().ChallengeID)
		if (err == nil) != (response == `{"ok":true}`) {
			test.Fatal("body size/ambiguity mismatch")
		}
		for _, path := range []string{"/friends/activate", "/friends/restricted-readiness/../activate", "https://other.example"} {
			if _, err := transport.Post(context.Background(), path, []byte(`{}`), cacheAttempt().ChallengeID); err == nil || calls != 1 {
				test.Fatal("expanded readiness path accepted")
			}
		}
	}
	for _, trust := range []error{x509.UnknownAuthorityError{}, x509.HostnameError{}, tls.RecordHeaderError{}, tls.AlertError(42), &net.OpError{Net: "tls", Err: errors.New("synthetic alert")}} {
		failure := readinessNetworkFailure("/friends/restricted-readiness/challenge", &url.Error{Op: "Post", URL: "secret", Err: trust}).(*ReadinessFailure)
		if failure.Availability || failure.Network || failure.Code != "TLS_TRUST_REJECTED" || strings.Contains(failure.Error(), "secret") {
			test.Fatal("TLS failure reclassified as transient")
		}
	}
	failure := readinessNetworkFailure("/friends/restricted-readiness/challenge", &net.DNSError{IsTimeout: true}).(*ReadinessFailure)
	if !failure.Availability || !failure.Network || failure.Code != "CHALLENGE_TIMEOUT" {
		test.Fatal("network timeout not classified")
	}
}
