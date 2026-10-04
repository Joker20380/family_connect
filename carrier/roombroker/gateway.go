package roombroker

import (
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/tls"
	"encoding/json"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/sessiondiag"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
	"github.com/Joker20380/family_connect/carrier/telemost"
)

type TelemostGateway struct {
	CredentialsPath string
	Event           func(string)
	Diagnostic      func(sessiondiag.Report)
}

const DedicatedMaxStreams = tcpforward.MuxMaxStreams

type telemostGateway struct {
	session     *telemost.Session
	credentials []byte
	setupID     string
	identity    Identity
	event       func(string)
	diagnostic  func(sessiondiag.Report)
}

func (starter TelemostGateway) Start(lifetime, ready context.Context, room Room, id string, identity Identity) (Gateway, error) {
	raw, err := LoadCredentials(starter.CredentialsPath)
	if err != nil {
		return nil, err
	}
	session, err := telemost.New(lifetime, telemost.Config{RoomURL: room.JoinURL, DisplayName: "Family gateway", Mode: telemost.ModeVP8})
	if err != nil {
		clear(raw)
		return nil, Code("gateway_configuration")
	}
	if err := session.Connect(ready); err != nil {
		session.Close()
		clear(raw)
		return nil, Code("gateway_join")
	}
	event := starter.Event
	if event == nil {
		event = func(string) {}
	}
	return &telemostGateway{session, raw, id, identity, event, starter.Diagnostic}, nil
}

func bindingMessage(id string, nonce []byte) []byte {
	return append([]byte("family-connect/room-setup/v1\x00"+id+"\x00"), nonce...)
}

func BindClient(ctx context.Context, session *familysession.Session, descriptor Descriptor, raw []byte) error {
	var credentials familysession.Credentials
	if json.Unmarshal(raw, &credentials) != nil {
		return Code("binding_rejected")
	}
	certificate, err := tls.X509KeyPair([]byte(credentials.Certificate), []byte(credentials.PrivateKey))
	if err != nil {
		return Code("binding_rejected")
	}
	key, ok := certificate.PrivateKey.(ed25519.PrivateKey)
	if !ok {
		return Code("binding_rejected")
	}
	nonce, err := session.Recv(ctx)
	if err != nil || len(nonce) != 32 {
		return Code("binding_rejected")
	}
	signature := ed25519.Sign(key, bindingMessage(descriptor.SetupID, nonce))
	if session.SendContext(ctx, signature) != nil {
		return Code("binding_rejected")
	}
	ack, err := session.Recv(ctx)
	if err != nil || string(ack) != "room-active-v1" {
		return Code("binding_rejected")
	}
	return nil
}

func (gateway *telemostGateway) Run(ctx context.Context, active func() error) error {
	trace := sessiontrace.From(ctx)
	trace.Add("FAMILY_TLS", "STARTED", "NONE")
	secured, err := familysession.Open(ctx, gateway.session, gateway.credentials, true)
	clear(gateway.credentials)
	if err != nil {
		trace.Add("FAMILY_TLS", "FAILED", "FAMILY_TLS_ERROR")
		return Code("family_admission_rejected")
	}
	trace.Add("FAMILY_TLS", "ESTABLISHED", "NONE")
	defer secured.Close()
	gateway.event("family_auth")
	if err := bindGateway(ctx, secured, gateway.setupID, gateway.identity, active); err != nil {
		trace.Add("GATEWAY_SESSION", "FAILED", "GATEWAY_CLOSE")
		return err
	}
	mux, err := tcpforward.NewMux(ctx, secured, true, tcpforward.MuxConfig{MaxStreams: DedicatedMaxStreams})
	if err != nil {
		trace.Add("GATEWAY_SESSION", "FAILED", "UNKNOWN_INTERNAL")
		return Code("mux_start_failed")
	}
	stopSample := sessiondiag.Sample(ctx, trace, func() (uint64, uint64) { stats := gateway.session.Stats(); return stats.BytesSent, stats.BytesReceived },
		func() *sessiontrace.Delivery {
			return sessiondiag.Delivery(secured.ReliabilityStats(), gateway.session.Stats())
		})
	defer stopSample()
	defer func() {
		mux.Close()
		stats := mux.Stats()
		if stats.ActiveSockets == 0 && stats.ActiveStreams == 0 && stats.RetainedBytes == 0 {
			gateway.event("dedicated_resources_closed")
		}
	}()
	err = mux.Wait()
	if gateway.diagnostic != nil {
		failure, failedAt := mux.Terminal()
		report := sessiondiag.Capture(gateway.setupID, failure, failedAt, secured.ReliabilityStats(), gateway.session.Stats(), mux.Stats())
		snapshot := trace.Snapshot()
		report.Trace = &snapshot
		gateway.diagnostic(report)
	}
	return err
}

func bindGateway(ctx context.Context, secured *familysession.Session, id string, identity Identity, active func() error) error {
	var nonce [32]byte
	if _, err := rand.Read(nonce[:]); err != nil {
		return Code("binding_rejected")
	}
	if secured.SendContext(ctx, nonce[:]) != nil {
		return Code("binding_rejected")
	}
	signature, err := secured.Recv(ctx)
	if err != nil || !ed25519.Verify(ed25519.PublicKey(identity.PublicKey[:]), bindingMessage(id, nonce[:]), signature) {
		return Code("binding_rejected")
	}
	if err := active(); err != nil {
		return err
	}
	if secured.SendContext(ctx, []byte("room-active-v1")) != nil {
		return Code("binding_rejected")
	}
	return nil
}

func (gateway *telemostGateway) Close() error {
	clear(gateway.credentials)
	return gateway.session.Close()
}
