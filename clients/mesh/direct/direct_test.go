package direct

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/binary"
	"encoding/json"
	"errors"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

type closeError struct {
	net.Conn
	closed *atomic.Int32
}

func (connection closeError) Close() error {
	connection.closed.Add(1)
	connection.Conn.Close()
	return errors.New("synthetic cleanup failure")
}

func TestFixedHTTPBoundsTerminalAndNoReplay(test *testing.T) {
	for _, scenario := range []struct {
		status                   int
		encoding, body, expected string
	}{
		{200, "", "{}", "OK"}, {400, "", "", "DENIED"}, {401, "", "", "DENIED"},
		{403, "", "", "DENIED"}, {409, "", "", "CONFLICT"}, {503, "", "", "OK"},
		{200, "gzip", "", "INVALID_RESPONSE"}, {200, "", strings.Repeat("x", 16385), "INVALID_RESPONSE"},
	} {
		test.Run(scenario.expected+http.StatusText(scenario.status)+scenario.encoding, func(test *testing.T) {
			var requests, closes, dials atomic.Int32
			server := httptest.NewTLSServer(http.HandlerFunc(func(output http.ResponseWriter, input *http.Request) {
				requests.Add(1)
				if input.URL.Path != "/friends/chat/challenge" || input.Method != "POST" || input.Header.Get("Accept-Encoding") != "identity" {
					test.Error("fixed request changed")
				}
				output.Header().Set("Content-Encoding", scenario.encoding)
				output.WriteHeader(scenario.status)
				io.WriteString(output, scenario.body)
			}))
			defer server.Close()
			roots := x509.NewCertPool()
			roots.AddCert(server.Certificate())
			dial := func(ctx context.Context, network, address string) (net.Conn, error) {
				dials.Add(1)
				if address != "185.251.89.19:8443" {
					test.Fatal("untrusted destination")
				}
				connection, err := (&net.Dialer{}).DialContext(ctx, network, server.Listener.Addr().String())
				return closeError{connection, &closes}, err
			}
			command := Command{Action: "request", Index: 2, Name: "eth0", Budget: 1000, Path: "/friends/chat/challenge", Data: []byte("{}")}
			ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
			defer cancel()
			reply := Request(ctx, command, dial, &tls.Config{RootCAs: roots, ServerName: "example.com", MinVersion: tls.VersionTLS12})
			if reply.Code != scenario.expected || requests.Load() != 1 || dials.Load() != 1 || closes.Load() == 0 {
				test.Fatalf("reply %s requests=%d dials=%d closes=%d", reply.Code, requests.Load(), dials.Load(), closes.Load())
			}
		})
	}
}

func TestTLSAndExplicitDeadlineAreTerminal(test *testing.T) {
	command := Command{Action: "request", Index: 2, Name: "eth0", Budget: 1000, Path: "/friends/chat/register"}
	for _, failure := range []error{&tls.CertificateVerificationError{}, tls.RecordHeaderError{}, tls.AlertError(40)} {
		reply := Request(context.Background(), command, func(context.Context, string, string) (net.Conn, error) { return nil, failure }, nil)
		if reply.Code != "DENIED" {
			test.Fatal(reply.Code)
		}
	}
	ctx, cancel := context.WithDeadline(context.Background(), time.Now().Add(-time.Second))
	defer cancel()
	reply := Request(ctx, command, func(context.Context, string, string) (net.Conn, error) { test.Fatal("expired dial"); return nil, nil }, nil)
	if reply.Code != "DEADLINE" {
		test.Fatal(reply.Code)
	}
}

type deniedProtector struct{ called atomic.Int32 }

func (protector *deniedProtector) Protect(net.Interface, int) bool {
	protector.called.Add(1)
	return false
}

func exchange(test *testing.T, raw []byte, protector Protector) Reply {
	test.Helper()
	parent, child := net.Pipe()
	defer parent.Close()
	done := make(chan error, 1)
	go func() { done <- Serve(context.Background(), child, protector) }()
	parent.SetDeadline(time.Now().Add(3 * time.Second))
	binary.Write(parent, binary.BigEndian, uint32(len(raw)))
	parent.Write(raw)
	var size uint32
	if err := binary.Read(parent, binary.BigEndian, &size); err != nil {
		test.Fatal(err)
	}
	data := make([]byte, size)
	if _, err := io.ReadFull(parent, data); err != nil {
		test.Fatal(err)
	}
	var reply Reply
	if err := json.Unmarshal(data, &reply); err != nil {
		test.Fatal(err)
	}
	if err := <-done; err != nil {
		test.Fatal(err)
	}
	return reply
}

func TestProtectionFailureNeverConnectsAndProtocolIsBounded(test *testing.T) {
	links, err := net.Interfaces()
	if err != nil {
		test.Fatal(err)
	}
	var link net.Interface
	for _, candidate := range links {
		if candidate.Flags&net.FlagUp != 0 && candidate.Flags&net.FlagLoopback == 0 {
			link = candidate
			break
		}
	}
	if link.Index == 0 {
		test.Fatal("test requires one up non-loopback interface")
	}
	protector := &deniedProtector{}
	command := Command{Action: "open", Index: link.Index, Name: link.Name, Budget: 1000, Host: "192.0.2.123", Port: 4242}
	raw, _ := json.Marshal(command)
	if reply := exchange(test, raw, protector); reply.Code != "UNAVAILABLE" || protector.called.Load() != 1 {
		test.Fatalf("protection not enforced: %s %d", reply.Code, protector.called.Load())
	}
	for _, raw := range []string{
		`{"action":"request","index":2,"name":"eth0","budget_ms":1000,"path":"/friends/configuration/nl"}`,
		`{"action":"open","index":2,"name":"eth0","budget_ms":1000,"host":"example.com","port":443}`,
		`{"action":"open","index":2,"name":"eth0","budget_ms":1000,"host":"192.0.2.1","port":80,"command":"evil"}`,
		`{"action":"open","action":"request"}`,
	} {
		if reply := exchange(test, []byte(raw), protector); reply.Code != "DENIED" {
			test.Fatal(reply.Code)
		}
	}
	if protector.called.Load() != 1 {
		test.Fatal("invalid command reached protection")
	}
}
