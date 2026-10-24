package bootstrap

import (
	"os"

	"github.com/Joker20380/family_connect/carrier/roombroker"
)

func (cache *Cache) lock() (*os.File, error) {
	return nil, roombroker.Code("cache_unavailable")
}
