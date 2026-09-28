package tcpforward

import (
	"bytes"
	"context"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"net"
	"sync"
	"testing"
	"time"

	"golang.org/x/net/dns/dnsmessage"
)

func muxFixture(test *testing.T, handle func(*net.TCPConn)) int {
	test.Helper()
	listener, err := net.ListenTCP("tcp4", &net.TCPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		test.Fatal(err)
	}
	var workers sync.WaitGroup
	var lock sync.Mutex
	connections := make(map[*net.TCPConn]bool)
	done := make(chan struct{})
	go func() {
		defer close(done)
		for {
			connection, err := listener.AcceptTCP()
			if err != nil {
				return
			}
			lock.Lock()
			connections[connection] = true
			lock.Unlock()
			workers.Add(1)
			go func() {
				defer workers.Done()
				defer connection.Close()
				defer func() { lock.Lock(); delete(connections, connection); lock.Unlock() }()
				connection.SetDeadline(time.Now().Add(15 * time.Second))
				handle(connection)
			}()
		}
	}()
	test.Cleanup(func() {
		listener.Close()
		<-done
		lock.Lock()
		for connection := range connections {
			connection.Close()
		}
		lock.Unlock()
		workers.Wait()
	})
	return listener.Addr().(*net.TCPAddr).Port
}

func muxEcho(connection *net.TCPConn) {
	buffer := make([]byte, 777)
	for {
		count, err := connection.Read(buffer)
		if count > 0 && writeTarget(connection, buffer[:count], &Metrics{}) != nil {
			return
		}
		if err != nil {
			connection.CloseWrite()
			return
		}
	}
}

func muxPair(test *testing.T, port, clientLimit, serverLimit int) (context.Context, *Mux, *Mux) {
	test.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	left, right := pipePair()
	client := newMux(ctx, left, false, MuxConfig{MaxStreams: clientLimit})
	server := newMux(ctx, right, true, MuxConfig{MaxStreams: serverLimit, Policy: Policy{TestOnlyLoopbackPort: port}})
	test.Cleanup(func() {
		cancel()
		client.Close()
		server.Close()
		if client.Stats().RetainedBytes != 0 || server.Stats().RetainedBytes != 0 {
			test.Error("retained buffers after shutdown")
		}
	})
	return ctx, client, server
}

func muxOpen(test *testing.T, ctx context.Context, mux *Mux, port int) *MuxStream {
	test.Helper()
	stream, err := mux.OpenTCP(ctx, OpenRequest{Host: "127.0.0.1", Port: port})
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() { stream.Close() })
	return stream
}

func exactMux(stream *MuxStream, payload []byte) error {
	written := make(chan error, 1)
	go func() {
		for offset := 0; offset < len(payload); {
			count := min(997, len(payload)-offset)
			if _, err := stream.Write(payload[offset : offset+count]); err != nil {
				written <- err
				return
			}
			offset += count
		}
		written <- stream.CloseWrite()
	}()
	actual, err := io.ReadAll(stream)
	if err != nil {
		stream.Reset()
		<-written
		return err
	}
	if err := <-written; err != nil {
		return err
	}
	if !bytes.Equal(actual, payload) {
		return errors.New("cross-stream, missing or duplicate bytes")
	}
	return stream.Close()
}

func TestMuxConcurrentExactSegmentation(test *testing.T) {
	for _, count := range []int{1, 4, 8, 16, 32} {
		test.Run(fmt.Sprint(count), func(test *testing.T) {
			port := muxFixture(test, muxEcho)
			ctx, client, server := muxPair(test, port, 32, 32)
			streams := make([]*MuxStream, count)
			for index := range streams {
				streams[index] = muxOpen(test, ctx, client, port)
			}
			results := make(chan error, count)
			for index, stream := range streams {
				payload := bytes.Repeat([]byte(fmt.Sprintf("stream-%03d:", index)), 30000+index)
				go func() { results <- exactMux(stream, payload) }()
			}
			for range streams {
				if err := <-results; err != nil {
					test.Fatal(err)
				}
			}
			if server.Stats().MaxActiveStreams != count {
				test.Fatal(server.Stats())
			}
			if client.Stats().ReceiveHighWater > MuxWindow || server.Stats().ReceiveHighWater > MuxWindow || client.Stats().SendHighWater > MaxData {
				test.Fatal("buffer bound")
			}
		})
	}
}

func TestMuxLimitAndIndependentReset(test *testing.T) {
	port := muxFixture(test, muxEcho)
	ctx, client, server := muxPair(test, port, 8, 4)
	streams := make([]*MuxStream, 4)
	for index := range streams {
		streams[index] = muxOpen(test, ctx, client, port)
	}
	_, err := client.OpenTCP(ctx, OpenRequest{Host: "127.0.0.1", Port: port})
	var failure *OpenError
	if !errors.As(err, &failure) || failure.Code != "stream_limit" {
		test.Fatal(err)
	}
	streams[2].Reset()
	for index, stream := range streams {
		if index != 2 {
			if err := exactMux(stream, bytes.Repeat([]byte{byte(index)}, 4097)); err != nil {
				test.Fatal(err)
			}
		}
	}
	if server.ctx.Err() != nil {
		test.Fatal("stream reset killed session")
	}
}

