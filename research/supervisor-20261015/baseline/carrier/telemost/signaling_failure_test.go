package telemost

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"os"
	"strings"
	"sync"
	"syscall"
	"testing"

	"github.com/gorilla/websocket"
)

func TestSignalingLowLevelClassifier(test *testing.T) {
	for _, item := range []struct {
		name string
		err  error
		kind string
		code int
	}{
		{"eof", io.EOF, "EOF", 0},
		{"partial", io.ErrUnexpectedEOF, "UNEXPECTED_EOF", 0},
		{"cancel", context.Canceled, "CONTEXT_CANCELLED", 0},
		{"deadline", context.DeadlineExceeded, "CONTEXT_DEADLINE", 0},
		{"closed", net.ErrClosed, "NET_CLOSED", 0},
		{"reset", syscall.ECONNRESET, "CONNECTION_RESET", 0},
		{"pipe", syscall.EPIPE, "BROKEN_PIPE", 0},
		{"timeout", &net.OpError{Op: "read", Err: os.ErrDeadlineExceeded}, "IO_TIMEOUT", 0},
		{"network", &net.OpError{Op: "read", Err: errors.New("SECRET")}, "NET_IO", 0},
		{"syntax", &json.SyntaxError{}, "JSON_SYNTAX", 0},
		{"type", &json.UnmarshalTypeError{Value: "SECRET"}, "JSON_TYPE", 0},
		{"limit", websocket.ErrReadLimit, "WS_READ_LIMIT", 0},
		{"normal", &websocket.CloseError{Code: 1000, Text: "SECRET"}, "WS_NORMAL_CLOSE", 1000},
		{"abnormal", &websocket.CloseError{Code: 1006, Text: "SECRET"}, "WS_ABNORMAL_CLOSE", 1006},
		{"policy", &websocket.CloseError{Code: 1008, Text: "SECRET"}, "WS_CLOSE", 1008},
		{"provider_code", &websocket.CloseError{Code: 4008, Text: "SECRET expired timeout"}, "WS_CLOSE", 4008},
		{"tls_alert_type_only", tls.AlertError(40), "UNKNOWN", 0},
		{"tls_record_type_only", tls.RecordHeaderError{Msg: "SECRET"}, "UNKNOWN", 0},
		{"unknown", errors.New("SECRET timeout expired ws: close 1000"), "UNKNOWN", 0},
	} {
		test.Run(item.name, func(test *testing.T) {
			for _, err := range []error{item.err, fmt.Errorf("SECRET wrapper %w", item.err)} {
				value := classifySignalingRead(err, context.Background(), false)
				if value.Kind != item.kind || value.CloseCode != item.code || value.ContextState != "ACTIVE" {
					test.Fatal("wrong safe mapping", value)
				}
				raw, _ := json.Marshal(value)
				if strings.Contains(string(raw), "SECRET") {
					test.Fatal("leak")
				}
			}
		})
	}
	ctx, cancel := context.WithCancelCause(context.Background())
	cancel(errors.New("SECRET cause"))
	if classifySignalingRead(io.EOF, ctx, true).ContextState != "CANCELLED" {
		test.Fatal("custom cause escaped")
	}
	value := SignalingReadFailure{Kind: "SECRET", ContextState: "SECRET", CloseCode: 9000}.Sanitized()
	if value.Kind != "UNKNOWN" || value.ContextState != "UNAVAILABLE" || value.CloseCode != 0 {
		test.Fatal("unsafe record")
	}
}

func TestSignalingLowLevelFirstImmutable(test *testing.T) {
	session := testSession(test)
	session.retainSignalingReadFailure(&websocket.CloseError{Code: 1008, Text: "SECRET"})
	first := session.SignalingReadFailure()
	var workers sync.WaitGroup
	for range 64 {
		workers.Add(1)
		go func() {
			defer workers.Done()
			session.retainSignalingReadFailure(context.Canceled)
			_ = session.SignalingReadFailure()
		}()
	}
	workers.Wait()
	session.Close()
	if session.SignalingReadFailure() != first {
		test.Fatal("late cleanup replaced first")
	}
	copy := session.SignalingReadFailure()
	copy.Kind = "SECRET"
	if session.SignalingReadFailure() != first {
		test.Fatal("mutable snapshot")
	}
}
