package telemost

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"strings"
	"syscall"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/gorilla/websocket"
	"github.com/pion/webrtc/v4"
)

func (s *Session) recordSignalingReadFailure(err error) {
	reason := "SIGNAL_WS_CLOSE"
	event := Evidence{Stage: "WS_FAIL", State: "read_error", ReadErrorClass: signalingReadErrorClass(err)}
	var networkError net.Error
	var closeError *websocket.CloseError
	var syntaxError *json.SyntaxError
	switch {
	case errors.As(err, &networkError) && networkError.Timeout():
		event.State = "read_timeout"
		reason = "HEARTBEAT_TIMEOUT"
	case errors.As(err, &closeError):
		event.State = fmt.Sprintf("close_code_%d", closeError.Code)
		for _, keyword := range []string{"ping", "timeout", "duplicate", "expired", "inactivity", "shutdown", "restart", "invalid", "ack", "idle", "session"} {
			if strings.Contains(strings.ToLower(closeError.Text), keyword) {
				event.ReasonKeywords = append(event.ReasonKeywords, keyword)
			}
		}
	case errors.As(err, &syntaxError):
		event.Stage = "SIGNALING_PROTOCOL_FAIL"
		event.State = "invalid_json"
	}
	trace := sessiontrace.Event{Stage: "WEBSOCKET", State: "CLOSED", Reason: reason, CloseReason: "READ_ERROR", ReadErrorClass: event.ReadErrorClass}
	if closeError != nil {
		trace.CloseCode = closeError.Code
		if len(event.ReasonKeywords) > 0 {
			trace.CloseReason = event.ReasonKeywords[0]
		}
	}
	if reason == "HEARTBEAT_TIMEOUT" {
		trace.Stage = "LIVENESS"
		trace.CloseReason = "READ_TIMEOUT"
		trace.HeartbeatKind = "WEBSOCKET"
	}
	if syntaxError != nil {
		trace.CloseReason = "INVALID_MESSAGE"
	}
	s.cfg.Trace.Record(trace)
	s.recordEvidence(event)
}

func signalingReadErrorClass(err error) string {
	var networkError net.Error
	var closeError *websocket.CloseError
	var syntaxError *json.SyntaxError
	var typeError *json.UnmarshalTypeError
	switch {
	case errors.As(err, &networkError) && networkError.Timeout():
		return "TIMEOUT"
	case errors.As(err, &closeError):
		return "WEBSOCKET_CLOSE"
	case errors.As(err, &syntaxError):
		return "INVALID_JSON"
	case errors.As(err, &typeError):
		return "INVALID_JSON_TYPE"
	case errors.Is(err, websocket.ErrReadLimit):
		return "READ_LIMIT"
	case errors.Is(err, syscall.ECONNRESET):
		return "CONNECTION_RESET"
	case errors.Is(err, syscall.ECONNABORTED):
		return "CONNECTION_ABORTED"
	case errors.Is(err, net.ErrClosed):
		return "LOCAL_CLOSED"
	case errors.Is(err, io.EOF):
		return "EOF"
	case errors.Is(err, io.ErrUnexpectedEOF):
		return "UNEXPECTED_EOF"
	case errors.As(err, &networkError):
		return "NETWORK_ERROR"
	default:
		return "OTHER"
	}
}

type Evidence struct {
	UTC            string   `json:"utc"`
	Stage          string   `json:"stage"`
	Target         string   `json:"target,omitempty"`
	State          string   `json:"state,omitempty"`
	LocalType      string   `json:"local_type,omitempty"`
	RemoteType     string   `json:"remote_type,omitempty"`
	Protocol       string   `json:"protocol,omitempty"`
	TURNUsed       *bool    `json:"turn_used,omitempty"`
	ReasonKeywords []string `json:"reason_keywords,omitempty"`
	ReadErrorClass string   `json:"read_error_class,omitempty"`
}

type MediaStats struct {
	SamplesWritten uint64
	RTPReceived    uint64
	EmptyRTP       uint64
	SequenceGaps   uint64
	FramesReceived uint64
	BinaryFrames   uint64
}

func (s *Session) recordEvidence(event Evidence) {
	s.traceEvidence(event)
	event.UTC = time.Now().UTC().Format(time.RFC3339Nano)
	s.statsMu.Lock()
	defer s.statsMu.Unlock()
	if len(s.evidence) < 128 {
		s.evidence = append(s.evidence, event)
	} else {
		s.evidenceDropped++
	}
}

func (s *Session) observePair(target string, pair *webrtc.ICECandidatePair) {
	if pair == nil || pair.Local == nil || pair.Remote == nil {
		return
	}
	relay := pair.Local.Typ == webrtc.ICECandidateTypeRelay || pair.Remote.Typ == webrtc.ICECandidateTypeRelay
	s.recordEvidence(Evidence{Stage: "ICE_SELECTED_PAIR", Target: target,
		LocalType: pair.Local.Typ.String(), RemoteType: pair.Remote.Typ.String(),
		Protocol: pair.Local.Protocol.String(), TURNUsed: &relay})
}
