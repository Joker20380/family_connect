package mixed

import (
	"fmt"
	"testing"
)

func TestMixedReverseSupported(test *testing.T) {
	versions := struct{ name, client, gateway string }{"OLD_GATEWAY_RECEIVES_NEW_CLIENT", "oldgateway", "new"}
	for _, count := range []int{8, 16, 19, 20, 40} {
		test.Run(fmt.Sprint(count), func(test *testing.T) { burstCase(test, versions, count, false) })
	}
}
