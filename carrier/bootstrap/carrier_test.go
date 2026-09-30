package bootstrap

import (
	"bytes"
	"context"
	"crypto/rand"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

func TestCarrierExclusiveLeaseIsolationAndShutdown(test *testing.T) {
	ctx, cancel := context.WithCancel(bounded(test))
	defer cancel()
	client, server := pair()
	finished := make(chan error, 1)
	var active, peak atomic.Int32
	go func() {
		finished <- ServeCarrier(ctx, server, func(ctx context.Context, endpoint familysession.PacketEndpoint) {
			count := active.Add(1)
			peak.Store(max(peak.Load(), count))
			defer active.Add(-1)
			for {
				raw, err := endpoint.Recv(ctx)
				if err != nil {
					return
				}
				if endpoint.SendContext(ctx, raw) != nil {
					return
				}
			}
		})
	}()
	lease, err := connectLease(ctx, client)
	if err != nil {
		test.Fatal(err)
	}
	var stranger [32]byte
	_, _ = rand.Read(stranger[:])
	for index := 0; index < 32; index++ {
		_ = client.SendContext(ctx, encodePacket(packet{kind: 'O', client: stranger}))
		_ = client.SendContext(ctx, encodePacket(packet{kind: 'C', client: stranger, server: lease.server, data: []byte("wrong client")}))
		_ = client.SendContext(ctx, encodePacket(packet{kind: 'C', client: lease.client, server: stranger, data: []byte("old lease")}))
	}
	if err := lease.SendContext(ctx, []byte("only owner")); err != nil {
		test.Fatal(err)
	}
	raw, err := client.Recv(ctx)
	message, ok := decodePacket(raw)
	if err != nil || !ok || message.kind != 'S' || !bytes.Equal(message.data, []byte("only owner")) {
		test.Fatal("mixed clients", err)
	}
	cancel()
	<-finished
	if active.Load() != 0 || peak.Load() != 1 {
		test.Fatal("unbounded exchange")
	}
}

func TestCarrierBusyTimeoutAndCancellation(test *testing.T) {
	client, server := pair()
	defer client.Close()
	defer server.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Millisecond)
	defer cancel()
	if _, err := connectLease(ctx, client); err == nil {
		test.Fatal("unavailable seed accepted")
	}
	ctx, cancel = context.WithCancel(context.Background())
	cancel()
	if _, err := connectLease(ctx, client); err == nil {
		test.Fatal("cancel ignored")
	}
}

func TestCarrierParser(test *testing.T) {
	var nonce [32]byte
	nonce[0] = 1
	valid := encodePacket(packet{kind: 'C', client: nonce, server: nonce, data: []byte("hello")})
	for _, raw := range [][]byte{nil, []byte("OPEN"), valid[:68], bytes.Repeat([]byte("x"), packetLimit+envelopeSize+1), encodePacket(packet{kind: 'O', client: nonce, server: nonce}), encodePacket(packet{kind: 'C', client: nonce, data: []byte("bad")})} {
		if _, ok := decodePacket(raw); ok {
			test.Fatal("invalid envelope")
		}
	}
	if _, ok := decodePacket(valid); !ok {
		test.Fatal("valid envelope")
	}
}

func FuzzCarrier(fuzz *testing.F) {
	fuzz.Add([]byte("FCB1"))
	fuzz.Fuzz(func(test *testing.T, raw []byte) { _, _ = decodePacket(raw) })
}

type dropFirst struct {
	familysession.PacketEndpoint
	kind    byte
	dropped bool
}

func (endpoint *dropFirst) SendContext(ctx context.Context, raw []byte) error {
	message, ok := decodePacket(raw)
	if ok && message.kind == endpoint.kind && !endpoint.dropped {
		endpoint.dropped = true
		return nil
	}
	return endpoint.PacketEndpoint.SendContext(ctx, raw)
}

func TestLostOpenAndAcceptDoNotAllocateExtraSessions(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 4*time.Second)
	defer cancel()
	client, server := pair()
	var sessions atomic.Int32
	done := make(chan error, 1)
	go func() {
		done <- ServeCarrier(ctx, &dropFirst{PacketEndpoint: server, kind: 'A'}, func(ctx context.Context, endpoint familysession.PacketEndpoint) {
			sessions.Add(1)
			_, _ = endpoint.Recv(ctx)
		})
	}()
	lease, err := connectLease(ctx, &dropFirst{PacketEndpoint: client, kind: 'O'})
	if err != nil || lease == nil {
		test.Fatal("lease did not survive loss", err)
	}
	cancel()
	<-done
	if sessions.Load() != 1 {
		test.Fatal("duplicate lease after control packet loss")
	}
}
