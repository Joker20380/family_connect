package roombroker

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"net"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestPublicationObserverUsesRuntimeLoader(test *testing.T) {
	profiles := newRotationProfiles(test, true)
	root := test.TempDir()
	path, socket := filepath.Join(root, "gateway.json"), filepath.Join(root, "reader.sock")
	raw := rotationRaw(test, profiles.server)
	if err := os.WriteFile(path, raw, 0600); err != nil {
		test.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	closeObserver, err := ObservePublication(ctx, socket, path)
	if err != nil {
		test.Fatal(err)
	}
	defer closeObserver()
	observe := func(candidate any) PublicationReceipt {
		connection, err := net.DialTimeout("unix", socket, time.Second)
		if err != nil {
			test.Fatal(err)
		}
		defer connection.Close()
		connection.SetDeadline(time.Now().Add(time.Second))
		json.NewEncoder(connection).Encode(map[string]any{"candidate": candidate})
		connection.(*net.UnixConn).CloseWrite()
		var receipt PublicationReceipt
		json.NewDecoder(connection).Decode(&receipt)
		return receipt
	}
	first := observe(nil)
	sum := sha256.Sum256(raw)
	if first.Profile != hex.EncodeToString(sum[:]) || first.Contract != OnlineRenewalContract {
		test.Fatal("runtime readback")
	}
	_, next := profiles.successorUntil(test, false, time.Now().Add(50*time.Minute), 2, 4, 5)
	public := next
	public.PrivateKey = ""
	prepared := observe(public)
	if prepared != first {
		test.Fatal("prepare must retain original runtime", prepared)
	}
	if observe(next).Contract != "" {
		test.Fatal("private key accepted")
	}
	public.Gateway = "wrong-node"
	if observe(public).Contract != "" {
		test.Fatal("cross-node successor accepted")
	}
	replaceRotationProfile(test, path, next)
	after := observe(nil)
	if after.Instance != first.Instance || after.Profile == first.Profile {
		test.Fatal("publication readback", after)
	}
}
