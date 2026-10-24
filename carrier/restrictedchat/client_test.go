package restrictedchat

import (
	"bytes"
	"context"
	"crypto/tls"
	"crypto/x509"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/restrictedowner"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

type testStream struct {
	net.Conn
	stop func() bool
}

func (stream *testStream) Close() error { stream.stop(); return stream.Conn.Close() }
func (stream *testStream) Reset() error { return stream.Close() }
func (stream *testStream) CloseWrite() error {
	if connection, ok := stream.Conn.(interface{ CloseWrite() error }); ok {
		return connection.CloseWrite()
	}
	return nil
}

type testPlane struct {
	dial  func(context.Context) (net.Conn, error)
	done  chan struct{}
	once  sync.Once
	calls atomic.Int64
	name  atomic.Value
}

func (plane *testPlane) Open(ctx context.Context, host string, port uint16) (wholedevice.Stream, error) {
	if (host != "chat-mailbox.family-connect.invalid" && host != "chat-api.family-connect.invalid") || port != 1 {
		return nil, ErrDenied
	}
	plane.calls.Add(1)
	plane.name.Store(host)
	connection, err := plane.dial(ctx)
	if err != nil {
		return nil, err
	}
	return &testStream{Conn: connection, stop: context.AfterFunc(ctx, func() { connection.Close() })}, nil
}

func (plane *testPlane) QueryDNS(context.Context, []byte) ([]byte, error) { return nil, ErrDenied }
func (plane *testPlane) Close() error                                     { plane.once.Do(func() { close(plane.done) }); return nil }
func (plane *testPlane) Wait() error                                      { <-plane.done; return io.EOF }

func fixture(test *testing.T, borrowed bool, dial func(context.Context) (net.Conn, error)) (*Client, *wholedevice.Session, *testPlane) {
	test.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	plane := &testPlane{dial: dial, done: make(chan struct{})}
	session := wholedevice.Attach(ctx, plane, nil)
	var coordinator restrictedowner.Coordinator
	profile := [32]byte{1}
	var vpn *restrictedowner.VPN
	var err error
	if borrowed {
		vpn, err = coordinator.ReserveVPN(ctx)
		if err != nil {
			test.Fatal(err)
		}
		if err = vpn.Publish(session, profile); err != nil {
			test.Fatal(err)
		}
	}
	lease, err := coordinator.AcquireChat(time.Now().Add(time.Minute), profile,
		func(context.Context) (restrictedowner.Session, func(), error) {
			if borrowed {
				test.Error("borrowed chat opened another media session")
			}
			return session, nil, nil
		}, func() {})
	if err != nil {
		test.Fatal(err)
	}
	client, err := New(lease)
	if err != nil {
		test.Fatal(err)
	}
	if _, err = lease.Session(ctx); err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() {
		client.Close()
		if vpn != nil {
			vpn.Release()
		}
		session.Close()
		cancel()
	})
	return client, session, plane
}

func pipeDial(ctx context.Context) (net.Conn, error) {
	client, peer := net.Pipe()
	go func() {
		defer peer.Close()
		stop := context.AfterFunc(ctx, func() { peer.Close() })
		defer stop()
		io.Copy(peer, peer)
	}()
	return client, nil
}

func trustServer(client *Client, server *httptest.Server) {
	roots := x509.NewCertPool()
	roots.AddCert(server.Certificate())
	client.tls = &tls.Config{MinVersion: tls.VersionTLS12, RootCAs: roots, ServerName: "example.com"}
}

func tlsDial(server *httptest.Server) func(context.Context) (net.Conn, error) {
	return func(ctx context.Context) (net.Conn, error) {
		return (&net.Dialer{}).DialContext(ctx, "tcp", server.Listener.Addr().String())
	}
}