func TestMuxSlowConsumerAndInteractive(test *testing.T) {
	port := muxFixture(test, muxEcho)
	ctx, client, _ := muxPair(test, port, 4, 4)
	slow := muxOpen(test, ctx, client, port)
	written := make(chan error, 1)
	go func() { _, err := slow.Write(bytes.Repeat([]byte("bulk"), 1<<20)); written <- err }()
	deadline := time.Now().Add(3 * time.Second)
	for slow.Stats().ReceiveBuffered < MuxWindow && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	if slow.Stats().ReceiveBuffered != MuxWindow {
		test.Fatal("slow buffer did not reach its fixed credit bound")
	}
	select {
	case <-written:
		test.Fatal("producer outran slow consumer")
	default:
	}
	started := time.Now()
	interactive := muxOpen(test, ctx, client, port)
	if err := exactMux(interactive, []byte("interactive-specific-identity")); err != nil {
		test.Fatal(err)
	}
	if time.Since(started) > time.Second {
		test.Fatal("interactive starvation")
	}
	slow.Reset()
	if err := <-written; err == nil {
		test.Fatal("blocked writer did not fail")
	}
}

func TestMuxHalfCloseAndOpenErrors(test *testing.T) {
	port := muxFixture(test, func(connection *net.TCPConn) { connection.CloseWrite(); io.Copy(io.Discard, connection) })
	ctx, client, _ := muxPair(test, port, 4, 4)
	stream := muxOpen(test, ctx, client, port)
	if _, err := stream.Read(make([]byte, 1)); err != io.EOF {
		test.Fatal(err)
	}
	if _, err := stream.Write([]byte("after remote FIN")); err != nil {
		test.Fatal(err)
	}
	if err := stream.CloseWrite(); err != nil {
		test.Fatal(err)
	}
	if err := stream.Close(); err != nil {
		test.Fatal(err)
	}
	_, err := client.OpenTCP(ctx, OpenRequest{Host: "169.254.169.254", Port: 80})
	var failure *OpenError
	if !errors.As(err, &failure) || failure.Code != "policy_rejected" {
		test.Fatal(err)
	}
	survivor := muxOpen(test, ctx, client, port)
	survivor.Close()
}

func TestMuxSessionCancellationManyStreams(test *testing.T) {
	port := muxFixture(test, muxEcho)
	ctx, client, server := muxPair(test, port, 32, 32)
	waiters := make(chan error, 16)
	for range 16 {
		stream := muxOpen(test, ctx, client, port)
		go func() { _, err := stream.Read(make([]byte, 100)); waiters <- err }()
	}
	client.Close()
	for range 16 {
		if err := <-waiters; err == nil || err == io.EOF {
			test.Fatal(err)
		}
	}
	server.Close()
	if len(server.jobs) != 0 || len(server.dnsJobs) != 0 {
		test.Fatal("worker leak")
	}
}

func TestMuxSchedulerRoundRobinAndPriority(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	mux := &Mux{ctx: ctx, streams: make(map[uint32]*MuxStream), changed: make(chan struct{})}
	for _, id := range []uint32{1, 3, 5} {
		stream := mux.makeStreamLocked(id)
		stream.send = []muxFrame{{dataFrame, id, []byte{byte(id)}}}
	}
	for index := 0; index < 24; index++ {
		mux.control = append(mux.control, muxFrame{resetFrame, 99, nil})
	}
	var dataIDs []uint32
	for index := 0; index < 27; index++ {
		frame, ok := mux.nextLocked()
		if !ok {
			test.Fatal("missing queued frame")
		}
		if frame.kind == dataFrame {
			dataIDs = append(dataIDs, frame.id)
			if index > 8+9*(len(dataIDs)-1) {
				test.Fatal("starvation")
			}
		}
	}
	if fmt.Sprint(dataIDs) != "[1 3 5]" {
		test.Fatal(dataIDs)
	}
}

func dnsQuestion(test *testing.T, kind dnsmessage.Type) []byte {
	test.Helper()
	name, _ := dnsmessage.NewName("example.com.")
	query, err := (&dnsmessage.Message{Header: dnsmessage.Header{ID: 42, RecursionDesired: true}, Questions: []dnsmessage.Question{{Name: name, Type: kind, Class: dnsmessage.ClassINET}}}).Pack()
	if err != nil {
		test.Fatal(err)
	}
	return query
}

func dnsAnswer(ctx context.Context, query []byte) ([]byte, error) {
	var message dnsmessage.Message
	if err := message.Unpack(query); err != nil {
		return nil, err
	}
	message.Header.Response = true
	message.Header.RCode = dnsmessage.RCodeNameError
	return message.Pack()
}

