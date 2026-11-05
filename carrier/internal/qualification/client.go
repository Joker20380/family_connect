package qualification

import (
	"bufio"
	"bytes"
	"context"
	"crypto/ecdh"
	"crypto/ed25519"
	"crypto/sha256"
	"crypto/tls"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/netip"
	"os"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
	"golang.org/x/net/dns/dnsmessage"
)

type clientConfig struct {
	Endpoint, Gateway, Identity, Wireguard, Anchor, Roots, OriginRoot string
	DurationSeconds                                                   int
	HTTPSAddress                                                      string
}

func roots(path string) (*x509.CertPool, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	pool := x509.NewCertPool()
	if !pool.AppendCertsFromPEM(raw) {
		return nil, fmt.Errorf("isolated CA rejected")
	}
	return pool, nil
}

func fetch(ctx context.Context, config clientConfig, identity, anchor []byte) ([]byte, []byte, error) {
	pool, err := roots(config.Roots)
	if err != nil {
		return nil, nil, err
	}
	transport := &http.Transport{TLSClientConfig: &tls.Config{RootCAs: pool, MinVersion: tls.VersionTLS13}}
	defer transport.CloseIdleConnections()
	client := &http.Client{Transport: transport, Timeout: 10 * time.Second}
	post := func(path string, body map[string]any) (map[string]any, error) {
		raw, err := json.Marshal(map[string]any{"gateway_id": config.Gateway, "request": body})
		if err != nil {
			return nil, err
		}
		request, err := http.NewRequestWithContext(ctx, "POST", config.Endpoint+path, bytes.NewReader(raw))
		if err != nil {
			return nil, err
		}
		request.Header.Set("Content-Type", "application/json")
		response, err := client.Do(request)
		if err != nil {
			return nil, err
		}
		defer response.Body.Close()
		if response.StatusCode != http.StatusOK {
			return nil, fmt.Errorf("readiness HTTP %d", response.StatusCode)
		}
		var envelope struct {
			Gateway  string         `json:"gateway_id"`
			Response map[string]any `json:"response"`
		}
		if err = json.NewDecoder(io.LimitReader(response.Body, 1<<20)).Decode(&envelope); err != nil {
			return nil, err
		}
		if envelope.Gateway != config.Gateway || envelope.Response == nil {
			return nil, fmt.Errorf("readiness binding")
		}
		return envelope.Response, nil
	}
	key := ed25519.NewKeyFromSeed(identity[32:])
	defer clear(key)
	exchange, err := ecdh.X25519().NewPrivateKey(identity[:32])
	if err != nil {
		return nil, nil, err
	}
	public := append(exchange.PublicKey().Bytes(), key.Public().(ed25519.PublicKey)...)
	request := map[string]any{"public_identity": base64.StdEncoding.EncodeToString(public), "wireguard_public_key": config.Wireguard}
	challenge, err := post("/friends/restricted-readiness/challenge", request)
	if err != nil {
		return nil, nil, err
	}
	request["schema_version"], request["transport"] = 1, "wireguard"
	request["challenge"], request["audience"] = challenge["challenge"], challenge["audience"]
	raw, _ := json.Marshal(request)
	request["signature"] = base64.StdEncoding.EncodeToString(ed25519.Sign(key, append([]byte("family-connect/transport-key-binding/v1\x00"), raw...)))
	delivery, err := post("/friends/restricted-readiness", request)
	if err != nil {
		return nil, nil, err
	}
	raw, _ = json.Marshal(delivery)
	defer clear(raw)
	return wholedevice.DeliveryMaterial(raw, identity, anchor, time.Now())
}

type streamConnection struct{ *tcpforward.MuxStream }

func (streamConnection) LocalAddr() net.Addr              { return &net.TCPAddr{} }
func (streamConnection) RemoteAddr() net.Addr             { return &net.TCPAddr{} }
func (streamConnection) SetDeadline(time.Time) error      { return nil }
func (streamConnection) SetReadDeadline(time.Time) error  { return nil }
func (streamConnection) SetWriteDeadline(time.Time) error { return nil }

