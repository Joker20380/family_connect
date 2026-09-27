package telemost

import (
	"time"

	"github.com/pion/webrtc/v4"
)

type Evidence struct {
	UTC        string `json:"utc"`
	Stage      string `json:"stage"`
	Target     string `json:"target,omitempty"`
	State      string `json:"state,omitempty"`
	LocalType  string `json:"local_type,omitempty"`
	RemoteType string `json:"remote_type,omitempty"`
	Protocol   string `json:"protocol,omitempty"`
	TURNUsed   *bool  `json:"turn_used,omitempty"`
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
