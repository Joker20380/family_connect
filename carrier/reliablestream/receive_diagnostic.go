//go:build fc_owner_diagnostic

package reliablestream

import "github.com/Joker20380/family_connect/carrier/sessiontrace"

func (state *engine) receiveObservation() sessiontrace.ReceiveState {
	flow := state.flow()
	return sessiontrace.ReceiveState{Next: flow.ReceiveNext, Mask: flow.ReceiveMask, Buffered: flow.Buffered}
}
