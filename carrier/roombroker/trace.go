package roombroker

import (
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"strings"
)

func (broker *Broker) emit(current *setup, state State, code Code) {
	reasonCode := string(code)
	if reasonCode != "" && !sessiontrace.Allowed(reasonCode, sessiontrace.BrokerReasons) {
		reasonCode = "unknown"
	}
	broker.ownershipLocked(current.ctx, current, nil, "transition", reasonCode)
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
	source := ""
	switch code {
	case "lifetime_expired":
		source = "BROKER_LIFETIME"
	case "unused_expired":
		source = "BROKER_UNUSED"
	case "authorization_changed":
		source = "BROKER_AUTHORIZATION"
	}
	deadline := current.lease.deadline()
	event := sessiontrace.Event{Stage: stage, State: result, Reason: reason, BrokerReason: string(code), CloseSource: source, LeaseDeadlineMS: deadline.UnixMilli()}
	broker.pending = append(broker.pending, func() { trace.Record(event); broker.event(state, code) })
}
