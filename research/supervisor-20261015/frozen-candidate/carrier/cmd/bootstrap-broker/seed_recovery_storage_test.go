package main

import (
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
)

func TestSeedRecoveryStorageRetention(test *testing.T) {
	directory := filepath.Join(test.TempDir(), "receipts")
	if err := os.Mkdir(directory, 0700); err != nil {
		test.Fatal(err)
	}
	foreign := filepath.Join(directory, "operator-note.json")
	if os.WriteFile(foreign, []byte("not a collector receipt"), 0600) != nil {
		test.Fatal("fixture")
	}
	prior := filepath.Join(directory, "seed-recovery-20000101T000000.000000000Z-00000000000000000001.json")
	if os.WriteFile(prior, []byte("malformed prior receipt"), 0600) != nil {
		test.Fatal("fixture")
	}
	for index := 0; index < 70; index++ {
		receipt := bootstrap.SeedRecovery{Schema: 1, UTC: time.Now().Add(time.Duration(index) * time.Nanosecond), Outcome: "RECOVERED"}
		if err := writeSeedRecovery(directory, receipt); err != nil {
			test.Fatal(err)
		}
	}
	entries, err := os.ReadDir(directory)
	if err != nil || len(entries) != 65 {
		test.Fatal("retention", len(entries), err)
	}
	if _, err := os.Stat(foreign); err != nil {
		test.Fatal("foreign file removed")
	}
	if _, err := os.Stat(prior); !os.IsNotExist(err) {
		test.Fatal("old malformed receipt not pruned")
	}
	info, _ := os.Stat(directory)
	if info.Mode().Perm() != 0700 {
		test.Fatal("directory permissions")
	}
	for _, entry := range entries {
		info, _ := entry.Info()
		if info.Mode().Perm() != 0600 || info.Size() > 4096 {
			test.Fatal("receipt permissions/size")
		}
	}
	if err := os.Chmod(directory, 0755); err != nil {
		test.Fatal(err)
	}
	if writeSeedRecovery(directory, bootstrap.SeedRecovery{}) == nil {
		test.Fatal("unsafe directory accepted")
	}
}
