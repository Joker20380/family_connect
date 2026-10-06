//go:build fc_owner_diagnostic

package sessiontrace

import (
	"context"
	"sync/atomic"
	"time"
)

type ReceiveIdentity struct {
	Known   bool
	Sender  uint32
	Message uint32
}
type ReceiveState struct {
	Next     uint64 `json:"receive_next"`
	Mask     uint32 `json:"receive_mask"`
	Buffered uint32 `json:"buffered"`
}
type ReceiveObservation struct{ identity ReceiveIdentity }
type receiveObservationKey struct{}
type ACKObservation struct {
	CreatedNS int64
	token     uint64
}

var ackObservationSequence atomic.Uint64

type ackObservationKey struct{}
type ackWrite struct {
	stamp ACKObservation
	base  uint64
	mask  uint32
}

func WithACKObservation(ctx context.Context, stamp ACKObservation, base uint64, mask uint32) context.Context {
	return context.WithValue(ctx, ackObservationKey{}, ackWrite{stamp: stamp, base: base, mask: mask})
}
func (point *Boundary) CaptureACK(ctx context.Context) {
	if ack, ok := ctx.Value(ackObservationKey{}).(ackWrite); ok {
		point.ackWrite = ack
	}
}
func (recorder *Recorder) receiverACKWritten(point Boundary) {
	if point.Stage == "carrier_written" && point.Direction == "tx" && point.ackWrite.stamp.CreatedNS != 0 && point.Total == 1 && Allowed(point.Result, "ok|write_error|no_rtp") {
		recorder.receiverACKSentLocked(point.ackWrite.stamp, point.ackWrite.base, point.ackWrite.mask, point.Result)
	}
}

func StampACK() ACKObservation {
	return ACKObservation{CreatedNS: time.Now().UnixNano(), token: ackObservationSequence.Add(1)}
}
func WithReceiveObservation(ctx context.Context) (context.Context, *ReceiveObservation) {
	observation := &ReceiveObservation{}
	return context.WithValue(ctx, receiveObservationKey{}, observation), observation
}
func (observation *ReceiveObservation) Identity() ReceiveIdentity { return observation.identity }
func ObserveReceived(ctx context.Context, identity ReceiveIdentity) {
	if observation, ok := ctx.Value(receiveObservationKey{}).(*ReceiveObservation); ok {
		observation.identity = identity
	}
}
func NewReceiveIdentity(point Boundary) ReceiveIdentity {
	return ReceiveIdentity{Known: point.MessageKnown, Sender: point.Sender, Message: point.Message}
}

type ReceiverTransition struct {
	BufferedSuccessorReady bool         `json:"buffered_successor_ready"`
	Sequence               uint64       `json:"sequence"`
	AtNS                   int64        `json:"at_ns"`
	Before                 ReceiveState `json:"before"`
	After                  ReceiveState `json:"after"`
}
type ReceiverACK struct {
	token     uint64
	Base      uint64 `json:"base"`
	Mask      uint32 `json:"mask"`
	CreatedNS int64  `json:"created_ns"`
	SentNS    int64  `json:"sent_ns,omitempty"`
	Result    string `json:"result"`
}
type ReceiverEvidence struct {
	Accepted *ReceiverTransition `json:"accepted,omitempty"`
	Consumed *ReceiverTransition `json:"consumed,omitempty"`
	ACK      *ReceiverACK        `json:"ack,omitempty"`
}

func receiverOpen(watch *correlationWatch) bool {
	return watch.local == "rx" && Allowed(watch.value.State, "ARMED|BOUND|CARRIER_COMPLETE|RELIABLE_ACCEPTED|CONSUMED|ACK_GENERATED|ACK_SENT")
}

func (recorder *Recorder) ReceiverAccepted(identity ReceiveIdentity, sequence uint64, result string, before, after ReceiveState) {
	if recorder == nil || !identity.Known || result != "ok" || before.Next > sequence || after.Next != before.Next || after.Buffered != before.Buffered+1 {
		return
	}
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	for _, watch := range recorder.correlation.watches {
		watch.expire(time.Now())
		if !receiverOpen(watch) || sequence != watch.value.Key.Sequence {
			continue
		}
		for index := range watch.value.Candidates {
			candidate := &watch.value.Candidates[index]
			if candidate.Sender != identity.Sender || candidate.Message != identity.Message || !candidate.Completed || candidate.callbacks != nil {
				continue
			}
			candidate.callbacks = &ReceiverEvidence{Accepted: &ReceiverTransition{Sequence: sequence, AtNS: time.Now().UnixNano(), Before: before, After: after}}
		}
		watch.complete()
	}
}

func (recorder *Recorder) ReceiverConsumed(sequence uint64, before, after ReceiveState, stamp ACKObservation, base uint64, mask uint32) {
	if recorder == nil || before.Next != sequence || after.Next != sequence+1 || before.Buffered == 0 || after.Buffered+1 != before.Buffered || base != after.Next || mask != after.Mask || stamp.CreatedNS == 0 || stamp.token == 0 {
		return
	}
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	for _, watch := range recorder.correlation.watches {
		watch.expire(time.Now())
		if !receiverOpen(watch) || sequence != watch.value.Key.Sequence {
			continue
		}
		for index := range watch.value.Candidates {
			proof := watch.value.Candidates[index].callbacks
			if proof == nil || proof.Consumed != nil {
				continue
			}
			proof.Consumed = &ReceiverTransition{Sequence: sequence, AtNS: stamp.CreatedNS, Before: before, After: after, BufferedSuccessorReady: after.Mask&1 != 0}
			proof.ACK = &ReceiverACK{Base: base, Mask: mask, CreatedNS: stamp.CreatedNS, token: stamp.token, Result: "generated"}
		}
		watch.complete()
	}
}

func (recorder *Recorder) ReceiverACKSent(stamp ACKObservation, base uint64, mask uint32, success bool) {
	if recorder == nil || stamp.CreatedNS == 0 {
		return
	}
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	result := "write_error"
	if success {
		result = "ok"
	}
	recorder.receiverACKSentLocked(stamp, base, mask, result)
}

func (recorder *Recorder) receiverACKSentLocked(stamp ACKObservation, base uint64, mask uint32, result string) {
	for _, watch := range recorder.correlation.watches {
		watch.expire(time.Now())
		if !receiverOpen(watch) {
			continue
		}
		for index := range watch.value.Candidates {
			proof := watch.value.Candidates[index].callbacks
			if proof == nil || proof.ACK == nil || proof.ACK.token != stamp.token || proof.ACK.CreatedNS != stamp.CreatedNS || proof.ACK.Base != base || proof.ACK.Mask != mask || proof.ACK.SentNS != 0 {
				continue
			}
			proof.ACK.SentNS = time.Now().UnixNano()
			proof.ACK.Result = result
		}
		watch.complete()
	}
}

func cloneReceiver(value *ReceiverEvidence) *ReceiverEvidence {
	if value == nil {
		return nil
	}
	copy := *value
	if value.Accepted != nil {
		accepted := *value.Accepted
		copy.Accepted = &accepted
	}
	if value.Consumed != nil {
		consumed := *value.Consumed
		copy.Consumed = &consumed
	}
	if value.ACK != nil {
		ack := *value.ACK
		copy.ACK = &ack
	}
	return &copy
}
