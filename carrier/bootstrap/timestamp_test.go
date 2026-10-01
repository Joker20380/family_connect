package bootstrap

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestSharedTimestampContract(test *testing.T) {
	var fixture struct {
		Valid []struct {
			Name, Value, Canonical string
			Seconds, Nanos         int64
		}
		Invalid   []string
		Directory map[string]any
		Now       int64
	}
	raw, err := os.ReadFile("../../tests/vectors/bootstrap-timestamps.json")
	if err != nil || json.Unmarshal(raw, &fixture) != nil {
		test.Fatal("fixture unavailable")
	}
	for _, entry := range fixture.Valid {
		test.Run(entry.Name, func(test *testing.T) {
			fixture.Directory["expires_at"] = entry.Value
			value, err := ParseDirectory(encode(fixture.Directory), testFamily, testGateway, time.Unix(fixture.Now, 0))
			if err != nil || !value.ExpiresAt.Equal(time.Unix(entry.Seconds, entry.Nanos)) {
				test.Fatal("instant mismatch", err)
			}
			var serialized map[string]any
			if json.Unmarshal(encode(value), &serialized) != nil || serialized["expires_at"] != entry.Canonical {
				test.Fatal("not canonical UTC")
			}
			for _, delta := range []time.Duration{-time.Nanosecond, 0, time.Nanosecond} {
				_, err := ParseDirectory(encode(fixture.Directory), testFamily, testGateway, value.ExpiresAt.Add(delta))
				if (err == nil) != (delta < 0) {
					test.Fatal("expiry boundary")
				}
			}
		})
	}
	for _, value := range fixture.Invalid {
		for _, field := range []string{"issued_at", "expires_at"} {
			var directory map[string]any
			if json.Unmarshal(raw, &struct{ Directory *map[string]any }{&directory}) != nil {
				test.Fatal("fixture")
			}
			directory[field] = value
			if _, err := ParseDirectory(encode(directory), testFamily, testGateway, time.Unix(fixture.Now, 0)); err == nil {
				test.Fatalf("accepted invalid %s", field)
			}
		}
	}
}

func TestTimestampReplayUsesInstants(test *testing.T) {
	now := time.Date(2026, 10, 1, 12, 0, 0, 0, time.UTC)
	value := testDirectory(now)
	value.IssuedAt = now.Add(-time.Minute).In(time.FixedZone("positive", 3*3600))
	value.ExpiresAt = now.Add(10 * time.Minute).In(time.FixedZone("negative", -19800))
	canonical := encode(value)
	if strings.Contains(string(canonical), "+03:00") || strings.Contains(string(canonical), "-05:30") {
		test.Fatal("serializer retained offset")
	}
	var input map[string]any
	if json.Unmarshal(canonical, &input) != nil {
		test.Fatal("fixture")
	}
	input["issued_at"] = "2026-10-01T14:59:00+03:00"
	cache := &Cache{Path: filepath.Join(test.TempDir(), "directory.json"), Family: testFamily, Gateway: testGateway}
	if err := cache.Store(encode(input), now); err != nil {
		test.Fatal(err)
	}
	if err := cache.Store(canonical, now); err != nil {
		test.Fatal("equivalent representation not idempotent", err)
	}
	input["issued_at"] = "2026-10-01T06:29:01-05:30"
	if err := cache.Store(encode(input), now); err != nil {
		test.Fatal("newer instant with lexically earlier string rejected", err)
	}
	input["issued_at"] = "2026-10-01T14:59:00+03:00"
	if err := cache.Store(encode(input), now); err == nil {
		test.Fatal("stale instant accepted")
	}
	input["issued_at"] = "2026-10-01T11:59:01Z"
	input["expires_at"] = "2026-10-01T12:11:00Z"
	if err := cache.Store(encode(input), now); err == nil {
		test.Fatal("equal-issued conflicting payload accepted")
	}
}
