//go:build fc_owner_diagnostic

package sessiontrace

import (
	"encoding/json"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
)

func establishedFaultRecorder() *Recorder {
	recorder := New(strings.Repeat("a", 64), nil)
	recorder.Add("FAMILY_TLS", "ESTABLISHED", "NONE")
	recorder.Add("GATEWAY_SESSION", "ESTABLISHED", "NONE")
	return recorder
}

func faultPoint() Boundary {
	return Boundary{Direction: "tx", DataKnown: true, AttemptKnown: true, DataSequence: 48}
}

func TestFaultF1OneShotConcurrent(test *testing.T) {
	recorder := establishedFaultRecorder()
	armed := recorder.FaultCommand("arm")
	if !armed.Armed || armed.Consumed || armed.Count != 0 || len(armed.Generation) != 32 {
		test.Fatal("invalid armed receipt", armed)
	}
	var consumed atomic.Uint32
	var workers sync.WaitGroup
	for index := 0; index < 64; index++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			if recorder.DropDiagnostic(faultPoint()) {
				consumed.Add(1)
			}
		}()
	}
	workers.Wait()
	receipt := recorder.FaultCommand("status")
	if consumed.Load() != 1 || receipt.Armed || !receipt.Consumed || receipt.Count != 1 || receipt.Generation != armed.Generation || receipt.Sequence != 48 || receipt.State != "DISARMED" {
		test.Fatal("one-shot violation", receipt)
	}
	if recorder.FaultCommand("arm").Armed {
		test.Fatal("same session rearmed")
	}
	for index := 0; index < Limit*2; index++ {
		recorder.Add("CARRIER_ACTIVITY", "ESTABLISHED", "NONE")
	}
	if !recorder.Snapshot().Fault.Consumed {
		test.Fatal("receipt evicted")
	}
}

func TestFaultF2AttemptsAndF3Unrelated(test *testing.T) {
	recorder := establishedFaultRecorder()
	recorder.FaultCommand("arm")
	for attempt := uint32(1); attempt <= 8; attempt++ {
		point := faultPoint()
		point.Attempt = attempt
		if recorder.DropDiagnostic(point) {
			test.Fatal("retry dropped", attempt)
		}
	}
	for _, point := range []Boundary{{Direction: "rx", DataKnown: true, AttemptKnown: true}, {Direction: "tx", DataKnown: true}, {Direction: "tx", AttemptKnown: true}, {}} {
		if recorder.DropDiagnostic(point) {
			test.Fatal("non-target dropped")
		}
	}
	if !recorder.FaultCommand("status").Armed || !recorder.DropDiagnostic(faultPoint()) {
		test.Fatal("target not consumed")
	}
	point := faultPoint()
	point.DataSequence++
	if recorder.DropDiagnostic(point) {
		test.Fatal("later DATA dropped")
	}
}

func TestFaultF4RestartAndF5Default(test *testing.T) {
	old := establishedFaultRecorder()
	old.FaultCommand("arm")
	restarted := establishedFaultRecorder()
	if restarted.FaultCommand("status").Armed || restarted.DropDiagnostic(faultPoint()) {
		test.Fatal("restart rearmed")
	}
	fresh := New(strings.Repeat("b", 64), nil)
	if fresh.FaultCommand("arm").Armed {
		test.Fatal("bootstrap armed")
	}
	fresh.Add("FAMILY_TLS", "ESTABLISHED", "NONE")
	if fresh.FaultCommand("arm").Armed {
		test.Fatal("missing gateway armed")
	}
	old.Add("LOCAL_CLOSE", "STARTED", "NONE")
	if old.DropDiagnostic(faultPoint()) || old.FaultCommand("status").Armed {
		test.Fatal("closed session armed")
	}
}

func TestFaultF6Privacy(test *testing.T) {
	recorder := establishedFaultRecorder()
	recorder.FaultCommand("arm")
	recorder.FaultCommand("PRIVATE KEY destination.example secret payload")
	recorder.DropDiagnostic(faultPoint())
	raw, err := json.Marshal(recorder.Snapshot().Fault)
	if err != nil || len(raw) > 512 {
		test.Fatal("receipt bounds", err)
	}
	for _, forbidden := range []string{"PRIVATE", "destination", "secret", "payload"} {
		if strings.Contains(string(raw), forbidden) {
			test.Fatal("privacy violation")
		}
	}
}
