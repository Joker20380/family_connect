package platform

import (
	"bytes"
	"context"
	"errors"
	"net"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/desktopbridge/worker"
)

func healthTunnel(string) (*net.Interface, error) {
	return &net.Interface{Name: worker.InterfaceName, Index: 77, Flags: net.FlagUp}, nil
}

func healthResponse(test *testing.T, transform func([]byte) []byte) net.Conn {
	test.Helper()
	client, server := net.Pipe()
	go func() {
		defer server.Close()
		server.SetDeadline(time.Now().Add(time.Second))
		query := make([]byte, 1232)
		count, err := server.Read(query)
		if err != nil {
			return
		}
		reply := bytes.Clone(query[:count])
		reply[2], reply[3] = 0x81, 0x83
		if transform != nil {
			reply = transform(reply)
		}
		server.Write(reply)
	}()
	return client
}

func TestHealthUsesOnlyOwnedTunnelAndFixedTargets(test *testing.T) {
	var targets []string
	network := healthNetwork{lookup: healthTunnel, dial: func(ctx context.Context, tunnel net.Interface, target string) (net.Conn, error) {
		if tunnel.Index != 77 || tunnel.Name != worker.InterfaceName {
			test.Fatal("health probe was not bound to owned TUN")
		}
		deadline, ok := ctx.Deadline()
		if !ok || time.Until(deadline) > 2500*time.Millisecond {
			test.Fatal("unbounded health attempt")
		}
		targets = append(targets, target)
		if len(targets) == 1 {
			return nil, errors.New("synthetic resolver unavailable")
		}
		return healthResponse(test, nil), nil
	}}
	if !probeHealth(context.Background(), network) || len(targets) != 2 || targets[0] != "1.1.1.1" || targets[1] != "9.9.9.9" {
		test.Fatal("health resolver contract changed")
	}
}

func TestHealthCannotUseAnotherInterfaceOrReplacedTunnel(test *testing.T) {
	for _, unavailable := range []string{"missing", "underlay", "loopback", "down", "replaced"} {
		lookups, dials := 0, 0
		network := healthNetwork{lookup: func(name string) (*net.Interface, error) {
			lookups++
			link, _ := healthTunnel(name)
			switch unavailable {
			case "missing":
				return nil, errors.New("not installed")
			case "underlay":
				link.Name = "eth0"
			case "loopback":
				link.Flags |= net.FlagLoopback
			case "down":
				link.Flags = 0
			case "replaced":
				if lookups > 1 {
					link.Index++
				}
			}
			return link, nil
		}, dial: func(context.Context, net.Interface, string) (net.Conn, error) {
			dials++
			return healthResponse(test, nil), nil
		}}
		if probeHealth(context.Background(), network) || (unavailable != "replaced" && dials != 0) || dials > 1 {
			test.Fatal("health escaped its TUN generation", unavailable)
		}
	}
}

func TestHealthMalformedReplyCannotMaskFailure(test *testing.T) {
	calls := 0
	network := healthNetwork{lookup: healthTunnel, dial: func(context.Context, net.Interface, string) (net.Conn, error) {
		calls++
		return healthResponse(test, func(reply []byte) []byte { reply[0] ^= 1; return reply }), nil
	}}
	if probeHealth(context.Background(), network) || calls != 2 {
		test.Fatal("unmatched DNS response accepted")
	}
}

func TestHealthCancelClosesOutstandingSocketWithoutFallback(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	client, server := net.Pipe()
	defer server.Close()
	var calls atomic.Int32
	network := healthNetwork{lookup: healthTunnel, dial: func(context.Context, net.Interface, string) (net.Conn, error) {
		calls.Add(1)
		return client, nil
	}}
	finished := make(chan bool, 1)
	go func() { finished <- probeHealth(ctx, network) }()
	query := make([]byte, 1232)
	server.SetReadDeadline(time.Now().Add(time.Second))
	if _, err := server.Read(query); err != nil {
		test.Fatal(err)
	}
	cancel()
	select {
	case good := <-finished:
		if good || calls.Load() != 1 {
			test.Fatal("cancelled health became success or another probe")
		}
	case <-time.After(time.Second):
		test.Fatal("cancellation did not close health socket")
	}
}
