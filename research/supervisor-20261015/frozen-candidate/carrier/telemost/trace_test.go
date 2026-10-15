package telemost

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"strings"
	"testing"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/gorilla/websocket"
	"github.com/pion/webrtc/v4"
)

func TestTypedLifecycleFirstFailureAndPrivacy(test *testing.T) {
	for _, fixture := range []struct {
		observe func(*Session)
		reason  string
	}{
		{func(session *Session) {
			session.recordSignalingReadFailure(&websocket.CloseError{Code: 4008, Text: "secret-room-token timeout"})
		}, "SIGNAL_WS_CLOSE"},
		{func(session *Session) { session.recordSignalingReadFailure(context.DeadlineExceeded) }, "HEARTBEAT_TIMEOUT"},
		{func(session *Session) { session.traceICE("SUBSCRIBER", webrtc.ICEConnectionStateDisconnected) }, "ICE_DISCONNECTED"},
		{func(session *Session) { session.traceICE("PUBLISHER", webrtc.ICEConnectionStateFailed) }, "ICE_FAILED"},
		{func(session *Session) { session.traceCarrierReadEnd("SUBSCRIBER", io.EOF) }, "CARRIER_EOF"},
		{func(session *Session) { session.traceCarrierReadEnd("PUBLISHER", errors.New("secret carrier error")) }, "CARRIER_ERROR"},
		{func(session *Session) {
			session.recordEvidence(Evidence{Stage: "CONNECTION_STATE", Target: "PUBLISHER", State: "failed"})
		}, "PEER_CONNECTION_FAILED"},
	} {
		session := testSession(test)
		session.cfg.Trace = sessiontrace.New(strings.Repeat("ab", 32), nil)
		fixture.observe(session)
		session.cfg.Trace.Add("CLEANUP", "FAILED", "RECOVERY_CLEANUP_FAILED")
		value := session.cfg.Trace.Snapshot()
		if value.FirstFailure == nil || value.FirstFailure.Reason != fixture.reason {
			test.Fatal("first precise failure overwritten")
		}
		raw, _ := json.Marshal(value)
		if strings.Contains(string(raw), "secret") {
			test.Fatal("unsafe provider close text")
		}
	}
}
