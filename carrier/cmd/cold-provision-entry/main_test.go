package main

import (
	"context"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

type disposableProvider struct{}

func (disposableProvider) CreateRoom(context.Context) (roombroker.Room, error) {
	return roombroker.Room{ID: "disposable", JoinURL: "https://telemost.yandex.ru/j/12345678901234"}, nil
}

type disposableEndpoint struct{ closed atomic.Bool }

func (*disposableEndpoint) SendContext(context.Context, []byte) error { return nil }
func (*disposableEndpoint) Recv(ctx context.Context) ([]byte, error) {
	<-ctx.Done()
	return nil, ctx.Err()
}
func (endpoint *disposableEndpoint) Close() error { endpoint.closed.Store(true); return nil }

func awaitFile(t *testing.T, ctx context.Context, path string) {
	t.Helper()
	for {
		if _, err := os.Stat(path); err == nil {
			return
		}
		select {
		case <-ctx.Done():
			t.Fatal("entry evidence missing before bounded test deadline")
		case <-time.After(10 * time.Millisecond):
		}
	}
}

func TestPackagedIssuerLifecycle(t *testing.T) {
	root, packageRoot := os.Getenv("FC_ENTRY_TEST_FIXTURE"), os.Getenv("FC_ENTRY_PACKAGE")
	if root == "" || packageRoot == "" {
		t.Skip("requires disposable authority and packaged issuer")
	}
	for _, scenario := range []string{"ready", "cancel_waiting", "invalid_locator"} {
		t.Run(scenario, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
			defer cancel()
			state := filepath.Join(root, scenario)
			value := options{profile: filepath.Join(root, "gateway.json"), anchor: filepath.Join(root, "anchor.pub"),
				backend: "127.0.0.1:18084", node: "nl-amsterdam-1", state: state, duration: time.Minute}
			endpoint := &disposableEndpoint{}
			completed := make(chan error, 1)
			go func() {
				completed <- serve(ctx, value, disposableProvider{}, func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
					return endpoint, nil
				})
			}()
			awaitFile(t, ctx, filepath.Join(state, "seed.json"))
			if scenario == "ready" {
				command := exec.CommandContext(ctx, "python3", filepath.Join(packageRoot, "cold-provision-locator.pyz"),
					"--database", filepath.Join(root, "access.db"), "--material", root, "--certificate", filepath.Join(root, "gateway.pem"),
					"--state", state, "--node", value.node, "--sequence", "1")
				command.Dir = root
				if err := command.Run(); err != nil {
					t.Fatal("closed packaged issuer failed", err)
				}
				awaitFile(t, ctx, filepath.Join(state, "ready.json"))
				var ready map[string]any
				raw, _ := os.ReadFile(filepath.Join(state, "ready.json"))
				if json.Unmarshal(raw, &ready) != nil || ready["phase"] != "LOCATOR_VERIFIED_SEED_CONNECTED" {
					t.Fatal("readiness marker invalid")
				}
				if err := verifyLocator(filepath.Join(state, "locator.json"), value.anchor, value.node); err != nil {
					t.Fatal("same public verifier rejected valid locator")
				}
			} else if scenario == "invalid_locator" {
				if err := exclusive(filepath.Join(state, "locator.json"), []byte("{}")); err != nil {
					t.Fatal(err)
				}
				awaitFile(t, ctx, filepath.Join(state, "stopped.json"))
			}
			cancel()
			select {
			case <-completed:
			case <-time.After(2 * time.Second):
				t.Fatal("entry did not stop")
			}
			if !endpoint.closed.Load() {
				t.Fatal("owned carrier leaked")
			}
			if _, err := os.Stat(filepath.Join(state, "stopped.json")); err != nil {
				t.Fatal("missing stop evidence")
			}
			if scenario != "ready" {
				if _, err := os.Stat(filepath.Join(state, "ready.json")); !os.IsNotExist(err) {
					t.Fatal("failed invocation advertised readiness")
				}
			}
		})
	}
}
