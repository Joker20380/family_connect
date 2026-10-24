package platform

import (
	"context"
	"io"
	"strings"
	"sync"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
	xnet "github.com/xtls/xray-core/common/net"
	"github.com/xtls/xray-core/proxy/tun"
	"gvisor.dev/gvisor/pkg/tcpip/stack"
)

type Native struct{}

type sessionAdapter struct{ session *wholedevice.Session }

func (adapter sessionAdapter) AllowDestination(destination xnet.Destination) bool {
	return adapter.session.Allow(strings.ToLower(destination.Network.String()), destination.Address.String(), uint16(destination.Port))
}

func (adapter sessionAdapter) HandleConnection(connection xnet.Conn, destination xnet.Destination) {
	adapter.session.Handle(connection, strings.ToLower(destination.Network.String()), destination.Address.String(), uint16(destination.Port))
}

type packetPath struct {
	once     sync.Once
	engine   tun.Stack
	endpoint stack.LinkEndpoint
	device   io.Closer
}

func (path *packetPath) Failed() bool {
	if device, ok := path.device.(interface{ Failed() bool }); ok {
		return device.Failed()
	}
	return false
}

func startPacket(ctx context.Context, endpoint stack.LinkEndpoint, device io.Closer, session *wholedevice.Session) (io.Closer, error) {
	path := &packetPath{endpoint: endpoint, device: device}
	engine, err := tun.NewEndpointStack(ctx, endpoint, sessionAdapter{session})
	path.engine = engine
	if err == nil {
		err = engine.Start()
	}
	if err != nil {
		path.Close()
		return nil, err
	}
	return path, nil
}

func (path *packetPath) Close() error {
	path.once.Do(func() {
		if device, ok := path.device.(interface{ Stop() }); ok {
			device.Stop()
		}
		if path.engine != nil {
			path.engine.Close()
		}
		if path.endpoint != nil {
			path.endpoint.Close()
		}
		if path.device != nil {
			path.device.Close()
		}
	})
	return nil
}
