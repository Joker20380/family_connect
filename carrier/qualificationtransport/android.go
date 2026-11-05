//go:build fc_local_core

package qualificationtransport

import (
	"context"

	"github.com/Joker20380/family_connect/carrier/internal/qualification"
	"github.com/Joker20380/family_connect/carrier/underlay"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

func Open(ctx context.Context, profile, directory []byte, network *underlay.Network, event func(string)) (*wholedevice.Session, error) {
	if network == nil {
		return nil, wholedevice.ErrClosed
	}
	provider := qualification.Provider{Address: "127.0.0.1:19091", DialContext: network.DialContext}
	return wholedevice.OpenProvisionedWithTransport(ctx, profile, directory, network, event,
		wholedevice.PacketTransport{Seed: provider.Seed, Dedicated: provider.Gateway})
}
