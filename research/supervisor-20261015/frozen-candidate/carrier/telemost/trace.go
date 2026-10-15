package telemost

import (
	"errors"
	"io"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/pion/webrtc/v4"
)

func (s *Session) traceCarrierReadEnd(target string, err error) {
	reason := "NONE"
	if !s.closed.Load() {
		reason = "CARRIER_ERROR"
		if errors.Is(err, io.EOF) || errors.Is(err, io.ErrUnexpectedEOF) {
			reason = "CARRIER_EOF"
		}
	}
	s.cfg.Trace.Record(sessiontrace.Event{Stage: "CARRIER", State: "CLOSED", Target: target, Reason: reason})
}

func (s *Session) traceEvidence(event Evidence) {
	trace := s.cfg.Trace
	switch event.Stage {
	case "SIGNALING_CONNECTED":
		trace.Add("SIGNALING", "ESTABLISHED", "NONE")
		trace.Add("WEBSOCKET", "ESTABLISHED", "NONE")
	case "VP8_MEDIA_ACTIVE":
		trace.Add("CARRIER", "ESTABLISHED", "NONE")
	case "CONNECTION_STATE":
		reason := "NONE"
		if !s.closed.Load() {
			if event.State == "failed" {
				reason = "PEER_CONNECTION_FAILED"
			}
			if event.State == "disconnected" {
				reason = "CARRIER_ERROR"
			}
		}
		trace.Record(sessiontrace.Event{Stage: "PEER_CONNECTION", State: event.State, Target: event.Target, Reason: reason})
	}
}

func (s *Session) traceICE(target string, state webrtc.ICEConnectionState) {
	reason := "NONE"
	if !s.closed.Load() {
		if state == webrtc.ICEConnectionStateDisconnected {
			reason = "ICE_DISCONNECTED"
		}
		if state == webrtc.ICEConnectionStateFailed {
			reason = "ICE_FAILED"
		}
	}
	s.cfg.Trace.Record(sessiontrace.Event{Stage: "ICE", State: state.String(), Target: target, Reason: reason})
}
