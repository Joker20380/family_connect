package bootstrap

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"
)

var testFamily = strings.Repeat("a", 32)
var testGateway = strings.Repeat("b", 32)

func testDirectory(now time.Time) Directory {
	return Directory{1, testFamily, now.Add(-time.Minute), now.Add(10 * time.Minute), []Seed{{"telemost-webrtc", "https://telemost.yandex.ru/j/test-only", testGateway}}}
}

func encode(value any) []byte { raw, _ := json.Marshal(value); return raw }

func TestFourHourDirectoryBoundaries(test *testing.T) {
	now := time.Now().UTC()
	value := testDirectory(now)
	value.IssuedAt = now
	value.ExpiresAt = now.Add(4 * time.Hour)
	for _, observed := range []time.Time{now, value.ExpiresAt.Add(-time.Nanosecond)} {
		if _, err := ParseDirectory(encode(value), testFamily, testGateway, observed); err != nil {
			test.Fatal("valid four-hour directory rejected", err)
		}
	}
	if _, err := ParseDirectory(encode(value), testFamily, testGateway, value.ExpiresAt); err == nil {
		test.Fatal("expired directory accepted")
	}
	value.ExpiresAt = value.ExpiresAt.Add(time.Nanosecond)
	if _, err := ParseDirectory(encode(value), testFamily, testGateway, now); err == nil {
		test.Fatal("overlong directory accepted")
	}
}

func TestDirectoryValidation(test *testing.T) {
	now := time.Now().UTC()
	for name, mutate := range map[string]func(*Directory){
		"version": func(value *Directory) { value.Version = 2 },
		"family":  func(value *Directory) { value.Family = testGateway },
		"empty":   func(value *Directory) { value.Seeds = nil },
		"too_many": func(value *Directory) {
			for len(value.Seeds) <= MaxSeeds {
				value.Seeds = append(value.Seeds, value.Seeds[0])
			}
		},
		"duplicate": func(value *Directory) { value.Seeds = append(value.Seeds, value.Seeds[0]) },
		"expired":   func(value *Directory) { value.ExpiresAt = now },
		"future":    func(value *Directory) { value.IssuedAt = now.Add(time.Second) },
		"lifetime":  func(value *Directory) { value.ExpiresAt = now.Add(MaxAge) },
		"pin":       func(value *Directory) { value.Seeds[0].Gateway = testFamily },
		"transport": func(value *Directory) { value.Seeds[0].Transport = "tcp" },
		"url":       func(value *Directory) { value.Seeds[0].JoinURL = "https://telemost.yandex.ru.evil/j/test" },
		"userinfo":  func(value *Directory) { value.Seeds[0].JoinURL = "https://user@telemost.yandex.ru/j/test" },
	} {
		test.Run(name, func(test *testing.T) {
			value := testDirectory(now)
			mutate(&value)
			if _, err := ParseDirectory(encode(value), testFamily, testGateway, now); err == nil {
				test.Fatal("accepted")
			}
		})
	}
	valid := encode(testDirectory(now))
	for _, raw := range [][]byte{nil, []byte("{"), append(valid, valid...), append([]byte(`{"version":1,`), valid[1:]...), bytes.Repeat([]byte(" "), MaxDirectory+1), bytes.Replace(valid, []byte(`"version":1`), []byte(`"version":1,"token":"no"`), 1)} {
		if _, err := ParseDirectory(raw, testFamily, testGateway, now); err == nil {
			test.Fatal("malformed accepted")
		}
	}
	if _, err := ParseDirectory(valid, testFamily, testGateway, now); err != nil {
		test.Fatal(err)
	}
	if strings.Contains(fmt.Sprintf("%+v %#v", testDirectory(now), testDirectory(now).Seeds[0]), "://") {
		test.Fatal("redaction")
	}
}

func TestCacheAtomicRestartStaleAndRace(test *testing.T) {
	now := time.Now().UTC()
	cache := &Cache{Path: filepath.Join(test.TempDir(), "bootstrap.json"), Family: testFamily, Gateway: testGateway}
	if _, err := cache.Load(now); err == nil {
		test.Fatal("missing cache")
	}
	value := testDirectory(now)
	if err := cache.Store(encode(value), now); err != nil {
		test.Fatal(err)
	}
	restarted := &Cache{Path: cache.Path, Family: testFamily, Gateway: testGateway}
	if err := os.WriteFile(cache.Path+".pending", []byte("interrupted write"), 0600); err != nil {
		test.Fatal(err)
	}
	if _, err := restarted.Load(now); err != nil {
		test.Fatal(err)
	}
	old := testDirectory(now.Add(-time.Second))
	if cache.Store(encode(old), now) == nil || cache.Store([]byte("garbage"), now) == nil {
		test.Fatal("replaced valid cache")
	}
	if err := cache.Store(encode(value), now); err != nil {
		test.Fatal("identical refresh", err)
	}
	var workers sync.WaitGroup
	for index := 0; index < 20; index++ {
		workers.Add(1)
		go func(index int) {
			defer workers.Done()
			fresh := testDirectory(now)
			fresh.IssuedAt = fresh.IssuedAt.Add(time.Duration(index) * time.Millisecond)
			_ = cache.Store(encode(fresh), now)
			_, _ = cache.Load(now)
		}(index)
	}
	workers.Wait()
	current, err := restarted.Load(now)
	if err != nil || !current.IssuedAt.Equal(value.IssuedAt.Add(19*time.Millisecond)) {
		test.Fatal("cache regression", err)
	}
	if _, err := cache.Load(now.Add(time.Hour)); err == nil {
		test.Fatal("expired accepted")
	}
	info, _ := os.Stat(cache.Path)
	if info.Mode().Perm() != 0600 {
		test.Fatal("permissions")
	}
	entries, _ := os.ReadDir(filepath.Dir(cache.Path))
	if len(entries) != 2 {
		test.Fatal("temporary files leaked")
	}
	if err := os.Chmod(cache.Path, 0644); err != nil {
		test.Fatal(err)
	}
	if _, err := cache.Load(now); err == nil {
		test.Fatal("unprotected cache")
	}
}

func FuzzDirectory(fuzz *testing.F) {
	now := time.Now()
	fuzz.Add(encode(testDirectory(now)))
	fuzz.Fuzz(func(test *testing.T, raw []byte) { _, _ = ParseDirectory(raw, testFamily, testGateway, now) })
}
