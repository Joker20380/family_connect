//go:build !fc_owner_diagnostic

package telemost

import (
	"context"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

type receiveMessage = []byte

func packReceive(payload []byte, _ sessiontrace.Boundary) receiveMessage { return payload }
func unpackReceive(_ context.Context, message receiveMessage) []byte     { return message }
func (*Session) configureReceiveObservation()                            {}
