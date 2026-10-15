package packet

import (
	"context"
	"strings"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
	xnet "github.com/xtls/xray-core/common/net"
	"github.com/xtls/xray-core/proxy/tun"
	"gvisor.dev/gvisor/pkg/tcpip/stack"
)

type adapter struct{ session *wholedevice.Session }

func (handler adapter) AllowDestination(destination xnet.Destination) bool {
	return handler.session.Allow(strings.ToLower(destination.Network.String()), destination.Address.String(), uint16(destination.Port))
}

func (handler adapter) HandleConnection(connection xnet.Conn, destination xnet.Destination) {
	handler.session.Handle(connection, strings.ToLower(destination.Network.String()), destination.Address.String(), uint16(destination.Port))
}

func Start(ctx context.Context, endpoint stack.LinkEndpoint, session *wholedevice.Session) (tun.Stack, error) {
	engine, err := tun.NewEndpointStack(ctx, endpoint, adapter{session})
	if err != nil {
		return nil, err
	}
	if err = engine.Start(); err != nil {
		engine.Close()
		return nil, err
	}
	return engine, nil
}
