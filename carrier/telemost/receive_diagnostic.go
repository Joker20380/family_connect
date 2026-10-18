//go:build fc_owner_diagnostic

package telemost

import (
	"context"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

type receiveMessage struct {
	payload  []byte
	identity sessiontrace.ReceiveIdentity
}

func packReceive(payload []byte, point sessiontrace.Boundary) receiveMessage {
	return receiveMessage{payload: payload, identity: sessiontrace.NewReceiveIdentity(point)}
}
func unpackReceive(ctx context.Context, message receiveMessage) []byte {
	sessiontrace.ObserveReceived(ctx, message.identity)
	return message.payload
}
func (session *Session) configureReceiveObservation() {
	session.reassembler.onMessage = session.deliverObserved
}
