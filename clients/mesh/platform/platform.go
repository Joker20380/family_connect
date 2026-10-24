package platform

import (
	"context"
	"io"
	"strings"
	"sync"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
	xnet "github.com/xtls/xray-core/common/net"
	"github.com/xtls/xray-core/proxy/tun"
	"gvisor.dev/gvisor/pkg/tcpip"
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
	endpoint *packetEndpoint
	device   io.Closer
}

type packetEndpoint struct {
	stack.LinkEndpoint
	mu    sync.RWMutex
	ready bool
}

type packetDispatcher struct {
	endpoint   *packetEndpoint
	dispatcher stack.NetworkDispatcher
}

func (endpoint *packetEndpoint) Attach(dispatcher stack.NetworkDispatcher) {
	if dispatcher == nil {
		endpoint.LinkEndpoint.Attach(nil)
		return
	}
	endpoint.LinkEndpoint.Attach(&packetDispatcher{endpoint: endpoint, dispatcher: dispatcher})
}

func (endpoint *packetEndpoint) setReady(ready bool) {
	endpoint.mu.Lock()
	defer endpoint.mu.Unlock()
	endpoint.ready = ready
}

func (dispatcher *packetDispatcher) DeliverNetworkPacket(protocol tcpip.NetworkProtocolNumber, packet *stack.PacketBuffer) {
	dispatcher.endpoint.mu.RLock()
	defer dispatcher.endpoint.mu.RUnlock()
	if dispatcher.endpoint.ready {
		dispatcher.dispatcher.DeliverNetworkPacket(protocol, packet)
	}
}

func (dispatcher *packetDispatcher) DeliverLinkPacket(protocol tcpip.NetworkProtocolNumber, packet *stack.PacketBuffer) {
	dispatcher.endpoint.mu.RLock()
	defer dispatcher.endpoint.mu.RUnlock()
	if dispatcher.endpoint.ready {
		dispatcher.dispatcher.DeliverLinkPacket(protocol, packet)
	}
}

func (path *packetPath) Failed() bool {
	if device, ok := path.device.(interface{ Failed() bool }); ok {
		return device.Failed()
	}
	return false
}

func startPacket(ctx context.Context, endpoint stack.LinkEndpoint, device io.Closer, session *wholedevice.Session) (io.Closer, error) {
	path := &packetPath{endpoint: &packetEndpoint{LinkEndpoint: endpoint}, device: device}
	engine, err := tun.NewEndpointStack(ctx, path.endpoint, sessionAdapter{session})
	path.engine = engine
	if err == nil {
		err = engine.Start()
	}
	if err != nil {
		path.Close()
		return nil, err
	}
	path.endpoint.setReady(true)
	return path, nil
}

func (path *packetPath) Close() error {
	path.once.Do(func() {
		if path.endpoint != nil {
			path.endpoint.setReady(false)
		}
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
