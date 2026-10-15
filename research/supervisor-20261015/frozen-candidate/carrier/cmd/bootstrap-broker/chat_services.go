package main

import "net/netip"

func pinnedChatServices(enabled bool) map[string]netip.AddrPort {
	if !enabled {
		return nil
	}
	return map[string]netip.AddrPort{
		"chat-api.family-connect.invalid":     netip.MustParseAddrPort("185.251.89.19:8443"),
		"chat-mailbox.family-connect.invalid": netip.MustParseAddrPort("127.0.0.1:4243"),
	}
}
