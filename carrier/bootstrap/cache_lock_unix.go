//go:build !windows

package bootstrap

import (
	"os"

	"github.com/Joker20380/family_connect/carrier/roombroker"
	"golang.org/x/sys/unix"
)

func (cache *Cache) lock() (*os.File, error) {
	file, err := os.OpenFile(cache.Path+".lock", os.O_CREATE|os.O_RDWR|unix.O_NOFOLLOW, 0600)
	if err != nil {
		return nil, roombroker.Code("cache_unavailable")
	}
	info, err := file.Stat()
	if err != nil || !info.Mode().IsRegular() || info.Mode().Perm() != 0600 || unix.Flock(int(file.Fd()), unix.LOCK_EX|unix.LOCK_NB) != nil {
		file.Close()
		return nil, roombroker.Code("cache_busy_or_unprotected")
	}
	return file, nil
}
