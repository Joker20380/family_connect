package bootstrap

import (
	"crypto/sha256"
	"encoding/hex"
	"os"
	"syscall"
	"time"

	"github.com/Joker20380/family_connect/carrier/roombroker"
)

type RecoveryPredecessor struct {
	SHA256 string `json:"sha256"`
	UID    uint32 `json:"uid"`
	GID    uint32 `json:"gid"`
	Device uint64 `json:"device"`
	Inode  uint64 `json:"inode"`
}

func (cache *Cache) WithRecoveryPredecessor(expected RecoveryPredecessor, action func() error) error {
	if os.Geteuid() != int(expected.UID) || os.Getegid() != int(expected.GID) {
		return roombroker.Code("recovery_publisher_identity")
	}
	cache.mu.Lock()
	defer cache.mu.Unlock()
	lock, err := cache.lock()
	if err != nil {
		return err
	}
	defer lock.Close()
	info, err := os.Lstat(cache.Path)
	if err != nil || !info.Mode().IsRegular() || info.Mode().Perm() != 0600 {
		return roombroker.Code("recovery_predecessor_changed")
	}
	metadata, ok := info.Sys().(*syscall.Stat_t)
	if !ok || metadata.Nlink != 1 || metadata.Uid != expected.UID || metadata.Gid != expected.GID || metadata.Dev != expected.Device || metadata.Ino != expected.Inode {
		return roombroker.Code("recovery_predecessor_changed")
	}
	raw, err := os.ReadFile(cache.Path)
	if err != nil {
		return roombroker.Code("recovery_predecessor_changed")
	}
	hash := sha256.Sum256(raw)
	if hex.EncodeToString(hash[:]) != expected.SHA256 {
		return roombroker.Code("recovery_predecessor_changed")
	}
	return action()
}

func (cache *Cache) StoreRecovery(raw []byte, now time.Time, expected RecoveryPredecessor) error {
	return cache.WithRecoveryPredecessor(expected, func() error { return cache.store(raw, now) })
}
