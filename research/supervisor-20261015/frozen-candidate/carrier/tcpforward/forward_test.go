package tcpforward

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"errors"
	"io"
	"net"
	"net/netip"
	"sync"
	"sync/atomic"
	"syscall"
	"testing"
	"time"
)

type packetPipe struct {
	net.Conn
	sendMu sync.Mutex
}

func (point *packetPipe) SendContext(ctx context.Context, data []byte) error {
	point.sendMu.Lock()
	defer point.sendMu.Unlock()
	stop := context.AfterFunc(ctx, func() { point.Close() })
	defer stop()
	header := make([]byte, 4)
	binary.BigEndian.PutUint32(header, uint32(len(data)))
	if _, err := point.Write(header); err != nil {
		return err
	}
	_, err := point.Write(data)
	return err
}
func (point *packetPipe) Recv(ctx context.Context) ([]byte, error) {
	stop := context.AfterFunc(ctx, func() { point.Close() })
	defer stop()
	header := make([]byte, 4)
	if _, err := io.ReadFull(point, header); err != nil {
		return nil, err
	}
	length := binary.BigEndian.Uint32(header)
	if length > 65536 {
		return nil, ErrProtocol
	}
	payload := make([]byte, int(length))
	_, err := io.ReadFull(point, payload)
	return payload, err
}
func pipePair() (*packetPipe, *packetPipe) {
	left, right := net.Pipe()
	return &packetPipe{Conn: left}, &packetPipe{Conn: right}
}

func startFixture(test *testing.T, handle func(*net.TCPConn)) int {
	test.Helper()
	listener, err := net.ListenTCP("tcp4", &net.TCPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		test.Fatal(err)
	}
	done := make(chan struct{})
	var connectionMu sync.Mutex
	var active *net.TCPConn
	go func() {
		defer close(done)
		connection, err := listener.AcceptTCP()
		if err != nil {
			return
		}
		connectionMu.Lock()
		active = connection
		connectionMu.Unlock()
		defer connection.Close()
		connection.SetDeadline(time.Now().Add(10 * time.Second))
		handle(connection)
	}()
	test.Cleanup(func() {
		listener.Close()
		connectionMu.Lock()
		if active != nil {
			active.Close()
		}
		connectionMu.Unlock()
		<-done
	})
	return listener.Addr().(*net.TCPAddr).Port
}

func startGateway(test *testing.T, port int) (*Stream, *Metrics, <-chan error, context.CancelFunc) {
	test.Helper()
	return startGatewayWithDialer(test, port, tcpDial)
}

func startGatewayWithDialer(test *testing.T, port int, dial dialer) (*Stream, *Metrics, <-chan error, context.CancelFunc) {
	test.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	test.Cleanup(cancel)
	client, gateway := pipePair()
	test.Cleanup(func() { client.Close(); gateway.Close() })
	metrics := &Metrics{}
	done := make(chan error, 1)
	go func() {
		done <- serve(ctx, gateway, Policy{TestOnlyLoopbackPort: port}, metrics, net.DefaultResolver, dial)
	}()
	stream, err := openTCP(ctx, client, OpenRequest{Host: "127.0.0.1", Port: port})
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() { stream.Close() })
	return stream, metrics, done, cancel
}

func tcpDial(ctx context.Context, network, address string) (socket, error) {
	connection, err := (&net.Dialer{}).DialContext(ctx, network, address)
	if err != nil {
		return nil, err
	}
	return connection.(*net.TCPConn), nil
}

func startResetFixture(test *testing.T, prefix string) (int, dialer) {
	test.Helper()
	ctx, cancel := context.WithCancel(context.Background())
	connected := make(chan struct{})
	reset := make(chan error, 1)
	port := startFixture(test, func(connection *net.TCPConn) {
		select {
		case <-connected:
		case <-ctx.Done():
			return
		}
		if prefix != "" {
			if _, err := io.WriteString(connection, prefix); err != nil {
				reset <- err
				return
			}
		}
		if err := connection.SetLinger(0); err != nil {
			reset <- err
			return
		}
		reset <- connection.Close()
	})
	test.Cleanup(cancel)
	return port, func(ctx context.Context, network, address string) (socket, error) {
		connection, err := tcpDial(ctx, network, address)
		if err != nil {
			return nil, err
		}
		close(connected)
		select {
		case err := <-reset:
			if err == nil {
				return connection, nil
			}
			connection.Close()
			return nil, err
		case <-ctx.Done():
			connection.Close()
			return nil, ctx.Err()
		}
	}
}

func completed(test *testing.T, done <-chan error, clean bool) {
	test.Helper()
	select {
	case err := <-done:
		if clean && err != nil {
			test.Fatal(err)
		}
	case <-time.After(2 * time.Second):
		test.Fatal("gateway task leak")
	}
}

