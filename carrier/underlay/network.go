package underlay

import (
	"context"
	"errors"
	"net"
	"net/http"
	"strconv"
	"sync"
	"sync/atomic"
	"syscall"
	"time"

	"github.com/pion/transport/v4"
	"github.com/pion/transport/v4/stdnet"
)

var ErrDenied = errors.New("underlay socket denied")

type Network struct {
	*stdnet.Net
	ctx       context.Context
	protect   func(int) bool
	resolver  *net.Resolver
	Protected atomic.Uint64
	Rejected  atomic.Uint64
	DNS       atomic.Uint64
	protectMu sync.RWMutex
	closed    bool
}

func New(ctx context.Context, resolverAddress string, protect func(int) bool) (*Network, error) {
	host, port, err := net.SplitHostPort(resolverAddress)
	if err != nil || net.ParseIP(host).To4() == nil || port != "53" || protect == nil {
		return nil, ErrDenied
	}
	base, err := stdnet.NewNet()
	if err != nil {
		return nil, err
	}
	network := &Network{Net: base, ctx: ctx, protect: protect}
	network.resolver = &net.Resolver{PreferGo: true, StrictErrors: true, Dial: func(ctx context.Context, protocol, _ string) (net.Conn, error) {
		if protocol != "udp" && protocol != "tcp" {
			return nil, ErrDenied
		}
		network.DNS.Add(1)
		dialer := net.Dialer{Control: network.control, Timeout: 10 * time.Second}
		return dialer.DialContext(ctx, protocol+"4", resolverAddress)
	}}
	return network, nil
}

func (network *Network) control(protocol, _ string, raw syscall.RawConn) error {
	network.protectMu.RLock()
	defer network.protectMu.RUnlock()
	if network.closed || network.ctx.Err() != nil || (protocol != "tcp4" && protocol != "udp4") {
		return ErrDenied
	}
	accepted := false
	if err := raw.Control(func(fd uintptr) { accepted = network.protect(int(fd)) }); err != nil {
		return err
	}
	if !accepted {
		network.Rejected.Add(1)
		return ErrDenied
	}
	network.Protected.Add(1)
	return nil
}

func (network *Network) Close() {
	network.protectMu.Lock()
	network.closed = true
	network.protectMu.Unlock()
}

func (network *Network) DialContext(parent context.Context, protocol, address string) (net.Conn, error) {
	if protocol == "tcp" || protocol == "udp" {
		protocol += "4"
	}
	if protocol != "tcp4" && protocol != "udp4" {
		return nil, ErrDenied
	}
	ctx, cancel := context.WithTimeout(parent, 15*time.Second)
	defer cancel()
	stop := context.AfterFunc(network.ctx, cancel)
	defer stop()
	dialer := net.Dialer{Control: network.control, Resolver: network.resolver, Timeout: 15 * time.Second, KeepAlive: 30 * time.Second}
	return dialer.DialContext(ctx, protocol, address)
}

func (network *Network) Dial(protocol, address string) (net.Conn, error) {
	return network.DialContext(network.ctx, protocol, address)
}

func (network *Network) DialUDP(protocol string, local, remote *net.UDPAddr) (transport.UDPConn, error) {
	if local != nil && (local.Port != 0 || !local.IP.IsUnspecified()) {
		return nil, ErrDenied
	}
	connection, err := network.Dial(protocol, remote.String())
	if err != nil {
		return nil, err
	}
	return connection.(*net.UDPConn), nil
}

func (network *Network) DialTCP(protocol string, local, remote *net.TCPAddr) (transport.TCPConn, error) {
	if local != nil && (local.Port != 0 || !local.IP.IsUnspecified()) {
		return nil, ErrDenied
	}
	connection, err := network.Dial(protocol, remote.String())
	if err != nil {
		return nil, err
	}
	return connection.(*net.TCPConn), nil
}

func (network *Network) ListenPacket(protocol, address string) (net.PacketConn, error) {
	if protocol == "udp" {
		protocol = "udp4"
	}
	if protocol != "udp4" {
		return nil, ErrDenied
	}
	config := net.ListenConfig{Control: network.control}
	return config.ListenPacket(network.ctx, protocol, address)
}

func (network *Network) ListenUDP(protocol string, local *net.UDPAddr) (transport.UDPConn, error) {
	address := "0.0.0.0:0"
	if local != nil {
		address = local.String()
	}
	connection, err := network.ListenPacket(protocol, address)
	if err != nil {
		return nil, err
	}
	return connection.(*net.UDPConn), nil
}

func (network *Network) ListenTCP(string, *net.TCPAddr) (transport.TCPListener, error) {
	return nil, ErrDenied
}

func (network *Network) ResolveIPAddr(protocol, address string) (*net.IPAddr, error) {
	if protocol != "ip" && protocol != "ip4" {
		return nil, ErrDenied
	}
	if ip := net.ParseIP(address); ip != nil {
		if ip.To4() == nil {
			return nil, ErrDenied
		}
		return &net.IPAddr{IP: ip.To4()}, nil
	}
	ctx, cancel := context.WithTimeout(network.ctx, 10*time.Second)
	defer cancel()
	addresses, err := network.resolver.LookupIP(ctx, "ip4", address)
	if err != nil || len(addresses) == 0 {
		return nil, ErrDenied
	}
	return &net.IPAddr{IP: addresses[0]}, nil
}

func (network *Network) ResolveUDPAddr(protocol, address string) (*net.UDPAddr, error) {
	if protocol != "udp" && protocol != "udp4" {
		return nil, ErrDenied
	}
	host, port, err := net.SplitHostPort(address)
	if err != nil {
		return nil, ErrDenied
	}
	number, err := strconv.Atoi(port)
	if err != nil || number < 0 || number > 65535 {
		return nil, ErrDenied
	}
	ip, err := network.ResolveIPAddr("ip4", host)
	if err != nil {
		return nil, err
	}
	return &net.UDPAddr{IP: ip.IP, Port: number}, nil
}

func (network *Network) ResolveTCPAddr(protocol, address string) (*net.TCPAddr, error) {
	if protocol != "tcp" && protocol != "tcp4" {
		return nil, ErrDenied
	}
	resolved, err := network.ResolveUDPAddr("udp4", address)
	if err != nil {
		return nil, err
	}
	return &net.TCPAddr{IP: resolved.IP, Port: resolved.Port}, nil
}

func (network *Network) CreateDialer(*net.Dialer) transport.Dialer { return network }
func (network *Network) CreateListenConfig(*net.ListenConfig) transport.ListenConfig {
	return protectedListener{network}
}

type protectedListener struct{ network *Network }

func (listener protectedListener) Listen(context.Context, string, string) (net.Listener, error) {
	return nil, ErrDenied
}
func (listener protectedListener) ListenPacket(_ context.Context, protocol, address string) (net.PacketConn, error) {
	return listener.network.ListenPacket(protocol, address)
}

func (network *Network) HTTPClient() *http.Client {
	return &http.Client{Timeout: 15 * time.Second, Transport: &http.Transport{
		DialContext: network.DialContext, TLSHandshakeTimeout: 10 * time.Second, DisableKeepAlives: true,
	}}
}

var _ transport.Net = (*Network)(nil)