func TestAPIExactBoundsNoArbitraryServiceOrNetwork(test *testing.T) {
	client, _, plane := fixture(test, true, pipeDial)
	if invalid, err := New(nil); err != ErrDenied || invalid != nil {
		test.Fatal("accepted missing owner")
	}
	for _, path := range []string{"", "https://example.com", "/friends/chat/register?extra=1", "/friends/device/diagnostics", "/friends/chat/challenge/", "/friends/chat/../configuration/nl"} {
		if _, err := client.Request(context.Background(), path, []byte("{}"), time.Second); err != ErrDenied {
			test.Fatal("untrusted path accepted", path, err)
		}
	}
	if _, err := client.Request(context.Background(), "/friends/chat/register", bytes.Repeat([]byte{'x'}, MaxRequest+1), time.Second); err != ErrDenied {
		test.Fatal("oversized request accepted", err)
	}
	for _, duration := range []time.Duration{0, -time.Second, MaxDuration + time.Nanosecond} {
		if connection, err := client.OpenMailbox(context.Background(), duration); err != ErrDenied || connection != nil {
			test.Fatal("invalid duration accepted", err)
		}
	}
	if connection, err := client.OpenMailbox(nil, time.Second); err != ErrDenied || connection != nil {
		test.Fatal("nil context accepted")
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if connection, err := client.OpenMailbox(ctx, time.Second); err != context.Canceled || connection != nil {
		test.Fatal("cancel opened mailbox", err)
	}
	if plane.calls.Load() != 0 {
		test.Fatal("validation touched network")
	}
}

func TestHTTPStatusRedirectAndProofBytesPreserved(test *testing.T) {
	test.Setenv("HTTPS_PROXY", "http://127.0.0.1:1")
	for _, status := range []int{200, 400, 401, 403, 409, 302, 500} {
		test.Run(fmt.Sprint(status), func(test *testing.T) {
			body := bytes.Repeat([]byte{'x'}, MaxRequest)
			var received atomic.Int64
			server := httptest.NewTLSServer(http.HandlerFunc(func(response http.ResponseWriter, request *http.Request) {
				raw, err := io.ReadAll(request.Body)
				if err != nil || !bytes.Equal(raw, body) || request.Method != "POST" || request.URL.Path != "/friends/chat/register" || request.Host != "185.251.89.19:8443" || request.Header.Get("Content-Type") != "application/json" {
					test.Error("request contract changed")
				}
				received.Add(1)
				response.Header().Set("Location", "https://other.invalid/not-allowed")
				response.WriteHeader(status)
				io.WriteString(response, `{"result":"synthetic-challenge"}`)
			}))
			defer server.Close()
			client, _, plane := fixture(test, true, tlsDial(server))
			trustServer(client, server)
			reply, err := client.Request(context.Background(), "/friends/chat/register", body, 3*time.Second)
			var expected error
			if status == 400 || status == 401 || status == 403 {
				expected = ErrDenied
			}
			if status == 409 {
				expected = ErrConflict
			}
			if err != expected || reply.Status != status || received.Load() != 1 || plane.calls.Load() != 1 {
				test.Fatal("bounded single service request failed", reply.Status, err, received.Load(), plane.calls.Load())
			}
			if expected == nil && string(reply.Body) != `{"result":"synthetic-challenge"}` {
				test.Fatal("response changed")
			}
			if expected != nil && len(reply.Body) != 0 {
				test.Fatal("rejected response retained body")
			}
			if plane.name.Load() != "chat-api.family-connect.invalid" {
				test.Fatal("wrong virtual service")
			}
			if strings.Contains(fmt.Sprintf("%v %+v %#v %s", reply, reply, reply, reply), "synthetic-challenge") {
				test.Fatal("reply exposed challenge in diagnostics")
			}
		})
	}
}

func TestTLSRejectionIsDeniedWithoutFallback(test *testing.T) {
	server := httptest.NewTLSServer(http.HandlerFunc(func(http.ResponseWriter, *http.Request) { test.Error("untrusted TLS reached API") }))
	defer server.Close()
	client, session, plane := fixture(test, true, tlsDial(server))
	if _, err := client.Request(context.Background(), "/friends/chat/challenge", []byte("{}"), 3*time.Second); err != ErrDenied {
		test.Fatal("TLS denial reclassified as retryable failure", err)
	}
	if plane.calls.Load() != 1 || session.Failed() {
		test.Fatal("trust failure retried or closed VPN")
	}
}

func TestAuthorizationStatusDoesNotWaitForErrorBody(test *testing.T) {
	server := httptest.NewTLSServer(http.HandlerFunc(func(response http.ResponseWriter, request *http.Request) {
		response.Header().Set("Content-Length", "1048576")
		response.WriteHeader(http.StatusForbidden)
		response.(http.Flusher).Flush()
		<-request.Context().Done()
	}))
	defer server.Close()
	client, _, plane := fixture(test, true, tlsDial(server))
	trustServer(client, server)
	reply, err := client.Request(context.Background(), "/friends/chat/challenge", nil, time.Second)
	if err != ErrDenied || reply.Status != 403 || len(reply.Body) != 0 || plane.calls.Load() != 1 {
		test.Fatal("authorization failure weakened by pending body", err)
	}
}

func TestResponseAndHeaderMemoryBounds(test *testing.T) {
	for _, size := range []int{MaxResponse, MaxResponse + 1} {
		test.Run(fmt.Sprint(size), func(test *testing.T) {
			server := httptest.NewTLSServer(http.HandlerFunc(func(response http.ResponseWriter, request *http.Request) {
				response.Write(bytes.Repeat([]byte{'x'}, size))
			}))
			defer server.Close()
			client, _, _ := fixture(test, true, tlsDial(server))
			trustServer(client, server)
			reply, err := client.Request(context.Background(), "/friends/chat/challenge", nil, 3*time.Second)
			if size == MaxResponse && (err != nil || len(reply.Body) != size) {
				test.Fatal("maximum response rejected", err)
			}
			if size > MaxResponse && (err != ErrUnavailable || len(reply.Body) != 0) {
				test.Fatal("truncated response accepted", err)
			}
		})
	}
	server := httptest.NewTLSServer(http.HandlerFunc(func(response http.ResponseWriter, request *http.Request) {
		response.Header().Set("Oversized", strings.Repeat("x", MaxResponse+1))
		response.WriteHeader(200)
	}))
	defer server.Close()
	client, _, _ := fixture(test, true, tlsDial(server))
	trustServer(client, server)
	if reply, err := client.Request(context.Background(), "/friends/chat/challenge", nil, 3*time.Second); err != ErrUnavailable || len(reply.Body) != 0 {
		test.Fatal("unbounded headers accepted", err)
	}
}

func TestByteExactMailboxQuotaAndBorrowedLifetime(test *testing.T) {
	client, session, plane := fixture(test, true, pipeDial)
	if client.Route() != "EXISTING_EXIT" {
		test.Fatal("wrong actual route")
	}
	connections := []net.Conn{}
	for index := 0; index < 4; index++ {
		connection, err := client.OpenMailbox(context.Background(), 3*time.Second)
		if err != nil {
			test.Fatal(err)
		}
		connections = append(connections, connection)
	}
	if connection, err := client.OpenMailbox(context.Background(), time.Second); err != ErrUnavailable || connection != nil {
		test.Fatal("service quota bypassed", err)
	}
	if plane.name.Load() != "chat-mailbox.family-connect.invalid" || plane.calls.Load() != 4 {
		test.Fatal("wrong mailbox path")
	}
	data := bytes.Repeat([]byte{0, 255, 127, 128}, 2048)
	if _, err := connections[0].Write(data); err != nil {
		test.Fatal(err)
	}
	actual := make([]byte, len(data))
	if _, err := io.ReadFull(connections[0], actual); err != nil || !bytes.Equal(data, actual) {
		test.Fatal("mailbox changed bytes", err)
	}
	connections[0].Close()
	replacement, err := client.OpenMailbox(context.Background(), time.Second)
	if err != nil {
		test.Fatal("released slot not reusable", err)
	}
	replacement.Close()
	client.Close()
	client.Close()
	if session.Failed() || client.Route() != "UNAVAILABLE" {
		test.Fatal("chat close killed borrowed VPN")
	}
	for _, connection := range connections {
		connection.Close()
	}
	if connection, err := client.OpenMailbox(context.Background(), time.Second); connection != nil || err == nil {
		test.Fatal("closed lease reused")
	}
}

func TestServiceOnlyCloseDrainsItsSession(test *testing.T) {
	client, session, plane := fixture(test, false, pipeDial)
	if client.Route() != "SERVICE_ONLY" {
		test.Fatal("service-only mislabeled")
	}
	connection, err := client.OpenMailbox(context.Background(), time.Second)
	if err != nil {
		test.Fatal(err)
	}
	client.Close()
	select {
	case <-plane.done:
	case <-time.After(2 * time.Second):
		test.Fatal("service-only owner leaked")
	}
	if !session.Failed() {
		test.Fatal("service-only session survived final release")
	}
	connection.Close()
}

func TestReadDeadlineCancelAndBudgetRemainDistinct(test *testing.T) {
	for _, mode := range []string{"cancel", "budget", "read-deadline", "write-deadline"} {
		test.Run(mode, func(test *testing.T) {
			client, session, _ := fixture(test, true, func(ctx context.Context) (net.Conn, error) {
				connection, peer := net.Pipe()
				context.AfterFunc(ctx, func() { peer.Close() })
				return connection, nil
			})
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			duration := time.Second
			if mode == "budget" {
				duration = 50 * time.Millisecond
			}
			connection, err := client.OpenMailbox(ctx, duration)
			if err != nil {
				test.Fatal(err)
			}
			defer connection.Close()
			expected := error(context.DeadlineExceeded)
			if mode == "cancel" {
				cancel()
				expected = context.Canceled
			}
			if mode == "read-deadline" {
				connection.SetReadDeadline(time.Now().Add(50 * time.Millisecond))
				expected = os.ErrDeadlineExceeded
			}
			if mode == "write-deadline" {
				connection.SetWriteDeadline(time.Now().Add(50 * time.Millisecond))
				expected = os.ErrDeadlineExceeded
			}
			if mode == "write-deadline" {
				_, err = connection.Write([]byte{1})
			} else {
				_, err = connection.Read(make([]byte, 1))
			}
			if !errors.Is(err, expected) {
				test.Fatal("cancel/timeout changed meaning", mode, err)
			}
			if session.Failed() {
				test.Fatal("operation cancellation killed VPN")
			}
		})
	}
}

func TestConcurrentDeadlineResetAndClose(test *testing.T) {
	client, _, _ := fixture(test, true, pipeDial)
	connection, err := client.OpenMailbox(context.Background(), 2*time.Second)
	if err != nil {
		test.Fatal(err)
	}
	var workers sync.WaitGroup
	for index := 0; index < 12; index++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			for attempt := 0; attempt < 30; attempt++ {
				connection.SetReadDeadline(time.Now().Add(time.Second))
				connection.SetWriteDeadline(time.Now().Add(time.Second))
				connection.SetDeadline(time.Time{})
			}
			connection.Close()
		}()
	}
	workers.Wait()
	if err := connection.SetDeadline(time.Now()); err != net.ErrClosed {
		test.Fatal("closed stream accepted deadline", err)
	}
}