func traffic(ctx context.Context, mux *tcpforward.Mux, original *tcpforward.MuxStream, trust *x509.CertPool, sequence int, httpsAddress string) error {
	bounded, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()
	stop := context.AfterFunc(bounded, func() { original.Reset() })
	defer stop()
	data := []byte(fmt.Sprintf("isolated-core-%08d", sequence))
	roundtrip := func(stream *tcpforward.MuxStream) error {
		if _, err := stream.Write(data); err != nil {
			return err
		}
		received := make([]byte, len(data))
		if _, err := io.ReadFull(stream, received); err != nil {
			return err
		}
		if !bytes.Equal(data, received) {
			return fmt.Errorf("TCP bytes differ")
		}
		return nil
	}
	if err := roundtrip(original); err != nil {
		return err
	}
	fresh, err := mux.OpenTCP(bounded, tcpforward.OpenRequest{Host: "chat-mailbox.family-connect.invalid", Port: 1})
	if err != nil {
		return err
	}
	defer fresh.Reset()
	stopFresh := context.AfterFunc(bounded, func() { fresh.Reset() })
	defer stopFresh()
	if err := roundtrip(fresh); err != nil {
		return err
	}
	name, _ := dnsmessage.NewName("isolated.family-connect.test.")
	query, _ := (&dnsmessage.Message{Header: dnsmessage.Header{ID: 47}, Questions: []dnsmessage.Question{{Name: name, Type: dnsmessage.TypeA, Class: dnsmessage.ClassINET}}}).Pack()
	answer, err := mux.QueryDNS(bounded, query)
	if err != nil {
		return err
	}
	var decoded dnsmessage.Message
	if decoded.Unpack(answer) != nil || !decoded.Header.Response || decoded.Header.ID != 47 || len(decoded.Answers) != 1 {
		return fmt.Errorf("DNS response invalid")
	}
	httpsRequest, serverName := tcpforward.OpenRequest{Host: "chat-api.family-connect.invalid", Port: 1}, "localhost"
	if httpsAddress != "" {
		address, err := netip.ParseAddrPort(httpsAddress)
		if err != nil || !address.Addr().IsGlobalUnicast() || address.Addr().IsPrivate() {
			return fmt.Errorf("isolated public HTTPS address rejected")
		}
		serverName = address.Addr().String()
		httpsRequest = tcpforward.OpenRequest{Host: serverName, Port: int(address.Port())}
	}
	secureStream, err := mux.OpenTCP(bounded, httpsRequest)
	if err != nil {
		return err
	}
	defer secureStream.Reset()
	stopTLS := context.AfterFunc(bounded, func() { secureStream.Reset() })
	defer stopTLS()
	secure := tls.Client(streamConnection{secureStream}, &tls.Config{RootCAs: trust, ServerName: serverName, MinVersion: tls.VersionTLS13})
	if err := secure.HandshakeContext(bounded); err != nil {
		return err
	}
	if _, err := io.WriteString(secure, "GET / HTTP/1.1\r\nHost: "+serverName+"\r\nConnection: close\r\n\r\n"); err != nil {
		return err
	}
	response, err := http.ReadResponse(bufio.NewReader(secure), nil)
	if err != nil {
		return err
	}
	defer response.Body.Close()
	body, err := io.ReadAll(io.LimitReader(response.Body, 4096))
	if err != nil || response.StatusCode != 200 || string(body) != "verified-isolated-origin" {
		return fmt.Errorf("verified HTTPS response invalid")
	}
	return nil
}

