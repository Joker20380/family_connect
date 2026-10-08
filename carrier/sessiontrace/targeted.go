//go:build fc_owner_diagnostic

package sessiontrace

import (
	"crypto/rand"
	"encoding/hex"
	"time"
)

type TargetedReceipt struct {
	Result string          `json:"result"`
	Reason string          `json:"reason,omitempty"`
	Fault  FaultReceipt    `json:"fault"`
	Key    *CorrelationKey `json:"key,omitempty"`
}

func (recorder *Recorder) BindFaultAllocation(allocation func(func(Flow)), alive func() bool) {
	if recorder == nil {
		return
	}
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	if recorder.fault.receipt.Armed {
		recorder.fault.receipt.Armed = false
		recorder.fault.receipt.State = "OWNER_CHANGED"
	}
	recorder.fault.allocation, recorder.fault.alive = allocation, alive
	recorder.fault.owner++
}

func (recorder *Recorder) targetValid(now time.Time) bool {
	if !recorder.fault.receipt.Armed {
		return false
	}
	state := ""
	watch := recorder.correlation.watches[recorder.fault.target.Direction]
	if recorder.closing || recorder.fault.target.Session != recorder.value.SessionTag || !recorder.fault.gateway || recorder.fault.alive == nil || !recorder.fault.alive() {
		state = "CLOSED"
	} else if !now.Before(recorder.fault.deadline) {
		state = "EXPIRED"
	} else if watch == nil || watch.local != "tx" || watch.value.Key != recorder.fault.target || !now.Before(watch.deadline) || watch.value.State != "ARMED" || recorder.watch.value == nil || recorder.watch.value.Target != (WatchTarget{Direction: "tx", Sequence: recorder.fault.target.Sequence, Attempt: 1}) || !now.Before(recorder.watch.deadline) {
		state = "BINDING_LOST"
	}
	if state != "" {
		recorder.fault.receipt.Armed = false
		recorder.fault.receipt.State = state
		return false
	}
	return true
}

func (recorder *Recorder) TargetedArm(receipt CorrelationReceipt) TargetedReceipt {
	if recorder == nil {
		return TargetedReceipt{Result: "UNAVAILABLE"}
	}
	recorder.mu.Lock()
	if recorder.fault.used && !recorder.fault.targeted {
		recorder.fault.receipt.Armed = false
		result := TargetedReceipt{Result: "PREPARATION_ABORTED", Fault: *recorder.faultSnapshot()}
		recorder.mu.Unlock()
		return result
	}
	allocation := recorder.fault.allocation
	owner := recorder.fault.owner
	recorder.fault.targeted = true
	recorder.mu.Unlock()
	result := TargetedReceipt{Result: "PREPARATION_ABORTED", Reason: "ALLOCATION_UNAVAILABLE"}
	if allocation == nil {
		return result
	}
	var nonce [16]byte
	if _, err := rand.Read(nonce[:]); err != nil {
		result.Reason = "NONCE_UNAVAILABLE"
		return result
	}
	allocation(func(flow Flow) {
		recorder.mu.Lock()
		defer recorder.mu.Unlock()
		now := time.Now()
		key := receipt.Key
		watch := recorder.correlation.watches[key.Direction]
		remaining := time.UnixMilli(receipt.ExpiresAtMS).Sub(now)
		result.Reason = "INVALID_PREARM_OR_SESSION"
		if owner != recorder.fault.owner || recorder.fault.used || recorder.closing || !recorder.fault.family || !recorder.fault.gateway || recorder.fault.alive == nil || !recorder.fault.alive() || recorder.value.CorrelationStatus != "VALID" ||
			receipt.Schema != CorrelationSchema || receipt.State != "ARMED" || key.Session != recorder.value.SessionTag || key.Attempt != 1 || !validGeneration(key.Generation) ||
			remaining <= 0 || remaining > EvidenceWatchTTL || watch == nil || watch.local != "tx" || watch.value.Key != key || watch.value.State != "ARMED" || !now.Before(watch.deadline) ||
			(recorder.watch.value != nil && (recorder.watch.value.Target != (WatchTarget{Direction: "tx", Sequence: key.Sequence, Attempt: 1}) || !now.Before(recorder.watch.deadline))) {
			result.Fault = *recorder.faultSnapshot()
			return
		}
		if flow.Pending != 0 || flow.SendBase != key.Sequence || flow.SendNext != key.Sequence {
			result.Reason = "HEAD_NOT_FREE"
			result.Fault = *recorder.faultSnapshot()
			return
		}
		deadline := now.Add(remaining)
		if watch.deadline.Before(deadline) {
			deadline = watch.deadline
		}
		if recorder.watch.value == nil && !recorder.enableEvidenceWatch(WatchTarget{Direction: "tx", Sequence: key.Sequence, Attempt: 1}, now) {
			result.Reason = "WATCH_UNAVAILABLE"
			return
		}
		if recorder.watch.deadline.Before(deadline) {
			deadline = recorder.watch.deadline
		}
		recorder.fault.used = true
		recorder.fault.target, recorder.fault.deadline = key, deadline
		recorder.fault.receipt = FaultReceipt{Schema: 1, State: "ARMED", Target: "logical_data_attempt0", Generation: hex.EncodeToString(nonce[:]), Sequence: key.Sequence, Armed: true, ArmedAtMS: now.UnixMilli()}
		result = TargetedReceipt{Result: "ARMED", Fault: *recorder.faultSnapshot(), Key: &key}
		if !result.Fault.Armed {
			result.Result, result.Reason = "PREPARATION_ABORTED", result.Fault.State
		}
	})
	return result
}
