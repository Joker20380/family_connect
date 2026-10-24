package desktopmesh

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/Joker20380/family_connect/carrier/underlay"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func normalFixture(test *testing.T, device string, sequence uint64) ([]byte, []byte) {
	test.Helper()
	raw, err := os.ReadFile(filepath.Join("..", "..", "tests", "fixtures", "desktop-friends-catalog-v2.json"))
	if err != nil {
		test.Fatal(err)
	}
	var fixture struct {
		Vectors []struct{ Reply map[string]json.RawMessage }
	}
	if json.Unmarshal(raw, &fixture) != nil {
		test.Fatal("fixture decode")
	}
	reply := fixture.Vectors[0].Reply
	var catalog map[string]string
	json.Unmarshal(reply["catalog"], &catalog)
	payload, _ := base64.StdEncoding.DecodeString(catalog["payload"])
	var value map[string]any
	json.Unmarshal(payload, &value)
	value["sequence"] = sequence
	payload, _ = json.Marshal(value)
	signing := ed25519.NewKeyFromSeed(bytes.Repeat([]byte{13}, 32))
	catalog["payload"] = base64.StdEncoding.EncodeToString(payload)
	catalog["signature"] = base64.StdEncoding.EncodeToString(ed25519.Sign(signing, append([]byte("family-connect/invited-test/v1\x00"), payload...)))
	reply["catalog"], _ = json.Marshal(catalog)
	reply["device"], _ = json.Marshal(device)
	raw, _ = json.Marshal(reply)
	return raw, signing.Public().(ed25519.PublicKey)
}

func TestNormalFreshProofAndCatalogBinding(test *testing.T) {
	client := testReadinessClient(test)
	raw, anchor := normalFixture(test, client.Reference(), 2)
	var paths []string
	transport := readinessPost(func(ctx context.Context, path string, body []byte, probe string) ([]byte, error) {
		paths = append(paths, path)
		if !validProbeID(probe) {
			test.Fatal("missing correlation")
		}
		if path == "/friends/challenge" {
			var request map[string]string
			if json.Unmarshal(body, &request) != nil || len(request) != 4 || request["purpose"] != "nl" || request["invitation"] != "" || request["public_identity"] != base64.StdEncoding.EncodeToString(client.Public()) {
				test.Fatal("challenge binding")
			}
			return []byte(`{"challenge":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=","expires_at":300,"audience":"family-connect/enrollment/v1"}`), nil
		}
		expected, _ := client.proof(base64.StdEncoding.EncodeToString(make([]byte, 32)))
		if path != "/friends/configuration/nl" || !bytes.Equal(body, expected) {
			test.Fatal("proof differs from existing accepted signer")
		}
		return bytes.Clone(raw), nil
	})
	result, err := client.FetchNormal(context.Background(), transport, "nl", anchor, nil)
	if err != nil || !bytes.Equal(result.Response, raw) || result.Sequence != 2 || len(paths) != 2 {
		test.Fatal("fresh exchange failed", err)
	}
	if text := fmt.Sprintf("%+v", result); strings.Contains(text, "tcp_id") || strings.Contains(text, "11111111") {
		test.Fatal("response leaked in format")
	}
	result.Clear()
	if result.Response != nil || result.Catalog != nil {
		test.Fatal("response retained")
	}
}

func TestNormalFloorsBindBothCountriesAndNeverAuthorizeOffline(test *testing.T) {
	client := testReadinessClient(test)
	old, anchor := normalFixture(test, client.Reference(), 2)
	fresh, _ := normalFixture(test, client.Reference(), 3)
	older, err := VerifyNormalResponse(old, anchor, client.Reference(), "nl", nil)
	if err != nil {
		test.Fatal(err)
	}
	newer, err := VerifyNormalResponse(fresh, anchor, client.Reference(), "nl", []json.RawMessage{older.Catalog})
	if err != nil || newer.Sequence != 3 {
		test.Fatal(err)
	}
	if _, err := VerifyNormalResponse(old, anchor, client.Reference(), "nl", []json.RawMessage{newer.Catalog}); err == nil {
		test.Fatal("rollback accepted")
	}
	for _, failure := range []error{&ReadinessFailure{Code: "AUTHORIZATION_REJECTED", Authorization: true}, &ReadinessFailure{Code: "NORMAL_FETCH_REJECTED", Availability: true}} {
		calls := 0
		transport := readinessPost(func(context.Context, string, []byte, string) ([]byte, error) { calls++; return nil, failure })
		result, err := client.FetchNormal(context.Background(), transport, "nl", anchor, []json.RawMessage{older.Catalog})
		if err != failure || calls != 1 || result.Response != nil {
			test.Fatal("cached normal authorization fallback")
		}
	}
}

