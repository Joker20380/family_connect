package tcpforward_test

import (
	"bufio"
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"strconv"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/tcpforward"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
	"golang.org/x/net/dns/dnsmessage"
)

type browserPlane struct{ *tcpforward.Mux }

func (plane browserPlane) Open(ctx context.Context, host string, port uint16) (wholedevice.Stream, error) {
	return plane.OpenTCP(ctx, tcpforward.OpenRequest{Host: host, Port: int(port)})
}

type browserFixture struct {
	test           *testing.T
	ctx            context.Context
	session        *wholedevice.Session
	client, server *tcpforward.Mux
	listener       *net.TCPListener
	tlsConfig      *tls.Config
	leases         atomic.Int32
	httpRequests   atomic.Int32
}

func newBrowserFixture(test *testing.T) *browserFixture {
	test.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	test.Cleanup(cancel)
	fixture := &browserFixture{test: test, ctx: ctx}
	origin := httptest.NewTLSServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		fixture.httpRequests.Add(1)
		if request.URL.Path == "/close" {
			writer.Header().Set("Connection", "close")
		}
		fmt.Fprintf(writer, "fixture:%s:%s", request.Host, request.URL.Path)
	}))
	test.Cleanup(origin.Close)
	port := origin.Listener.Addr().(*net.TCPAddr).Port
	roots := x509.NewCertPool()
	roots.AddCert(origin.Certificate())
	fixture.tlsConfig = &tls.Config{RootCAs: roots, ServerName: origin.Certificate().DNSNames[0]}
	fixture.client, fixture.server = tcpforward.BrowserAdmissionPair(test, ctx, port, &fixture.leases)
	fixture.session = wholedevice.Attach(ctx, browserPlane{fixture.client}, nil)
	test.Cleanup(fixture.session.Close)
	listener, err := net.ListenTCP("tcp4", &net.TCPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		test.Fatal(err)
	}
	fixture.listener = listener
	var workers sync.WaitGroup
	accepted := make(chan struct{})
	go func() {
		defer close(accepted)
		for {
			connection, err := listener.AcceptTCP()
			if err != nil {
				return
			}
			workers.Add(1)
			go func() {
				defer workers.Done()
				fixture.session.Handle(connection, "tcp", "127.0.0.1", uint16(port))
			}()
		}
	}()
	test.Cleanup(func() {
		listener.Close()
		<-accepted
		fixture.session.Close()
		workers.Wait()
	})
	return fixture
}

func (fixture *browserFixture) dial() (*tls.Conn, error) {
	connection, err := net.DialTimeout("tcp4", fixture.listener.Addr().String(), 2*time.Second)
	if err != nil {
		return nil, err
	}
	connection.SetDeadline(time.Now().Add(3 * time.Second))
	secured := tls.Client(connection, fixture.tlsConfig)
	if err := secured.HandshakeContext(fixture.ctx); err != nil {
		connection.Close()
		return nil, err
	}
	connection.SetDeadline(time.Time{})
	fixture.test.Cleanup(func() { secured.Close() })
	return secured, nil
}

func (fixture *browserFixture) open() *tls.Conn {
	fixture.test.Helper()
	connection, err := fixture.dial()
	if err != nil {
		fixture.test.Fatal(err)
	}
	return connection
}

func (fixture *browserFixture) request(connection *tls.Conn, host, target string) {
	fixture.test.Helper()
	connection.SetDeadline(time.Now().Add(3 * time.Second))
	defer connection.SetDeadline(time.Time{})
	request, err := http.NewRequest("GET", "https://"+host+target, nil)
	if err != nil {
		fixture.test.Fatal(err)
	}
	if err := request.Write(connection); err != nil {
		fixture.test.Fatal(err)
	}
	response, err := http.ReadResponse(bufio.NewReader(connection), request)
	if err != nil {
		fixture.test.Fatal(err)
	}
	body, err := io.ReadAll(response.Body)
	response.Body.Close()
	if err != nil || response.StatusCode != http.StatusOK || string(body) != "fixture:"+host+":"+target {
		fixture.test.Fatalf("HTTP body mismatch: status=%d bytes=%d error=%v", response.StatusCode, len(body), err)
	}
}

