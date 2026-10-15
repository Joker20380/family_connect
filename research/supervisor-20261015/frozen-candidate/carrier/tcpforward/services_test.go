package tcpforward

import (
	"context"
	"net/netip"
	"testing"
)

func TestServiceDestinationsAreClosedAndOperatorPinned(test *testing.T) {
	target := netip.MustParseAddrPort("127.0.0.1:4243")
	configured := map[string]netip.AddrPort{"chat-mailbox.family-connect.invalid": target}
	policy, err := gatewayPolicy(Policy{Services: configured})
	if err != nil {
		test.Fatal(err)
	}
	configured["chat-mailbox.family-connect.invalid"] = netip.MustParseAddrPort("127.0.0.1:22")
	called := 0
	dial := func(_ context.Context, network, address string) (socket, error) {
		called++
		if network != "tcp" || address != target.String() {
			test.Fatal("unpinned destination")
		}
		return nil, nil
	}
	if _, err := connect(context.Background(), OpenRequest{Host: "chat-mailbox.family-connect.invalid", Port: 1}, policy, nil, dial); err != nil {
		test.Fatal(err)
	}
	for _, request := range []OpenRequest{
		{Host: "chat-mailbox.family-connect.invalid", Port: 22},
		{Host: "unknown.family-connect.invalid", Port: 1},
		{Host: "chat-api.family-connect.invalid", Port: 1},
		{Host: "127.0.0.1", Port: 4243},
		{Host: "10.0.0.1", Port: 80},
	} {
		if _, err := connect(context.Background(), request, policy, nil, dial); err == nil {
			test.Fatal("destination accepted", request)
		}
	}
	if called != 1 {
		test.Fatal("denied request dialled")
	}
	if _, err := gatewayPolicy(Policy{Services: map[string]netip.AddrPort{"arbitrary": target}}); err == nil {
		test.Fatal("unknown service configured")
	}
}

func TestServiceOnlyRejectsPublicAndPrivateWithoutDial(test *testing.T) {
	policy, err := gatewayPolicy(Policy{ServicesOnly: true})
	if err != nil {
		test.Fatal(err)
	}
	for _, host := range []string{"example.com", "1.1.1.1", "127.0.0.1", "10.0.0.1", "chat-api.family-connect.invalid"} {
		if _, err := connect(context.Background(), OpenRequest{Host: host, Port: 443}, policy, nil, nil); err == nil {
			test.Fatal("accepted", host)
		}
	}
}
