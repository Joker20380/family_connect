//go:build fc_owner_diagnostic

package sessiontrace

import (
	"encoding/json"
	"strings"
	"sync"
	"testing"
	"time"
)

func targetedFixture(test *testing.T) (*Recorder, CorrelationReceipt, *sync.Mutex, *Flow) {
	test.Helper()
	receiver, key := correlationFixture(test)
	prearm, err := receiver.CorrelationStatus(key, false)
	if err != nil {
		test.Fatal(err)
	}
	sender := establishedFaultRecorder()
	if _, err := sender.PrearmCorrelation(key, "tx"); err != nil {
		test.Fatal(err)
	}
	allocation := &sync.Mutex{}
	flow := &Flow{SendBase: 19, SendNext: 19}
	sender.BindFaultAllocation(func(check func(Flow)) { allocation.Lock(); defer allocation.Unlock(); check(*flow) }, func() bool { return true })
	return sender, prearm, allocation, flow
}

func targetedPoint() Boundary {
	return Boundary{Direction: "tx", DataKnown: true, AttemptKnown: true, DataSequence: 19, Attempt: 0}
}

func TestTargetedAllocationOrder(test *testing.T) {
	for _, before := range []bool{true, false} {
		sender, receipt, allocation, flow := targetedFixture(test)
		allocation.Lock()
		if before {
			flow.SendNext++
			flow.Pending++
		}
		allocation.Unlock()
		armed := sender.TargetedArm(receipt)
		if before {
			if armed.Result != "PREPARATION_ABORTED" || armed.Reason != "HEAD_NOT_FREE" || sender.DropDiagnostic(targetedPoint()) {
				test.Fatal(armed)
			}
		} else {
			if armed.Result != "ARMED" {
				test.Fatal(armed)
			}
			allocation.Lock()
			flow.SendNext++
			flow.Pending++
			allocation.Unlock()
			if !sender.DropDiagnostic(targetedPoint()) {
				test.Fatal("matching DATA from any writer must drop")
			}
		}
	}
}

func TestTargetedWrongInputs(test *testing.T) {
	for _, name := range []string{"session", "direction", "sequence", "generation", "expired", "extended", "attempt"} {
		test.Run(name, func(test *testing.T) {
			sender, receipt, _, _ := targetedFixture(test)
			switch name {
			case "session":
				receipt.Key.Session = strings.Repeat("b", 64)
			case "direction":
				receipt.Key.Direction = "gateway_to_client"
			case "sequence":
				receipt.Key.Sequence++
			case "generation":
				receipt.Key.Generation = strings.Repeat("b", 32)
			case "expired":
				receipt.ExpiresAtMS = time.Now().Add(-time.Second).UnixMilli()
			case "extended":
				receipt.ExpiresAtMS = time.Now().Add(time.Hour).UnixMilli()
			case "attempt":
				receipt.Key.Attempt = 2
			}
			if sender.TargetedArm(receipt).Result != "PREPARATION_ABORTED" || sender.DropDiagnostic(targetedPoint()) || sender.FaultCommand("arm").Armed {
				test.Fatal("unsafe rejection or generic fallback")
			}
		})
	}
}

func TestTargetedTerminalBeforeDrop(test *testing.T) {
	for _, terminal := range []string{"expiry", "cancel", "close", "cleanup", "owner"} {
		test.Run(terminal, func(test *testing.T) {
			sender, receipt, _, _ := targetedFixture(test)
			if sender.TargetedArm(receipt).Result != "ARMED" {
				test.Fatal("arm")
			}
			switch terminal {
			case "expiry":
				sender.mu.Lock()
				sender.fault.deadline = time.Now().Add(-time.Second)
				sender.mu.Unlock()
			case "cancel":
				sender.FaultCommand("disarm")
			case "close":
				sender.Add("LOCAL_CLOSE", "STARTED", "NONE")
			case "cleanup":
				sender.CorrelationStatus(receipt.Key, true)
			case "owner":
				sender.BindFaultAllocation(nil, nil)
			}
			if sender.DropDiagnostic(targetedPoint()) || sender.FaultCommand("status").Armed || sender.FaultCommand("status").Count != 0 {
				test.Fatal("terminal trap")
			}
		})
	}
}

