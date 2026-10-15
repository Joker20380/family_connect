package telemost

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"net"
	"syscall"

	"github.com/gorilla/websocket"
)

type SignalingReadFailure struct {
	Kind          string `json:"error_kind"`
	CloseCode     int    `json:"close_code,omitempty"`
	ContextState  string `json:"context_state"`
	CarrierClosed bool   `json:"carrier_closed_at_observation"`
}

func (failure SignalingReadFailure) Sanitized() SignalingReadFailure {
	switch failure.Kind {
	case "WS_NORMAL_CLOSE", "WS_ABNORMAL_CLOSE", "WS_CLOSE", "WS_READ_LIMIT", "JSON_SYNTAX", "JSON_TYPE", "EOF", "UNEXPECTED_EOF", "CONTEXT_CANCELLED", "CONTEXT_DEADLINE", "NET_CLOSED", "CONNECTION_RESET", "BROKEN_PIPE", "IO_TIMEOUT", "NET_IO", "UNKNOWN":
	default:
		failure.Kind = "UNKNOWN"
	}
	if failure.Kind != "WS_NORMAL_CLOSE" && failure.Kind != "WS_ABNORMAL_CLOSE" && failure.Kind != "WS_CLOSE" || failure.CloseCode < 1000 || failure.CloseCode > 4999 {
		failure.CloseCode = 0
	}
	switch failure.ContextState {
	case "ACTIVE", "CANCELLED", "DEADLINE", "UNAVAILABLE":
	default:
		failure.ContextState = "UNAVAILABLE"
	}
	return failure
}

func classifySignalingRead(err error, ctx context.Context, closed bool) SignalingReadFailure {
	failure := SignalingReadFailure{Kind: "UNKNOWN", ContextState: "UNAVAILABLE", CarrierClosed: closed}
	if ctx != nil {
		failure.ContextState = "ACTIVE"
		if errors.Is(context.Cause(ctx), context.DeadlineExceeded) {
			failure.ContextState = "DEADLINE"
		} else if ctx.Err() != nil {
			failure.ContextState = "CANCELLED"
		}
	}
	var closeError *websocket.CloseError
	var syntaxError *json.SyntaxError
	var typeError *json.UnmarshalTypeError
	var networkError net.Error
	switch {
	case errors.As(err, &closeError):
		failure.Kind, failure.CloseCode = "WS_CLOSE", closeError.Code
		if closeError.Code == websocket.CloseNormalClosure || closeError.Code == websocket.CloseGoingAway {
			failure.Kind = "WS_NORMAL_CLOSE"
		} else if closeError.Code == websocket.CloseAbnormalClosure {
			failure.Kind = "WS_ABNORMAL_CLOSE"
		}
	case errors.Is(err, websocket.ErrReadLimit):
		failure.Kind = "WS_READ_LIMIT"
	case errors.As(err, &syntaxError):
		failure.Kind = "JSON_SYNTAX"
	case errors.As(err, &typeError):
		failure.Kind = "JSON_TYPE"
	case errors.Is(err, context.DeadlineExceeded):
		failure.Kind = "CONTEXT_DEADLINE"
	case errors.Is(err, context.Canceled):
		failure.Kind = "CONTEXT_CANCELLED"
	case errors.Is(err, io.ErrUnexpectedEOF):
		failure.Kind = "UNEXPECTED_EOF"
	case errors.Is(err, io.EOF):
		failure.Kind = "EOF"
	case errors.Is(err, net.ErrClosed):
		failure.Kind = "NET_CLOSED"
	case errors.Is(err, syscall.ECONNRESET):
		failure.Kind = "CONNECTION_RESET"
	case errors.Is(err, syscall.EPIPE):
		failure.Kind = "BROKEN_PIPE"
	case errors.As(err, &networkError):
		failure.Kind = "NET_IO"
		if networkError.Timeout() {
			failure.Kind = "IO_TIMEOUT"
		}
	}
	return failure.Sanitized()
}

func (s *Session) retainSignalingReadFailure(err error) {
	failure := classifySignalingRead(err, s.ctx, s.closed.Load())
	s.errMu.Lock()
	defer s.errMu.Unlock()
	if s.signalingReadFailure.Kind == "" {
		s.signalingReadFailure = failure
	}
}

func (s *Session) SignalingReadFailure() SignalingReadFailure {
	s.errMu.Lock()
	defer s.errMu.Unlock()
	return s.signalingReadFailure
}
