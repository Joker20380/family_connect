package direct

import (
	"bytes"
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"strconv"
	"strings"
	"sync/atomic"
	"time"

	"github.com/Joker20380/family_connect/carrier/underlay"
	"github.com/Joker20380/family_connect/desktopbridge/worker"
)

const Origin = "https://185.251.89.19:8443"

type Command struct {
	Action string `json:"action"`
	Index  int    `json:"index"`
	Name   string `json:"name"`
	Budget int    `json:"budget_ms"`
	Path   string `json:"path,omitempty"`
	Data   []byte `json:"data,omitempty"`
	Host   string `json:"host,omitempty"`
	Port   int    `json:"port,omitempty"`
}

func (Command) Format(output fmt.State, verb rune) { fmt.Fprint(output, "[direct command redacted]") }

type Reply struct {
	Code   string `json:"code"`
	Status int    `json:"status,omitempty"`
	Data   []byte `json:"data,omitempty"`
}

func (Reply) Format(output fmt.State, verb rune) { fmt.Fprint(output, "[direct reply redacted]") }

type Protector interface{ Protect(net.Interface, int) bool }

func valid(command Command) bool {
	if command.Index <= 0 || command.Name == "" || command.Budget <= 0 || command.Budget > 30000 {
		return false
	}
	if command.Action == "request" {
		return (command.Path == "/friends/chat/challenge" || command.Path == "/friends/chat/register") && len(command.Data) <= 8192 && command.Host == "" && command.Port == 0
	}
	ip := net.ParseIP(command.Host)
	return command.Action == "open" && command.Path == "" && len(command.Data) == 0 && ip.To4() != nil && ip.String() == command.Host && command.Port > 0 && command.Port <= 65535
}

func failure(ctx context.Context, err error) string {
	var verification *tls.CertificateVerificationError
	var record tls.RecordHeaderError
	var alert tls.AlertError
	var authority x509.UnknownAuthorityError
	var hostname x509.HostnameError
	var invalid x509.CertificateInvalidError
	var operation *net.OpError
	if errors.As(err, &verification) || errors.As(err, &record) || errors.As(err, &alert) || errors.As(err, &authority) || errors.As(err, &hostname) || errors.As(err, &invalid) || (errors.As(err, &operation) && operation.Net == "tls") {
		return "DENIED"
	}
	if errors.Is(ctx.Err(), context.Canceled) {
		return "CANCELLED"
	}
	if errors.Is(ctx.Err(), context.DeadlineExceeded) {
		return "DEADLINE"
	}
	return "UNAVAILABLE"
}