func TestFullDuplexSegmentationAndHalfClose(test *testing.T) {
	for _, size := range []int{1, 32, 1024, 16384, 65536, 3 << 20} {
		test.Run(stringSize(size), func(test *testing.T) {
			payload := make([]byte, size)
			for index := range payload {
				payload[index] = byte(index*31 + index/251)
			}
			port := startFixture(test, func(connection *net.TCPConn) {
				io.CopyBuffer(connection, connection, make([]byte, 777))
				connection.CloseWrite()
			})
			stream, metrics, done, _ := startGateway(test, port)
			written := make(chan error, 1)
			go func() {
				for offset := 0; offset < len(payload); {
					count := min(1+offset%17003, len(payload)-offset)
					if _, err := stream.Write(payload[offset : offset+count]); err != nil {
						written <- err
						return
					}
					offset += count
				}
				written <- stream.CloseWrite()
			}()
			var received bytes.Buffer
			_, err := io.CopyBuffer(&received, stream, make([]byte, 333))
			if err != nil || !bytes.Equal(received.Bytes(), payload) {
				test.Fatalf("bytes: %d/%d err=%v", received.Len(), size, err)
			}
			if err := <-written; err != nil {
				test.Fatal(err)
			}
			if err := stream.Close(); err != nil {
				test.Fatal(err)
			}
			completed(test, done, true)
			stats := metrics.Snapshot()
			if stats.ToTarget != uint64(size) || stats.FromTarget != uint64(size) || stats.ActiveSockets != 0 || stats.LocalFIN != 1 || stats.RemoteFIN != 1 || stats.RetainedHighWater > ForwarderBufferBound || stats.RetainedBytes != 0 {
				test.Fatalf("stats %+v", stats)
			}
		})
	}
}

func stringSize(size int) string { payload, _ := json.Marshal(size); return string(payload) }

func TestRemoteHalfCloseStillAllowsWrite(test *testing.T) {
	target := make(chan []byte, 1)
	port := startFixture(test, func(connection *net.TCPConn) {
		connection.Write([]byte("response"))
		connection.CloseWrite()
		payload, _ := io.ReadAll(connection)
		target <- payload
	})
	stream, _, done, _ := startGateway(test, port)
	response, err := io.ReadAll(stream)
	if err != nil || string(response) != "response" {
		test.Fatal(string(response), err)
	}
	if _, err := stream.Write([]byte("after EOF")); err != nil {
		test.Fatal(err)
	}
	if err := stream.CloseWrite(); err != nil {
		test.Fatal(err)
	}
	if string(<-target) != "after EOF" {
		test.Fatal("half close lost reverse direction")
	}
	if err := stream.Close(); err != nil {
		test.Fatal(err)
	}
	completed(test, done, true)
}

func TestLocalHalfCloseResponseAfterEOF(test *testing.T) {
	port := startFixture(test, func(connection *net.TCPConn) {
		payload, _ := io.ReadAll(connection)
		connection.Write(append([]byte("afterFIN:"), payload...))
		connection.CloseWrite()
	})
	stream, _, done, _ := startGateway(test, port)
	stream.Write([]byte{0, 255, 1})
	stream.CloseWrite()
	response, err := io.ReadAll(stream)
	if err != nil || !bytes.Equal(response, append([]byte("afterFIN:"), 0, 255, 1)) {
		test.Fatal(response, err)
	}
	stream.Close()
	completed(test, done, true)
}

func TestImmediateCloseResetCancellation(test *testing.T) {
	for _, mode := range []string{"eof", "reset", "cancel", "session_close", "client_reset"} {
		test.Run(mode, func(test *testing.T) {
			var port int
			dial := dialer(tcpDial)
			if mode == "reset" {
				port, dial = startResetFixture(test, "prefix")
			} else {
				port = startFixture(test, func(connection *net.TCPConn) {
					if mode != "eof" {
						io.Copy(io.Discard, connection)
					}
				})
			}
			stream, metrics, done, cancel := startGatewayWithDialer(test, port, dial)
			switch mode {
			case "cancel":
				cancel()
			case "session_close":
				stream.endpoint.Close()
			case "client_reset":
				stream.Reset()
			}
			_, err := io.ReadAll(stream)
			if mode == "eof" {
				if err != nil {
					test.Fatal(err)
				}
				stream.CloseWrite()
				stream.Close()
			} else if mode == "reset" && err != ErrReset {
				test.Fatalf("RST became another terminal result: %v", err)
			} else if err == nil {
				test.Fatal("failure converted to EOF")
			}
			completed(test, done, mode == "eof")
			if metrics.Snapshot().ActiveSockets != 0 {
				test.Fatal("socket leak")
			}
			if stats := metrics.Snapshot(); stats.OpenOK != 1 || stats.OpenErrors != 0 {
				test.Fatal("expected exactly one successful OPEN", stats)
			}
		})
	}
}

