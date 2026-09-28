package tcpforward

import (
	"context"
	"errors"
	"net"
	"net/netip"
	"strconv"
	"strings"
	"syscall"
	"time"
)

type Policy struct {
	TestOnlyLoopbackPort int
	Metrics              *DestinationMetrics
	localAddresses       []netip.Addr
}

var forbidden = []netip.Prefix{
	netip.MustParsePrefix("0.0.0.0/8"), netip.MustParsePrefix("10.0.0.0/8"),
	netip.MustParsePrefix("100.64.0.0/10"), netip.MustParsePrefix("127.0.0.0/8"),
	netip.MustParsePrefix("169.254.0.0/16"), netip.MustParsePrefix("172.16.0.0/12"),
	netip.MustParsePrefix("192.0.0.0/24"), netip.MustParsePrefix("192.0.2.0/24"),
	netip.MustParsePrefix("192.168.0.0/16"), netip.MustParsePrefix("198.18.0.0/15"),
	netip.MustParsePrefix("198.51.100.0/24"), netip.MustParsePrefix("203.0.113.0/24"),
	netip.MustParsePrefix("224.0.0.0/3"), netip.MustParsePrefix("192.88.99.0/24"),
	netip.MustParsePrefix("168.63.129.16/32"),
	netip.MustParsePrefix("2001::/23"), netip.MustParsePrefix("2001:db8::/32"),
	netip.MustParsePrefix("2002::/16"), netip.MustParsePrefix("3fff::/20"),
}

func validate(request OpenRequest) error {
	if len(request.Host) > 254 {
		return &OpenError{Code: "malformed_request"}
	}
	request.Host = canonicalHost(request.Host)
	if request.Port < 1 || request.Port > 65535 || request.TimeoutMS < 0 || request.TimeoutMS > 30000 || len(request.Host) == 0 || len(request.Host) > 253 {
		return &OpenError{Code: "malformed_request"}
	}
	if address, err := netip.ParseAddr(request.Host); err == nil {
		if address.Zone() != "" {
			return &OpenError{Code: "malformed_request"}
		}
		return nil
	}
	for _, label := range strings.Split(request.Host, ".") {
		if len(label) == 0 || len(label) > 63 || label[0] == '-' || label[len(label)-1] == '-' {
			return &OpenError{Code: "malformed_request"}
		}
		for _, character := range label {
			if !(character >= 'a' && character <= 'z' || character >= 'A' && character <= 'Z' || character >= '0' && character <= '9' || character == '-') {
				return &OpenError{Code: "malformed_request"}
			}
		}
	}
	return nil
}

func (policy Policy) permits(address netip.Addr, port int) bool {
	address = address.Unmap()
	if address == netip.MustParseAddr("127.0.0.1") && policy.TestOnlyLoopbackPort == port {
		return true
	}
	for _, local := range policy.localAddresses {
		if local == address {
			return false
		}
	}
	if !address.IsGlobalUnicast() || address.IsPrivate() || address.IsLoopback() || address.IsLinkLocalUnicast() {
		return false
	}
	if address.Is6() && !netip.MustParsePrefix("2000::/3").Contains(address) {
		return false
	}
	for _, prefix := range forbidden {
		if prefix.Contains(address) {
			return false
		}
	}
	return true
}

type resolver interface {
	LookupNetIP(context.Context, string, string) ([]netip.Addr, error)
}
type socket interface {
	net.Conn
	CloseWrite() error
}
type dialer func(context.Context, string, string) (socket, error)

func connect(ctx context.Context, request OpenRequest, policy Policy, lookup resolver, dial dialer) (socket, error) {
	if err := validate(request); err != nil {
		return nil, err
	}
	request.Host = canonicalHost(request.Host)
	timeout := 10 * time.Second
	if request.TimeoutMS != 0 {
		timeout = time.Duration(request.TimeoutMS) * time.Millisecond
	}
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()
	var addresses []netip.Addr
	if literal, err := netip.ParseAddr(request.Host); err == nil {
		addresses = []netip.Addr{literal}
	} else {
		var err error
		policy.Metrics.update(func(stats *DestinationStats) { stats.HostnameOpenRequests++ })
		lookupContext, cancelLookup := context.WithTimeout(ctx, 3*time.Second)
		addresses, err = lookup.LookupNetIP(lookupContext, "ip", request.Host)
		lookupErr := lookupContext.Err()
		cancelLookup()
		if err != nil {
			policy.Metrics.update(func(stats *DestinationStats) { stats.DNSLookupFailure++ })
			if ctx.Err() == context.Canceled {
				return nil, &OpenError{Code: "cancelled"}
			}
			var dnsError *net.DNSError
			if lookupErr == context.DeadlineExceeded || errors.Is(err, context.DeadlineExceeded) || errors.As(err, &dnsError) && dnsError.IsTimeout {
				policy.Metrics.update(func(stats *DestinationStats) { stats.DNSLookupTimeout++ })
				return nil, &OpenError{Code: "timeout"}
			}
			return nil, &OpenError{Code: "dns_failure"}
		}
		policy.Metrics.update(func(stats *DestinationStats) { stats.DNSLookupSuccess++ })
	}
	if len(addresses) == 0 {
		return nil, &OpenError{Code: "dns_failure"}
	}
	if len(addresses) > 32 {
		return nil, &OpenError{Code: "policy_rejected"}
	}
	for _, address := range addresses {
		if !policy.permits(address, request.Port) {
			policy.Metrics.update(func(stats *DestinationStats) { stats.DestinationDenied++ })
			return nil, &OpenError{Code: "policy_rejected"}
		}
	}
	var last error
	for _, address := range addresses {
		attempt, cancelAttempt := context.WithTimeout(ctx, 3*time.Second)
		connection, err := dial(attempt, "tcp", net.JoinHostPort(address.Unmap().String(), strconv.Itoa(request.Port)))
		cancelAttempt()
		if err == nil {
			policy.Metrics.update(func(stats *DestinationStats) {
				if address.Unmap().Is4() {
					stats.IPv4Selected++
				} else {
					stats.IPv6Selected++
				}
			})
			return connection, nil
		}
		last = err
		policy.Metrics.update(func(stats *DestinationStats) { stats.ConnectFailure++ })
		if ctx.Err() != nil {
			break
		}
	}
	return nil, &OpenError{Code: errorCode(last)}
}

func errorCode(err error) string {
	var network net.Error
	switch {
	case errors.Is(err, context.DeadlineExceeded):
		return "timeout"
	case errors.As(err, &network) && network.Timeout():
		return "timeout"
	case errors.Is(err, syscall.ECONNREFUSED):
		return "connection_refused"
	case errors.Is(err, syscall.ENETUNREACH), errors.Is(err, syscall.EHOSTUNREACH):
		return "unreachable"
	case errors.Is(err, context.Canceled):
		return "cancelled"
	default:
		return "connect_failed"
	}
}
