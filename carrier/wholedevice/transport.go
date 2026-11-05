package wholedevice

import (
	"context"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

type PacketTransport struct {
	Seed      bootstrap.SeedConnector
	Dedicated func(context.Context, context.Context, roombroker.Room) (roombroker.GatewayCarrier, error)
}
