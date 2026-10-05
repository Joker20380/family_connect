package bootstrap

import (
	"context"
	"encoding/json"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/Joker20380/family_connect/carrier/telemost"
	"github.com/Joker20380/family_connect/carrier/underlay"
)

type message struct {
	Type       string                 `json:"type"`
	SetupID    string                 `json:"setup_id,omitempty"`
	Descriptor *roombroker.Descriptor `json:"descriptor,omitempty"`
}

func receive(ctx context.Context, endpoint familysession.PacketEndpoint, kind, id string) (message, error) {
	raw, err := endpoint.Recv(ctx)
	var input message
	limit := 256
	if kind == "TRANSPORT_READY" {
		limit = 4096
	}
	if err != nil || strictJSON(raw, &input, limit) != nil || input.Type != kind || input.SetupID != id || (kind != "TRANSPORT_READY" && input.Descriptor != nil) {
		return message{}, roombroker.Code("bootstrap_protocol_rejected")
	}
	return input, nil
}

func send(ctx context.Context, endpoint familysession.PacketEndpoint, input message) error {
	raw, err := json.Marshal(input)
	if err != nil {
		return roombroker.Code("bootstrap_protocol_rejected")
	}
	return endpoint.SendContext(ctx, raw)
}

func Exchange(ctx context.Context, endpoint familysession.PacketEndpoint, broker *roombroker.Broker, authorize roombroker.Authorize, onHandoff ...func()) (resultErr error) {
	return exchange(ctx, endpoint, broker, authorize, nil, onHandoff...)
}

func exchange(ctx context.Context, endpoint familysession.PacketEndpoint, broker *roombroker.Broker, authorize roombroker.Authorize, observe func(ExchangeFailure), onHandoff ...func()) (resultErr error) {
	ctx, cancel := context.WithTimeout(ctx, ExchangeTimeout)
	defer cancel()
	stage := "challenge"
	defer func() {
		if resultErr != nil && observe != nil {
			observe(ExchangeFailure{Stage: stage, Reason: exchangeReason(resultErr)})
		}
	}()
	defer endpoint.Close()
	defer func() {
		if resultErr != nil {
			bounded, cancel := context.WithTimeout(ctx, 200*time.Millisecond)
			defer cancel()
			_ = send(bounded, endpoint, message{Type: "ERROR"})
		}
	}()
	id, err := broker.ChallengeAfterCleanup(ctx, authorize)
	if err != nil {
		return err
	}
	handedOff := false
	defer func() {
		if !handedOff {
			cleanup, cancel := context.WithTimeout(context.Background(), 3*time.Second)
			defer cancel()
			_ = broker.Cancel(cleanup, id, authorize)
		}
	}()
	stage = "hello_send"
	if err := send(ctx, endpoint, message{Type: "HELLO", SetupID: id}); err != nil {
		return err
	}
	stage = "request_receive"
	if _, err := receive(ctx, endpoint, "REQUEST_TRANSPORT", id); err != nil {
		return err
	}
	stage = "create"
	descriptor, err := broker.Create(ctx, id, authorize)
	if err != nil {
		return err
	}
	stage = "claim"
	if err := broker.Claim(ctx, id, authorize); err != nil {
		return err
	}
	stage = "ready_send"
	if err := send(ctx, endpoint, message{Type: "TRANSPORT_READY", SetupID: id, Descriptor: &descriptor}); err != nil {
		return err
	}
	stage = "bye_receive"
	if _, err := receive(ctx, endpoint, "BYE", id); err != nil {
		return err
	}
	stage = "descriptor_expiry"
	if !time.Now().Before(descriptor.ExpiresAt) {
		return roombroker.Code("descriptor_expired")
	}
	stage = "authorize"
	if _, err := authorize(ctx); err != nil {
		return err
	}
	stage = "bye_send"
	if err := send(ctx, endpoint, message{Type: "BYE", SetupID: id}); err != nil {
		return err
	}
	handedOff = true
	for _, notify := range onHandoff {
		notify()
	}
	linger, cancel := context.WithTimeout(ctx, 3*time.Second)
	defer cancel()
	_, _ = receive(linger, endpoint, "BYE", id)
	return nil
}

