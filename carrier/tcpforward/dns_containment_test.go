package tcpforward

import (
	"bufio"
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"errors"
	"io"
	"net"
	"net/http"
	"net/netip"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

type muxTLSStream struct{ *MuxStream }

func (connection muxTLSStream) LocalAddr() net.Addr  { return &net.TCPAddr{} }
func (connection muxTLSStream) RemoteAddr() net.Addr { return &net.TCPAddr{} }
func (connection muxTLSStream) SetDeadline(time.Time) error {
	return errors.New("context deadline only")
}
func (connection muxTLSStream) SetReadDeadline(time.Time) error {
	return errors.New("context deadline only")
}
func (connection muxTLSStream) SetWriteDeadline(time.Time) error {
	return errors.New("context deadline only")
}

func TestHostnameHTTPSWithBrokenClientDNS(test *testing.T) {
	_, raw := testCredentials(test)
	var profile familysession.Credentials
	if json.Unmarshal(raw, &profile) != nil {
		test.Fatal("fixture")
	}
	certificate, err := tls.X509KeyPair([]byte(profile.Certificate), []byte(profile.PrivateKey))
	if err != nil {
		test.Fatal(err)
	}
	roots := x509.NewCertPool()
	roots.AppendCertsFromPEM([]byte(profile.Authority))
	port := muxFixture(test, func(connection *net.TCPConn) {
		secure := tls.Server(connection, &tls.Config{Certificates: []tls.Certificate{certificate}, MinVersion: tls.VersionTLS13})
		defer secure.Close()
		request, err := http.ReadRequest(bufio.NewReader(secure))
		if err != nil {
			return
		}
		request.Body.Close()
		io.WriteString(secure, "HTTP/1.1 200 OK\r\nContent-Length: 12\r\nConnection: close\r\n\r\nexact HTTPS!")
	})
	previous := net.DefaultResolver
	var escaped atomic.Int32
	net.DefaultResolver = &net.Resolver{PreferGo: true, Dial: func(context.Context, string, string) (net.Conn, error) {
		escaped.Add(1)
		return nil, errors.New("client system DNS intentionally disabled")
	}}
	defer func() { net.DefaultResolver = previous }()
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if _, err := net.DefaultResolver.LookupHost(ctx, "fc-negative-condition.invalid."); err == nil || escaped.Load() == 0 {
		test.Fatal("negative DNS condition unproven")
	}
	escaped.Store(0)
	clientSession, serverSession := authenticatedPair(test, ctx)
	server, err := NewMux(ctx, serverSession, true, MuxConfig{Policy: Policy{TestOnlyLoopbackPort: port}})
	if err != nil {
		test.Fatal(err)
	}
	var gatewayLookups atomic.Int32
	server.lookup = lookupFunction(func(ctx context.Context, network, host string) ([]netip.Addr, error) {
		if host != "gateway.family-connect.test" {
			test.Error("hostname not passed intact")
		}
		gatewayLookups.Add(1)
		return []netip.Addr{netip.MustParseAddr("127.0.0.1")}, nil
	})
	client, err := NewMux(ctx, clientSession, false, MuxConfig{})
	if err != nil {
		test.Fatal(err)
	}
	defer func() { client.Close(); server.Close() }()
	stream, err := client.OpenTCP(ctx, OpenRequest{Host: "gateway.family-connect.test", Port: port})
	if err != nil {
		test.Fatal(err)
	}
	secure := tls.Client(muxTLSStream{stream}, &tls.Config{ServerName: "gateway.family-connect.test", RootCAs: roots, MinVersion: tls.VersionTLS13})
	if err := secure.HandshakeContext(ctx); err != nil {
		test.Fatal(err)
	}
	if _, err := io.WriteString(secure, "GET / HTTP/1.1\r\nHost: gateway.family-connect.test\r\nConnection: close\r\n\r\n"); err != nil {
		test.Fatal(err)
	}
	response, err := http.ReadResponse(bufio.NewReader(secure), nil)
	if err != nil {
		test.Fatal(err)
	}
	body, err := io.ReadAll(response.Body)
	response.Body.Close()
	if err != nil || response.StatusCode != 200 || string(body) != "exact HTTPS!" {
		test.Fatal(response.StatusCode, string(body), err)
	}
	io.Copy(io.Discard, secure)
	stream.CloseWrite()
	io.Copy(io.Discard, stream)
	if err := stream.Close(); err != nil {
		test.Fatal(err)
	}
	if escaped.Load() != 0 || gatewayLookups.Load() != 1 {
		test.Fatal("destination DNS escaped", escaped.Load(), gatewayLookups.Load())
	}
}
