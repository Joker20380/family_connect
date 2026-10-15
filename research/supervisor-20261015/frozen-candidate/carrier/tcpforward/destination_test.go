package tcpforward

import (
	"context"
	"errors"
	"net"
	"net/netip"
	"strings"
	"sync"
	"syscall"
	"testing"
	"time"
)

type lookupFunction func(context.Context, string, string) ([]netip.Addr, error)

func (lookup lookupFunction) LookupNetIP(ctx context.Context, network, host string) ([]netip.Addr, error) {
	return lookup(ctx, network, host)
}

func TestDestinationCanonicalPinnedDualStack(test *testing.T) {
	for _, addresses := range [][]netip.Addr{
		{netip.MustParseAddr("93.184.215.14")},
		{netip.MustParseAddr("2001:4860:4860::8888")},
		{netip.MustParseAddr("2001:4860:4860::8888"), netip.MustParseAddr("93.184.215.14")},
	} {
		metrics := &DestinationMetrics{}
		lookups, dials := 0, 0
		lookup := lookupFunction(func(ctx context.Context, network, host string) ([]netip.Addr, error) {
			lookups++
			if host != "example.com" || network != "ip" {
				test.Error("hostname not canonical")
			}
			return addresses, nil
		})
		connection, err := connect(context.Background(), OpenRequest{Host: "ExAmPlE.COM.", Port: 443}, Policy{Metrics: metrics}, lookup, func(ctx context.Context, network, address string) (socket, error) {
			dials++
			host, _, _ := net.SplitHostPort(address)
			parsed, err := netip.ParseAddr(host)
			if err != nil {
				test.Fatal("dial resolved hostname again")
			}
			if len(addresses) == 2 && parsed.Is6() {
				return nil, syscall.ENETUNREACH
			}
			left, right := net.Pipe()
			test.Cleanup(func() { left.Close(); right.Close() })
			return pipeSocket{left}, nil
		})
		if err != nil || connection == nil || lookups != 1 || dials != len(addresses) {
			test.Fatal(err, lookups, dials)
		}
		if metrics.Snapshot().DNSLookupSuccess != 1 || metrics.Snapshot().IPv4Selected+metrics.Snapshot().IPv6Selected != 1 {
			test.Fatal(metrics.Snapshot())
		}
	}
}

func TestDestinationResolvedSSRFAllCandidates(test *testing.T) {
	for _, blocked := range []string{"127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "fc00::1", "fe80::1", "100.64.0.1", "0.0.0.0", "ff02::1", "186.246.45.246"} {
		test.Run(blocked, func(test *testing.T) {
			metrics := &DestinationMetrics{}
			policy := Policy{Metrics: metrics, localAddresses: []netip.Addr{netip.MustParseAddr("186.246.45.246")}}
			lookup := fixedResolver{addresses: []netip.Addr{netip.MustParseAddr("93.184.215.14"), netip.MustParseAddr(blocked)}}
			_, err := connect(context.Background(), OpenRequest{Host: "example.com", Port: 443}, policy, lookup, func(context.Context, string, string) (socket, error) {
				test.Fatal("unsafe DNS set dialed")
				return nil, nil
			})
			var failure *OpenError
			if !errors.As(err, &failure) || failure.Code != "policy_rejected" || metrics.Snapshot().DestinationDenied != 1 {
				test.Fatal(err)
			}
		})
	}
}

func TestDestinationDNSFailureTimeoutCancellation(test *testing.T) {
	for _, scenario := range []string{"nxdomain", "timeout", "cancelled", "empty"} {
		test.Run(scenario, func(test *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 20*time.Millisecond)
			defer cancel()
			code := "dns_failure"
			if scenario == "timeout" {
				code = "timeout"
			}
			if scenario == "cancelled" {
				cancel()
				code = "cancelled"
			}
			lookup := lookupFunction(func(ctx context.Context, network, host string) ([]netip.Addr, error) {
				if scenario == "nxdomain" {
					return nil, &net.DNSError{IsNotFound: true}
				}
				if scenario == "empty" {
					return nil, nil
				}
				<-ctx.Done()
				return nil, ctx.Err()
			})
			_, err := connect(ctx, OpenRequest{Host: "example.com", Port: 443}, Policy{}, lookup, func(context.Context, string, string) (socket, error) {
				test.Fatal("dial after DNS failure")
				return nil, nil
			})
			var failure *OpenError
			if !errors.As(err, &failure) || failure.Code != code {
				test.Fatal(err)
			}
		})
	}
}

func TestDestinationIDNAPolicyAndBounds(test *testing.T) {
	for _, host := range []string{"xn--bcher-kva.example", "EXAMPLE.COM.", "2001:4860:4860::8888", "93.184.215.14"} {
		if err := validate(OpenRequest{Host: host, Port: 443}); err != nil {
			test.Fatal(host, err)
		}
	}
	for _, host := range []string{"bücher.example", "example..com", "example.com..", "user@example.com", "example.com:443", "[::1]", " example.com", strings.Repeat("a", 255)} {
		if validate(OpenRequest{Host: host, Port: 443}) == nil {
			test.Fatal("malformed accepted", host)
		}
	}
}

func TestDestinationConcurrentResolutionNoSharedUnboundedCache(test *testing.T) {
	metrics := &DestinationMetrics{}
	var workers sync.WaitGroup
	for range 32 {
		workers.Add(1)
		go func() {
			defer workers.Done()
			_, err := connect(context.Background(), OpenRequest{Host: "example.com", Port: 443}, Policy{Metrics: metrics}, fixedResolver{addresses: []netip.Addr{netip.MustParseAddr("93.184.215.14")}}, func(context.Context, string, string) (socket, error) { return nil, syscall.ECONNREFUSED })
			if err == nil {
				test.Error("unexpected connection")
			}
		}()
	}
	workers.Wait()
	if metrics.Snapshot().HostnameOpenRequests != 32 || metrics.Snapshot().ConnectFailure != 32 {
		test.Fatal(metrics.Snapshot())
	}
}
