//go:build !fc_owner_diagnostic

package sessiontrace

import "context"

type ReceiveIdentity struct{}
type ReceiveState struct{}
type ReceiveObservation struct{}
type ACKObservation struct{}

func WithACKObservation(ctx context.Context, _ ACKObservation, _ uint64, _ uint32) context.Context {
	return ctx
}
func (*Boundary) CaptureACK(context.Context)  {}
func (*Recorder) receiverACKWritten(Boundary) {}

func WithReceiveObservation(ctx context.Context) (context.Context, *ReceiveObservation) {
	return ctx, nil
}
func (*ReceiveObservation) Identity() ReceiveIdentity                                          { return ReceiveIdentity{} }
func ObserveReceived(context.Context, ReceiveIdentity)                                         {}
func NewReceiveIdentity(Boundary) ReceiveIdentity                                              { return ReceiveIdentity{} }
func StampACK() ACKObservation                                                                 { return ACKObservation{} }
func (*Recorder) ReceiverAccepted(ReceiveIdentity, uint64, string, ReceiveState, ReceiveState) {}
func (*Recorder) ReceiverConsumed(uint64, ReceiveState, ReceiveState, ACKObservation, uint64, uint32) {
}
func (*Recorder) ReceiverACKSent(ACKObservation, uint64, uint32, bool) {}
