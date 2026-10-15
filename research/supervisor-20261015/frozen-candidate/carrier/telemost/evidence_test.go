package telemost

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"sync"
	"testing"

	"github.com/gorilla/websocket"
	"github.com/pion/webrtc/v4"
)

func TestSignalingCloseEvidenceRedactsReason(t *testing.T) {
	session := testSession(t)
	session.recordSignalingReadFailure(&websocket.CloseError{Code: 1008, Text: "secret-room-token"})
	encoded, err := json.Marshal(session.Stats())
	if err != nil || strings.Contains(string(encoded), "secret") || !strings.Contains(string(encoded), "close_code_1008") {
		t.Fatal("missing code or unsafe close reason")
	}
}

func TestSignalingFailureClassification(t *testing.T) {
	var decoded any
	syntaxError := json.Unmarshal([]byte(`{"secret":`), &decoded)
	for _, fixture := range []struct {
		err   error
		stage string
		state string
	}{
		{context.DeadlineExceeded, "WS_FAIL", "read_timeout"},
		{syntaxError, "SIGNALING_PROTOCOL_FAIL", "invalid_json"},
		{errors.New("secret-url"), "WS_FAIL", "read_error"},
	} {
		session := testSession(t)
		session.recordSignalingReadFailure(fixture.err)
		event := session.Stats().Evidence[0]
		if event.Stage != fixture.stage || event.State != fixture.state {
			t.Fatal("wrong signaling failure boundary")
		}
	}
	session := testSession(t)
	session.recordSignalingReadFailure(&websocket.CloseError{Code: 4008, Text: "secret-room: ping timeout"})
	snapshot := session.Stats()
	if strings.Join(snapshot.Evidence[0].ReasonKeywords, ",") != "ping,timeout" {
		t.Fatal("wrong safe keywords")
	}
	snapshot.Evidence[0].ReasonKeywords[0] = "modified"
	if session.Stats().Evidence[0].ReasonKeywords[0] != "ping" {
		t.Fatal("mutable reason evidence")
	}
}

func TestEvidenceBoundAndRedaction(t *testing.T) {
	session := testSession(t)
	session.observePair("PUBLISHER", nil)
	session.observePair("PUBLISHER", &webrtc.ICECandidatePair{
		Local:  &webrtc.ICECandidate{Address: "secret-address", Foundation: "secret-foundation", Typ: webrtc.ICECandidateTypeRelay, Protocol: webrtc.ICEProtocolUDP},
		Remote: &webrtc.ICECandidate{Address: "secret-remote", Typ: webrtc.ICECandidateTypeHost, Protocol: webrtc.ICEProtocolUDP},
	})
	stats := session.Stats()
	if len(stats.Evidence) != 1 || stats.Evidence[0].TURNUsed == nil || !*stats.Evidence[0].TURNUsed || stats.Evidence[0].Protocol != "udp" {
		t.Fatal("missing selected pair evidence")
	}
	encoded, err := json.Marshal(stats)
	if err != nil || strings.Contains(string(encoded), "secret") {
		t.Fatal("unsafe evidence")
	}
	stats.Evidence[0].Stage = "modified"
	*stats.Evidence[0].TURNUsed = false
	var workers sync.WaitGroup
	for range 256 {
		workers.Add(1)
		go func() {
			defer workers.Done()
			session.recordEvidence(Evidence{Stage: "CONNECTION_STATE"})
			_ = session.Stats()
		}()
	}
	workers.Wait()
	stats = session.Stats()
	if len(stats.Evidence) != 128 || stats.EvidenceDropped != 129 || stats.Evidence[0].Stage != "ICE_SELECTED_PAIR" || !*stats.Evidence[0].TURNUsed {
		t.Fatal("unbounded or mutable evidence")
	}
}