func Client(parent context.Context, provider Provider, path string) error {
	raw, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	var config clientConfig
	err = json.Unmarshal(raw, &config)
	clear(raw)
	if err != nil || config.DurationSeconds <= 0 {
		return fmt.Errorf("invalid client configuration")
	}
	identity, err := base64.StdEncoding.DecodeString(config.Identity)
	if err != nil || len(identity) != 64 {
		return fmt.Errorf("invalid isolated identity")
	}
	defer clear(identity)
	anchor, err := base64.StdEncoding.DecodeString(config.Anchor)
	if err != nil || len(anchor) != 32 {
		return fmt.Errorf("invalid isolated anchor")
	}
	trust, err := roots(config.OriginRoot)
	if err != nil {
		return err
	}
	ctx, cancel := context.WithTimeout(parent, time.Duration(config.DurationSeconds)*time.Second+time.Minute)
	defer cancel()
	var output sync.Mutex
	emit := func(event string, values map[string]any) {
		output.Lock()
		defer output.Unlock()
		values["event"], values["pid"], values["at"] = event, os.Getpid(), time.Now().UTC()
		json.NewEncoder(os.Stdout).Encode(values)
	}
	event := func(value string) { emit(value, map[string]any{}) }
	profile, directory, err := fetch(ctx, config, identity, anchor)
	if err != nil {
		return err
	}
	defer clear(profile)
	var locator bootstrap.Directory
	if err := json.Unmarshal(directory, &locator); err != nil {
		return err
	}
	descriptor, err := bootstrap.RecoverWithConnector(ctx, locator, profile, event, provider.Seed)
	if err != nil {
		return err
	}
	connecting, finish := context.WithTimeout(ctx, 45*time.Second)
	carrier, err := provider.Connect(ctx, connecting, roombroker.Room{JoinURL: descriptor.JoinURL})
	if err != nil {
		finish()
		return err
	}
	defer carrier.Close()
	stop := context.AfterFunc(connecting, func() { carrier.Close() })
	secured, err := familysession.OpenMux(ctx, carrier, profile, false, true)
	if err == nil {
		err = roombroker.BindClient(connecting, secured, descriptor, profile)
	}
	stop()
	finish()
	if err != nil {
		return err
	}
	defer secured.Close()
	mux, err := tcpforward.NewMux(ctx, secured, false, tcpforward.MuxConfig{MaxStreams: roombroker.DedicatedMaxStreams, WaitForSlot: true, Lifecycle: true})
	if err != nil {
		return fmt.Errorf("new mux: %w", err)
	}
	defer mux.Close()
	maintenance := roombroker.NewSessionMaintenance(ctx, mux, secured, descriptor.SetupID, func() { cancel(); secured.Close() })
	maintained := make(chan struct{})
	go func() { defer close(maintained); maintenance.Run() }()
	defer func() { cancel(); <-maintained }()
	original, err := mux.OpenTCP(ctx, tcpforward.OpenRequest{Host: "chat-mailbox.family-connect.invalid", Port: 1})
	if err != nil {
		return fmt.Errorf("original echo: %w", err)
	}
	defer original.Reset()
	emit("connected", map[string]any{"session": descriptor.SetupID, "stream": original.Stats().ID, "security": secured.SecurityDeadline()})
	finishAt := time.Now().Add(time.Duration(config.DurationSeconds) * time.Second)
	previous := sha256.Sum256(profile)
	ticker := time.NewTicker(time.Second)
	defer ticker.Stop()
	for sequence := 0; ; sequence++ {
		if err := traffic(ctx, mux, original, trust, sequence, config.HTTPSAddress); err != nil {
			return err
		}
		if err := secured.WithAuthorization(ctx, func(auth familysession.Authorization) error {
			emit("traffic", map[string]any{"session": descriptor.SetupID, "generation": auth.Generation, "security": auth.Deadline, "original": original.Stats(), "carrier": carrier.Stats(), "tcp": true, "dns": true, "verified_https": true})
			return nil
		}); err != nil {
			return err
		}
		if !time.Now().Before(finishAt) {
			event("finished")
			return nil
		}
		if sequence%5 == 0 {
			next, _, refreshErr := fetch(ctx, config, identity, anchor)
			if refreshErr == nil {
				fingerprint := sha256.Sum256(next)
				if fingerprint != previous && maintenance.Offer(next, func() { event("credentials_committed") }) {
					previous = fingerprint
					event("credentials_offered")
				}
				clear(next)
			} else {
				event("refresh_unavailable")
			}
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-secured.Done():
			return fmt.Errorf("Family session closed")
		case <-ticker.C:
		}
	}
}