func (fixture *browserFixture) waitCounts(active int) {
	fixture.test.Helper()
	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		if fixture.session.Counters.TCPActive.Load() == int64(active) && fixture.client.Stats().ActiveStreams == active && fixture.server.Stats().ActiveStreams == active && fixture.server.Stats().ActiveSockets == active {
			return
		}
		time.Sleep(time.Millisecond)
	}
	fixture.test.Fatalf("lifecycle not settled: packet=%d client=%+v server=%+v", fixture.session.Counters.TCPActive.Load(), fixture.client.Stats(), fixture.server.Stats())
}

func (fixture *browserFixture) dns(protocol string, rejected bool) {
	fixture.test.Helper()
	query := dnsmessage.Message{Header: dnsmessage.Header{ID: 7}, Questions: []dnsmessage.Question{{Name: dnsmessage.MustNewName("asset.fixture.invalid."), Type: dnsmessage.TypeA, Class: dnsmessage.ClassINET}}}
	payload, err := query.Pack()
	if err != nil {
		fixture.test.Fatal(err)
	}
	if protocol == "tcp" {
		framed := make([]byte, len(payload)+2)
		binary.BigEndian.PutUint16(framed, uint16(len(payload)))
		copy(framed[2:], payload)
		payload = framed
	}
	app, engine := net.Pipe()
	defer app.Close()
	completed := make(chan struct{})
	go func() { defer close(completed); fixture.session.Handle(engine, protocol, "10.79.0.1", 53) }()
	defer func() { app.Close(); <-completed }()
	app.SetDeadline(time.Now().Add(2 * time.Second))
	_, err = app.Write(payload)
	if rejected {
		if !errors.Is(err, io.ErrClosedPipe) {
			fixture.test.Fatalf("expected immediate TCP DNS refusal, got %v", err)
		}
		return
	}
	if err != nil {
		fixture.test.Fatal(err)
	}
	response := make([]byte, len(payload))
	if _, err = io.ReadFull(app, response); err != nil {
		fixture.test.Fatal(err)
	}
	if protocol == "tcp" {
		response = response[2:]
	}
	var answer dnsmessage.Message
	if err = answer.Unpack(response); err != nil || !answer.Response || answer.ID != query.ID || len(answer.Questions) != 1 || answer.Questions[0] != query.Questions[0] {
		fixture.test.Fatal("DNS exchange mismatch", err)
	}
}

func TestBrowserAdmissionSearchAndNewOrigins(test *testing.T) {
	fixture := newBrowserFixture(test)
	connections := make([]*tls.Conn, 32)
	for index := range connections {
		connections[index] = fixture.open()
		fixture.request(connections[index], "origin-"+strconv.Itoa(index)+".fixture.invalid", "/initial")
	}
	fixture.waitCounts(32)
	time.Sleep(100 * time.Millisecond)
	for index := 0; index < 3; index++ {
		fixture.request(connections[0], "search.fixture.invalid", "/query-"+strconv.Itoa(index))
	}
	fixture.request(connections[1], "asset.fixture.invalid", "/already-open.css")
	before := fixture.client.Stats()
	requests := fixture.httpRequests.Load()
	if unexpected, err := fixture.dial(); err == nil {
		unexpected.Close()
		test.Fatal("33rd connection unexpectedly admitted")
	} else if failure, ok := err.(net.Error); ok && failure.Timeout() {
		test.Fatal("expected refusal, not TLS deadline", err)
	}
	fixture.dns("udp", false)
	fixture.dns("tcp", true)
	if _, err := fixture.client.OpenTCP(fixture.ctx, tcpforward.OpenRequest{Host: tcpforward.LeaseRenewalHost, Port: 1}); err != tcpforward.ErrStreamLimit {
		test.Fatal("control stream cap", err)
	}
	after := fixture.client.Stats()
	if fixture.session.Counters.LimitDenied.Load() != 2 || after.OpenOK != before.OpenOK || after.OpenErrors != before.OpenErrors || fixture.httpRequests.Load() != requests || fixture.leases.Load() != 0 {
		test.Fatal("refusal accounting", fixture.session.Snapshot(), after)
	}
	connections[31].Close()
	fixture.waitCounts(31)
	replacement := fixture.open()
	fixture.request(replacement, "new-origin.fixture.invalid", "/new.css")
	fixture.waitCounts(32)
	for _, connection := range connections {
		connection.Close()
	}
	replacement.Close()
	fixture.waitCounts(0)
	test.Logf("32 occupied: reused search=3/3 asset=1/1; new TLS refused before origin; UDP DNS=PASS TCP DNS=REFUSED; limit_denied=2 mux_open_errors_delta=0 control=stream_limit; release_one_new_HTTPS=PASS; cleanup=0")
}

