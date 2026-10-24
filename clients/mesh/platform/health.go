package platform

import (
	"context"
	"crypto/rand"
	"encoding/binary"
	"encoding/hex"
	"net"
	"syscall"
	"time"

	"github.com/Joker20380/family_connect/carrier/desktopmesh"
	"github.com/Joker20380/family_connect/desktopbridge/worker"
)

type healthNetwork struct {
	lookup func(string) (*net.Interface, error)
	dial   func(context.Context, net.Interface, string) (net.Conn, error)
}

func (platform Native) Probe(parent context.Context) bool {
	return probeHealth(parent, healthNetwork{lookup: net.InterfaceByName,
		dial: func(ctx context.Context, tunnel net.Interface, target string) (net.Conn, error) {
			dialer := net.Dialer{LocalAddr: &net.UDPAddr{IP: net.ParseIP(worker.TunnelIPv4)},
				Control: func(protocol, address string, raw syscall.RawConn) error {
					if protocol != "udp4" {
						return desktopmesh.ErrConfiguration
					}
					accepted := false
					if err := raw.Control(func(descriptor uintptr) { accepted = platform.bindVPN(tunnel, int(descriptor)) }); err != nil {
						return err
					}
					if !accepted {
						return desktopmesh.ErrConfiguration
					}
					return nil
				}}
			return dialer.DialContext(ctx, "udp4", net.JoinHostPort(target, "53"))
		}})
}

func probeHealth(parent context.Context, network healthNetwork) bool {
	ctx, cancel := context.WithTimeout(parent, 5*time.Second)
	defer cancel()
	tunnel, err := network.lookup(worker.InterfaceName)
	if err != nil || tunnel == nil || tunnel.Name != worker.InterfaceName || tunnel.Index <= 0 ||
		tunnel.Flags&net.FlagUp == 0 || tunnel.Flags&net.FlagLoopback != 0 || ctx.Err() != nil {
		return false
	}
	for _, target := range []string{"1.1.1.1", "9.9.9.9"} {
		if ctx.Err() != nil {
			return false
		}
		attempt, stop := context.WithTimeout(ctx, 2500*time.Millisecond)
		good := probeTarget(attempt, *tunnel, target, network.dial)
		stop()
		if ctx.Err() != nil {
			return false
		}
		current, err := network.lookup(worker.InterfaceName)
		if err != nil || current == nil || current.Index != tunnel.Index || current.Name != tunnel.Name || current.Flags&net.FlagUp == 0 {
			return false
		}
		if good {
			return true
		}
	}
	return false
}

func probeTarget(ctx context.Context, tunnel net.Interface, target string, dial func(context.Context, net.Interface, string) (net.Conn, error)) bool {
	var random [18]byte
	if _, err := rand.Read(random[:]); err != nil {
		return false
	}
	query := desktopmesh.HealthDNSQuery(binary.BigEndian.Uint16(random[:2]), "fc-"+hex.EncodeToString(random[2:]))
	connection, err := dial(ctx, tunnel, target)
	if err != nil || connection == nil {
		return false
	}
	defer connection.Close()
	stop := context.AfterFunc(ctx, func() { connection.Close() })
	defer stop()
	deadline, ok := ctx.Deadline()
	if !ok || connection.SetDeadline(deadline) != nil || ctx.Err() != nil {
		return false
	}
	count, err := connection.Write(query)
	if err != nil || count != len(query) {
		return false
	}
	var response [1233]byte
	count, err = connection.Read(response[:])
	return err == nil && ctx.Err() == nil && desktopmesh.HealthDNSValid(query, response[:count])
}
