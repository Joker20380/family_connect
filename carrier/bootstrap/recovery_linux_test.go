package bootstrap

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"syscall"
	"testing"
	"time"
)

func recoveryFixture(t *testing.T) (*Cache, RecoveryPredecessor, []byte, []byte) {
	t.Helper()
	now := time.Now().UTC()
	directory := Directory{Version: 1, Family: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", IssuedAt: now.Add(-5 * time.Hour), ExpiresAt: now.Add(-time.Hour),
		Seeds: []Seed{{Transport: "telemost-webrtc", JoinURL: "https://telemost.yandex.ru/j/previous-test", Gateway: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}}}
	before, err := json.Marshal(directory)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "directory.json")
	if err = os.WriteFile(path, before, 0600); err != nil {
		t.Fatal(err)
	}
	info, err := os.Stat(path)
	if err != nil {
		t.Fatal(err)
	}
	metadata := info.Sys().(*syscall.Stat_t)
	hash := sha256.Sum256(before)
	expected := RecoveryPredecessor{SHA256: hex.EncodeToString(hash[:]), UID: metadata.Uid, GID: metadata.Gid, Device: metadata.Dev, Inode: metadata.Ino}
	directory.IssuedAt = now
	directory.ExpiresAt = now.Add(4 * time.Hour)
	directory.Seeds[0].JoinURL = "https://telemost.yandex.ru/j/fresh-test"
	fresh, err := json.Marshal(directory)
	if err != nil {
		t.Fatal(err)
	}
	return &Cache{Path: path, Family: directory.Family, Gateway: directory.Seeds[0].Gateway}, expected, before, fresh
}

func TestRecoveryUsesAtomicWriterAndPreservesMetadata(t *testing.T) {
	cache, expected, before, fresh := recoveryFixture(t)
	if _, err := ParseDirectory(before, cache.Family, cache.Gateway, time.Now()); err == nil {
		t.Fatal("expired predecessor accepted as current")
	}
	if err := cache.StoreRecovery(fresh, time.Now(), expected); err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile(cache.Path)
	if err != nil || string(raw) != string(fresh) {
		t.Fatal("readback")
	}
	info, _ := os.Stat(cache.Path)
	metadata := info.Sys().(*syscall.Stat_t)
	if metadata.Uid != expected.UID || metadata.Gid != expected.GID || metadata.Nlink != 1 || info.Mode().Perm() != 0600 || metadata.Ino == expected.Inode {
		t.Fatal("atomic metadata")
	}
	if err := cache.StoreRecovery(fresh, time.Now(), expected); err == nil {
		t.Fatal("second publication accepted")
	}
}

func TestRecoveryPublisherLockRejectsConcurrentWriter(t *testing.T) {
	cache, expected, _, fresh := recoveryFixture(t)
	lock, err := cache.lock()
	if err != nil {
		t.Fatal(err)
	}
	defer lock.Close()
	if err = cache.StoreRecovery(fresh, time.Now(), expected); err == nil {
		t.Fatal("concurrent publisher accepted")
	}
}

func TestRecoveryRejectsChangedPredecessor(t *testing.T) {
	for _, field := range []string{"hash", "inode", "uid", "gid", "device", "mode", "symlink"} {
		t.Run(field, func(t *testing.T) {
			cache, expected, _, fresh := recoveryFixture(t)
			switch field {
			case "hash":
				expected.SHA256 = "bad"
			case "inode":
				expected.Inode++
			case "uid":
				expected.UID++
			case "gid":
				expected.GID++
			case "device":
				expected.Device++
			case "mode":
				if err := os.Chmod(cache.Path, 0644); err != nil {
					t.Fatal(err)
				}
			case "symlink":
				if err := os.Rename(cache.Path, cache.Path+".saved"); err != nil {
					t.Fatal(err)
				}
				if err := os.Symlink(cache.Path+".saved", cache.Path); err != nil {
					t.Fatal(err)
				}
			}
			if err := cache.StoreRecovery(fresh, time.Now(), expected); err == nil {
				t.Fatal("changed predecessor accepted")
			}
		})
	}
}

func TestRecoveryDoesNotRelaxFreshDirectoryValidator(t *testing.T) {
	cache, expected, before, _ := recoveryFixture(t)
	if err := cache.StoreRecovery(before, time.Now(), expected); err == nil {
		t.Fatal("expired promotion accepted")
	}
}
