package tcpforward

import (
	"bytes"
	"context"
	"encoding/binary"
	"errors"
	"fmt"
	"sync/atomic"
	"syscall"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"golang.org/x/net/dns/dnsmessage"
)

func TestMuxAuthenticatedLossReorderDuplicate(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	clientSession, serverSession := authenticatedPair(test, ctx)
	port := muxFixture(test, muxEcho)
	server, err := NewMux(ctx, serverSession, true, MuxConfig{Policy: Policy{TestOnlyLoopbackPort: port}})
	if err != nil {
		test.Fatal(err)
	}
	client, err := NewMux(ctx, clientSession, false, MuxConfig{})
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() { client.Close(); server.Close() })
	if _, err := NewMux(ctx, clientSession, false, MuxConfig{}); err == nil {
		test.Fatal("second session owner")
	}
	results := make(chan error, 4)
	for index := 0; index < 4; index++ {
		stream := muxOpen(test, ctx, client, port)
		payload := bytes.Repeat([]byte(fmt.Sprintf("stream-%02d", index)), 40000)
		go func() { results <- exactMux(stream, payload) }()
	}
	for range 4 {
		if err := <-results; err != nil {
			test.Fatal(err)
		}
	}
	if clientSession.ReliabilityStats().Retransmissions == 0 || serverSession.ReliabilityStats().RecoveredGaps == 0 {
		test.Fatal("faults not exercised")
	}
	if _, err := NewMux(ctx, &familysession.Session{}, false, MuxConfig{}); err == nil {
		test.Fatal("unauthenticated mux")
	}
}

func TestMuxConnectFailuresDoNotKillSibling(test *testing.T) {
	for _, failure := range []error{syscall.ECONNREFUSED, context.DeadlineExceeded, context.Canceled} {
		test.Run(failure.Error(), func(test *testing.T) {
			port := muxFixture(test, muxEcho)
			ctx, client, server := muxPair(test, port, 4, 4)
			var calls atomic.Int32
			server.dial = func(ctx context.Context, network, address string) (socket, error) {
				if calls.Add(1) == 2 {
					return nil, failure
				}
				return tcpDial(ctx, network, address)
			}
			sibling := muxOpen(test, ctx, client, port)
			if _, err := client.OpenTCP(ctx, OpenRequest{Host: "127.0.0.1", Port: port}); err == nil {
				test.Fatal("expected OPEN_ERROR")
			}
			if err := exactMux(sibling, []byte("surviving connection")); err != nil {
				test.Fatal(err)
			}
		})
	}
}

func TestMuxCollisionStaleAndExhaustion(test *testing.T) {
	port := muxFixture(test, muxEcho)
	ctx, client, server := muxPair(test, port, 4, 4)
	stream := muxOpen(test, ctx, client, port)
	sibling := muxOpen(test, ctx, client, port)
	server.mu.Lock()
	server.dispatchLocked(muxFrame{openFrame, stream.id, []byte(`{"host":"example.com","port":443}`)})
	server.signalLocked()
	server.mu.Unlock()
	deadline := time.Now().Add(time.Second)
	for stream.Stats().State != "reset" && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	if stream.Stats().State != "reset" {
		test.Fatal("collision not reset")
	}
	if err := exactMux(sibling, []byte("independent")); err != nil {
		test.Fatal(err)
	}
	client.mu.Lock()
	client.nextID = muxMaxID + 2
	client.mu.Unlock()
	if _, err := client.OpenTCP(ctx, OpenRequest{Host: "127.0.0.1", Port: port}); err != ErrIDExhausted {
		test.Fatal(err)
	}
	server.mu.Lock()
	before := len(server.streams)
	server.dispatchLocked(muxFrame{openFrame, 1, []byte(`{"host":"example.com","port":443}`)})
	if len(server.streams) > before {
		test.Error("stale stream recreated")
	}
	server.mu.Unlock()
}

