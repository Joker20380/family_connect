package telemost

import (
	"context"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/gorilla/websocket"
	"github.com/pion/webrtc/v4"
)

type transportFunc func(*http.Request) (*http.Response, error)

func (function transportFunc) RoundTrip(request *http.Request) (*http.Response, error) {
	return function(request)
}

func testSession(t *testing.T) *Session {
	t.Helper()
	session, err := New(context.Background(), Config{RoomURL: "test-room", ConnectTimeout: 100 * time.Millisecond})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = session.Close() })
	return session
}

func TestRoomAndSignalingValidation(t *testing.T) {
	for _, room := range []string{"", "http://telemost.yandex.ru/j/test", "https://evil.invalid/j/test", "https://telemost.yandex.ru/j/test?token=secret", "../test", "https://telemost.yandex.ru/j/"} {
		if validRoom(room) {
			t.Fatal("invalid room accepted")
		}
	}
	for _, address := range []string{"ws://media.yandex.net/", "wss://localhost/", "wss://media.yandex.net.evil.invalid/", "wss://user:pass@media.yandex.net/", "wss://media.yandex.net:8443/"} {
		if validSignalingURL(address) {
			t.Fatal("unsafe signaling accepted")
		}
	}
	if !validRoom("test-room") || !validSignalingURL("wss://media.yandex.net/signal") {
		t.Fatal("valid URL rejected")
	}
}

func TestHTTPFlowAndRedaction(t *testing.T) {
	for _, status := range []int{200, 202, 403, 404, 500} {
		client := &http.Client{Transport: transportFunc(func(request *http.Request) (*http.Response, error) {
			if request.Method != "GET" || !strings.HasSuffix(request.URL.Path, "/connection") || request.URL.Query().Get("waiting_room_supported") != "true" {
				t.Error("wrong request")
			}
			body := `{"room_id":"test-room","peer_id":"peer","credentials":"secret","client_configuration":{"media_server_url":"wss://media.yandex.net/signal"}}`
			return &http.Response{StatusCode: status, Body: io.NopCloser(strings.NewReader(body)), Header: make(http.Header)}, nil
		})}
		info, err := NewAuth(client).FetchConnection(context.Background(), "test-room", "synthetic-test")
		if status == 200 {
			if err != nil || info.PeerID != "peer" {
				t.Fatal(err)
			}
		} else if err == nil || strings.Contains(err.Error(), "secret") {
			t.Fatal("unsafe error")
		}
	}
	client := &http.Client{Transport: transportFunc(func(*http.Request) (*http.Response, error) { return nil, errors.New("secret-url") })}
	_, err := NewAuth(client).FetchConnection(context.Background(), "test-room", "test")
	if err == nil || strings.Contains(err.Error(), "secret") {
		t.Fatal("network error leaked")
	}
}

func TestConnectFailureAndCancellationCleanup(t *testing.T) {
	session := testSession(t)
	session.auth.Client = &http.Client{Transport: transportFunc(func(request *http.Request) (*http.Response, error) {
		<-request.Context().Done()
		return nil, request.Context().Err()
	})}
	if err := session.Connect(context.Background()); err == nil {
		t.Fatal("unexpected connect")
	}
	select {
	case <-session.cleanupDone:
	case <-time.After(time.Second):
		t.Fatal("cleanup timeout")
	}
	if err := session.Send([]byte{1}); err != ErrClosed {
		t.Fatal(err)
	}
}

func TestConcurrentCloseAndReady(t *testing.T) {
	session := testSession(t)
	session.subReady.Store(true)
	session.pubReady.Store(true)
	var group sync.WaitGroup
	for range 20 {
		group.Add(1)
		go func() {
			defer group.Done()
			session.maybeConnected()
			session.signalClosed(errors.New("closed"))
			_ = session.Stats()
			_ = session.Close()
		}()
	}
	group.Wait()
}

