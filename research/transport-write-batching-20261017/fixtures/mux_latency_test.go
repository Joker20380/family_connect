package tcpforward

import (
	"bytes"
	"context"
	"fmt"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

type timedMuxPacket struct {
	payload []byte
	ready   time.Time
}

type timedMuxEndpoint struct {
	familysession.PacketEndpoint
	ctx   context.Context
	queue chan timedMuxPacket
}

func timedMuxLink(ctx context.Context, endpoint familysession.PacketEndpoint) *timedMuxEndpoint {
	link := &timedMuxEndpoint{PacketEndpoint: endpoint, ctx: ctx, queue: make(chan timedMuxPacket, 64)}
	go func() {
		for {
			select {
			case packet := <-link.queue:
				timer := time.NewTimer(time.Until(packet.ready))
				select {
				case <-timer.C:
				case <-ctx.Done():
					timer.Stop()
					return
				}
				if endpoint.SendContext(ctx, packet.payload) != nil {
					return
				}
			case <-ctx.Done():
				return
			}
		}
	}()
	return link
}

func (link *timedMuxEndpoint) SendContext(ctx context.Context, payload []byte) error {
	select {
	case link.queue <- timedMuxPacket{bytes.Clone(payload), time.Now().Add(40 * time.Millisecond)}:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	case <-link.ctx.Done():
		return link.ctx.Err()
	}
}

func TestMuxLatencyEnvelope(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	clientProfile, serverProfile := testCredentials(test)
	left, right := pipePair()
	type result struct {
		session *familysession.Session
		err     error
	}
	ready := make(chan result, 1)
	go func() {
		session, err := familysession.Open(ctx, timedMuxLink(ctx, right), serverProfile, true)
		ready <- result{session, err}
	}()
	clientSession, err := familysession.Open(ctx, timedMuxLink(ctx, left), clientProfile, false)
	if err != nil {
		test.Fatal(err)
	}
	defer clientSession.Close()
	opened := <-ready
	if opened.err != nil {
		test.Fatal(opened.err)
	}
	defer opened.session.Close()
	port := muxFixture(test, muxEcho)
	client, err := NewMux(ctx, clientSession, false, MuxConfig{MaxStreams: 64, WaitForSlot: true})
	if err != nil {
		test.Fatal(err)
	}
	server, err := NewMux(ctx, opened.session, true, MuxConfig{MaxStreams: 64, Policy: Policy{TestOnlyLoopbackPort: port}})
	if err != nil {
		test.Fatal(err)
	}
	defer client.Close()
	defer server.Close()
	streams := make([]*MuxStream, 4)
	for index := range streams {
		streams[index] = muxOpen(test, ctx, client, port)
	}
	beforeClient, beforeServer := clientSession.ReliabilityStats(), opened.session.ReliabilityStats()
	start := time.Now()
	done := make(chan error, len(streams))
	for index, stream := range streams {
		payload := bytes.Repeat([]byte{byte(index)}, 64<<10)
		go func() { done <- exactMux(stream, payload) }()
	}
	for range streams {
		if err := <-done; err != nil {
			test.Fatal(err)
		}
	}
	afterClient, afterServer := clientSession.ReliabilityStats(), opened.session.ReliabilityStats()
	test.Logf("flows=4 body_each=65536 byte_exact=true synthetic_one_way_ms=40 elapsed_ms=%d client_frames=%d server_frames=%d retransmits=%d", time.Since(start).Milliseconds(), afterClient.DataSent-beforeClient.DataSent, afterServer.DataSent-beforeServer.DataSent, afterClient.Retransmissions-beforeClient.Retransmissions+afterServer.Retransmissions-beforeServer.Retransmissions)
	if client.Stats().ProtocolErrors != 0 || server.Stats().ProtocolErrors != 0 {
		test.Fatal("unexpected protocol error")
	}
}

func TestBrowserSlotsReleaseEnvelope(test *testing.T) {
	port := muxFixture(test, muxEcho)
	ctx, client, server := muxPair(test, port, 64, 64)
	client.config.WaitForSlot = true
	streams := make([]*MuxStream, 64)
	for index := range streams {
		streams[index] = muxOpen(test, ctx, client, port)
	}
	type result struct {
		stream *MuxStream
		err    error
	}
	ready := make(chan result, 1)
	go func() {
		stream, err := client.OpenTCP(ctx, OpenRequest{Host: "127.0.0.1", Port: port})
		ready <- result{stream, err}
	}()
	awaitAdmission(test, client, 1)
	select {
	case <-ready:
		test.Fatal("idle connections evicted or limit bypassed")
	case <-time.After(50 * time.Millisecond):
	}
	start := time.Now()
	if err := exactMux(streams[0], []byte("normal half-close releases a slot")); err != nil {
		test.Fatal(err)
	}
	var admitted result
	select {
	case admitted = <-ready:
	case <-time.After(2 * time.Second):
		test.Fatal("slot not released")
	}
	if admitted.err != nil {
		test.Fatal(admitted.err)
	}
	test.Logf("held=64 waiter=1 release_ms=%d", time.Since(start).Milliseconds())
	if err := exactMux(admitted.stream, []byte("admitted without bypass")); err != nil {
		test.Fatal(err)
	}
	for index, stream := range streams[1:] {
		if index%2 == 0 {
			stream.Reset()
		} else if err := exactMux(stream, []byte(fmt.Sprint(index))); err != nil {
			test.Fatal(err)
		}
	}
	deadline := time.Now().Add(2 * time.Second)
	for time.Now().Before(deadline) {
		if client.Stats().ActiveStreams == 0 && server.Stats().ActiveStreams == 0 && server.Stats().ActiveSockets == 0 {
			return
		}
		time.Sleep(time.Millisecond)
	}
	test.Fatal("retained slots/sockets", client.Stats(), server.Stats())
}