func requestTransport(ctx context.Context, endpoint familysession.PacketEndpoint) (result roombroker.Descriptor, failure error) {
	raw, err := endpoint.Recv(ctx)
	var hello message
	if err != nil || strictJSON(raw, &hello, 256) != nil || hello.Type != "HELLO" || !hexID(hello.SetupID, 32) || hello.Descriptor != nil {
		return roombroker.Descriptor{}, roombroker.Code("bootstrap_protocol_rejected")
	}
	trace := sessiontrace.New(hello.SetupID, nil)
	sessiontrace.Publish(ctx, trace)
	trace.Add("DESCRIPTOR", "STARTED", "NONE")
	defer func() {
		if failure != nil {
			trace.Add("DESCRIPTOR", "FAILED", "RECOVERY_DESCRIPTOR_FAILED")
		} else {
			trace.Add("DESCRIPTOR", "ISSUED", "NONE")
		}
	}()
	if err := send(ctx, endpoint, message{Type: "REQUEST_TRANSPORT", SetupID: hello.SetupID}); err != nil {
		return roombroker.Descriptor{}, err
	}
	ready, err := receive(ctx, endpoint, "TRANSPORT_READY", hello.SetupID)
	if err != nil {
		return roombroker.Descriptor{}, err
	}
	descriptor := ready.Descriptor
	if descriptor == nil || descriptor.SetupID != hello.SetupID || descriptor.Transport != "telemost-webrtc" || !roombroker.ValidJoinURL(descriptor.JoinURL) || !time.Now().Before(descriptor.ExpiresAt) || time.Until(descriptor.ExpiresAt) > 2*time.Minute {
		return roombroker.Descriptor{}, roombroker.Code("descriptor_rejected")
	}
	if err := send(ctx, endpoint, message{Type: "BYE", SetupID: hello.SetupID}); err != nil {
		return roombroker.Descriptor{}, err
	}
	if _, err := receive(ctx, endpoint, "BYE", hello.SetupID); err != nil {
		return roombroker.Descriptor{}, err
	}
	if !time.Now().Before(descriptor.ExpiresAt) {
		return roombroker.Descriptor{}, roombroker.Code("descriptor_expired")
	}
	_ = send(ctx, endpoint, message{Type: "BYE", SetupID: hello.SetupID})
	return *descriptor, nil
}

func OpenServer(ctx context.Context, endpoint familysession.PacketEndpoint, path string, broker *roombroker.Broker, event func(string), failures ...func(ExchangeFailure)) {
	raw, err := roombroker.LoadCredentials(path)
	if err != nil {
		return
	}
	defer clear(raw)
	admission, cancel := context.WithTimeout(ctx, AdmissionTimeout)
	stop := context.AfterFunc(admission, func() { endpoint.Close() })
	secured, err := familysession.Open(ctx, endpoint, raw, true)
	stop()
	cancel()
	if err != nil {
		return
	}
	defer secured.Close()
	event("bootstrap_family_auth")
	err = exchange(ctx, secured, broker, roombroker.SessionAuthorizer(path, secured.ConnectionState()), func(failure ExchangeFailure) {
		for _, observe := range failures {
			if observe != nil {
				observe(failure)
			}
		}
	}, func() { event("bootstrap_handoff") })
	if err != nil {
		event("bootstrap_exchange_failed")
	}
}

func Recover(ctx context.Context, directory Directory, raw []byte, event func(string), networks ...*underlay.Network) (roombroker.Descriptor, error) {
	var credentials familysession.Credentials
	if json.Unmarshal(raw, &credentials) != nil {
		return roombroker.Descriptor{}, roombroker.Code("credentials_rejected")
	}
	encoded, _ := json.Marshal(directory)
	if _, err := ParseDirectory(encoded, credentials.Family, credentials.Gateway, time.Now()); err != nil {
		return roombroker.Descriptor{}, err
	}
	ctx, cancel := context.WithTimeout(ctx, ExchangeTimeout)
	defer cancel()
	config := telemost.Config{RoomURL: directory.Seeds[0].JoinURL, DisplayName: "Family bootstrap device", Mode: telemost.ModeVP8, MaxVideoTracks: 4}
	if len(networks) > 0 {
		config.Underlay = networks[0]
	}
	carrier, err := telemost.New(ctx, config)
	if err != nil {
		return roombroker.Descriptor{}, roombroker.Code("bootstrap_carrier")
	}
	defer carrier.Close()
	connecting, stop := context.WithTimeout(ctx, ConnectTimeout)
	err = carrier.Connect(connecting)
	stop()
	if err != nil {
		return roombroker.Descriptor{}, roombroker.Code("bootstrap_connect_timeout")
	}
	event("bootstrap_carrier_connected")
	descriptor, err := recoverCarrier(ctx, carrier, raw, event)
	if err == nil && descriptor.JoinURL == directory.Seeds[0].JoinURL {
		return roombroker.Descriptor{}, roombroker.Code("dedicated_room_required")
	}
	if err == nil && !time.Now().Before(descriptor.ExpiresAt) {
		return roombroker.Descriptor{}, roombroker.Code("descriptor_expired")
	}
	return descriptor, err
}

func recoverCarrier(ctx context.Context, carrier familysession.PacketEndpoint, raw []byte, event func(string)) (roombroker.Descriptor, error) {
	ctx, cancel := context.WithTimeout(ctx, ExchangeTimeout)
	defer cancel()
	defer carrier.Close()
	admission, stop := context.WithTimeout(ctx, AdmissionTimeout)
	defer stop()
	session, err := connectLease(admission, carrier)
	if err != nil {
		return roombroker.Descriptor{}, err
	}
	defer session.Close()
	readerDone := make(chan struct{})
	go func() { defer close(readerDone); readLease(ctx, session) }()
	defer func() { cancel(); carrier.Close(); <-readerDone }()
	closeAdmission := context.AfterFunc(admission, func() { session.Close() })
	secured, err := familysession.Open(ctx, session, raw, false)
	closeAdmission()
	stop()
	if err != nil {
		return roombroker.Descriptor{}, roombroker.Code("bootstrap_auth_failed")
	}
	defer secured.Close()
	event("bootstrap_family_auth")
	descriptor, err := requestTransport(ctx, secured)
	if err == nil {
		event("bootstrap_descriptor_received")
	}
	return descriptor, err
}
