//go:build fc_owner_diagnostic

package sessiontrace

import (
	"crypto/rand"
	"encoding/hex"
	"time"
)

type faultControl struct {
	family  bool
	gateway bool
	used    bool
	receipt FaultReceipt
}

func evidenceWatchEnabled() bool { return true }

func (recorder *Recorder) faultEvent(event Event) {
	if event.State == "ESTABLISHED" && event.Stage == "FAMILY_TLS" {
		recorder.fault.family = true
	}
	if event.State == "ESTABLISHED" && event.Stage == "GATEWAY_SESSION" {
		recorder.fault.gateway = true
	}
	if event.Stage == "LOCAL_CLOSE" || event.Stage == "CLEANUP" || event.State == "FAILED" || event.State == "CLOSED" {
		recorder.fault.gateway = false
		recorder.fault.receipt.Armed = false
	}
}

func (recorder *Recorder) faultSnapshot() *FaultReceipt {
	value := recorder.fault.receipt
	value.Schema = 1
	value.Target = "outbound_data_attempt0_after_established"
	value.State = "DISARMED"
	if value.Armed {
		value.State = "ARMED"
	}
	return &value
}

func (recorder *Recorder) FaultCommand(command string) FaultReceipt {
	if recorder == nil {
		return FaultReceipt{Schema: 1, State: "UNAVAILABLE"}
	}
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	if command == "arm" && recorder.value.CorrelationStatus == "VALID" && recorder.fault.family && recorder.fault.gateway && !recorder.closing && !recorder.fault.used {
		var nonce [16]byte
		if _, err := rand.Read(nonce[:]); err == nil {
			recorder.fault.used = true
			recorder.fault.receipt = FaultReceipt{Armed: true, Generation: hex.EncodeToString(nonce[:]), ArmedAtMS: time.Now().UnixMilli()}
		}
	}
	if command == "disarm" {
		recorder.fault.receipt.Armed = false
	}
	return *recorder.faultSnapshot()
}

func (recorder *Recorder) DropDiagnostic(point Boundary) bool {
	if recorder == nil || point.Direction != "tx" || !point.DataKnown || !point.AttemptKnown || point.Attempt != 0 {
		return false
	}
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	if !recorder.fault.receipt.Armed || !recorder.fault.family || !recorder.fault.gateway || recorder.closing {
		return false
	}
	if recorder.watch.value == nil {
		recorder.enableEvidenceWatch(WatchTarget{Direction: "tx", Sequence: point.DataSequence, Attempt: 1}, time.Now())
	}
	recorder.fault.receipt.Armed = false
	recorder.fault.receipt.Consumed = true
	recorder.fault.receipt.Count = 1
	recorder.fault.receipt.Sequence = point.DataSequence
	recorder.fault.receipt.ConsumedAtMS = time.Now().UnixMilli()
	return true
}
