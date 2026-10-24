package restrictedchat

import (
	"bytes"
	"context"
	"crypto/tls"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"sync"
	"sync/atomic"
	"time"

	"github.com/Joker20380/family_connect/carrier/restrictedowner"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

const MaxRequest = 8192
const MaxResponse = 16384
const MaxDuration = 30 * time.Second
const apiOrigin = "https://185.251.89.19:8443"

var ErrDenied = errors.New("chat service denied")
var ErrConflict = errors.New("chat registration conflict")
var ErrUnavailable = errors.New("chat service unavailable")

type Reply struct {
	Status int
	Body   []byte
}

func (Reply) Format(output fmt.State, verb rune) { fmt.Fprint(output, "[chat API reply redacted]") }

type Client struct {
	lease   *restrictedowner.Chat
	once    sync.Once
	tls     *tls.Config
	onClose func()
}

func New(lease *restrictedowner.Chat) (*Client, error) {
	if lease == nil {
		return nil, ErrDenied
	}
	return &Client{lease: lease, tls: &tls.Config{MinVersion: tls.VersionTLS12}}, nil
}

func (client *Client) Route() string {
	switch client.lease.State() {
	case 0:
		return "CONNECTING"
	case 1:
		return "SERVICE_ONLY"
	case 2:
		return "EXISTING_EXIT"
	default:
		return "UNAVAILABLE"
	}
}

func (client *Client) Close() error {
	client.once.Do(func() {
		client.lease.Release()
		if client.onClose != nil {
			client.onClose()
		}
	})
	return nil
}

func (client *Client) open(parent context.Context, name string, duration time.Duration) (*streamConn, error) {
	if parent == nil || duration <= 0 || duration > MaxDuration {
		return nil, ErrDenied
	}
	if err := parent.Err(); err != nil {
		return nil, err
	}
	finish, err := client.lease.Work()
	if err != nil {
		return nil, ErrUnavailable
	}
	ctx, cancel := context.WithTimeout(client.lease.Context(), duration)
	stopParent := context.AfterFunc(parent, cancel)
	release := func() { stopParent(); cancel(); finish() }
	resource, err := client.lease.Session(ctx)
	if err != nil {
		result := client.failure(parent, ctx, err)
		release()
		return nil, result
	}
	session, ok := resource.(*wholedevice.Session)
	if !ok {
		release()
		return nil, ErrDenied
	}
	stream, err := session.OpenService(ctx, name)
	if err != nil {
		result := client.failure(parent, ctx, err)
		release()
		return nil, result
	}
	return newStreamConn(ctx, stream, release), nil
}

func (client *Client) failure(parent, ctx context.Context, err error) error {
	var verification *tls.CertificateVerificationError
	if errors.As(err, &verification) {
		return ErrDenied
	}
	if parent.Err() != nil {
		return parent.Err()
	}
	if client.lease.Context().Err() != nil {
		return client.lease.Context().Err()
	}
	if ctx.Err() == context.DeadlineExceeded || errors.Is(err, context.DeadlineExceeded) || errors.Is(err, os.ErrDeadlineExceeded) {
		return context.DeadlineExceeded
	}
	return ErrUnavailable
}

func (client *Client) OpenMailbox(ctx context.Context, duration time.Duration) (net.Conn, error) {
	connection, err := client.open(ctx, "chat-mailbox", duration)
	if err != nil {
		return nil, err
	}
	return connection, nil
}

func (client *Client) Request(ctx context.Context, path string, body []byte, duration time.Duration) (Reply, error) {
	if (path != "/friends/chat/challenge" && path != "/friends/chat/register") || len(body) > MaxRequest || ctx == nil || duration <= 0 || duration > MaxDuration {
		return Reply{}, ErrDenied
	}
	requestCtx, cancel := context.WithTimeout(ctx, duration)
	defer cancel()
	connection, err := client.open(requestCtx, "chat-api", duration)
	if err != nil {
		return Reply{}, err
	}
	defer connection.Close()
	var dialed atomic.Bool
	transport := &http.Transport{TLSClientConfig: client.tls.Clone(), DisableKeepAlives: true,
		MaxResponseHeaderBytes: MaxResponse,
		DialContext: func(context.Context, string, string) (net.Conn, error) {
			if !dialed.CompareAndSwap(false, true) {
				return nil, ErrUnavailable
			}
			return connection, nil
		}}
	defer transport.CloseIdleConnections()
	httpClient := &http.Client{Transport: transport,
		CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	request, err := http.NewRequestWithContext(requestCtx, "POST", apiOrigin+path, bytes.NewReader(body))
	if err != nil {
		return Reply{}, ErrDenied
	}
	request.Header.Set("Content-Type", "application/json")
	response, err := httpClient.Do(request)
	if err != nil {
		return Reply{}, client.failure(ctx, requestCtx, err)
	}
	defer response.Body.Close()
	if response.StatusCode == http.StatusBadRequest || response.StatusCode == http.StatusUnauthorized || response.StatusCode == http.StatusForbidden {
		return Reply{Status: response.StatusCode}, ErrDenied
	}
	if response.StatusCode == http.StatusConflict {
		return Reply{Status: response.StatusCode}, ErrConflict
	}
	raw, err := io.ReadAll(io.LimitReader(response.Body, MaxResponse+1))
	if err != nil || len(raw) > MaxResponse {
		clear(raw)
		return Reply{}, client.failure(ctx, requestCtx, err)
	}
	if requestCtx.Err() != nil || client.lease.Context().Err() != nil {
		clear(raw)
		return Reply{}, client.failure(ctx, requestCtx, nil)
	}
	return Reply{Status: response.StatusCode, Body: raw}, nil
}
