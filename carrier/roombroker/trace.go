package roombroker

import (
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"strings"
)

func (broker *Broker) emit(current *setup, state State, code Code) {
	trace := sessiontrace.From(current.ctx)
	stage, result, reason := "GATEWAY_SESSION", "CLOSED", "NONE"
	switch state {
	case Creating:
		stage, result = "ROOM_CREATION", "STARTED"
	case Created:
		stage, result = "ROOM_CREATION", "ESTABLISHED"
	case GatewayJoining:
		stage, result = "GATEWAY_JOIN", "STARTED"
	case Ready:
		stage, result = "GATEWAY_JOIN", "ESTABLISHED"
	case ClientIssued:
		stage, result = "DESCRIPTOR", "ISSUED"
	case Active:
		result = "ESTABLISHED"
	case Cancelled:
		stage, result = "LOCAL_CLOSE", "STARTED"
	case Failed, Expired:
		result, reason = "FAILED", "GATEWAY_CLOSE"
		if strings.HasPrefix(string(code), "provider_") {
			stage, reason = "ROOM_CREATION", "RECOVERY_DESCRIPTOR_FAILED"
		} else if code == "gateway_failed" || code == "gateway_ready_timeout" {
			stage, reason = "GATEWAY_JOIN", "RECOVERY_JOIN_FAILED"
		}
	}
	trace.Record(sessiontrace.Event{Stage: stage, State: result, Reason: reason, BrokerReason: string(code)})
	broker.event(state, code)
}
