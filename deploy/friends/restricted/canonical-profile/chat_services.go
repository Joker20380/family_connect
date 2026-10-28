package main

import (
	"errors"
	"net/netip"
)

func pinnedChatServices(enabled bool, target string) (map[string]netip.AddrPort, error) {
	if !enabled {
		if target != "" {
			return nil, errors.New("chat target without enabled services")
		}
		return nil, nil
	}
	endpoint, err := netip.ParseAddrPort(target)
	if err != nil || endpoint.Port() == 0 || !endpoint.Addr().Is4() || !endpoint.Addr().IsGlobalUnicast() || endpoint.Addr().IsPrivate() {
		return nil, errors.New("invalid fixed chat target")
	}
	return map[string]netip.AddrPort{
		"chat-api.family-connect.invalid":     endpoint,
		"chat-mailbox.family-connect.invalid": netip.MustParseAddrPort("127.0.0.1:4243"),
	}, nil
}
