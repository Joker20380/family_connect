//go:build !fc_owner_diagnostic

package reliablestream

import "github.com/Joker20380/family_connect/carrier/sessiontrace"

func (*engine) receiveObservation() sessiontrace.ReceiveState { return sessiontrace.ReceiveState{} }