func TestBrowserAdmissionLifecycle(test *testing.T) {
	for _, mode := range []string{"application_close", "origin_close", "application_reset"} {
		test.Run(mode, func(test *testing.T) {
			fixture := newBrowserFixture(test)
			for index := 0; index < 40; index++ {
				connection := fixture.open()
				target := "/static.css"
				if mode == "origin_close" {
					target = "/close"
				}
				fixture.request(connection, "origin.fixture.invalid", target)
				if mode == "application_reset" {
					raw := connection.NetConn().(*net.TCPConn)
					raw.SetLinger(0)
					raw.Close()
				} else {
					connection.Close()
				}
				fixture.waitCounts(0)
			}
			if fixture.session.Counters.LimitDenied.Load() != 0 || fixture.client.Stats().OpenErrors != 0 {
				test.Fatal("unexpected refusal")
			}
			test.Logf("40 sequential verified HTTPS bodies; active packet/client/server sockets=0 after each; refusal=0; client_protocol_errors=%d server_protocol_errors=%d", fixture.client.Stats().ProtocolErrors, fixture.server.Stats().ProtocolErrors)
		})
	}
}

func TestBrowserAdmissionControlUsesSharedCap(test *testing.T) {
	fixture := newBrowserFixture(test)
	connections := make([]*tls.Conn, 31)
	for index := range connections {
		connections[index] = fixture.open()
		fixture.request(connections[index], "origin.fixture.invalid", "/initial")
	}
	fixture.waitCounts(31)
	control, err := fixture.client.OpenTCP(fixture.ctx, tcpforward.OpenRequest{Host: tcpforward.LeaseRenewalHost, Port: 1})
	if err != nil {
		test.Fatal(err)
	}
	defer control.Reset()
	var marker [1]byte
	if _, err := io.ReadFull(control, marker[:]); err != nil || marker[0] != 42 {
		test.Fatal("control callback", err)
	}
	before := fixture.client.Stats()
	if unexpected, err := fixture.dial(); err == nil {
		unexpected.Close()
		test.Fatal("new TCP admitted with full shared mux")
	} else if failure, ok := err.(net.Error); ok && failure.Timeout() {
		test.Fatal("expected immediate refusal", err)
	}
	fixture.request(connections[0], "search.fixture.invalid", "/still-live")
	if fixture.session.Counters.LimitDenied.Load() != 0 || fixture.client.Stats().OpenErrors != before.OpenErrors || fixture.session.Counters.TCPActive.Load() != 31 || fixture.leases.Load() != 1 {
		test.Fatal("shared cap accounting", fixture.session.Snapshot())
	}
	control.Reset()
	fixture.waitCounts(31)
	replacement := fixture.open()
	fixture.request(replacement, "new-origin.fixture.invalid", "/restored.css")
	replacement.Close()
	for _, connection := range connections {
		connection.Close()
	}
	fixture.waitCounts(0)
	test.Log("31 TCP + 1 control fills mux; new TLS refused; packet limit_denied=0 mux_open_errors_delta=0; search=PASS; control_release_new_HTTPS=PASS")
}
