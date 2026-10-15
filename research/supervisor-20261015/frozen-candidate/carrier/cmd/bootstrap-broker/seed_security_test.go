package main

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

func TestSeedRecoverySecurity(test *testing.T) {
	root := os.Getenv("FC_FAMILY_TEST_FIXTURES")
	if root == "" {
		test.Skip("synthetic profile fixture required")
	}
	path := filepath.Join(root, "gateway.json")
	raw, err := os.ReadFile(path)
	if err != nil {
		test.Fatal("fixture read")
	}
	defer clear(raw)
	var credentials familysession.Credentials
	if json.Unmarshal(raw, &credentials) != nil {
		test.Fatal("fixture schema")
	}
	check := seedRecoverySecurity(path, credentials.Family, credentials.Gateway)
	deadline, err := check(context.Background())
	if err != nil || !time.Now().Before(deadline) {
		test.Fatal("valid gateway rejected")
	}
	cancelled, cancel := context.WithCancel(context.Background())
	cancel()
	if _, err := check(cancelled); err != context.Canceled {
		test.Fatal("local stop")
	}
	for _, name := range []string{"valid", "revoked", "wrong-family", "unknown"} {
		if _, err := seedRecoverySecurity(filepath.Join(root, name+".json"), credentials.Family, credentials.Gateway)(context.Background()); err == nil {
			test.Fatal("non-gateway security accepted", name)
		}
	}
	if _, err := seedRecoverySecurity(path, "wrong", credentials.Gateway)(context.Background()); err == nil {
		test.Fatal("binding accepted")
	}
	test.Log("RECOVERY_SECURITY strict_chain=PASS gateway_role=PASS binding=PASS crl_floors=REUSED expiry_bound=PASS")
}
