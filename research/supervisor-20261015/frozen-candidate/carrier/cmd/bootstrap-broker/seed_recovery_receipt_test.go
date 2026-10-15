package main

import (
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
)

func TestSeedRecoveryReceipts(test *testing.T) {
	directory := filepath.Join(test.TempDir(), "private")
	sink, stop := bufferedSeedRecovery(directory)
	var workers sync.WaitGroup
	for index := 0; index < 1000; index++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			sink(bootstrap.SeedRecovery{Schema: 1, UTC: time.Now().UTC(), State: "SEED_ACTIVE", Outcome: "RECOVERED"})
		}()
	}
	workers.Wait()
	stop()
	stop()
	sink(bootstrap.SeedRecovery{})
	entries, err := os.ReadDir(filepath.Join(directory, "seed-recovery"))
	if err != nil {
		test.Fatal(err)
	}
	if len(entries) == 0 || len(entries) > 64 {
		test.Fatal("retention", len(entries))
	}
	for _, entry := range entries {
		info, _ := entry.Info()
		if info.Mode().Perm() != 0600 {
			test.Fatal("permissions")
		}
		raw, _ := os.ReadFile(filepath.Join(directory, "seed-recovery", entry.Name()))
		for _, secret := range []string{"http:", "https:", "token", "payload", "cookie", "private_key", "sdp"} {
			if strings.Contains(string(raw), secret) {
				test.Fatal("privacy", secret)
			}
		}
	}
}

func TestSeedRecoveryWriteFailure(test *testing.T) {
	directory := filepath.Join(test.TempDir(), "not-directory")
	if os.WriteFile(directory, []byte("occupied"), 0600) != nil {
		test.Fatal("fixture")
	}
	sink, stop := bufferedSeedRecovery(directory)
	sink(bootstrap.SeedRecovery{Schema: 1, UTC: time.Now()})
	stop()
	if writeSeedRecovery(directory, bootstrap.SeedRecovery{}) == nil {
		test.Fatal("write failure not recognized")
	}
}
