package bootstrap

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestWindowsRejectsUnixPlaintextCache(test *testing.T) {
	cache := Cache{Path: filepath.Join(test.TempDir(), "not-a-dpapi-cache")}
	if _, err := cache.Load(time.Now()); err == nil {
		test.Fatal("Windows cannot use the Unix mode0600 cache")
	}
	if err := cache.Store([]byte("{}"), time.Now()); err == nil {
		test.Fatal("Windows must keep readiness in the broker-owned protected store")
	}
	if _, err := os.Stat(cache.Path + ".lock"); !os.IsNotExist(err) {
		test.Fatal("Windows cache fallback wrote an unprotected file")
	}
}