func Request(ctx context.Context, command Command, dial func(context.Context, string, string) (net.Conn, error), trust *tls.Config) Reply {
	if !valid(command) || command.Action != "request" {
		return Reply{Code: "DENIED"}
	}
	if ctx.Err() != nil {
		return Reply{Code: failure(ctx, ctx.Err())}
	}
	connection, err := dial(ctx, "tcp4", "185.251.89.19:8443")
	if err != nil {
		return Reply{Code: failure(ctx, err)}
	}
	defer connection.Close()
	var dialed atomic.Bool
	transport := &http.Transport{TLSClientConfig: trust, DisableKeepAlives: true, DisableCompression: true,
		MaxResponseHeaderBytes: 16384, DialContext: func(ctx context.Context, network, address string) (net.Conn, error) {
			if address != "185.251.89.19:8443" || !dialed.CompareAndSwap(false, true) {
				return nil, underlay.ErrDenied
			}
			return connection, nil
		}}
	defer transport.CloseIdleConnections()
	client := &http.Client{Transport: transport, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	request, err := http.NewRequestWithContext(ctx, "POST", Origin+command.Path, bytes.NewReader(command.Data))
	if err != nil {
		return Reply{Code: "DENIED"}
	}
	request.Header.Set("Content-Type", "application/json")
	request.Header.Set("Accept-Encoding", "identity")
	response, err := client.Do(request)
	if err != nil {
		return Reply{Code: failure(ctx, err)}
	}
	defer response.Body.Close()
	if response.StatusCode == 400 || response.StatusCode == 401 || response.StatusCode == 403 {
		return Reply{Code: "DENIED"}
	}
	if response.StatusCode == 409 {
		return Reply{Code: "CONFLICT"}
	}
	if response.StatusCode != 200 {
		return Reply{Code: "OK", Status: response.StatusCode}
	}
	encoding := strings.ToLower(strings.TrimSpace(response.Header.Get("Content-Encoding")))
	if encoding != "" && encoding != "identity" {
		return Reply{Code: "INVALID_RESPONSE"}
	}
	body, err := io.ReadAll(io.LimitReader(response.Body, 16385))
	if len(body) > 16384 {
		clear(body)
		return Reply{Code: "INVALID_RESPONSE"}
	}
	if err != nil || ctx.Err() != nil {
		clear(body)
		return Reply{Code: failure(ctx, err)}
	}
	return Reply{Code: "OK", Status: 200, Data: body}
}

func write(connection net.Conn, reply Reply) error {
	raw, err := json.Marshal(reply)
	if err != nil {
		return err
	}
	defer clear(raw)
	connection.SetWriteDeadline(time.Now().Add(4 * time.Second))
	if err = binary.Write(connection, binary.BigEndian, uint32(len(raw))); err != nil {
		return err
	}
	_, err = connection.Write(raw)
	connection.SetWriteDeadline(time.Time{})
	return err
}

func Serve(parent context.Context, channel net.Conn, platform Protector) error {
	defer channel.Close()
	channel.SetReadDeadline(time.Now().Add(4 * time.Second))
	var command Command
	if err := worker.ReadControlMessage(channel, &command, 16384); err != nil || !valid(command) {
		return write(channel, Reply{Code: "DENIED"})
	}
	defer clear(command.Data)
	channel.SetReadDeadline(time.Time{})
	ctx, cancel := context.WithTimeout(parent, time.Duration(command.Budget)*time.Millisecond)
	defer cancel()
	stop := context.AfterFunc(ctx, func() { channel.Close() })
	defer stop()
	link, err := net.InterfaceByIndex(command.Index)
	if err != nil || link.Name != command.Name || link.Flags&net.FlagUp == 0 || link.Flags&net.FlagLoopback != 0 || strings.HasPrefix(link.Name, "fcmesh") || strings.HasPrefix(link.Name, "fcawg") || strings.HasPrefix(link.Name, "fctcp") {
		return write(channel, Reply{Code: "UNAVAILABLE"})
	}
	network, err := underlay.New(ctx, "1.1.1.1:53", func(descriptor int) bool {
		current, err := net.InterfaceByIndex(command.Index)
		return err == nil && current.Name == command.Name && current.Flags&net.FlagUp != 0 && platform.Protect(*current, descriptor)
	})
	if err != nil {
		return write(channel, Reply{Code: "UNAVAILABLE"})
	}
	defer network.Close()
	if command.Action == "request" {
		reply := Request(ctx, command, network.DialContext, &tls.Config{MinVersion: tls.VersionTLS12})
		defer clear(reply.Data)
		return write(channel, reply)
	}
	connection, err := network.DialContext(ctx, "tcp4", net.JoinHostPort(command.Host, strconv.Itoa(command.Port)))
	if err != nil {
		return write(channel, Reply{Code: failure(ctx, err)})
	}
	defer connection.Close()
	stopConnection := context.AfterFunc(ctx, func() { connection.Close() })
	defer stopConnection()
	if err = write(channel, Reply{Code: "OK"}); err != nil {
		return err
	}
	done := make(chan struct{})
	go func() {
		defer close(done)
		io.Copy(connection, channel)
		if half, ok := connection.(interface{ CloseWrite() error }); ok {
			half.CloseWrite()
		}
	}()
	io.Copy(channel, connection)
	if half, ok := channel.(interface{ CloseWrite() error }); ok {
		half.CloseWrite()
	}
	select {
	case <-done:
	case <-ctx.Done():
	}
	return nil
}
