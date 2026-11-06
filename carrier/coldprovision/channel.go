package coldprovision

import (
	"bytes"
	"context"
	"crypto/tls"
	"encoding/binary"
	"encoding/json"
	"errors"
	"io"
	"log"
	"net"
	"net/http"
	"regexp"
	"strconv"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

const Challenge = "/friends/restricted-readiness/challenge"
const Fetch = "/friends/restricted-readiness"

type Request struct {
	Path string          `json:"path"`
	ID   string          `json:"request_id"`
	Body json.RawMessage `json:"body"`
}
type Reply struct {
	Status int             `json:"status"`
	Body   json.RawMessage `json:"body"`
}
type BoundRequest struct {
	Gateway string          `json:"gateway_id"`
	Request json.RawMessage `json:"request"`
}
type BoundReply struct {
	Gateway  string          `json:"gateway_id"`
	Response json.RawMessage `json:"response"`
}

var requestID = regexp.MustCompile(`^[a-f0-9]{32}$`)

func read(connection io.Reader, value any) error {
	var header [4]byte
	if _, err := io.ReadFull(connection, header[:]); err != nil {
		return err
	}
	size := binary.BigEndian.Uint32(header[:])
	if size == 0 || size > MaxMessage {
		return ErrRejected
	}
	raw := make([]byte, size)
	defer clear(raw)
	if _, err := io.ReadFull(connection, raw); err != nil {
		return err
	}
	return strict(raw, value)
}

func write(connection io.Writer, value any) error {
	raw, err := json.Marshal(value)
	defer clear(raw)
	if err != nil || len(raw) == 0 || len(raw) > MaxMessage {
		return ErrRejected
	}
	var header [4]byte
	binary.BigEndian.PutUint32(header[:], uint32(len(raw)))
	_, err = io.Copy(connection, io.MultiReader(bytes.NewReader(header[:]), bytes.NewReader(raw)))
	return err
}

type Client struct {
	connection *tls.Conn
	ctx        context.Context
	cancel     context.CancelFunc
	mu         sync.Mutex
	requests   int
	cleanup    func()
	once       sync.Once
}

func Open(parent context.Context, locator, anchor []byte, gateway string, connect bootstrap.SeedConnector) (*Client, error) {
	address, config, err := Verify(locator, anchor, gateway, time.Now())
	if err != nil || connect == nil {
		return nil, ErrRejected
	}
	deadline := time.Now().Add(Timeout)
	if expires := time.Unix(address.ExpiresAt, 0); expires.Before(deadline) {
		deadline = expires
	}
	ctx, cancel := context.WithDeadline(parent, deadline)
	carrier, err := connect(ctx, ctx, roombroker.Room{JoinURL: address.Room})
	if err != nil || carrier == nil {
		cancel()
		if carrier != nil {
			carrier.Close()
		}
		return nil, ErrUnavailable
	}
	stop := context.AfterFunc(ctx, func() { carrier.Close() })
	cleanup := func() { cancel(); carrier.Close(); stop() }
	endpoint, err := bootstrap.OpenPacketExchange(ctx, carrier)
	if err != nil {
		cleanup()
		return nil, err
	}
	connection, err := familysession.ReliableConnection(ctx, endpoint)
	if err != nil {
		cleanup()
		return nil, err
	}
	secured := tls.Client(connection, config)
	secured.SetDeadline(deadline)
	if err = secured.HandshakeContext(ctx); err != nil {
		connection.Close()
		cleanup()
		var certificateError *tls.CertificateVerificationError
		if errors.Is(err, ErrRejected) || errors.As(err, &certificateError) {
			return nil, ErrRejected
		}
		return nil, ErrUnavailable
	}
	client := &Client{connection: secured, ctx: ctx, cancel: cancel, cleanup: func() { connection.Close(); cleanup() }}
	return client, nil
}

func (client *Client) Close() { client.once.Do(client.cleanup) }

func (client *Client) Post(path string, body []byte, id string) (Reply, error) {
	client.mu.Lock()
	defer client.mu.Unlock()
	var reply Reply
	if client.ctx.Err() != nil || !requestID.MatchString(id) || client.requests == 0 && path != Challenge || client.requests == 1 && path != Fetch || client.requests > 1 {
		return reply, ErrRejected
	}
	client.requests++
	if err := write(client.connection, Request{path, id, body}); err != nil {
		client.Close()
		return reply, err
	}
	if err := read(client.connection, &reply); err != nil {
		client.Close()
		return reply, err
	}
	if client.ctx.Err() != nil || reply.Status < 200 || reply.Status > 599 {
		client.Close()
		return Reply{}, ErrRejected
	}
	if reply.Status != 200 || client.requests == 2 {
		client.Close()
	}
	return reply, nil
}

type Backend func(context.Context, Request) (Reply, error)

func Serve(parent context.Context, endpoint familysession.PacketEndpoint, identity tls.Certificate, expires time.Time, gateway string, backend Backend) {
	started := time.Now()
	if backend == nil || !expires.After(time.Now()) {
		endpoint.Close()
		return
	}
	deadline := time.Now().Add(Timeout)
	if expires.Before(deadline) {
		deadline = expires
	}
	ctx, cancel := context.WithDeadline(parent, deadline)
	defer cancel()
	connection, err := familysession.ReliableConnection(ctx, endpoint)
	if err != nil {
		return
	}
	defer connection.Close()
	secured := tls.Server(connection, &tls.Config{MinVersion: tls.VersionTLS13, MaxVersion: tls.VersionTLS13, Certificates: []tls.Certificate{identity}, NextProtos: []string{Protocol}, SessionTicketsDisabled: true})
	secured.SetDeadline(deadline)
	if secured.HandshakeContext(ctx) != nil || secured.ConnectionState().NegotiatedProtocol != Protocol {
		log.Printf("cold_provision stage=tls_failed elapsed_ms=%d", time.Since(started).Milliseconds())
		return
	}
	log.Printf("cold_provision stage=tls_ready elapsed_ms=%d", time.Since(started).Milliseconds())
	var public, wireguard, nonce, challengeID string
	for index, path := range []string{Challenge, Fetch} {
		var request Request
		var bound BoundRequest
		var fields map[string]json.RawMessage
		if read(secured, &request) != nil || request.Path != path || !requestID.MatchString(request.ID) || strict(request.Body, &bound) != nil || bound.Gateway != gateway || strict(bound.Request, &fields) != nil {
			return
		}
		text := func(name string) string { var value string; json.Unmarshal(fields[name], &value); return value }
		if index == 0 {
			public, wireguard, challengeID = text("public_identity"), text("wireguard_public_key"), request.ID
			if public == "" || wireguard == "" || len(fields) != 2 {
				return
			}
		} else if text("public_identity") != public || text("wireguard_public_key") != wireguard || text("challenge") != nonce || request.ID == challengeID {
			return
		}
		log.Printf("cold_provision stage=request_accepted operation=%d request_id=%s elapsed_ms=%d", index, request.ID, time.Since(started).Milliseconds())
		reply, err := backend(ctx, request)
		log.Printf("cold_provision stage=backend_complete operation=%d request_id=%s status=%d bytes=%d success=%t elapsed_ms=%d", index, request.ID, reply.Status, len(reply.Body), err == nil, time.Since(started).Milliseconds())
		if err != nil || ctx.Err() != nil {
			return
		}
		if reply.Status == 200 {
			var response BoundReply
			var value map[string]json.RawMessage
			if strict(reply.Body, &response) != nil || response.Gateway != gateway || strict(response.Response, &value) != nil {
				log.Printf("cold_provision stage=response_binding_failed operation=%d request_id=%s elapsed_ms=%d", index, request.ID, time.Since(started).Milliseconds())
				return
			}
			var returned string
			json.Unmarshal(value["challenge"], &returned)
			if index == 0 {
				nonce = returned
				if nonce == "" {
					return
				}
			} else if returned != nonce {
				log.Printf("cold_provision stage=response_nonce_failed operation=%d request_id=%s elapsed_ms=%d", index, request.ID, time.Since(started).Milliseconds())
				return
			}
		}
		if write(secured, reply) != nil {
			log.Printf("cold_provision stage=write_failed operation=%d request_id=%s elapsed_ms=%d", index, request.ID, time.Since(started).Milliseconds())
			return
		}
		log.Printf("cold_provision stage=write_complete operation=%d request_id=%s elapsed_ms=%d", index, request.ID, time.Since(started).Milliseconds())
		if reply.Status != 200 || index == 1 {
			var end [1]byte
			secured.Read(end[:])
			log.Printf("cold_provision stage=peer_end operation=%d request_id=%s elapsed_ms=%d", index, request.ID, time.Since(started).Milliseconds())
			return
		}
	}
}

func LoopbackBackend(address string) (Backend, error) {
	host, port, err := net.SplitHostPort(address)
	number, portError := strconv.Atoi(port)
	if err != nil || portError != nil || number < 1 || number > 65535 || net.ParseIP(host) == nil || !net.ParseIP(host).IsLoopback() {
		return nil, ErrRejected
	}
	transport := &http.Transport{Proxy: nil, DisableKeepAlives: true, MaxResponseHeaderBytes: 4096}
	client := &http.Client{Transport: transport, Timeout: 10 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	return func(ctx context.Context, request Request) (Reply, error) {
		if request.Path != Challenge && request.Path != Fetch || !requestID.MatchString(request.ID) || len(request.Body) > MaxMessage {
			return Reply{}, ErrRejected
		}
		message, err := http.NewRequestWithContext(ctx, "POST", "http://"+address+request.Path, bytes.NewReader(request.Body))
		if err != nil {
			return Reply{}, err
		}
		message.Header.Set("Content-Type", "application/json")
		message.Header.Set("X-FC-Probe-ID", request.ID)
		response, err := client.Do(message)
		if err != nil {
			return Reply{}, err
		}
		defer response.Body.Close()
		raw, err := io.ReadAll(io.LimitReader(response.Body, MaxMessage+1))
		if err != nil || len(raw) > MaxMessage {
			return Reply{}, ErrRejected
		}
		return Reply{response.StatusCode, raw}, nil
	}, nil
}