func TestSendAndRecvBackpressure(t *testing.T) {
	session := testSession(t)
	if session.Send([]byte{1}) == nil {
		t.Fatal("send before ready")
	}
	session.subReady.Store(true)
	session.pubReady.Store(true)
	for range cap(session.sendQueue) {
		session.sendQueue <- []byte{1}
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Millisecond)
	defer cancel()
	if err := session.SendContext(ctx, []byte{1}); !errors.Is(err, context.DeadlineExceeded) {
		t.Fatal(err)
	}
	for range cap(session.recvQueue) + 1 {
		session.deliver([]byte{1})
	}
	if !session.closed.Load() {
		t.Fatal("queue overflow did not fail closed")
	}
}

func TestVP8ModeRejectsDataChannelDelivery(t *testing.T) {
	session := testSession(t)
	fragments, _ := encodeFragments(session.senderID+1, 1, []byte{1, 0, 255})
	session.onDataChannelMessage(webrtc.DataChannelMessage{Data: fragments[0]})
	if len(session.recvQueue) != 0 || session.Stats().BytesReceived != 0 {
		t.Fatal("DataChannel falsely counted as VP8")
	}
}

func TestSignalingClosureAndInvalidJSON(t *testing.T) {
	for _, content := range []string{"{", `{"conferenceEnded":{}}`, `{"subscriberSdpOffer":{"sdp":"invalid-secret-sdp"}}`, ""} {
		t.Run(content, func(t *testing.T) {
			upgrader := websocket.Upgrader{}
			server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
				connection, err := upgrader.Upgrade(writer, request, nil)
				if err != nil {
					return
				}
				defer connection.Close()
				if content != "" {
					_ = connection.WriteMessage(websocket.TextMessage, []byte(content))
				}
			}))
			defer server.Close()
			session := testSession(t)
			connection, _, err := websocket.DefaultDialer.Dial("ws"+strings.TrimPrefix(server.URL, "http"), nil)
			if err != nil {
				t.Fatal(err)
			}
			session.ws = connection
			session.startWorker(session.signalingLoop)
			select {
			case <-session.closeCh:
			case <-time.After(time.Second):
				t.Fatal("signaling did not stop")
			}
			select {
			case <-session.connected:
				t.Fatal("failure reported connected")
			default:
			}
			if strings.Contains(session.failure().Error(), "secret") {
				t.Fatal("SDP leaked")
			}
		})
	}
}

func TestEarlyICEBoundAndEndParser(t *testing.T) {
	session := testSession(t)
	if err := session.setupPeerConnections(webrtc.Configuration{}); err != nil {
		t.Fatal(err)
	}
	candidate := map[string]any{"candidate": "candidate:1 1 udp 1 192.0.2.1 1234 typ host", "target": "SUBSCRIBER", "sdpMlineIndex": float64(0), "sdpMid": "0"}
	for range 128 {
		session.handleRemoteICE(candidate)
	}
	if len(session.pendingICE["SUBSCRIBER"]) != 128 {
		t.Fatal("early ICE lost")
	}
	session.handleRemoteICE(candidate)
	if !session.closed.Load() {
		t.Fatal("unbounded ICE")
	}
	for _, state := range []string{"closed", "ENDED", "terminated"} {
		if !isEndMessage(map[string]any{"conferenceState": map[string]any{"state": state}}) {
			t.Fatal("end missed")
		}
	}
	if isEndMessage(map[string]any{"conferenceState": "bad"}) {
		t.Fatal("malformed end")
	}
}