type fixedResolver struct {
	addresses []netip.Addr
	err       error
}

func (lookup fixedResolver) LookupNetIP(context.Context, string, string) ([]netip.Addr, error) {
	return lookup.addresses, lookup.err
}

func TestOpenErrorsAndPolicy(test *testing.T) {
	for _, scenario := range []struct {
		name              string
		request           OpenRequest
		ips               []netip.Addr
		dnsErr, errorDial error
		code              string
	}{
		{"port", OpenRequest{Host: "example.com", Port: 65536}, nil, nil, nil, "malformed_request"},
		{"url", OpenRequest{Host: "https://example.com", Port: 443}, nil, nil, nil, "malformed_request"},
		{"private", OpenRequest{Host: "10.0.0.1", Port: 443}, nil, nil, nil, "policy_rejected"},
		{"dns", OpenRequest{Host: "example.com", Port: 443}, nil, errors.New("dns"), nil, "dns_failure"},
		{"mixedDNS", OpenRequest{Host: "example.com", Port: 443}, []netip.Addr{netip.MustParseAddr("93.184.215.14"), netip.MustParseAddr("127.0.0.1")}, nil, nil, "policy_rejected"},
		{"refused", OpenRequest{Host: "93.184.215.14", Port: 443}, nil, nil, syscall.ECONNREFUSED, "connection_refused"},
		{"timeout", OpenRequest{Host: "93.184.215.14", Port: 443}, nil, nil, context.DeadlineExceeded, "timeout"},
		{"unreachable", OpenRequest{Host: "93.184.215.14", Port: 443}, nil, nil, syscall.ENETUNREACH, "unreachable"},
	} {
		test.Run(scenario.name, func(test *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), time.Second)
			defer cancel()
			client, gateway := pipePair()
			defer client.Close()
			done := make(chan error, 1)
			go func() {
				done <- serve(ctx, gateway, Policy{}, &Metrics{}, fixedResolver{scenario.ips, scenario.dnsErr}, func(context.Context, string, string) (socket, error) {
					if scenario.errorDial == nil {
						test.Error("unexpected dial")
					}
					return nil, scenario.errorDial
				})
			}()
			_, err := openTCP(ctx, client, scenario.request)
			var failure *OpenError
			if !errors.As(err, &failure) || failure.Code != scenario.code {
				test.Fatalf("got %v", err)
			}
			completed(test, done, true)
		})
	}
	for _, host := range []string{"127.0.0.1", "::1", "::ffff:127.0.0.1", "169.254.169.254", "100.100.100.200", "192.168.1.2", "fc00::1", "fe80::1", "64:ff9b::a00:1", "2002:7f00:1::1", "224.0.0.1", "0.0.0.0", "2001:db8::1"} {
		if (Policy{}).permits(netip.MustParseAddr(host), 443) {
			test.Fatalf("SSRF permitted %s", host)
		}
	}
}

func TestDNSPinnedAndConnectDeadline(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	started := time.Now()
	_, err := connect(ctx, OpenRequest{Host: "example.com", Port: 443, TimeoutMS: 20}, Policy{}, fixedResolver{addresses: []netip.Addr{netip.MustParseAddr("93.184.215.14")}}, func(ctx context.Context, network, address string) (socket, error) {
		if address != "93.184.215.14:443" {
			test.Error("second DNS lookup")
		}
		<-ctx.Done()
		return nil, ctx.Err()
	})
	var failure *OpenError
	if !errors.As(err, &failure) || failure.Code != "timeout" || time.Since(started) > 300*time.Millisecond {
		test.Fatal(err)
	}
}

type partialWriter struct {
	bytes.Buffer
	zero bool
}

func (writer *partialWriter) Write(payload []byte) (int, error) {
	if writer.zero {
		return 0, nil
	}
	return writer.Buffer.Write(payload[:min(3, len(payload))])
}
func TestPartialTCPWrites(test *testing.T) {
	writer := &partialWriter{}
	metrics := &Metrics{}
	if err := writeTarget(writer, []byte("abcdefghij"), metrics); err != nil || writer.String() != "abcdefghij" || metrics.Snapshot().PartialWrites != 3 {
		test.Fatal(err, metrics.Snapshot())
	}
	if !errors.Is(writeTarget(&partialWriter{zero: true}, []byte{1}, metrics), io.ErrNoProgress) {
		test.Fatal("zero write")
	}
}

