package roombroker

import "github.com/Joker20380/family_connect/carrier/sessiontrace"

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
	}
	trace.Add(stage, result, reason)
	broker.event(state, code)
}
