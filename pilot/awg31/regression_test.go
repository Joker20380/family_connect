// SPDX-License-Identifier: MIT
// Synthetic keys and loopback sockets only. Copied into the pinned engine's device package.
package device

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"net/netip"
	"testing"
	"time"

	"github.com/amnezia-vpn/amneziawg-go/v3/conn"
	"github.com/amnezia-vpn/amneziawg-go/v3/tun"
	"github.com/amnezia-vpn/amneziawg-go/v3/tun/tuntest"
)

// Make the startup interleaving deterministic: TUN Read is waiting before IpcSet.
type fcObservedTUN struct {
	tun.Device
	entered chan struct{}
}

func (t *fcObservedTUN) Read(bufs [][]byte, sizes []int, offset int) (int, error) {
	select {
	case t.entered <- struct{}{}:
	default:
	}
	return t.Device.Read(bufs, sizes, offset)
}

func TestFCFirstPacketAfterConfiguration(t *testing.T) {
	key := make([]byte, 32)
	if _, err := rand.Read(key); err != nil {
		t.Fatal(err)
	}
	protected := []string{"s1", "16", "s2", "16", "s3", "16", "s4", "16", "header_protection_key", hex.EncodeToString(key)}
	cases := []struct {
		name string
		cfg  []string
	}{
		{"wireguard", nil},
		{"s4", []string{"s4", "25"}},
		{"header_protection", protected},
		{"content_padding", append(append([]string{}, protected...), "content_padding_addition", "0-32")},
		{"random_trailers", append(append([]string{}, protected...), "random_trailers", "true")},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			cfg, endpoints := genConfigs(t, tc.cfg...)
			var pair testPair
			for i := range pair {
				p := &pair[i]
				p.tun = tuntest.NewChannelTUN()
				p.ip = netip.AddrFrom4([4]byte{1, 0, 0, byte(i + 1)})
				observed := &fcObservedTUN{Device: p.tun.TUN(), entered: make(chan struct{}, 1)}
				p.dev = NewDevice(observed, conn.NewDefaultBind(), NewLogger(LogLevelError, ""))
				t.Cleanup(p.dev.Close)
				select {
				case <-observed.entered:
				case <-time.After(time.Second):
					t.Fatal("TUN reader did not start")
				}
				if err := p.dev.IpcSet(cfg[i]); err != nil {
					t.Fatal(err)
				}
				if err := p.dev.Up(); err != nil {
					t.Fatal(err)
				}
				endpoints[i^1] = fmt.Sprintf(endpoints[i^1], p.dev.net.port)
			}
			for i := range pair {
				if err := pair[i].dev.IpcSet(endpoints[i]); err != nil {
					t.Fatal(err)
				}
			}
			pair.Send(t, Ping, nil)
			pair.Send(t, Pong, nil)
		})
	}
}
