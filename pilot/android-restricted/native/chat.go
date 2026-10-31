//go:build android

package main

// #include <stdint.h>
// #include <stdlib.h>
// int fcRestrictedProtect(uintptr_t owner, int fd);
// void fcRestrictedRelease(uintptr_t owner);
import "C"

import (
	"bytes"
	"context"
	"crypto/sha256"
	"crypto/tls"
	"encoding/json"
	"errors"
	"io"
	"net"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/restrictedowner"
	"github.com/Joker20380/family_connect/carrier/underlay"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
	"golang.org/x/sys/unix"
)

var chatMu sync.Mutex
var chatSequence int64
var chatLeases = map[int64]*restrictedowner.Chat{}
var openChatSession = wholedevice.OpenProvisioned
var chatTLS = &tls.Config{MinVersion: tls.VersionTLS12}
var chatAPIOrigin = "https://185.251.89.19:8443"

//export fcChatAcquire
func fcChatAcquire(response, identity, anchor, resolver string, owner C.uintptr_t) int64 {
	resolver = strings.Clone(resolver)
	material := []byte(identity)
	defer clear(material)
	profile, seed, err := wholedevice.DeliveryMaterial([]byte(response), material, []byte(anchor), time.Now())
	if err != nil {
		C.fcRestrictedRelease(owner)
		return 0
	}
	hash := sha256.Sum256(profile)
	var expiry struct {
		ExpiresAt int64 `json:"expires_at"`
	}
	if json.Unmarshal([]byte(response), &expiry) != nil || expiry.ExpiresAt <= time.Now().Unix() {
		clear(profile)
		C.fcRestrictedRelease(owner)
		return 0
	}
	chatMu.Lock()
	defer chatMu.Unlock()
	if len(chatLeases) >= 8 {
		clear(profile)
		C.fcRestrictedRelease(owner)
		return 0
	}
	lease, err := transportOwner.AcquireChat(time.Unix(expiry.ExpiresAt, 0), hash,
		func(parent context.Context) (restrictedowner.Session, func(), error) {
			ctx, cancel := context.WithCancel(parent)
			network, err := underlay.New(ctx, resolver, func(fd int) bool { return C.fcRestrictedProtect(owner, C.int(fd)) != 0 })
			if err != nil {
				cancel()
				return nil, nil, err
			}
			cleanup := func() { cancel(); network.Close() }
			timer := time.AfterFunc(30*time.Second, cancel)
			session, err := openChatSession(ctx, profile, seed, network, func(string) {})
			timer.Stop()
			if session == nil {
				return nil, cleanup, err
			}
			return session, cleanup, err
		}, func() { clear(profile); C.fcRestrictedRelease(owner) })
	if err != nil {
		return 0
	}
	chatSequence++
	chatLeases[chatSequence] = lease
	return chatSequence
}

func chatLease(handle int64) *restrictedowner.Chat {
	chatMu.Lock()
	defer chatMu.Unlock()
	return chatLeases[handle]
}

//export fcChatState
func fcChatState(handle int64) int32 {
	owned := chatLease(handle)
	if owned == nil {
		return -1
	}
	return owned.State()
}

//export fcChatRelease
func fcChatRelease(handle int64) {
	chatMu.Lock()
	defer chatMu.Unlock()
	if owned := chatLeases[handle]; owned != nil {
		delete(chatLeases, handle)
		owned.Release()
	}
}

func chatStream(handle int64, name string, timeout int32) (wholedevice.Stream, context.Context, context.CancelFunc, error) {
	owned := chatLease(handle)
	if owned == nil || timeout < 1 || timeout > 30000 {
		return nil, nil, nil, errors.New("invalid_handle")
	}
	ctx, cancel := context.WithTimeout(owned.Context(), time.Duration(timeout)*time.Millisecond)
	resource, err := owned.Session(ctx)
	if err != nil {
		cancel()
		return nil, nil, nil, err
	}
	session := resource.(*wholedevice.Session)
	stream, err := session.OpenService(ctx, name)
	if err != nil {
		cancel()
		return nil, nil, nil, err
	}
	return stream, ctx, cancel, nil
}

