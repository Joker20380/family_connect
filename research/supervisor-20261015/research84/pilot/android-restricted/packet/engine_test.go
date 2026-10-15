package packet

import (
	"context"
	"io"
	"net"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
	"gvisor.dev/gvisor/pkg/tcpip"
	"gvisor.dev/gvisor/pkg/tcpip/adapters/gonet"
	"gvisor.dev/gvisor/pkg/tcpip/header"
	"gvisor.dev/gvisor/pkg/tcpip/link/channel"
	"gvisor.dev/gvisor/pkg/tcpip/network/ipv4"
	"gvisor.dev/gvisor/pkg/tcpip/stack"
	"gvisor.dev/gvisor/pkg/tcpip/transport/tcp"
	"gvisor.dev/gvisor/pkg/tcpip/transport/udp"
)

type fixtureStream struct{ *net.TCPConn }

func (stream fixtureStream) Reset() error { return stream.Close() }

type fixturePlane struct {
	address string
	done    chan struct{}
	once    sync.Once
	opens   atomic.Int32
	dns     atomic.Int32
}

func (plane *fixturePlane) Open(ctx context.Context, host string, port uint16) (wholedevice.Stream, error) {
	plane.opens.Add(1)
	connection, err := (&net.Dialer{}).DialContext(ctx, "tcp4", plane.address)
	if err != nil {
		return nil, err
	}
	return fixtureStream{connection.(*net.TCPConn)}, nil
}
func (plane *fixturePlane) QueryDNS(_ context.Context, query []byte) ([]byte, error) {
	plane.dns.Add(1)
	answer := append([]byte{}, query...)
	answer[2] |= 0x80
	return answer, nil
}
func (plane *fixturePlane) Close() error { plane.once.Do(func() { close(plane.done) }); return nil }
func (plane *fixturePlane) Wait() error  { <-plane.done; return wholedevice.ErrClosed }

func TestExistingPacketEngineTCPDNSAndFailClosed(test *testing.T) {
	listener, err := net.Listen("tcp4", "127.0.0.1:0")
	if err != nil {
		test.Fatal(err)
	}
	defer listener.Close()
	go func() {
		for {
			connection, err := listener.Accept()
			if err != nil {
				return
			}
			go func() { defer connection.Close(); io.Copy(connection, connection) }()
		}
	}()
	plane := &fixturePlane{address: listener.Addr().String(), done: make(chan struct{})}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	session := wholedevice.Attach(ctx, plane, nil)
	defer session.Close()
	applicationLink := channel.New(64, 1280, "")
	familyLink := channel.New(64, 1280, "")
	engine, err := Start(ctx, familyLink, session)
	if err != nil {
		test.Fatal(err)
	}
	defer engine.Close()
	application := stack.New(stack.Options{NetworkProtocols: []stack.NetworkProtocolFactory{ipv4.NewProtocol}, TransportProtocols: []stack.TransportProtocolFactory{tcp.NewProtocol, udp.NewProtocol}})
	defer application.Close()
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
	defer func() { cancel(); pumps.Wait() }()
	var flows sync.WaitGroup
	for index := 0; index < 4; index++ {
		flows.Add(1)
		go func(value byte) {
			defer flows.Done()
			bounded, finish := context.WithTimeout(ctx, 3*time.Second)
			defer finish()
			connection, err := gonet.DialTCPWithBind(bounded, application, tcpip.FullAddress{NIC: 1}, tcpip.FullAddress{NIC: 1, Addr: tcpip.AddrFrom4([4]byte{93, 184, 216, 34}), Port: 443}, ipv4.ProtocolNumber)
			if err != nil {
				test.Error(err)
				return
			}
			defer connection.Close()
			connection.SetDeadline(time.Now().Add(3 * time.Second))
			payload := []byte{value, 42, value}
			if _, err = connection.Write(payload); err != nil {
				test.Error(err)
				return
			}
			connection.CloseWrite()
			response, err := io.ReadAll(connection)
			if err != nil || string(response) != string(payload) {
				test.Error("TCP lifecycle", err)
			}
		}(byte(index))
	}
	flows.Wait()
	if plane.opens.Load() != 4 {
		test.Fatal("TCP conversion", plane.opens.Load())
	}
	for _, port := range []uint16{53, 443} {
		connection, err := gonet.DialUDP(application, nil, &tcpip.FullAddress{NIC: 1, Addr: tcpip.AddrFrom4([4]byte{10, 79, 0, 1}), Port: port}, ipv4.ProtocolNumber)
		if err != nil {
			test.Fatal(err)
		}
		connection.SetDeadline(time.Now().Add(100 * time.Millisecond))
		query := make([]byte, 12)
		query[0] = 12
		connection.Write(query)
		answer := make([]byte, 32)
		count, err := connection.Read(answer)
		connection.Close()
		if port == 53 && (err != nil || count != 12 || answer[2]&0x80 == 0) {
			test.Fatal("Family DNS", err)
		}
		if port == 443 && err == nil {
			test.Fatal("UDP bypass")
		}
	}
	if plane.dns.Load() != 1 {
		test.Fatal("DNS bypass")
	}
	plane.Close()
	session.Close()
	if session.Counters.Active.Load() != 0 || session.Allow("tcp", "1.1.1.1", 443) {
		test.Fatal("failure cleanup")
	}
}
