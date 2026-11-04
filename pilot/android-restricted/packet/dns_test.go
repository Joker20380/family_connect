package packet

import (
	"bytes"
	"context"
	"encoding/binary"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
	"golang.org/x/net/dns/dnsmessage"
	"gvisor.dev/gvisor/pkg/tcpip"
	"gvisor.dev/gvisor/pkg/tcpip/adapters/gonet"
	"gvisor.dev/gvisor/pkg/tcpip/header"
	"gvisor.dev/gvisor/pkg/tcpip/link/channel"
	"gvisor.dev/gvisor/pkg/tcpip/network/ipv4"
	"gvisor.dev/gvisor/pkg/tcpip/stack"
	"gvisor.dev/gvisor/pkg/tcpip/transport/tcp"
	"gvisor.dev/gvisor/pkg/tcpip/transport/udp"
)

func dnsPacketQuery(test *testing.T, identifier uint16, kind dnsmessage.Type) []byte {
	test.Helper()
	message := dnsmessage.Message{Header: dnsmessage.Header{ID: identifier, RecursionDesired: true}, Questions: []dnsmessage.Question{{Name: dnsmessage.MustNewName("example.com."), Type: kind, Class: dnsmessage.ClassINET}}}
	query, err := message.Pack()
	if err != nil {
		test.Fatal(err)
	}
	return query
}

func dnsPacketFixture(test *testing.T, plane wholedevice.DataPlane) (*stack.Stack, *wholedevice.Session) {
	test.Helper()
	ctx, cancel := context.WithCancel(context.Background())
	test.Cleanup(cancel)
	session := wholedevice.Attach(ctx, plane, nil)
	test.Cleanup(session.Close)
	applicationLink := channel.New(64, 1280, "")
	familyLink := channel.New(64, 1280, "")
	engine, err := Start(ctx, familyLink, session)
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() { engine.Close() })
	application := stack.New(stack.Options{NetworkProtocols: []stack.NetworkProtocolFactory{ipv4.NewProtocol}, TransportProtocols: []stack.TransportProtocolFactory{tcp.NewProtocol, udp.NewProtocol}})
	test.Cleanup(application.Close)
	if err := application.CreateNIC(1, applicationLink); err != nil {
		test.Fatal(err)
	}
	if err := application.AddProtocolAddress(1, tcpip.ProtocolAddress{Protocol: ipv4.ProtocolNumber, AddressWithPrefix: tcpip.AddrFrom4([4]byte{10, 79, 0, 2}).WithPrefix()}, stack.AddressProperties{}); err != nil {
		test.Fatal(err)
	}
	application.SetRouteTable([]tcpip.Route{{Destination: header.IPv4EmptySubnet, NIC: 1}})
	var pumps sync.WaitGroup
	pump := func(source, destination *channel.Endpoint) {
		defer pumps.Done()
		for {
			packet := source.ReadContext(ctx)
			if packet == nil {
				return
			}
			incoming := stack.NewPacketBuffer(stack.PacketBufferOptions{Payload: packet.ToBuffer()})
			destination.InjectInbound(ipv4.ProtocolNumber, incoming)
			incoming.DecRef()
			packet.DecRef()
		}
	}
	pumps.Add(2)
	go pump(applicationLink, familyLink)
	go pump(familyLink, applicationLink)
	test.Cleanup(func() { cancel(); pumps.Wait() })
	return application, session
}

func TestDNSCompletedQueriesDoNotOccupyUDPFlowLimit(test *testing.T) {
	plane := &fixturePlane{done: make(chan struct{})}
	application, session := dnsPacketFixture(test, plane)
	for index := 0; index < 64; index++ {
		connection, err := gonet.DialUDP(application, &tcpip.FullAddress{NIC: 1, Port: uint16(40000 + index)}, &tcpip.FullAddress{NIC: 1, Addr: tcpip.AddrFrom4([4]byte{10, 79, 0, 1}), Port: 53}, ipv4.ProtocolNumber)
		if err != nil {
			test.Fatal(err)
		}
		connection.SetDeadline(time.Now().Add(time.Second))
		query := dnsPacketQuery(test, uint16(index+1), dnsmessage.TypeA)
		if _, err := connection.Write(query); err != nil {
			connection.Close()
			test.Fatal(err)
		}
		answer := make([]byte, 4096)
		count, err := connection.Read(answer)
		connection.Close()
		query[2] |= 0x80
		if err != nil || !bytes.Equal(answer[:count], query) {
			test.Fatalf("query %d lost after completed requests: %v; counters=%v", index+1, err, session.Snapshot())
		}
	}
	if plane.dns.Load() != 64 || plane.opens.Load() != 0 {
		test.Fatal("DNS routing", plane.dns.Load(), plane.opens.Load())
	}
}

func TestDNSPairedDatagramsReuseSourcePort(test *testing.T) {
	plane := &fixturePlane{done: make(chan struct{})}
	application, _ := dnsPacketFixture(test, plane)
	connection, err := gonet.DialUDP(application, &tcpip.FullAddress{NIC: 1, Port: 41000}, &tcpip.FullAddress{NIC: 1, Addr: tcpip.AddrFrom4([4]byte{10, 79, 0, 1}), Port: 53}, ipv4.ProtocolNumber)
	if err != nil {
		test.Fatal(err)
	}
	defer connection.Close()
	connection.SetDeadline(time.Now().Add(time.Second))
	expected := make(map[uint16][]byte)
	for _, kind := range []dnsmessage.Type{dnsmessage.TypeA, dnsmessage.TypeAAAA} {
		query := dnsPacketQuery(test, uint16(kind), kind)
		if _, err := connection.Write(query); err != nil {
			test.Fatal(err)
		}
		query[2] |= 0x80
		expected[uint16(kind)] = query
	}
	seen := make(map[uint16]bool)
	for index := 0; index < 2; index++ {
		answer := make([]byte, 4096)
		count, err := connection.Read(answer)
		if err != nil || count < 12 || !bytes.Equal(answer[:count], expected[binary.BigEndian.Uint16(answer)]) {
			test.Fatal("paired DNS packet lost", err)
		}
		seen[binary.BigEndian.Uint16(answer)] = true
	}
	if !seen[1] || !seen[28] || plane.dns.Load() != 2 {
		test.Fatal("DNS responses mixed", seen)
	}
}
