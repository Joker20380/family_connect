package familysession

import (
	"context"
	"crypto/ed25519"
	"crypto/sha256"
	"crypto/tls"
	"crypto/x509"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"errors"
	"io"
	"net"
	"strconv"
	"strings"
	"sync"
	"time"
)

const Protocol = "family-connect-5n3-test-v1"
const MaxPayload = 65536

var ErrRejected = errors.New("family session rejected")

type PacketEndpoint interface {
	SendContext(context.Context, []byte) error
	Recv(context.Context) ([]byte, error)
	Close() error
}

type Credentials struct {
	Certificate     string `json:"certificate"`
	PrivateKey      string `json:"private_key"`
	Authority       string `json:"authority"`
	Revocations     string `json:"revocations"`
	Family          string `json:"family"`
	Gateway         string `json:"gateway"`
	MinimumRevision int    `json:"minimum_revision"`
	MinimumCRL      int64  `json:"minimum_crl"`
}

func Configuration(raw []byte, server bool) (*tls.Config, time.Time, error) {
	if len(raw) > 48<<10 {
		return nil, time.Time{}, ErrRejected
	}
	var credentials Credentials
	decoder := json.NewDecoder(strings.NewReader(string(raw)))
	decoder.DisallowUnknownFields()
	if decoder.Decode(&credentials) != nil || decoder.Decode(new(any)) != io.EOF || len(credentials.Family) != 32 || len(credentials.Gateway) != 32 || credentials.MinimumRevision < 1 || credentials.MinimumCRL < 1 {
		return nil, time.Time{}, ErrRejected
	}
	identity, err := tls.X509KeyPair([]byte(credentials.Certificate), []byte(credentials.PrivateKey))
	if err != nil || len(identity.Certificate) != 1 {
		return nil, time.Time{}, ErrRejected
	}
	block, remaining := pem.Decode([]byte(credentials.Authority))
	if block == nil || len(strings.TrimSpace(string(remaining))) != 0 {
		return nil, time.Time{}, ErrRejected
	}
	authority, err := x509.ParseCertificate(block.Bytes)
	if err != nil || !authority.IsCA || authority.CheckSignatureFrom(authority) != nil {
		return nil, time.Time{}, ErrRejected
	}
	block, remaining = pem.Decode([]byte(credentials.Revocations))
	if block == nil || len(strings.TrimSpace(string(remaining))) != 0 {
		return nil, time.Time{}, ErrRejected
	}
	revocations, err := x509.ParseRevocationList(block.Bytes)
	if err != nil || revocations.CheckSignatureFrom(authority) != nil || revocations.Number == nil || !revocations.Number.IsInt64() || revocations.Number.Int64() < credentials.MinimumCRL {
		return nil, time.Time{}, ErrRejected
	}
	now := time.Now()
	if now.Before(revocations.ThisUpdate) || !now.Before(revocations.NextUpdate) || !now.Before(authority.NotAfter) || now.Before(authority.NotBefore) {
		return nil, time.Time{}, ErrRejected
	}
	roots := x509.NewCertPool()
	roots.AddCert(authority)
	local, err := x509.ParseCertificate(identity.Certificate[0])
	if err != nil {
		return nil, time.Time{}, ErrRejected
	}
	expiry := minTime(local.NotAfter, revocations.NextUpdate, authority.NotAfter)
	config := &tls.Config{
		MinVersion: tls.VersionTLS13, MaxVersion: tls.VersionTLS13,
		Certificates: []tls.Certificate{identity}, RootCAs: roots, ClientCAs: roots,
		ServerName: "gateway.family-connect.test", NextProtos: []string{Protocol},
		SessionTicketsDisabled: true,
	}
	if server {
		config.ClientAuth = tls.RequireAndVerifyClientCert
	}
	config.VerifyConnection = func(state tls.ConnectionState) error {
		if state.Version != tls.VersionTLS13 || state.NegotiatedProtocol != Protocol || state.DidResume || len(state.PeerCertificates) != 1 || len(state.VerifiedChains) == 0 {
			return ErrRejected
		}
		peer := state.PeerCertificates[0]
		if err := authorize(peer, credentials, revocations, server); err != nil {
			return err
		}
		return nil
	}
	return config, expiry, nil
}

func authorize(peer *x509.Certificate, credentials Credentials, revocations *x509.RevocationList, server bool) error {
	now := time.Now()
	if now.Before(revocations.ThisUpdate) || !now.Before(revocations.NextUpdate) {
		return ErrRejected
	}
	for _, revoked := range revocations.RevokedCertificateEntries {
		if peer.SerialNumber.Cmp(revoked.SerialNumber) == 0 {
			return ErrRejected
		}
	}
	fields := peer.Subject.OrganizationalUnit
	claims := make(map[string]string, 4)
	for _, field := range fields {
		key, value, ok := strings.Cut(field, "=")
		if !ok || claims[key] != "" || value == "" {
			return ErrRejected
		}
		claims[key] = value
	}
	if len(fields) != 4 || claims["protocol"] != Protocol || claims["family"] != credentials.Family {
		return ErrRejected
	}
	role := "gateway"
	if server {
		role = "device"
	}
	revision, err := strconv.Atoi(claims["revision"])
	if err != nil || revision < credentials.MinimumRevision || claims["role"] != role {
		return ErrRejected
	}
	if len(peer.URIs) != 1 || peer.URIs[0].Scheme != "urn" || !strings.HasPrefix(peer.URIs[0].Opaque, "family-connect:identity:") {
		return ErrRejected
	}
	public, err := hex.DecodeString(strings.TrimPrefix(peer.URIs[0].Opaque, "family-connect:identity:"))
	if err != nil || len(public) != 64 {
		return ErrRejected
	}
	key, ok := peer.PublicKey.(ed25519.PublicKey)
	if !ok || !key.Equal(ed25519.PublicKey(public[32:])) {
		return ErrRejected
	}
	reference := sha256.Sum256(public)
	if peer.Subject.SerialNumber != hex.EncodeToString(reference[:16]) {
		return ErrRejected
	}
	if !server && hex.EncodeToString(reference[:16]) != credentials.Gateway {
		return ErrRejected
	}
	return nil
}