func TestMuxDNSConcurrentBulkAndMatching(test *testing.T) {
	port := muxFixture(test, muxEcho)
	ctx, client, server := muxPair(test, port, 16, 16)
	server.exchange = dnsAnswer
	bulk := muxOpen(test, ctx, client, port)
	results := make(chan error, 17)
	go func() { results <- exactMux(bulk, bytes.Repeat([]byte("bulk identity"), 100000)) }()
	for index := 0; index < 16; index++ {
		kind := dnsmessage.TypeA
		if index%2 != 0 {
			kind = dnsmessage.TypeAAAA
		}
		query := dnsQuestion(test, kind)
		go func() {
			response, err := client.QueryDNS(ctx, query)
			if err == nil && !matchesDNS(query, response) {
				err = ErrDNS
			}
			results <- err
		}()
	}
	for range 17 {
		if err := <-results; err != nil {
			test.Fatal(err)
		}
	}
	if client.Stats().DNSResponses != 16 || server.Stats().DNSRequests != 16 {
		test.Fatal(client.Stats(), server.Stats())
	}
	if _, err := client.QueryDNS(ctx, []byte{1, 2, 3}); err == nil {
		test.Fatal("malformed DNS accepted")
	}
}

func TestMuxDNSCancellationAndShutdown(test *testing.T) {
	ctx, client, server := muxPair(test, 0, 4, 4)
	server.exchange = func(ctx context.Context, query []byte) ([]byte, error) { <-ctx.Done(); return nil, ctx.Err() }
	query := dnsQuestion(test, dnsmessage.TypeA)
	short, cancel := context.WithTimeout(ctx, 20*time.Millisecond)
	defer cancel()
	if _, err := client.QueryDNS(short, query); err != context.DeadlineExceeded {
		test.Fatal(err)
	}
	results := make(chan error, 8)
	for range 8 {
		go func() { _, err := client.QueryDNS(ctx, query); results <- err }()
	}
	client.Close()
	server.Close()
	for range 8 {
		if err := <-results; err == nil {
			test.Fatal("DNS waiter succeeded after shutdown")
		}
	}
}

func TestMuxMalformedStateIsolation(test *testing.T) {
	for _, kind := range []byte{dataFrame, finFrame, openFrame, closeFrame, muxWindowUpdate} {
		test.Run(fmt.Sprint(kind), func(test *testing.T) {
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			mux := &Mux{ctx: ctx, streams: make(map[uint32]*MuxStream), changed: make(chan struct{})}
			stream := mux.makeStreamLocked(1)
			survivor := mux.makeStreamLocked(3)
			payload := []byte{0, 0, 0, 1}
			mux.dispatchLocked(muxFrame{kind, 1, payload})
			if stream.terminal != ErrProtocol || survivor.terminal != nil {
				test.Fatal("transition leaked")
			}
			mux.dispatchLocked(muxFrame{resetFrame, 999, nil})
			if len(mux.streams) > 2 {
				test.Fatal("unknown ID allocation")
			}
		})
	}
}

func FuzzMuxFrame(test *testing.F) {
	test.Add(muxFrame{dataFrame, 1, []byte("data")}.encode())
	test.Add(dnsFrame(muxDNSQuery, 1, make([]byte, 12)).encode())
	test.Fuzz(func(test *testing.T, encoded []byte) {
		frame, err := decodeMux(encoded)
		if err == nil && !bytes.Equal(frame.encode(), encoded) {
			test.Fatal("noncanonical frame")
		}
	})
}

func FuzzMuxCreditAndState(test *testing.F) {
	test.Add([]byte{4, 5, 6, 8, 255})
	test.Fuzz(func(test *testing.T, operations []byte) {
		ctx, cancel := context.WithCancel(context.Background())
		defer cancel()
		mux := &Mux{ctx: ctx, streams: make(map[uint32]*MuxStream), changed: make(chan struct{})}
		stream := mux.makeStreamLocked(1)
		stream.opened = true
		for _, kind := range operations[:min(len(operations), 128)] {
			payload := []byte{0, 0, 0, 1}
			if kind == muxWindowUpdate {
				binary.BigEndian.PutUint32(payload, uint32(kind)*100000000)
			}
			mux.dispatchLocked(muxFrame{kind, 1, payload})
			if stream.used > MuxWindow || stream.sendCredit > MuxWindow || stream.receiveCredit < 0 {
				test.Fatal("credit bound")
			}
		}
	})
}

func FuzzMuxDNS(test *testing.F) {
	test.Add(make([]byte, 12))
	test.Fuzz(func(test *testing.T, payload []byte) {
		_, _ = validDNS(payload, false)
		_ = matchesDNS(payload, payload)
	})
}

func TestMuxPartialSocketWriter(test *testing.T) {
	target := &partialWriter{}
	writer := &muxTargetWriter{target: target}
	payload := []byte("mux-stream-specific-partial-writes")
	count, err := writer.Write(payload)
	if err != nil || count != len(payload) || !bytes.Equal(target.Bytes(), payload) {
		test.Fatal(count, err)
	}
	writer = &muxTargetWriter{target: &partialWriter{zero: true}}
	if _, err := writer.Write(payload); err != io.ErrNoProgress {
		test.Fatal(err)
	}
}
