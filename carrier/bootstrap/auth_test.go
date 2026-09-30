package bootstrap

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
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

func fixture(test *testing.T, name string) []byte {
	test.Helper()
	directory := os.Getenv("FC_FAMILY_TEST_FIXTURES")
	if directory == "" {
		test.Skip("requires disposable ProductStore-issued profiles")
	}
	raw, err := os.ReadFile(filepath.Join(directory, name+".json"))
	if err != nil {
		test.Fatal("fixture unavailable")
	}
	return raw
}

func gatewayProfile(test *testing.T) string {
	test.Helper()
	path := filepath.Join(test.TempDir(), "gateway.json")
	if err := os.WriteFile(path, fixture(test, "gateway"), 0600); err != nil {
		test.Fatal(err)
	}
	return path
}

func TestProductIdentityOverBootstrapCarrier(test *testing.T) {
	path := gatewayProfile(test)
	for _, name := range []string{"valid", "unknown", "wrong-family", "revoked", "wrong-gateway", "stale-crl", "stale-revision"} {
		test.Run(name, func(test *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			defer cancel()
			var calls, admissions atomic.Int32
			broker, _ := testBroker(test, &calls, nil, "")
			client, server := pair()
			finished := make(chan error, 1)
			go func() {
				finished <- ServeCarrier(ctx, server, func(ctx context.Context, endpoint familysession.PacketEndpoint) {
					OpenServer(ctx, endpoint, path, broker, func(event string) {
						if event == "bootstrap_family_auth" {
							admissions.Add(1)
						}
					})
				})
			}()
			profileName := name
			if strings.HasPrefix(name, "stale-") || name == "wrong-gateway" {
				profileName = "valid"
			}
			raw := fixture(test, profileName)
			if profileName != name {
				var credentials familysession.Credentials
				_ = json.Unmarshal(raw, &credentials)
				if name == "wrong-gateway" {
					credentials.Gateway = strings.Repeat("0", 32)
				}
				if name == "stale-crl" {
					credentials.MinimumCRL = 999
				}
				if name == "stale-revision" {
					credentials.MinimumRevision = 999
				}
				raw = encode(credentials)
			}
			descriptor, err := recoverCarrier(ctx, client, raw, func(string) {})
			cancel()
			<-finished
			if name == "valid" {
				if err != nil || descriptor.SetupID == "" || calls.Load() != 1 || admissions.Load() != 1 {
					test.Fatal("valid auth/handoff failed", err)
				}
			} else if err == nil || calls.Load() != 0 {
				test.Fatal("unauthorized creation", name)
			}
		})
	}
}

func TestAuthenticatedDirectoryDeliveryAndRestart(test *testing.T) {
	path := gatewayProfile(test)
	var credentials familysession.Credentials
	raw := fixture(test, "valid")
	if json.Unmarshal(raw, &credentials) != nil {
		test.Fatal("profile")
	}
	directory := testDirectory(time.Now().UTC())
	directory.Family = credentials.Family
	directory.Seeds[0].Gateway = credentials.Gateway
	manager := &SeedManager{directory: &directory}
	server := httptest.NewUnstartedServer(manager.Handler(path))
	var err error
	server.TLS, err = roombroker.ServerTLS(path)
	if err != nil {
		test.Fatal(err)
	}
	server.StartTLS()
	defer server.Close()
	cachePath := filepath.Join(test.TempDir(), "bootstrap.json")
	for _, name := range []string{"unknown", "wrong-family", "revoked", "valid"} {
		client, err := roombroker.NewClient(server.URL, fixture(test, name))
		if err != nil {
			test.Fatal(err)
		}
		response, err := client.BootstrapDirectory(bounded(test))
		if name != "valid" {
			if err == nil {
				test.Fatal("unadmitted directory")
			}
			continue
		}
		if err != nil {
			test.Fatal(err)
		}
		cache := &Cache{Path: cachePath, Family: credentials.Family, Gateway: credentials.Gateway}
		if err := cache.Store(response, time.Now()); err != nil {
			test.Fatal(err)
		}
		freshProcess := &Cache{Path: cachePath, Family: credentials.Family, Gateway: credentials.Gateway}
		if _, err := freshProcess.Load(time.Now()); err != nil {
			test.Fatal(err)
		}
	}
	writer := httptest.NewRecorder()
	manager.Handler(path).ServeHTTP(writer, httptest.NewRequest(http.MethodGet, "/v1/bootstrap/directory", nil))
	if writer.Code != 403 {
		test.Fatal("missing TLS accepted")
	}
}

func TestSilentHandshakeDeadlineCleanup(test *testing.T) {
	path := gatewayProfile(test)
	ctx, cancel := context.WithTimeout(context.Background(), 40*time.Millisecond)
	defer cancel()
	var calls atomic.Int32
	broker, _ := testBroker(test, &calls, nil, "")
	client, server := pair()
	defer client.Close()
	finished := make(chan struct{})
	go func() { OpenServer(ctx, server, path, broker, func(string) {}); close(finished) }()
	select {
	case <-finished:
	case <-time.After(time.Second):
		test.Fatal("handshake leaked")
	}
	if calls.Load() != 0 {
		test.Fatal("silent peer created room")
	}
}

func TestAuthorizationRevisionChangeBeforeReady(test *testing.T) {
	path := gatewayProfile(test)
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	var calls atomic.Int32
	ready := make(chan struct{})
	broker, _ := testBroker(test, &calls, ready, "")
	client, server := pair()
	finished, result := make(chan error, 1), make(chan error, 1)
	clientRaw := fixture(test, "valid")
	go func() {
		finished <- ServeCarrier(ctx, server, func(ctx context.Context, endpoint familysession.PacketEndpoint) {
			OpenServer(ctx, endpoint, path, broker, func(string) {})
		})
	}()
	go func() { _, err := recoverCarrier(ctx, client, clientRaw, func(string) {}); result <- err }()
	for calls.Load() == 0 {
		select {
		case <-ctx.Done():
			test.Fatal("request did not reach broker")
		case <-time.After(time.Millisecond):
		}
	}
	var changed familysession.Credentials
	_ = json.Unmarshal(fixture(test, "gateway"), &changed)
	changed.MinimumRevision = 999
	if err := os.WriteFile(path, encode(changed), 0600); err != nil {
		test.Fatal(err)
	}
	close(ready)
	if err := <-result; err == nil {
		test.Fatal("stale authorization issued descriptor")
	}
	cancel()
	<-finished
}
