package telemost

import (
	"context"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/gorilla/websocket"
)

func boundaryPair(test *testing.T, encrypted bool) (*websocket.Conn, *websocket.Conn) {
	test.Helper()
	accepted := make(chan *websocket.Conn, 1)
	upgrader := websocket.Upgrader{}
	handler := http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		connection, err := upgrader.Upgrade(writer, request, nil)
		if err == nil {
			accepted <- connection
		}
	})
	var server *httptest.Server
	dialer := *websocket.DefaultDialer
	if encrypted {
		server = httptest.NewTLSServer(handler)
		dialer.TLSClientConfig = server.Client().Transport.(*http.Transport).TLSClientConfig
	} else {
		server = httptest.NewServer(handler)
	}
	test.Cleanup(server.Close)
	client, _, err := dialer.Dial("ws"+strings.TrimPrefix(server.URL, "http"), nil)
	if err != nil {
		test.Fatal(err)
	}
	peer := <-accepted
	test.Cleanup(func() { client.Close(); peer.Close() })
	client.SetReadLimit(wsReadLimit)
	client.SetReadDeadline(time.Now().Add(2 * time.Second))
	return client, peer
}

func boundaryAction(test *testing.T, name string, client, peer *websocket.Conn) {
	test.Helper()
	switch name {
	case "normal_json":
		peer.WriteJSON(map[string]any{"ack": map[string]any{}})
	case "provider_end":
		peer.WriteJSON(map[string]any{"conferenceState": map[string]any{"state": "ended"}})
	case "remote_normal", "remote_policy", "remote_restart":
		code := websocket.CloseNormalClosure
		if name == "remote_policy" {
			code = websocket.ClosePolicyViolation
		}
		if name == "remote_restart" {
			code = websocket.CloseServiceRestart
		}
		peer.WriteControl(websocket.CloseMessage, websocket.FormatCloseMessage(code, "SECRET_URL_TOKEN"), time.Now().Add(time.Second))
	case "remote_eof", "tls_close_notify":
		peer.UnderlyingConn().Close()
	case "partial_frame":
		peer.UnderlyingConn().Write([]byte{0x81, 30, '{'})
		peer.UnderlyingConn().Close()
	case "invalid_frame":
		peer.UnderlyingConn().Write([]byte{0xc1, 2, '{', '}'})
	case "malformed_json":
		peer.WriteMessage(websocket.TextMessage, []byte(`{"SECRET_URL_TOKEN":!}`))
	case "json_type":
		peer.WriteMessage(websocket.TextMessage, []byte(`[]`))
	case "empty_json":
		peer.WriteMessage(websocket.TextMessage, nil)
	case "oversized":
		client.SetReadLimit(8)
		peer.WriteMessage(websocket.TextMessage, []byte(`{"padding":"0123456789"}`))
	case "read_timeout", "no_pong":
		client.SetReadDeadline(time.Now().Add(40 * time.Millisecond))
		if name == "no_pong" {
			client.WriteControl(websocket.PingMessage, nil, time.Now().Add(time.Second))
		}
	case "tcp_reset":
		connection := peer.UnderlyingConn().(*net.TCPConn)
		connection.SetLinger(0)
		connection.Close()
	default:
		test.Fatal("unknown case")
	}
}

func boundaryObservation(session *Session) any {
	method := reflect.ValueOf(session).MethodByName("SignalingReadFailure")
	if !method.IsValid() {
		return nil
	}
	return method.Call(nil)[0].Interface()
}