func minTime(values ...time.Time) time.Time {
	result := values[0]
	for _, value := range values[1:] {
		if value.Before(result) {
			result = value
		}
	}
	return result
}

type stream struct {
	net.Conn
	peer     net.Conn
	endpoint PacketEndpoint
	cancel   context.CancelFunc
	once     sync.Once
	workers  sync.WaitGroup
}

func bridge(ctx context.Context, endpoint PacketEndpoint) *stream {
	ctx, cancel := context.WithCancel(ctx)
	local, peer := net.Pipe()
	connection := &stream{Conn: local, peer: peer, endpoint: endpoint, cancel: cancel}
	connection.workers.Add(2)
	go func() {
		defer connection.workers.Done()
		defer connection.stop()
		buffer := make([]byte, MaxPayload)
		for {
			count, err := peer.Read(buffer)
			if err != nil || endpoint.SendContext(ctx, buffer[:count]) != nil {
				return
			}
		}
	}()
	go func() {
		defer connection.workers.Done()
		defer connection.stop()
		for {
			payload, err := endpoint.Recv(ctx)
			if err != nil || len(payload) == 0 || len(payload) > MaxPayload {
				return
			}
			if _, err := peer.Write(payload); err != nil {
				return
			}
		}
	}()
	context.AfterFunc(ctx, connection.stop)
	return connection
}

func (connection *stream) stop() {
	connection.once.Do(func() {
		connection.cancel()
		connection.Conn.Close()
		connection.peer.Close()
		connection.endpoint.Close()
	})
}

func (connection *stream) Close() error {
	connection.stop()
	connection.workers.Wait()
	return nil
}

type Session struct {
	connection   *tls.Conn
	stream       *stream
	expiry       time.Time
	sendSequence uint64
	recvSequence uint64
	sendMu       sync.Mutex
	recvMu       sync.Mutex
}

func Open(ctx context.Context, endpoint PacketEndpoint, raw []byte, server bool) (*Session, error) {
	config, expiry, err := Configuration(raw, server)
	if err != nil {
		return nil, err
	}
	transport := bridge(ctx, endpoint)
	var connection *tls.Conn
	if server {
		connection = tls.Server(transport, config)
	} else {
		connection = tls.Client(transport, config)
	}
	handshakeContext, cancel := context.WithTimeout(ctx, 30*time.Second)
	err = connection.HandshakeContext(handshakeContext)
	cancel()
	if err != nil {
		transport.Close()
		return nil, ErrRejected
	}
	expiry = minTime(expiry, connection.ConnectionState().PeerCertificates[0].NotAfter)
	return &Session{connection: connection, stream: transport, expiry: expiry}, nil
}

func (session *Session) SendContext(ctx context.Context, payload []byte) error {
	session.sendMu.Lock()
	defer session.sendMu.Unlock()
	if len(payload) > MaxPayload || session.sendSequence == ^uint64(0) || !time.Now().Before(session.expiry) || ctx.Err() != nil {
		session.stream.stop()
		return ErrRejected
	}
	deadline := session.expiry
	if bound, ok := ctx.Deadline(); ok {
		deadline = minTime(deadline, bound)
	}
	session.connection.SetWriteDeadline(deadline)
	stop := context.AfterFunc(ctx, session.stream.stop)
	defer stop()
	message := make([]byte, 12+len(payload))
	binary.BigEndian.PutUint32(message, uint32(len(payload)))
	binary.BigEndian.PutUint64(message[4:], session.sendSequence)
	copy(message[12:], payload)
	if _, err := session.connection.Write(message); err != nil {
		session.stream.stop()
		return err
	}
	session.sendSequence++
	return nil
}

func (session *Session) Recv(ctx context.Context) ([]byte, error) {
	session.recvMu.Lock()
	defer session.recvMu.Unlock()
	if session.recvSequence == ^uint64(0) || !time.Now().Before(session.expiry) || ctx.Err() != nil {
		session.stream.stop()
		return nil, ErrRejected
	}
	deadline := session.expiry
	if bound, ok := ctx.Deadline(); ok {
		deadline = minTime(deadline, bound)
	}
	session.connection.SetReadDeadline(deadline)
	stop := context.AfterFunc(ctx, session.stream.stop)
	defer stop()
	header := make([]byte, 12)
	if _, err := io.ReadFull(session.connection, header); err != nil {
		session.stream.stop()
		return nil, err
	}
	length := binary.BigEndian.Uint32(header)
	if length > MaxPayload || binary.BigEndian.Uint64(header[4:]) != session.recvSequence {
		session.stream.stop()
		return nil, ErrRejected
	}
	payload := make([]byte, length)
	if _, err := io.ReadFull(session.connection, payload); err != nil {
		session.stream.stop()
		return nil, err
	}
	session.recvSequence++
	return payload, nil
}

func (session *Session) Close() error {
	session.stream.Close()
	return session.connection.Close()
}
