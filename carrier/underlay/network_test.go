package underlay

import (
	"context"
	"net"
	"net/http/httptest"
	"sync/atomic"
	"testing"
	"time"
)

func TestProtectionBeforeTCPAndUDP(test *testing.T) {
	var calls atomic.Int32
	network, err := New(context.Background(), "127.0.0.1:53", func(fd int) bool { calls.Add(1); return false })
	if err != nil {
		test.Fatal(err)
	}
	for _, protocol := range []string{"tcp4", "udp4"} {
		if connection, err := network.Dial(protocol, "127.0.0.1:9"); err == nil {
			connection.Close()
			test.Fatal("unprotected socket")
		}
	}
	if connection, err := network.ListenPacket("udp4", "127.0.0.1:0"); err == nil {
		connection.Close()
		test.Fatal("unprotected listener")
	}
	if calls.Load() != 3 || network.Rejected.Load() != 3 {
		test.Fatal("protection not enforced", calls.Load())
	}
}

func TestProtectedPionAndFactoryPaths(test *testing.T) {
	network, err := New(context.Background(), "127.0.0.1:53", func(fd int) bool { return fd > 0 })
	if err != nil {
		test.Fatal(err)
	}
	listener, err := network.ListenUDP("udp4", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		test.Fatal(err)
	}
	defer listener.Close()
	connection, err := network.CreateDialer(&net.Dialer{}).Dial("udp4", listener.LocalAddr().String())
	if err != nil {
		test.Fatal(err)
	}
	defer connection.Close()
	if _, err = connection.Write([]byte("protected")); err != nil {
		test.Fatal(err)
	}
	listener.SetReadDeadline(time.Now().Add(time.Second))
	buffer := make([]byte, 32)
	if count, _, err := listener.ReadFrom(buffer); err != nil || string(buffer[:count]) != "protected" {
		test.Fatal("udp", err)
	}
	packet, err := network.CreateListenConfig(&net.ListenConfig{}).ListenPacket(context.Background(), "udp4", "127.0.0.1:0")
	if err != nil {
		test.Fatal(err)
	}
	packet.Close()
	if network.Protected.Load() != 3 {
		test.Fatal("factory bypass")
	}
}

func TestCancelledAndIPv6FailClosed(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	network, err := New(ctx, "127.0.0.1:53", func(int) bool { return true })
	if err != nil {
		test.Fatal(err)
	}
	if _, err = network.ResolveIPAddr("ip6", "::1"); err == nil {
		test.Fatal("ipv6")
	}
	if _, err = network.Dial("udp6", "[::1]:53"); err == nil {
		test.Fatal("ipv6 socket")
	}
	cancel()
	if _, err = network.Dial("udp4", "127.0.0.1:53"); err == nil {
		test.Fatal("stale session")
	}
}

func TestResolverCannotFallbackWithoutProtection(test *testing.T) {
	network, err := New(context.Background(), "127.0.0.1:53", func(int) bool { return false })
	if err != nil {
		test.Fatal(err)
	}
	if _, err = network.ResolveIPAddr("ip4", "provider.invalid"); err == nil {
		test.Fatal("resolver fallback")
	}
	if network.DNS.Load() == 0 || network.Rejected.Load() == 0 || network.Protected.Load() != 0 {
		test.Fatal("resolver bypass")
	}
}

func TestHTTPSAndClosedOwnerCannotBypassProtection(test *testing.T) {
	server := httptest.NewTLSServer(nil)
	defer server.Close()
	network, err := New(context.Background(), "127.0.0.1:53", func(int) bool { return false })
	if err != nil {
		test.Fatal(err)
	}
	if response, err := network.HTTPClient().Get(server.URL); err == nil {
		response.Body.Close()
		test.Fatal("HTTPS bypassed protect")
	}
	if network.Rejected.Load() != 1 {
		test.Fatal("HTTPS did not use protection hook")
	}
	network.Close()
	if _, err := network.ListenUDP("udp4", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)}); err == nil {
		test.Fatal("released owner accepted socket")
	}
}