func TestBackpressure(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	client, gateway := pipePair()
	defer client.Close()
	defer gateway.Close()
	var sent atomic.Int64
	stream := &Stream{endpoint: client, ctx: ctx, cancel: cancel, stop: func() bool { return true }, metrics: &Metrics{}}
	done := make(chan error, 1)
	go func() { _, err := stream.Write(make([]byte, 4<<20)); sent.Add(1); done <- err }()
	time.Sleep(30 * time.Millisecond)
	if sent.Load() != 0 {
		test.Fatal("unbounded send accepted")
	}
	cancel()
	select {
	case <-done:
	case <-time.After(time.Second):
		test.Fatal("blocked writer leak")
	}
}

func TestMalformedAndLifecycleFrames(test *testing.T) {
	for _, wire := range [][]byte{nil, encode(99, nil), encode(dataFrame, nil), encode(finFrame, []byte{1}), encode(openFrame, make([]byte, 513))} {
		if _, _, err := decode(wire); err == nil {
			test.Fatal("bad frame accepted")
		}
	}
	for _, payload := range []string{`{}`, `{"host":5}`, `{"host":"example.com","port":443,"unknown":true}`} {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		client, gateway := pipePair()
		done := make(chan error, 1)
		go func() { done <- serve(ctx, gateway, Policy{}, &Metrics{}, net.DefaultResolver, tcpDial) }()
		client.SendContext(ctx, encode(openFrame, []byte(payload)))
		kind, body, err := receive(ctx, client)
		var failure OpenError
		if err != nil || kind != openError || decodeJSON(body, &failure) != nil || failure.Code != "malformed_request" {
			test.Fatal(kind, err, string(body))
		}
		client.Close()
		completed(test, done, true)
		cancel()
	}
}

func FuzzFrame(test *testing.F) {
	test.Add(encode(openFrame, []byte(`{"host":"example.com","port":443}`)))
	test.Add(encode(dataFrame, []byte{0, 255, 1}))
	test.Fuzz(func(test *testing.T, wire []byte) {
		kind, payload, err := decode(wire)
		if err == nil && !bytes.Equal(encode(kind, payload), wire) {
			test.Fatal("noncanonical frame")
		}
	})
}

type pipeSocket struct{ net.Conn }

func (connection pipeSocket) CloseWrite() error { return nil }

func TestGatewayBackpressureBothDirections(test *testing.T) {
	for _, reverse := range []bool{false, true} {
		test.Run(stringSize(boolInt(reverse)), func(test *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			defer cancel()
			client, gateway := pipePair()
			defer client.Close()
			socketSide, targetSide := net.Pipe()
			defer targetSide.Close()
			metrics := &Metrics{}
			done := make(chan error, 1)
			go func() {
				done <- serve(ctx, gateway, Policy{}, metrics, net.DefaultResolver, func(context.Context, string, string) (socket, error) { return pipeSocket{socketSide}, nil })
			}()
			stream, err := openTCP(ctx, client, OpenRequest{Host: "93.184.215.14", Port: 443})
			if err != nil {
				test.Fatal(err)
			}
			writeDone := make(chan error, 1)
			go func() {
				var err error
				if reverse {
					_, err = targetSide.Write(make([]byte, 4*MaxData))
				} else {
					_, err = stream.Write(make([]byte, 4*MaxData))
				}
				writeDone <- err
			}()
			time.Sleep(30 * time.Millisecond)
			select {
			case <-writeDone:
				test.Fatal("downstream did not bound producer")
			default:
			}
			stats := metrics.Snapshot()
			if stats.TCPReads > 1 || stats.DataReceived > 1 || stats.RetainedHighWater > ForwarderBufferBound {
				test.Fatal(stats)
			}
			cancel()
			completed(test, done, false)
			<-writeDone
			stream.Close()
		})
	}
}

func TestActualRefusedAndPrematureClose(test *testing.T) {
	listener, err := net.Listen("tcp4", "127.0.0.1:0")
	if err != nil {
		test.Fatal(err)
	}
	port := listener.Addr().(*net.TCPAddr).Port
	listener.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	_, err = connect(ctx, OpenRequest{Host: "127.0.0.1", Port: port}, Policy{TestOnlyLoopbackPort: port}, net.DefaultResolver, tcpDial)
	var failure *OpenError
	if !errors.As(err, &failure) || failure.Code != "connection_refused" {
		test.Fatal(err)
	}
	port = startFixture(test, func(connection *net.TCPConn) { io.Copy(io.Discard, connection); time.Sleep(100 * time.Millisecond) })
	stream, _, done, _ := startGateway(test, port)
	stream.CloseWrite()
	stream.endpoint.SendContext(ctx, encode(closeFrame, nil))
	select {
	case err := <-done:
		if !errors.Is(err, ErrProtocol) {
			test.Fatal(err)
		}
	case <-time.After(time.Second):
		test.Fatal("premature CLOSE hung")
	}
}
