package platform

import (
	"sync/atomic"
	"testing"
	"time"

	"gvisor.dev/gvisor/pkg/tcpip"
	"gvisor.dev/gvisor/pkg/tcpip/link/channel"
	"gvisor.dev/gvisor/pkg/tcpip/network/ipv4"
	"gvisor.dev/gvisor/pkg/tcpip/stack"
)

type fencedDispatcher struct {
	entered chan struct{}
	finish  chan struct{}
	network atomic.Int32
	link    atomic.Int32
}

func (dispatcher *fencedDispatcher) DeliverNetworkPacket(tcpip.NetworkProtocolNumber, *stack.PacketBuffer) {
	dispatcher.network.Add(1)
	close(dispatcher.entered)
	<-dispatcher.finish
}

func (dispatcher *fencedDispatcher) DeliverLinkPacket(tcpip.NetworkProtocolNumber, *stack.PacketBuffer) {
	dispatcher.link.Add(1)
}

func TestPacketIngressInitializationAndDrainFence(test *testing.T) {
	link := channel.New(4, 1280, "")
	defer link.Close()
	endpoint := &packetEndpoint{LinkEndpoint: link}
	target := &fencedDispatcher{entered: make(chan struct{}), finish: make(chan struct{})}
	endpoint.Attach(target)
	packet := stack.NewPacketBuffer(stack.PacketBufferOptions{})
	defer packet.DecRef()
	dispatcher := &packetDispatcher{endpoint: endpoint, dispatcher: target}
	link.InjectInbound(ipv4.ProtocolNumber, packet)
	dispatcher.DeliverLinkPacket(ipv4.ProtocolNumber, packet)
	if target.network.Load() != 0 || target.link.Load() != 0 {
		test.Fatal("ingress before transport handlers initialized")
	}
	endpoint.setReady(true)
	dispatcher.DeliverLinkPacket(ipv4.ProtocolNumber, packet)
	delivered := make(chan struct{})
	go func() { link.InjectInbound(ipv4.ProtocolNumber, packet); close(delivered) }()
	select {
	case <-target.entered:
	case <-time.After(time.Second):
		test.Fatal("enabled ingress not delivered")
	}
	drained := make(chan struct{})
	go func() { endpoint.setReady(false); close(drained) }()
	close(target.finish)
	select {
	case <-drained:
	case <-time.After(time.Second):
		test.Fatal("ingress did not drain")
	}
	<-delivered
	link.InjectInbound(ipv4.ProtocolNumber, packet)
	dispatcher.DeliverLinkPacket(ipv4.ProtocolNumber, packet)
	if target.network.Load() != 1 || target.link.Load() != 1 {
		test.Fatal("late ingress after drain", target.network.Load(), target.link.Load())
	}
}
