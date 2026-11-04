package telemost

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"syscall"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/gorilla/websocket"
)

func TestSignalingReadErrorClassPreservesLegacyFailure(test *testing.T) {
	for _, fixture := range []struct {
		class string
		err   error
		state string
	}{
		{"TIMEOUT", context.DeadlineExceeded, "read_timeout"},
		{"WEBSOCKET_CLOSE", &websocket.CloseError{Code: 1008, Text: "secret-token"}, "close_code_1008"},
		{"INVALID_JSON", &json.SyntaxError{}, "invalid_json"},
		{"INVALID_JSON_TYPE", &json.UnmarshalTypeError{Value: "secret-value"}, "read_error"},
		{"READ_LIMIT", websocket.ErrReadLimit, "read_error"},
		{"CONNECTION_RESET", &net.OpError{Op: "read", Net: "secret-network", Err: syscall.ECONNRESET}, "read_error"},
		{"CONNECTION_ABORTED", syscall.ECONNABORTED, "read_error"},
		{"LOCAL_CLOSED", net.ErrClosed, "read_error"},
		{"EOF", io.EOF, "read_error"},
		{"UNEXPECTED_EOF", io.ErrUnexpectedEOF, "read_error"},
		{"NETWORK_ERROR", &net.OpError{Op: "read", Net: "secret-network", Err: errors.New("secret-error")}, "read_error"},
		{"OTHER", errors.New("secret-url: connection reset by peer"), "read_error"},
	} {
		test.Run(fixture.class, func(test *testing.T) {
			session := testSession(test)
			session.cfg.Trace = sessiontrace.New(strings.Repeat("ab", 32), nil)
			session.recordSignalingReadFailure(fmt.Errorf("secret-wrapper: %w", fixture.err))
			event := session.Stats().Evidence[0]
			first := session.cfg.Trace.Snapshot().FirstFailure
			if event.ReadErrorClass != fixture.class || event.State != fixture.state || first == nil || first.ReadErrorClass != fixture.class {
				test.Fatal("typed class or legacy failure lost")
			}
			session.cfg.Trace.Add("CLEANUP", "FAILED", "RECOVERY_CLEANUP_FAILED")
			for range sessiontrace.Limit + 1 {
				session.cfg.Trace.Add("HEARTBEAT", "TX", "NONE")
			}
			if session.cfg.Trace.Snapshot().FirstFailure.ReadErrorClass != fixture.class {
				test.Fatal("first read cause lost after trace rollover")
			}
			raw, err := json.Marshal([]any{session.Stats(), session.cfg.Trace.Snapshot()})
			if err != nil || strings.Contains(string(raw), "secret") {
				test.Fatal("untrusted error text escaped")
			}
		})
	}
}

func TestSignalingReaderClassifiesAndStillCloses(test *testing.T) {
	for _, fixture := range []struct {
		class string
		body  string
		state string
	}{
		{"INVALID_JSON", `{"secret": @}`, "invalid_json"},
		{"INVALID_JSON_TYPE", `["secret-token"]`, "read_error"},
		{"READ_LIMIT", strings.Repeat("secret", 32), "read_error"},
	} {
		test.Run(fixture.class, func(test *testing.T) {
			server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
				upgrader := websocket.Upgrader{}
				connection, err := upgrader.Upgrade(writer, request, nil)
				if err != nil {
					return
				}
				defer connection.Close()
				_ = connection.SetWriteDeadline(time.Now().Add(time.Second))
				_ = connection.WriteMessage(websocket.TextMessage, []byte(fixture.body))
				_ = connection.SetReadDeadline(time.Now().Add(time.Second))
				_, _, _ = connection.ReadMessage()
			}))
			defer server.Close()
			connection, response, err := websocket.DefaultDialer.Dial("ws"+strings.TrimPrefix(server.URL, "http"), nil)
			if response != nil && response.Body != nil {
				_ = response.Body.Close()
			}
			if err != nil {
				test.Fatal("local signaling dial failed")
			}
			session := testSession(test)
			session.cfg.Trace = sessiontrace.New(strings.Repeat("ab", 32), nil)
			connection.SetReadLimit(64)
			_ = connection.SetReadDeadline(time.Now().Add(time.Second))
			session.ws = connection
			done := make(chan struct{})
			go func() {
				defer close(done)
				session.signalingLoop()
			}()
			select {
			case <-done:
			case <-time.After(2 * time.Second):
				test.Fatal("signaling reader did not terminate")
			}
			first := session.cfg.Trace.Snapshot().FirstFailure
			if !session.closed.Load() || first == nil || first.ReadErrorClass != fixture.class {
				test.Fatal("reader did not retain cause and fail closed")
			}
			if session.Stats().Evidence[0].State != fixture.state || session.cfg.Trace.Snapshot().FirstClose.CloseSource != "SIGNAL_READ" {
				test.Fatal("legacy close policy changed")
			}
		})
	}
}