func TestSignalingHelloAndSDPSequence(t *testing.T) {
	messages := make(chan map[string]any, 8)
	upgrader := websocket.Upgrader{}
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		connection, err := upgrader.Upgrade(writer, request, nil)
		if err != nil {
			return
		}
		defer connection.Close()
		for {
			var message map[string]any
			if err := connection.ReadJSON(&message); err != nil {
				return
			}
			select {
			case messages <- message:
			default:
				return
			}
		}
	}))
	defer server.Close()
	session := testSession(t)
	defer session.Close()
	connection, _, err := websocket.DefaultDialer.Dial("ws"+strings.TrimPrefix(server.URL, "http"), nil)
	if err != nil {
		t.Fatal(err)
	}
	session.ws = connection
	if err := session.setupPeerConnections(webrtc.Configuration{}); err != nil {
		t.Fatal(err)
	}
	if err := session.setupTransport(); err != nil {
		t.Fatal(err)
	}
	if err := session.sendHello(); err != nil {
		t.Fatal(err)
	}
	api, err := newWebRTCAPI()
	if err != nil {
		t.Fatal(err)
	}
	remote, err := api.NewPeerConnection(webrtc.Configuration{})
	if err != nil {
		t.Fatal(err)
	}
	defer remote.Close()
	if _, err := remote.AddTransceiverFromKind(webrtc.RTPCodecTypeVideo, webrtc.RTPTransceiverInit{Direction: webrtc.RTPTransceiverDirectionSendonly}); err != nil {
		t.Fatal(err)
	}
	offer, err := remote.CreateOffer(nil)
	if err != nil {
		t.Fatal(err)
	}
	if err := session.handleSubscriberOffer(map[string]any{"sdp": offer.SDP, "pcSeq": float64(7)}, "test-uid", true); err != nil {
		t.Fatal(err)
	}
	foundAnswer, foundPublisher, foundHello := false, false, false
	for range 5 {
		select {
		case message := <-messages:
			if hello, ok := message["hello"].(map[string]any); ok {
				foundHello = hello["disablePublisher"] == false && hello["sendVideo"] == true
			}
			if answer, ok := message["subscriberSdpAnswer"].(map[string]any); ok {
				foundAnswer = answer["pcSeq"] == float64(7)
			}
			if _, ok := message["publisherSdpOffer"].(map[string]any); ok {
				foundPublisher = true
			}
		case <-time.After(time.Second):
			t.Fatal("missing signaling message")
		}
	}
	if !foundAnswer || !foundPublisher || !foundHello {
		t.Fatal("signaling schema regression")
	}
}

func TestApplicationHeartbeatAndPongAcknowledgment(t *testing.T) {
	acknowledged := make(chan bool, 1)
	upgrader := websocket.Upgrader{}
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		connection, err := upgrader.Upgrade(writer, request, nil)
		if err != nil {
			return
		}
		defer connection.Close()
		_ = connection.SetReadDeadline(time.Now().Add(8 * time.Second))
		var ping map[string]any
		if connection.ReadJSON(&ping) != nil || !hasKey(ping, "ping") || ping["uid"] == "" {
			return
		}
		if connection.WriteJSON(map[string]any{"uid": "fixture-pong", "pong": map[string]any{}}) != nil {
			return
		}
		var ack map[string]any
		if connection.ReadJSON(&ack) != nil {
			return
		}
		acknowledged <- ack["uid"] == "fixture-pong" && hasKey(ack, "ack")
		var ignored any
		_ = connection.ReadJSON(&ignored)
	}))
	defer server.Close()
	session := testSession(t)
	defer session.Close()
	connection, _, err := websocket.DefaultDialer.Dial("ws"+strings.TrimPrefix(server.URL, "http"), nil)
	if err != nil {
		t.Fatal(err)
	}
	session.ws = connection
	session.startWorker(session.signalingLoop)
	session.startWorker(session.heartbeatLoop)
	select {
	case ok := <-acknowledged:
		if !ok || session.Stats().ApplicationPongs != 1 {
			t.Fatal("application heartbeat protocol mismatch")
		}
	case <-time.After(7 * time.Second):
		t.Fatal("application heartbeat missing")
	}
	if err := session.Close(); err != nil {
		t.Fatal(err)
	}
}
