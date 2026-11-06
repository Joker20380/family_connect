package underlay

import (
	"context"
	"errors"
	"net"
	"strings"
	"testing"
)

func TestDeniedRetainsTypedCauseWithoutPrintingPrivateAddress(test *testing.T) {
	original := &net.DNSError{Name: "private-room.example", Err: "private resolver detail"}
	failure := preserveDenied(original)
	var dns *net.DNSError
	if !errors.Is(failure, ErrDenied) || !errors.As(failure, &dns) || dns != original {
		test.Fatal("legacy denial or typed DNS cause lost")
	}
	if strings.Contains(failure.Error(), "private") {
		test.Fatal("private cause exposed")
	}
	ctx, cancel := context.WithCancel(context.Background())
	network, err := New(ctx, "127.0.0.1:53", func(int) bool { return true })
	if err != nil {
		test.Fatal(err)
	}
	defer network.Close()
	cancel()
	_, err = network.RouteIPv4()
	if !errors.Is(err, ErrDenied) || !errors.Is(err, context.Canceled) {
		test.Fatal("route probe erased cancellation")
	}
}