func TestMuxDNSAnswersDuplicateAndMismatch(test *testing.T) {
	for _, kind := range []dnsmessage.Type{dnsmessage.TypeA, dnsmessage.TypeAAAA, dnsmessage.TypeCNAME} {
		test.Run(fmt.Sprint(kind), func(test *testing.T) {
			ctx, client, server := muxPair(test, 0, 4, 4)
			server.exchange = func(ctx context.Context, query []byte) ([]byte, error) {
				var message dnsmessage.Message
				message.Unpack(query)
				message.Response = true
				var body dnsmessage.ResourceBody
				switch kind {
				case dnsmessage.TypeA:
					body = &dnsmessage.AResource{A: [4]byte{93, 184, 216, 34}}
				case dnsmessage.TypeAAAA:
					body = &dnsmessage.AAAAResource{AAAA: [16]byte{0x20, 1, 0x48, 0x60}}
				case dnsmessage.TypeCNAME:
					name, _ := dnsmessage.NewName("www.example.com.")
					body = &dnsmessage.CNAMEResource{CNAME: name}
				}
				message.Answers = []dnsmessage.Resource{{Header: dnsmessage.ResourceHeader{Name: message.Questions[0].Name, Class: dnsmessage.ClassINET, TTL: 123}, Body: body}}
				return message.Pack()
			}
			response, err := client.QueryDNS(ctx, dnsQuestion(test, kind))
			if err != nil {
				test.Fatal(err)
			}
			var answer dnsmessage.Message
			if answer.Unpack(response) != nil || len(answer.Answers) != 1 || answer.Answers[0].Header.TTL != 123 {
				test.Fatal("DNS records not preserved")
			}
		})
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	mux := &Mux{ctx: ctx, streams: make(map[uint32]*MuxStream), dns: make(map[uint32]*dnsCall), changed: make(chan struct{})}
	query := dnsQuestion(test, dnsmessage.TypeA)
	mux.dns[1] = &dnsCall{ctx: ctx, cancel: cancel, query: query}
	response, _ := dnsAnswer(ctx, query)
	binary.BigEndian.PutUint16(response, 99)
	mux.dnsFrameLocked(dnsFrame(muxDNSResponse, 2, response))
	if mux.dns[1].done {
		test.Fatal("unmatched Family ID affected caller")
	}
	mux.dnsFrameLocked(dnsFrame(muxDNSResponse, 1, response))
	if !errors.Is(mux.dns[1].err, ErrDNS) {
		test.Fatal("mismatched wire ID accepted")
	}
	mux.server = true
	mux.dnsLast = 1
	mux.dnsFrameLocked(dnsFrame(muxDNSQuery, 1, query))
	if len(mux.dns) != 1 {
		test.Fatal("duplicate request allocated state")
	}
}

func TestMuxOpenCloseCancellationStress(test *testing.T) {
	port := muxFixture(test, muxEcho)
	ctx, client, _ := muxPair(test, port, 32, 32)
	for range 10 {
		results := make(chan error, 16)
		for index := 0; index < 16; index++ {
			go func() {
				local, cancel := context.WithCancel(ctx)
				defer cancel()
				stream, err := client.OpenTCP(local, OpenRequest{Host: "127.0.0.1", Port: port})
				if err == nil {
					stream.Reset()
				}
				results <- err
			}()
		}
		for range 16 {
			if err := <-results; err != nil {
				test.Fatal(err)
			}
		}
		deadline := time.Now().Add(time.Second)
		for client.Stats().ActiveStreams != 0 && time.Now().Before(deadline) {
			time.Sleep(time.Millisecond)
		}
	}
}

func TestMuxGlobalBlockedWriterShutdown(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	left, right := pipePair()
	defer right.Close()
	mux := newMux(ctx, left, false, MuxConfig{MaxStreams: 4})
	results := make(chan error, 4)
	for range 4 {
		go func() { _, err := mux.OpenTCP(ctx, OpenRequest{Host: "example.com", Port: 443}); results <- err }()
	}
	deadline := time.Now().Add(time.Second)
	for mux.Stats().ActiveStreams != 4 && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	if mux.Stats().RetainedBytes > 4*(MuxWindow+512) {
		test.Fatal("global bound")
	}
	mux.Close()
	for range 4 {
		if err := <-results; err == nil {
			test.Fatal("unexpected open")
		}
	}
}
