package sessiondiag

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"io"
	"net"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/reliablestream"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
	"github.com/Joker20380/family_connect/carrier/telemost"
)

type Report struct {
	SessionTag       string `json:"session_tag"`
	TerminalReason   string `json:"terminal_reason"`
	TerminalAtMS     int64  `json:"terminal_at_ms"`
	ObservedAtMS     int64  `json:"observed_at_ms"`
	ReliableTerminal string `json:"reliable_terminal"`
	SignalingFailure string `json:"signaling_failure"`
	ICEFailure       string `json:"ice_failure"`
	EvidenceDropped  uint64 `json:"evidence_dropped"`
	SubscriberState  string `json:"subscriber_state"`
	PublisherState   string `json:"publisher_state"`
	Retransmissions  uint64 `json:"retransmissions"`
	RecoveryTimeouts uint64 `json:"recovery_timeouts"`
	ReceivedFrames   uint64 `json:"received_frames"`
	SentFrames       uint64 `json:"sent_frames"`
	ProtocolErrors   uint64 `json:"protocol_errors"`
	DNSResponses     uint64 `json:"dns_responses"`
	DNSErrors        uint64 `json:"dns_errors"`
	OpenOK           uint64 `json:"tcp_open_ok"`
	OpenErrors       uint64 `json:"tcp_open_errors"`
	SentBytes        uint64 `json:"sent_bytes"`
	ReceivedBytes    uint64 `json:"received_bytes"`
}

func Reason(err error) string {
	var network net.Error
	switch {
	case err == nil:
		return "NONE"
	case errors.Is(err, reliablestream.ErrExhausted):
		return "RELIABLE_EXHAUSTED"
	case errors.Is(err, reliablestream.ErrProtocol):
		return "RELIABLE_PROTOCOL"
	case errors.Is(err, reliablestream.ErrReset):
		return "REMOTE_RESET"
	case errors.Is(err, reliablestream.ErrClosed):
		return "RELIABLE_CLOSED"
	case errors.Is(err, familysession.ErrRejected):
		return "FAMILY_REJECTED"
	case errors.Is(err, tcpforward.ErrProtocol):
		return "MUX_PROTOCOL"
	case errors.Is(err, context.DeadlineExceeded):
		return "DEADLINE"
	case errors.Is(err, context.Canceled):
		return "CANCELLED"
	case errors.Is(err, io.EOF), errors.Is(err, io.ErrUnexpectedEOF):
		return "EOF"
	case errors.Is(err, net.ErrClosed), errors.Is(err, io.ErrClosedPipe):
		return "IO_CLOSED"
	case errors.As(err, &network):
		if network.Timeout() {
			return "NETWORK_TIMEOUT"
		}
		return "NETWORK_ERROR"
	default:
		return "UNKNOWN"
	}
}

func choice(value string, allowed ...string) string {
	for _, candidate := range allowed {
		if value == candidate {
			return value
		}
	}
	return "UNKNOWN"
}

func Capture(setupID string, err error, terminalAt time.Time, reliable reliablestream.Stats, media telemost.Stats, mux tcpforward.MuxStats) Report {
	report := Report{TerminalReason: Reason(err), ObservedAtMS: time.Now().UnixMilli(),
		ReliableTerminal: choice(reliable.Terminal, "", "closed", "recovery_exhausted", "protocol_violation", "remote_reset", "cancelled", "carrier_closed"),
		SignalingFailure: "NONE", ICEFailure: "NONE", EvidenceDropped: media.EvidenceDropped,
		SubscriberState: choice(media.SubscriberState, "new", "connecting", "connected", "disconnected", "failed", "closed"),
		PublisherState:  choice(media.PublisherState, "new", "connecting", "connected", "disconnected", "failed", "closed"),
		Retransmissions: reliable.Retransmissions, RecoveryTimeouts: reliable.Timeouts,
		ReceivedFrames: media.Media.FramesReceived, SentFrames: media.Media.SamplesWritten,
		ProtocolErrors: mux.ProtocolErrors, DNSResponses: mux.DNSResponses, DNSErrors: mux.DNSErrors,
		OpenOK: mux.OpenOK, OpenErrors: mux.OpenErrors, SentBytes: mux.SentBytes, ReceivedBytes: mux.ReceivedBytes}
	if !terminalAt.IsZero() {
		report.TerminalAtMS = terminalAt.UnixMilli()
	}
	if decoded, decodeErr := hex.DecodeString(setupID); decodeErr == nil && len(decoded) == 16 {
		digest := sha256.Sum256(append([]byte("family-connect/session-diagnostic/v1\x00"), decoded...))
		report.SessionTag = hex.EncodeToString(digest[:16])
	}
	for _, event := range media.Evidence {
		if event.Stage == "CONNECTION_STATE" && (event.State == "failed" || event.State == "disconnected") {
			report.ICEFailure = choice(event.Target+"_"+event.State, "SUBSCRIBER_failed", "SUBSCRIBER_disconnected", "PUBLISHER_failed", "PUBLISHER_disconnected")
		}
		if event.Stage == "WS_FAIL" || event.Stage == "SIGNALING_PROTOCOL_FAIL" {
			report.SignalingFailure = choice(event.State, "read_error", "read_timeout", "invalid_json", "close_code_1000", "close_code_1001", "close_code_1002", "close_code_1003", "close_code_1006", "close_code_1007", "close_code_1008", "close_code_1009", "close_code_1010", "close_code_1011", "close_code_1012", "close_code_1013", "close_code_1015")
		}
	}
	return report
}