func TestNormalExactEnvelopeAndAssignments(test *testing.T) {
	client := testReadinessClient(test)
	raw, anchor := normalFixture(test, client.Reference(), 2)
	for _, mutation := range []func(map[string]json.RawMessage){
		func(value map[string]json.RawMessage) { value["Device"] = value["device"]; delete(value, "device") },
		func(value map[string]json.RawMessage) { value["unknown"] = json.RawMessage(`false`) },
		func(value map[string]json.RawMessage) { value["country"] = json.RawMessage(`"ru"`) },
		func(value map[string]json.RawMessage) {
			value["device"] = json.RawMessage(`"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"`)
		},
		func(value map[string]json.RawMessage) { value["address"] = json.RawMessage(`"10.83.0.1/32"`) },
		func(value map[string]json.RawMessage) { value["address"] = json.RawMessage(`"10.83.255.255/32"`) },
		func(value map[string]json.RawMessage) { value["address"] = json.RawMessage(`"10.84.0.2/32"`) },
		func(value map[string]json.RawMessage) { value["tcp_id"] = json.RawMessage(`null`) },
		func(value map[string]json.RawMessage) {
			value["tcp_id"] = json.RawMessage(`"00000000-0000-0000-0000-000000000000"`)
		},
		func(value map[string]json.RawMessage) {
			value["catalog"] = json.RawMessage(`{"payload":"AA==","signature":"AA=="}`)
		},
	} {
		var value map[string]json.RawMessage
		json.Unmarshal(raw, &value)
		mutation(value)
		changed, _ := json.Marshal(value)
		if _, err := VerifyNormalResponse(changed, anchor, client.Reference(), "nl", nil); err == nil {
			test.Fatal("malformed assignment accepted")
		}
	}
}

func TestNormalCancelClosedIdentityAndInvalidSeedMakeNoRequest(test *testing.T) {
	client := testReadinessClient(test)
	_, anchor := normalFixture(test, client.Reference(), 2)
	transport := readinessPost(func(context.Context, string, []byte, string) ([]byte, error) {
		test.Fatal("unexpected request")
		return nil, nil
	})
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if _, err := client.FetchNormal(ctx, transport, "nl", anchor, nil); !errors.Is(err, context.Canceled) {
		test.Fatal(err)
	}
	if _, err := client.FetchNormal(context.Background(), transport, "nl", anchor, []json.RawMessage{json.RawMessage(`{}`)}); err == nil {
		test.Fatal("invalid migration floor")
	}
	client.Close()
	if _, err := client.FetchNormal(context.Background(), transport, "nl", anchor, nil); !errors.Is(err, ErrClosed) {
		test.Fatal(err)
	}
}

func TestNormalHTTPSFixedMethodsStatusAndEncoding(test *testing.T) {
	for _, item := range []struct {
		status   int
		encoding string
		body     string
		expected string
	}{
		{200, "", `{}`, ""}, {401, "", `secret`, "AUTHORIZATION_REJECTED"}, {403, "", `secret`, "AUTHORIZATION_REJECTED"},
		{409, "", `secret`, "AUTHORIZATION_REJECTED"}, {429, "", `secret`, "NORMAL_FETCH_REJECTED"}, {503, "", `secret`, "NORMAL_FETCH_REJECTED"},
		{302, "", `{}`, "NORMAL_FETCH_REJECTED"}, {200, "gzip", `secret`, "configuration"}, {200, "", strings.Repeat("x", MaxNormalResponse+1), "configuration"},
	} {
		server := httptest.NewTLSServer(http.HandlerFunc(func(output http.ResponseWriter, request *http.Request) {
			if request.Method != "POST" || request.URL.Path != "/friends/configuration/nl" || request.Header.Get("Accept-Encoding") != "identity" {
				test.Error("unsafe request")
			}
			output.Header().Set("Content-Encoding", item.encoding)
			output.WriteHeader(item.status)
			io.WriteString(output, item.body)
		}))
		client := server.Client()
		client.CheckRedirect = func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }
		transport := &NormalHTTPS{client: client, origin: server.URL}
		raw, err := transport.Post(context.Background(), "/friends/configuration/nl", []byte(`{}`), strings.Repeat("a", 32))
		if item.expected == "" {
			if err != nil || string(raw) != "{}" {
				test.Fatal(err)
			}
		} else if err == nil || raw != nil {
			test.Fatal("unsafe response accepted")
		}
		if failure, ok := err.(*ReadinessFailure); ok && failure.Code != item.expected {
			test.Fatal("wrong failure classification")
		}
		transport.Close()
		server.Close()
	}
}

func TestNormalHTTPSDeniesUnprotectedAndCallerChosenDestinations(test *testing.T) {
	protected := 0
	network, err := underlay.New(context.Background(), "1.1.1.1:53", func(int) bool { protected++; return false })
	if err != nil {
		test.Fatal(err)
	}
	defer network.Close()
	transport, err := NewNormalHTTPS(network)
	if err != nil {
		test.Fatal(err)
	}
	defer transport.Close()
	for _, path := range []string{"https://elsewhere.example/friends/challenge", "/friends/configuration/nl?override=1", "/friends/configuration/../nl", "/friends/restricted-readiness", "/friends/register"} {
		if _, err := transport.Post(context.Background(), path, []byte(`{}`), strings.Repeat("a", 32)); err == nil {
			test.Fatal("unlisted path")
		}
	}
	if protected != 0 {
		test.Fatal("invalid path tried to connect")
	}
	_, err = transport.Post(context.Background(), "/friends/challenge", []byte(`{}`), strings.Repeat("a", 32))
	var failure *ReadinessFailure
	if !errors.As(err, &failure) || failure.Code != "UNDERLAY_PROTECTION_REJECTED" || protected != 1 {
		test.Fatal("missing fail-closed socket protection")
	}
}
