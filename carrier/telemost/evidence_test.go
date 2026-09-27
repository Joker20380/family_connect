package telemost

import (
	"encoding/json"
	"strings"
	"sync"
	"testing"

	"github.com/pion/webrtc/v4"
)

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