//export fcChatOpen
func fcChatOpen(handle int64, timeout int32) int32 {
	owned := chatLease(handle)
	if owned == nil {
		return -1
	}
	finish, err := owned.Work()
	if err != nil {
		return -1
	}
	transferred := false
	defer func() {
		if !transferred {
			finish()
		}
	}()
	stream, ctx, cancel, err := chatStream(handle, "chat-mailbox", timeout)
	if err != nil {
		return -1
	}
	fds, err := unix.Socketpair(unix.AF_UNIX, unix.SOCK_STREAM|unix.SOCK_CLOEXEC, 0)
	if err != nil {
		cancel()
		stream.Reset()
		return -1
	}
	file := os.NewFile(uintptr(fds[0]), "chat-service")
	connection, err := net.FileConn(file)
	file.Close()
	if err != nil {
		unix.Close(fds[1])
		cancel()
		stream.Reset()
		return -1
	}
	transferred = true
	go func() {
		defer finish()
		defer cancel()
		defer stream.Reset()
		defer connection.Close()
		stop := context.AfterFunc(ctx, func() { connection.Close(); stream.Reset() })
		defer stop()
		done := make(chan struct{})
		go func() { io.Copy(stream, connection); stream.CloseWrite(); close(done) }()
		io.Copy(connection, stream)
		connection.Close()
		stream.Reset()
		<-done
	}()
	return int32(fds[1])
}

type chatConn struct {
	wholedevice.Stream
	cancel     context.CancelFunc
	mu         sync.Mutex
	readTimer  *time.Timer
	writeTimer *time.Timer
}

func (connection *chatConn) LocalAddr() net.Addr {
	return &net.UnixAddr{Name: "chat-service", Net: "unix"}
}
func (connection *chatConn) RemoteAddr() net.Addr { return connection.LocalAddr() }
func (connection *chatConn) timer(previous **time.Timer, deadline time.Time) {
	if *previous != nil {
		(*previous).Stop()
		*previous = nil
	}
	if !deadline.IsZero() {
		*previous = time.AfterFunc(time.Until(deadline), func() { connection.cancel(); connection.Stream.Reset() })
	}
}
func (connection *chatConn) SetDeadline(deadline time.Time) error {
	connection.mu.Lock()
	defer connection.mu.Unlock()
	connection.timer(&connection.readTimer, deadline)
	connection.timer(&connection.writeTimer, deadline)
	return nil
}
func (connection *chatConn) SetReadDeadline(deadline time.Time) error {
	connection.mu.Lock()
	defer connection.mu.Unlock()
	connection.timer(&connection.readTimer, deadline)
	return nil
}
func (connection *chatConn) SetWriteDeadline(deadline time.Time) error {
	connection.mu.Lock()
	defer connection.mu.Unlock()
	connection.timer(&connection.writeTimer, deadline)
	return nil
}
func (connection *chatConn) Close() error {
	connection.SetDeadline(time.Time{})
	connection.cancel()
	return connection.Stream.Reset()
}

//export fcChatRequest
func fcChatRequest(handle int64, path, body string, timeout int32) *C.char {
	result := map[string]any{"error": "unavailable"}
	if (path != "/friends/chat/challenge" && path != "/friends/chat/register") || len(body) > 8192 {
		return C.CString(`{"error":"denied"}`)
	}
	owned := chatLease(handle)
	if owned == nil {
		return C.CString(`{"error":"unavailable"}`)
	}
	finish, err := owned.Work()
	if err != nil {
		return C.CString(`{"error":"unavailable"}`)
	}
	defer finish()
	stream, ctx, cancel, err := chatStream(handle, "chat-api", timeout)
	if err == nil {
		defer cancel()
		defer stream.Reset()
		stop := context.AfterFunc(ctx, func() { stream.Reset() })
		defer stop()
		transport := &http.Transport{TLSClientConfig: chatTLS.Clone(), DisableKeepAlives: true,
			DialContext: func(context.Context, string, string) (net.Conn, error) {
				return &chatConn{Stream: stream, cancel: cancel}, nil
			}}
		defer transport.CloseIdleConnections()
		client := &http.Client{Transport: transport, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
		request, requestErr := http.NewRequestWithContext(ctx, "POST", chatAPIOrigin+path, bytes.NewBufferString(body))
		if requestErr == nil {
			request.Header.Set("Content-Type", "application/json")
			response, requestErr := client.Do(request)
			if requestErr == nil {
				data, readErr := io.ReadAll(io.LimitReader(response.Body, 16385))
				response.Body.Close()
				if readErr == nil && len(data) <= 16384 {
					result = map[string]any{"status": response.StatusCode, "body": string(data)}
				}
			} else {
				var verification *tls.CertificateVerificationError
				if errors.As(requestErr, &verification) {
					result["error"] = "denied"
				}
			}
		}
	}
	raw, _ := json.Marshal(result)
	return C.CString(string(raw))
}
