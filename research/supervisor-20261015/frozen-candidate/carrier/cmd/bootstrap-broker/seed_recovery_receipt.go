package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"sync/atomic"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
)

var recoveryReceiptSequence atomic.Uint64

func bufferedSeedRecovery(directory string) (func(bootstrap.SeedRecovery), func()) {
	queue := make(chan bootstrap.SeedRecovery, 32)
	done := make(chan struct{})
	var lock sync.Mutex
	closed := false
	go func() {
		defer close(done)
		for receipt := range queue {
			if directory != "" {
				_ = writeSeedRecovery(filepath.Join(directory, "seed-recovery"), receipt)
			}
		}
	}()
	return func(receipt bootstrap.SeedRecovery) {
			lock.Lock()
			defer lock.Unlock()
			if closed {
				return
			}
			select {
			case queue <- receipt:
			default:
			}
		}, func() {
			lock.Lock()
			if !closed {
				closed = true
				close(queue)
			}
			lock.Unlock()
			<-done
		}
}

func writeSeedRecovery(directory string, receipt bootstrap.SeedRecovery) error {
	receipt.FirstSignaling = receipt.FirstSignaling.Sanitized()
	raw, err := json.Marshal(receipt)
	if err != nil || len(raw) > 4096 {
		return fmt.Errorf("recovery_receipt_size")
	}
	if err := os.MkdirAll(directory, 0700); err != nil {
		return err
	}
	info, err := os.Lstat(directory)
	if err != nil || !info.IsDir() || info.Mode().Perm() != 0700 {
		return fmt.Errorf("recovery_receipt_directory")
	}
	file, err := os.CreateTemp(directory, ".seed-recovery-*")
	if err != nil {
		return err
	}
	defer os.Remove(file.Name())
	if _, err = file.Write(raw); err == nil {
		err = file.Sync()
	}
	closeErr := file.Close()
	if err != nil {
		return err
	}
	if closeErr != nil {
		return closeErr
	}
	name := fmt.Sprintf("seed-recovery-%s-%020d.json", receipt.UTC.UTC().Format("20060102T150405.000000000Z"), recoveryReceiptSequence.Add(1))
	if err := os.Link(file.Name(), filepath.Join(directory, name)); err != nil {
		return err
	}
	entries, err := os.ReadDir(directory)
	if err != nil {
		return err
	}
	var names []string
	for _, entry := range entries {
		if !entry.Type().IsRegular() || !strings.HasPrefix(entry.Name(), "seed-recovery-") || !strings.HasSuffix(entry.Name(), ".json") {
			continue
		}
		names = append(names, entry.Name())
	}
	sort.Strings(names)
	for len(names) > 64 {
		if err := os.Remove(filepath.Join(directory, names[0])); err != nil {
			return err
		}
		names = names[1:]
	}
	return nil
}
