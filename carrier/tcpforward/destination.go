package tcpforward

import (
	"net"
	"net/netip"
	"strings"
	"sync"
)

type DestinationStats struct {
	HostnameOpenRequests uint64 `json:"hostname_open_requests"`
	DNSLookupSuccess     uint64 `json:"dns_lookup_success"`
	DNSLookupFailure     uint64 `json:"dns_lookup_failure"`
	DNSLookupTimeout     uint64 `json:"dns_lookup_timeout"`
	IPv4Selected         uint64 `json:"ipv4_selected"`
	IPv6Selected         uint64 `json:"ipv6_selected"`
	DestinationDenied    uint64 `json:"destination_denied"`
	ConnectFailure       uint64 `json:"connect_failure"`
}

type DestinationMetrics struct {
	mu    sync.Mutex
	stats DestinationStats
}

func (metrics *DestinationMetrics) Snapshot() DestinationStats {
	if metrics == nil {
		return DestinationStats{}
	}
	metrics.mu.Lock()
	defer metrics.mu.Unlock()
	return metrics.stats
}

func (metrics *DestinationMetrics) update(change func(*DestinationStats)) {
	if metrics == nil {
		return
	}
	metrics.mu.Lock()
	defer metrics.mu.Unlock()
	change(&metrics.stats)
}

func canonicalHost(host string) string {
	if address, err := netip.ParseAddr(host); err == nil {
		return address.String()
	}
	return strings.ToLower(strings.TrimSuffix(host, "."))
}

func gatewayPolicy(policy Policy) (Policy, error) {
	addresses, err := net.InterfaceAddrs()
	if err != nil {
		return policy, ErrProtocol
	}
	policy.localAddresses = append([]netip.Addr(nil), policy.localAddresses...)
	for _, value := range addresses {
		prefix, err := netip.ParsePrefix(value.String())
		if err == nil {
			policy.localAddresses = append(policy.localAddresses, prefix.Addr().Unmap())
		}
	}
	if policy.Metrics == nil {
		policy.Metrics = &DestinationMetrics{}
	}
	return policy, nil
}
