package tcpforward

import (
	"context"
	"encoding/binary"
	"errors"
	"fmt"
	"testing"
	"time"

	"golang.org/x/net/dns/dnsmessage"
)

func TestMuxDNSOutstandingLimitAndRelease(test *testing.T) {
	ctx, client, server := muxPair(test, 0, 4, 4)
	server.exchange = func(ctx context.Context, query []byte) ([]byte, error) {
		<-ctx.Done()
		return nil, ctx.Err()
	}
	query := dnsQuestion(test, dnsmessage.TypeA)
	results := make(chan error, MuxMaxDNS)
	for range MuxMaxDNS {
		go func() { _, err := client.QueryDNS(ctx, query); results <- err }()
	}
	deadline := time.Now().Add(2 * time.Second)
	for server.Stats().DNSRequests != MuxMaxDNS && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	if server.Stats().DNSRequests != MuxMaxDNS {
		test.Fatal("outstanding fixture incomplete")
	}
	if _, err := client.QueryDNS(ctx, query); !errors.Is(err, ErrStreamLimit) {
		test.Fatal("client DNS N+1", err)
	}
	server.mu.Lock()
	server.dnsFrameLocked(dnsFrame(muxDNSQuery, MuxMaxDNS+1, query))
	bounded := len(server.dns) == MuxMaxDNS && len(server.dnsJobs) == MuxMaxDNS && server.stats.DNSErrors == 1
	server.signalLocked()
	server.mu.Unlock()
	if !bounded {
		test.Fatal("gateway DNS N+1 allocated a worker")
	}
	client.Close()
	server.Close()
	for range MuxMaxDNS {
		if err := <-results; err == nil {
			test.Fatal("cancelled query succeeded")
		}
	}
	if client.Stats().RetainedBytes != 0 || server.Stats().RetainedBytes != 0 {
		test.Fatal("DNS retention after shutdown")
	}
}

func TestMuxMalformedWireBounds(test *testing.T) {
	frames := []muxFrame{
		{dataFrame, 0, []byte("data")}, {dataFrame, 2, []byte("data")},
		{dataFrame, 0xffffffff, []byte("data")}, {255, 1, nil},
		{dataFrame, 1, make([]byte, MaxData+1)},
		{muxWindowUpdate, 1, []byte{255, 255, 255, 255}},
		{muxWindowUpdate, 1, make([]byte, 4)},
		dnsFrame(muxDNSQuery, 0, make([]byte, 12)),
		dnsFrame(muxDNSQuery, 1, make([]byte, MuxMaxDNSMessage+1)),
		dnsFrame(muxDNSResponse, 1, make([]byte, 11)),
	}
	for index, frame := range frames {
		if _, err := decodeMux(frame.encode()); err == nil {
			test.Fatalf("invalid frame %d accepted", index)
		}
	}
	encoded := muxFrame{dataFrame, 1, []byte("data")}.encode()
	binary.BigEndian.PutUint32(encoded[6:10], 0xffffffff)
	if _, err := decodeMux(encoded); err == nil {
		test.Fatal("length mismatch accepted")
	}
	query := dnsQuestion(test, dnsmessage.TypeA)
	for _, payload := range [][]byte{nil, make([]byte, MuxMaxDNSMessage+1), append([]byte(nil), query...)} {
		if len(payload) == len(query) {
			binary.BigEndian.PutUint16(payload[10:12], 129)
		}
		if _, err := validDNS(payload, false); err == nil {
			test.Fatal("invalid DNS length/count accepted")
		}
	}
}

func TestMuxTerminalTransitionsIsolated(test *testing.T) {
	for _, kind := range []byte{dataFrame, finFrame} {
		test.Run(fmt.Sprint(kind), func(test *testing.T) {
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			mux := &Mux{ctx: ctx, streams: make(map[uint32]*MuxStream), changed: make(chan struct{})}
			stream, sibling := mux.makeStreamLocked(1), mux.makeStreamLocked(3)
			stream.opened, sibling.opened = true, true
			mux.dispatchLocked(muxFrame{finFrame, 1, nil})
			var payload []byte
			if kind == dataFrame {
				payload = []byte("after-FIN")
			}
			mux.dispatchLocked(muxFrame{kind, 1, payload})
			if stream.terminal != ErrProtocol || sibling.terminal != nil || ctx.Err() != nil {
				test.Fatal("post-FIN transition leaked")
			}
			mux.removeLocked(1)
			for _, terminal := range []byte{dataFrame, resetFrame, finFrame, closeFrame} {
				mux.dispatchLocked(muxFrame{terminal, 1, nil})
			}
			mux.dispatchLocked(muxFrame{dataFrame, 3, []byte("survivor")})
			if len(mux.streams) != 1 || sibling.used != len("survivor") || sibling.terminal != nil {
				test.Fatal("stale terminal frame changed sibling")
			}
		})
	}
}
