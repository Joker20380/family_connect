package telemost

import (
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"strings"
	"time"

	"github.com/gorilla/websocket"
	"github.com/pion/webrtc/v4"
)

func (s *Session) recordSignalingReadFailure(err error) {
	event := Evidence{Stage: "WS_FAIL", State: "read_error"}
	var networkError net.Error
	var closeError *websocket.CloseError
	var syntaxError *json.SyntaxError
	switch {
	case errors.As(err, &networkError) && networkError.Timeout():
		event.State = "read_timeout"
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
	s.recordEvidence(event)
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
