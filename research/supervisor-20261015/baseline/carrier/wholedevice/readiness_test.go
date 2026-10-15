package wholedevice

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
)

func TestReadinessMissingNoWrites(test *testing.T) {
	directory := test.TempDir()
	result := InspectReadiness(filepath.Join(directory, "family.json"), filepath.Join(directory, "bootstrap.json"), time.Now())
	if result.Provisioning != "ABSENT" || result.Cache != "ABSENT" || result.Usable || result.Valid != "UNKNOWN" {
		test.Fatal(result)
	}
	files, _ := os.ReadDir(directory)
	if len(files) != 0 {
		test.Fatal("readiness created state")
	}
}

func TestReadinessDirectoryMetadata(test *testing.T) {
	now := time.Now().UTC().Truncate(time.Second)
	cache := &bootstrap.Cache{Path: filepath.Join(test.TempDir(), "bootstrap.json"), Family: strings.Repeat("a", 32), Gateway: strings.Repeat("b", 32)}
	directory := bootstrap.Directory{Version: 1, Family: cache.Family, IssuedAt: now.Add(-time.Minute), ExpiresAt: now.Add(10 * time.Minute), Seeds: []bootstrap.Seed{{Transport: "telemost-webrtc", JoinURL: "https://telemost.yandex.ru/j/test-only", Gateway: cache.Gateway}}}
	raw, _ := json.Marshal(directory)
	if err := cache.Store(raw, now); err != nil {
		test.Fatal(err)
	}
	for _, sample := range []struct {
		at             time.Time
		valid, expired string
		usable         bool
	}{
		{now, "YES", "NO", true}, {directory.ExpiresAt, "YES", "YES", false}, {now.Add(-2 * time.Minute), "NO", "UNKNOWN", false},
	} {
		result := inspectDirectory(cache, Readiness{Cache: "PRESENT", Valid: "UNKNOWN", Expired: "UNKNOWN"}, sample.at)
		if result.Valid != sample.valid || result.Expired != sample.expired || result.Usable != sample.usable {
			test.Fatal(result)
		}
		encoded, _ := json.Marshal(result)
		for _, secret := range []string{directory.Family, directory.Seeds[0].JoinURL, cache.Gateway, "private_key"} {
			if strings.Contains(string(encoded), secret) {
				test.Fatal("readiness leaked private data")
			}
		}
	}
	if err := cache.Store([]byte("invalid"), now); err == nil {
		test.Fatal("invalid refresh accepted")
	}
	if result := inspectDirectory(cache, Readiness{Cache: "PRESENT"}, now); !result.Usable {
		test.Fatal("valid cache lost after rejected refresh")
	}
	before, _ := os.ReadFile(cache.Path)
	for count := 0; count < 3; count++ {
		inspectDirectory(cache, Readiness{Cache: "PRESENT"}, now)
	}
	after, _ := os.ReadFile(cache.Path)
	if string(before) != string(after) {
		test.Fatal("inspection mutated cache")
	}
	os.Chmod(cache.Path, 0644)
	if result := inspectDirectory(cache, Readiness{Cache: "PRESENT"}, now); result.Usable || result.Valid != "NO" {
		test.Fatal("unprotected cache accepted")
	}
}
