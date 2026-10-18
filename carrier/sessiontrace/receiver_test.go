//go:build fc_owner_diagnostic

package sessiontrace

import (
	"context"
	"encoding/json"
	"strings"
	"testing"
	"time"
)

func receiverFixture(test *testing.T) (*Recorder, CorrelationKey) {
	test.Helper()
	recorder, key := correlationFixture(test)
	correlationAttempt(recorder, 11, 1)
	if _, err := recorder.BindCorrelation(correlationDescriptor(key, 11, 1)); err != nil {
		test.Fatal(err)
	}
	return recorder, key
}

func acceptSelected(recorder *Recorder, message uint32) {
	recorder.ReceiverAccepted(ReceiveIdentity{Known: true, Sender: 7, Message: message}, 19, "ok", ReceiveState{Next: 19, Mask: 2, Buffered: 1}, ReceiveState{Next: 19, Mask: 3, Buffered: 2})
}

func consumeSelected(recorder *Recorder) ACKObservation {
	stamp := StampACK()
	recorder.ReceiverConsumed(19, ReceiveState{Next: 19, Mask: 3, Buffered: 2}, ReceiveState{Next: 20, Mask: 1, Buffered: 1}, stamp, 20, 1)
	return stamp
}

func requireReceiverState(test *testing.T, recorder *Recorder, key CorrelationKey, expected string) CorrelationReceipt {
	test.Helper()
	value, err := recorder.CorrelationStatus(key, false)
	if err != nil || value.State != expected {
		test.Fatalf("state=%s want=%s error=%v", value.State, expected, err)
	}
	return value
}

func TestReceiverCallbackLifecycle(test *testing.T) {
	recorder, key := receiverFixture(test)
	requireReceiverState(test, recorder, key, "CARRIER_COMPLETE")
	acceptSelected(recorder, 11)
	accepted := requireReceiverState(test, recorder, key, "RELIABLE_ACCEPTED")
	if accepted.Reliable.Accepted.Before.Mask != 2 || accepted.Reliable.Accepted.After.Mask != 3 || accepted.Reliable.Accepted.AtNS == 0 {
		test.Fatal("acceptance transition missing")
	}
	stamp := consumeSelected(recorder)
	generated := requireReceiverState(test, recorder, key, "ACK_GENERATED")
	if generated.Reliable.Consumed.Sequence != 19 || generated.Reliable.Consumed.After.Next != 20 || generated.Reliable.Consumed.After.Mask&1 == 0 || generated.Reliable.ACK.SentNS != 0 {
		test.Fatal("consumption/order/generation missing")
	}
	recorder.ReceiverACKSent(stamp, 20, 1, true)
	complete := requireReceiverState(test, recorder, key, "COMPLETE")
	encoded, _ := json.Marshal(complete.Reliable)
	for index := 0; index < 2101; index++ {
		recorder.Boundary(Boundary{Direction: "rx", Stage: "reliable_consumed", Result: "ok", DataKnown: true, DataSequence: 55, ACKBase: 56})
		recorder.ReceiverACKSent(StampACK(), 56, 0, true)
		recorder.ReceiverConsumed(55, ReceiveState{Next: 55, Buffered: 1}, ReceiveState{Next: 56}, StampACK(), 56, 0)
		correlationAttempt(recorder, 12, 1)
	}
	retained := requireReceiverState(test, recorder, key, "COMPLETE")
	after, _ := json.Marshal(retained.Reliable)
	if string(after) != string(encoded) || len(retained.Candidates) > CandidateLimit {
		test.Fatal("pinned callback evicted/changed")
	}
	complete.Reliable.Accepted.After.Next = 999
	complete.Reliable.ACK.Base = 999
	if requireReceiverState(test, recorder, key, "COMPLETE").Reliable.ACK.Base != 20 {
		test.Fatal("export alias")
	}
	raw, _ := json.Marshal(retained)
	if len(raw) > 8192 {
		test.Fatal("unbounded export")
	}
	for _, secret := range []string{"payload", "destination", "credential", "private_key"} {
		if strings.Contains(string(raw), secret) {
			test.Fatal("privacy", secret)
		}
	}
}

