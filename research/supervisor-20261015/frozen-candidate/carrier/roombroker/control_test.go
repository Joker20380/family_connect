package roombroker

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync/atomic"
	"testing"
)

func TestProductStoreMTLSControl(t *testing.T) {
	directory := os.Getenv("FC_FAMILY_TEST_FIXTURES")
	if directory == "" {
		t.Skip("requires disposable ProductStore issuer profiles")
	}
	path := filepath.Join(t.TempDir(), "gateway.json")
	raw, err := os.ReadFile(filepath.Join(directory, "gateway.json"))
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, raw, 0600); err != nil {
		t.Fatal(err)
	}
	var calls atomic.Int32
	broker := makeBroker(t, providerFunc(func(ctx context.Context) (Room, error) { calls.Add(1); return fresh(ctx) }),
		gatewayFunc(func(context.Context, context.Context, Room, string, Identity) (Gateway, error) {
			return &fakeGateway{run: waiting}, nil
		}), shortLimits())
	config, err := ServerTLS(path)
	if err != nil {
		t.Fatal(err)
	}
	server := httptest.NewUnstartedServer(broker.Handler(path))
	server.TLS = config
	server.StartTLS()
	defer server.Close()
	for _, name := range []string{"unknown", "wrong-family", "revoked", "valid"} {
		t.Run(name, func(t *testing.T) {
			raw, err := os.ReadFile(filepath.Join(directory, name+".json"))
			if err != nil {
				t.Fatal(err)
			}
			client, err := NewClient(server.URL, raw)
			if err != nil {
				t.Fatal(err)
			}
			descriptor, err := client.Create(context.Background())
			if name != "valid" {
				if err == nil {
					t.Fatal("unadmitted identity accepted")
				}
				return
			}
			if err != nil {
				t.Fatal(err)
			}
			encoded, _ := json.Marshal(descriptor)
			if strings.Contains(string(encoded), "fake-secret") || strings.Contains(string(encoded), "private_key") {
				t.Fatal("secret leak")
			}
			if err := client.call(context.Background(), "claim", descriptor.SetupID, &struct{}{}); err == nil {
				t.Fatal("replayed descriptor")
			}
			client.Cancel(descriptor.SetupID)
			waitEmpty(t, broker)
		})
	}
	if calls.Load() != 1 {
		t.Fatal("unauthorized provider use", calls.Load())
	}
	request := httptest.NewRequest(http.MethodPost, "/v1/rooms/challenge", strings.NewReader(`{}`))
	request.Header.Set("Content-Type", "application/json")
	writer := httptest.NewRecorder()
	broker.Handler(path).ServeHTTP(writer, request)
	if writer.Code != 403 {
		t.Fatal("missing TLS accepted")
	}
}