func TestSignalingBoundaryMatrix(test *testing.T) {
	for _, name := range []string{"normal_json", "remote_normal", "remote_policy", "remote_restart", "remote_eof", "partial_frame", "malformed_json", "json_type", "empty_json", "oversized", "invalid_frame", "read_timeout", "no_pong", "tcp_reset", "tls_close_notify", "provider_end"} {
		test.Run(name, func(test *testing.T) {
			client, peer := boundaryPair(test, name == "tls_close_notify")
			boundaryAction(test, name, client, peer)
			var decoded map[string]any
			underlying := client.ReadJSON(&decoded)
			if (name == "normal_json" || name == "provider_end") != (underlying == nil) {
				test.Fatal("unexpected direct reader result")
			}
			direct := testSession(test)
			if underlying != nil {
				direct.recordSignalingReadFailure(underlying)
			}
			client, peer = boundaryPair(test, name == "tls_close_notify")
			session := testSession(test)
			session.cfg.Trace = sessiontrace.New(strings.Repeat("ab", 32), nil)
			session.ws = client
			boundaryAction(test, name, client, peer)
			session.startWorker(session.signalingLoop)
			if name == "normal_json" {
				limit := time.NewTimer(time.Second)
				defer limit.Stop()
				for session.Stats().SignalingACKs != 1 {
					select {
					case <-limit.C:
						test.Fatal("JSON was not dispatched")
					default:
						time.Sleep(time.Millisecond)
					}
				}
				if session.closed.Load() {
					test.Fatal("normal message closed carrier")
				}
				session.Close()
			} else {
				select {
				case <-session.closeCh:
				case <-time.After(3 * time.Second):
					test.Fatal("reader failed to terminate")
				}
			}
			first := session.cfg.Trace.Snapshot().FirstClose
			if first == nil {
				test.Fatal("missing terminal trace")
			}
			expected := "SIGNAL_READ"
			if name == "normal_json" {
				expected = "UPPER_CLOSE"
			}
			if name == "provider_end" {
				expected = "CONFERENCE_ENDED"
			}
			if first.CloseSource != expected {
				test.Fatal("changed close policy", first.CloseSource)
			}
			_, result := session.Recv(context.Background())
			if result == nil {
				test.Fatal("closed carrier accepted read")
			}
			observation := boundaryObservation(session)
			if observation != nil {
				raw, _ := json.Marshal(observation)
				var observed struct {
					Kind string `json:"error_kind"`
				}
				if json.Unmarshal(raw, &observed) != nil {
					test.Fatal("invalid typed observation")
				}
				expectedKinds := map[string]string{
					"remote_normal": "WS_NORMAL_CLOSE", "remote_policy": "WS_CLOSE", "remote_restart": "WS_CLOSE",
					"remote_eof": "WS_ABNORMAL_CLOSE", "partial_frame": "WS_ABNORMAL_CLOSE", "tls_close_notify": "WS_ABNORMAL_CLOSE",
					"malformed_json": "JSON_SYNTAX", "json_type": "JSON_TYPE", "empty_json": "UNEXPECTED_EOF",
					"oversized": "WS_READ_LIMIT", "invalid_frame": "UNKNOWN", "read_timeout": "IO_TIMEOUT",
					"no_pong": "IO_TIMEOUT", "tcp_reset": "CONNECTION_RESET",
				}
				if observed.Kind != expectedKinds[name] {
					test.Fatal("wrong real WebSocket classification", name, observed.Kind)
				}
			}
			session.Close()
			if !reflect.DeepEqual(observation, boundaryObservation(session)) {
				test.Fatal("cleanup rewrote cause")
			}
			receipt := map[string]any{"case": name, "underlying_type": fmt.Sprintf("%T", underlying), "direct_classification": boundaryObservation(direct), "low_level": observation, "first_close": first.CloseSource, "legacy_error_type": fmt.Sprintf("%T", result), "cleanup_complete": true, "normal_message_dispatched": name == "normal_json"}
			raw, _ := json.Marshal(receipt)
			if strings.Contains(string(raw), "SECRET") {
				test.Fatal("private error leaked")
			}
			test.Log("SIGNAL_MATRIX " + string(raw))
			if destination := os.Getenv("FC_SIGNAL_MATRIX_DIR"); destination != "" {
				if err := os.WriteFile(filepath.Join(destination, name+".json"), raw, 0600); err != nil {
					test.Fatal(err)
				}
			}
		})
	}
}

func TestSignalingBoundaryLocalShutdown(test *testing.T) {
	for _, name := range []string{"local_close", "context_cancel", "context_deadline"} {
		test.Run(name, func(test *testing.T) {
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			if name == "context_deadline" {
				var stop context.CancelFunc
				ctx, stop = context.WithDeadline(ctx, time.Now().Add(80*time.Millisecond))
				defer stop()
			}
			session, err := New(ctx, Config{RoomURL: "test-room", Trace: sessiontrace.New(strings.Repeat("cd", 32), nil)})
			if err != nil {
				test.Fatal(err)
			}
			defer session.Close()
			client, _ := boundaryPair(test, false)
			session.ws = client
			session.startWorker(session.signalingLoop)
			if name == "local_close" {
				session.Close()
			} else if name == "context_cancel" {
				cancel()
			}
			select {
			case <-session.cleanupDone:
			case <-time.After(3 * time.Second):
				test.Fatal("cleanup hung")
			}
			first := session.cfg.Trace.Snapshot().FirstClose
			if first == nil || first.CloseSource == "SIGNAL_READ" {
				test.Fatal("local shutdown became signal failure")
			}
			raw, _ := json.Marshal(map[string]any{"case": name, "first_close": first.CloseSource, "low_level": boundaryObservation(session), "cleanup_complete": true})
			test.Log("SIGNAL_SHUTDOWN " + string(raw))
		})
	}
}