func TestReceiverWrongCallbacks(test *testing.T) {
	for _, mode := range []string{"seq", "sender", "message", "duplicate", "already_consumed", "direction", "missing_identity"} {
		test.Run(mode, func(test *testing.T) {
			recorder, key := receiverFixture(test)
			identity := ReceiveIdentity{Known: true, Sender: 7, Message: 11}
			sequence, result, before, after := uint64(19), "ok", ReceiveState{Next: 19}, ReceiveState{Next: 19, Mask: 1, Buffered: 1}
			switch mode {
			case "seq":
				sequence = 20
			case "sender":
				identity.Sender++
			case "message":
				identity.Message = 12
			case "duplicate":
				result = "duplicate"
			case "already_consumed":
				before.Next = 20
				after.Next = 20
			case "missing_identity":
				identity.Known = false
			case "direction":
				recorder.Boundary(Boundary{Direction: "tx", Stage: "reliable_data_accepted", Result: "ok", DataKnown: true, DataSequence: 19})
				requireReceiverState(test, recorder, key, "CARRIER_COMPLETE")
				return
			}
			recorder.ReceiverAccepted(identity, sequence, result, before, after)
			requireReceiverState(test, recorder, key, "CARRIER_COMPLETE")
		})
	}
	recorder, key := receiverFixture(test)
	acceptSelected(recorder, 11)
	recorder.ReceiverConsumed(20, ReceiveState{Next: 20, Buffered: 1}, ReceiveState{Next: 21}, StampACK(), 21, 0)
	requireReceiverState(test, recorder, key, "RELIABLE_ACCEPTED")
	stamp := consumeSelected(recorder)
	recorder.ReceiverACKSent(stamp, 21, 0, true)
	unrelated := StampACK()
	unrelated.CreatedNS = stamp.CreatedNS
	recorder.ReceiverACKSent(unrelated, 20, 1, true)
	recorder.ReceiverACKSent(StampACK(), 20, 1, true)
	requireReceiverState(test, recorder, key, "ACK_GENERATED")
	recorder.ReceiverACKSent(stamp, 20, 1, false)
	failed := requireReceiverState(test, recorder, key, "ACK_GENERATED")
	if failed.Reliable.ACK.Result != "write_error" || failed.Reliable.ACK.SentNS == 0 {
		test.Fatal("write failure not retained")
	}
	recorder.ReceiverACKSent(stamp, 20, 1, true)
	requireReceiverState(test, recorder, key, "ACK_GENERATED")
}

func TestReceiverACKRequiresActualWrite(test *testing.T) {
	for _, result := range []string{"ok", "write_error", "no_rtp"} {
		recorder, key := receiverFixture(test)
		acceptSelected(recorder, 11)
		stamp := consumeSelected(recorder)
		point := Boundary{Direction: "tx", Stage: "carrier_queued", Result: "ok", MessageKnown: true, Sender: 9, Message: 30, Total: 1}
		point.CaptureACK(WithACKObservation(context.Background(), stamp, 20, 1))
		recorder.Boundary(point)
		requireReceiverState(test, recorder, key, "ACK_GENERATED")
		point.Stage = "ack_sent"
		recorder.Boundary(point)
		requireReceiverState(test, recorder, key, "ACK_GENERATED")
		point.Stage, point.Result = "carrier_written", result
		recorder.Boundary(point)
		expected := "ACK_GENERATED"
		if result == "ok" {
			expected = "COMPLETE"
		}
		proof := requireReceiverState(test, recorder, key, expected).Reliable
		if proof.ACK.Result != result || proof.ACK.SentNS == 0 {
			test.Fatal("actual write result missing")
		}
	}
}

func TestReceiverLateBindingAndAttemptIdentity(test *testing.T) {
	for _, acceptedMessage := range []uint32{10, 11, 12} {
		recorder, key := correlationFixture(test)
		for _, message := range []uint32{10, 11, 12} {
			correlationAttempt(recorder, message, 1)
		}
		acceptSelected(recorder, acceptedMessage)
		stamp := consumeSelected(recorder)
		recorder.ReceiverACKSent(stamp, 20, 1, true)
		for index := 0; index < 2101; index++ {
			recorder.Boundary(Boundary{Direction: "rx", Stage: "rtp_received", Result: "ok"})
		}
		if _, err := recorder.BindCorrelation(correlationDescriptor(key, 11, 1)); err != nil {
			test.Fatal(err)
		}
		expected := "CARRIER_COMPLETE"
		if acceptedMessage == 11 {
			expected = "COMPLETE"
		}
		requireReceiverState(test, recorder, key, expected)
	}
}

func TestReceiverCleanupIncompleteAndRestart(test *testing.T) {
	for _, mode := range []string{"cleanup", "timeout", "close"} {
		recorder, key := receiverFixture(test)
		acceptSelected(recorder, 11)
		consumeSelected(recorder)
		expected := "CLEANED"
		switch mode {
		case "cleanup":
			recorder.CorrelationStatus(key, true)
		case "timeout":
			recorder.mu.Lock()
			recorder.correlation.watches[key.Direction].deadline = time.Now().Add(-time.Second)
			recorder.mu.Unlock()
			expected = "EXPIRED"
		case "close":
			recorder.Add("CLEANUP", "COMPLETED", "NONE")
			expected = "CLOSED"
		}
		value := requireReceiverState(test, recorder, key, expected)
		if value.Reliable != nil || value.Descriptor != nil || len(value.Candidates) != 0 {
			test.Fatal("stale callback retained")
		}
		acceptSelected(recorder, 11)
		requireReceiverState(test, recorder, key, expected)
		restarted := New(key.Session, nil)
		if _, err := restarted.CorrelationStatus(key, false); err == nil {
			test.Fatal("restart reused nonce")
		}
	}
}