func TestTargetedOnlyMatchingAttemptAndOnce(test *testing.T) {
	sender, receipt, _, _ := targetedFixture(test)
	if sender.TargetedArm(receipt).Result != "ARMED" {
		test.Fatal("arm")
	}
	for _, point := range []Boundary{{Direction: "tx"}, {Direction: "rx", DataKnown: true, AttemptKnown: true, DataSequence: 19}, {Direction: "tx", DataKnown: true, AttemptKnown: true, DataSequence: 18}, {Direction: "tx", DataKnown: true, AttemptKnown: true, DataSequence: 19, Attempt: 1}} {
		if sender.DropDiagnostic(point) {
			test.Fatal("wrong boundary consumed")
		}
	}
	if !sender.DropDiagnostic(targetedPoint()) {
		test.Fatal("target missed")
	}
	sender.FaultCommand("disarm")
	if sender.TargetedArm(receipt).Result == "ARMED" || sender.DropDiagnostic(targetedPoint()) || sender.FaultCommand("status").Count != 1 {
		test.Fatal("second drop")
	}
	watch := sender.Snapshot().Watch
	if watch == nil || watch.Target.Sequence != 19 || watch.Target.Attempt != 1 {
		test.Fatal("wrong evidence watch")
	}
}

func TestTargetedCancelWhileAllocationCommandWaits(test *testing.T) {
	sender, receipt, _, flow := targetedFixture(test)
	entered, release := make(chan struct{}), make(chan struct{})
	sender.BindFaultAllocation(func(check func(Flow)) { close(entered); <-release; check(*flow) }, func() bool { return true })
	done := make(chan TargetedReceipt, 1)
	go func() { done <- sender.TargetedArm(receipt) }()
	<-entered
	sender.FaultCommand("disarm")
	close(release)
	if result := <-done; result.Result == "ARMED" {
		test.Fatal(result)
	}
}

func TestTargetedControlRoute(test *testing.T) {
	sender, receipt, _, _ := targetedFixture(test)
	raw, _ := json.Marshal(correlationRequest{Operation: "targeted_arm", Key: receipt.Key, Prearm: &receipt})
	if response := sender.CorrelationCommand(string(raw), "gateway"); response != `{"error":"rejected"}` {
		test.Fatal(response)
	}
	var result TargetedReceipt
	if err := json.Unmarshal([]byte(sender.CorrelationCommand(string(raw), "client")), &result); err != nil || result.Result != "ARMED" {
		test.Fatal(result, err)
	}
	if result.Key == nil || *result.Key != receipt.Key || len(result.Fault.Generation) != 32 {
		test.Fatal("correlation key/fault nonce conflated", result)
	}
	if response := sender.CorrelationCommand(strings.Repeat("x", 16385), "client"); response != `{"error":"rejected"}` {
		test.Fatal("unbounded control")
	}
}

func TestTargetedQueuedAllocationVersusArm(test *testing.T) {
	for _, queuedFirst := range []bool{true, false} {
		sender, receipt, allocation, flow := targetedFixture(test)
		entered, release := make(chan struct{}), make(chan struct{})
		sender.BindFaultAllocation(func(check func(Flow)) {
			close(entered)
			<-release
			allocation.Lock()
			defer allocation.Unlock()
			check(*flow)
		}, func() bool { return true })
		done := make(chan TargetedReceipt, 1)
		go func() { done <- sender.TargetedArm(receipt) }()
		<-entered
		if queuedFirst {
			allocation.Lock()
			flow.SendNext++
			flow.Pending++
			allocation.Unlock()
		}
		close(release)
		result := <-done
		if queuedFirst {
			if result.Result != "PREPARATION_ABORTED" || sender.DropDiagnostic(targetedPoint()) {
				test.Fatal(result)
			}
		} else {
			if result.Result != "ARMED" {
				test.Fatal(result)
			}
			allocation.Lock()
			flow.SendNext++
			flow.Pending++
			allocation.Unlock()
			if !sender.DropDiagnostic(targetedPoint()) {
				test.Fatal("post-arm allocation missed")
			}
		}
	}
}

func TestTargetedMissedAndSessionCancellation(test *testing.T) {
	sender, receipt, _, _ := targetedFixture(test)
	if sender.TargetedArm(receipt).Result != "ARMED" {
		test.Fatal("arm")
	}
	point := targetedPoint()
	point.DataSequence++
	if sender.DropDiagnostic(point) || sender.FaultCommand("status").State != "TARGET_MISSED" || sender.DropDiagnostic(targetedPoint()) {
		test.Fatal("trap")
	}
}

func TestTargetedConcurrentBoundariesOnlyOneDrop(test *testing.T) {
	sender, receipt, _, _ := targetedFixture(test)
	if sender.TargetedArm(receipt).Result != "ARMED" {
		test.Fatal("arm")
	}
	if sender.FaultCommand("arm").Armed {
		test.Fatal("generic command accepted in targeted mode")
	}
	results := make(chan bool, 16)
	start := make(chan struct{})
	for index := 0; index < 16; index++ {
		go func() { <-start; results <- sender.DropDiagnostic(targetedPoint()) }()
	}
	close(start)
	count := 0
	for index := 0; index < 16; index++ {
		if <-results {
			count++
		}
	}
	sender.FaultCommand("disarm")
	if count != 1 || sender.FaultCommand("status").Count != 1 || sender.FaultCommand("status").State != "CONSUMED" {
		test.Fatal("lost consumed receipt")
	}
}
