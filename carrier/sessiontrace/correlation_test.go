//go:build fc_owner_diagnostic

package sessiontrace

import (
	"encoding/json"
	"strings"
	"sync"
	"testing"
	"time"
)

func correlationFixture(test *testing.T) (*Recorder, CorrelationKey) {
	test.Helper()
	recorder := New(strings.Repeat("a", 64), nil)
	key := CorrelationKey{Session: recorder.Snapshot().SessionTag, Direction: "client_to_gateway", Sequence: 19, Attempt: 1}
	receipt, err := recorder.PrearmCorrelation(key, "rx")
	if err != nil {
		test.Fatal(err)
	}
	return recorder, receipt.Key
}

func correlationMedia(message, fragment, total uint32) MediaIdentity {
	return MediaIdentity{Fragment: fragment, Total: total, Picture: uint16(message*8 + fragment), Timestamp: message*100 + fragment, First: uint16(message*100 + fragment*3), Last: uint16(message*100 + fragment*3 + 2), Packets: 3}
}

func correlationPoint(recorder *Recorder, message, fragment, total uint32) {
	media := correlationMedia(message, fragment, total)
	point := Boundary{Direction: "rx", Stage: "rtp_received", Result: "ok", DataKnown: fragment == 0, DataSequence: 19, MessageKnown: true, Sender: 7, Message: message, Fragment: fragment, Total: total, PictureKnown: true, PictureID: media.Picture, FrameKnown: true, Timestamp: media.Timestamp, FirstRTP: media.First, LastRTP: media.Last, Packets: media.Packets}
	point.Stage = "rtp_correlated"
	recorder.CorrelationMedia(point)
	point.Stage = "vp8_reassembled"
	recorder.Boundary(point)
}

func correlationComplete(recorder *Recorder, message, total uint32) {
	recorder.Boundary(Boundary{Direction: "rx", Stage: "carrier_message_completed", Result: "ok", DataKnown: true, DataSequence: 19, MessageKnown: true, Sender: 7, Message: message, Total: total})
}

func correlationAttempt(recorder *Recorder, message, total uint32) {
	for fragment := int(total) - 1; fragment >= 0; fragment-- {
		correlationPoint(recorder, message, uint32(fragment), total)
	}
	correlationComplete(recorder, message, total)
}

func correlationDescriptor(key CorrelationKey, message, total uint32) CorrelationDescriptor {
	descriptor := CorrelationDescriptor{Key: key, Sender: 7, Message: message}
	for fragment := uint32(0); fragment < total; fragment++ {
		descriptor.Media = append(descriptor.Media, correlationMedia(message, fragment, total))
	}
	return descriptor
}

func TestCorrelationRetryMatrix(test *testing.T) {
	for _, scenario := range []struct {
		name          string
		before, after []uint32
		total         uint32
	}{
		{"late_original", []uint32{10}, []uint32{11}, 1},
		{"original_after_retry", []uint32{11}, []uint32{10}, 1},
		{"duplicate_original", []uint32{10, 10}, []uint32{11}, 1},
		{"duplicate_retry", []uint32{11, 11}, []uint32{11}, 1},
		{"fragmented", []uint32{10, 12}, []uint32{11, 10, 11}, 3},
		{"attempt2", []uint32{12}, []uint32{11, 12}, 1},
	} {
		test.Run(scenario.name, func(test *testing.T) {
			recorder, key := correlationFixture(test)
			for _, message := range scenario.before {
				correlationAttempt(recorder, message, scenario.total)
			}
			receipt, _ := recorder.CorrelationStatus(key, false)
			if receipt.State != "ARMED" {
				test.Fatal("finalized without descriptor", receipt.State)
			}
			descriptor := correlationDescriptor(key, 11, scenario.total)
			if _, err := recorder.BindCorrelation(descriptor); err != nil {
				test.Fatal(err)
			}
			receipt, _ = recorder.CorrelationStatus(key, false)
			if scenario.name == "late_original" && receipt.State != "BOUND" {
				test.Fatal("late attempt0 satisfied attempt1")
			}
			for _, message := range scenario.after {
				correlationAttempt(recorder, message, scenario.total)
			}
			for index := 0; index < 2100; index++ {
				recorder.Boundary(Boundary{Direction: "rx", Stage: "rtp_received", Result: "ok"})
			}
			receipt, _ = recorder.CorrelationStatus(key, false)
			if receipt.State != "COMPLETE" || receipt.Descriptor.Message != 11 {
				test.Fatal("selected proof lost", receipt)
			}
			if _, err := recorder.BindCorrelation(descriptor); err == nil {
				test.Fatal("replay accepted")
			}
		})
	}
}

func TestCorrelationFragmentMixAndIdentity(test *testing.T) {
	for _, field := range []string{"fragment_mix", "picture", "timestamp", "range"} {
		test.Run(field, func(test *testing.T) {
			recorder, key := correlationFixture(test)
			descriptor := correlationDescriptor(key, 11, 2)
			if field == "picture" {
				descriptor.Media[0].Picture++
			}
			if field == "timestamp" {
				descriptor.Media[0].Timestamp++
			}
			if field == "range" {
				descriptor.Media[0].First++
				descriptor.Media[0].Last++
			}
			if _, err := recorder.BindCorrelation(descriptor); err != nil {
				test.Fatal(err)
			}
			if field == "fragment_mix" {
				correlationPoint(recorder, 10, 0, 2)
				correlationPoint(recorder, 11, 1, 2)
				correlationComplete(recorder, 11, 2)
			} else {
				correlationAttempt(recorder, 11, 2)
			}
			receipt, _ := recorder.CorrelationStatus(key, false)
			if receipt.State == "COMPLETE" {
				test.Fatal("mixed identity accepted")
			}
		})
	}
}

func TestCorrelationCleanupTimeoutSessionPrivacy(test *testing.T) {
	for _, mode := range []string{"cleanup", "timeout", "close"} {
		test.Run(mode, func(test *testing.T) {
			recorder, key := correlationFixture(test)
			correlationAttempt(recorder, 10, 2)
			wrong := correlationDescriptor(key, 11, 2)
			for _, field := range []string{"session", "generation", "direction", "sequence", "attempt"} {
				copy := wrong
				switch field {
				case "session":
					copy.Key.Session = strings.Repeat("b", 64)
				case "generation":
					copy.Key.Generation = strings.Repeat("b", 32)
				case "direction":
					copy.Key.Direction = "gateway_to_client"
				case "sequence":
					copy.Key.Sequence++
				case "attempt":
					copy.Key.Attempt++
				}
				if _, err := recorder.BindCorrelation(copy); err == nil {
					test.Fatal("wrong key accepted", field)
				}
			}
			if mode == "cleanup" {
				recorder.CorrelationStatus(key, true)
			}
			if mode == "timeout" {
				recorder.mu.Lock()
				recorder.correlation.watches[key.Direction].deadline = time.Now().Add(-time.Second)
				recorder.mu.Unlock()
			}
			if mode == "close" {
				recorder.Add("CLEANUP", "COMPLETED", "NONE")
			}
			receipt, _ := recorder.CorrelationStatus(key, false)
			if len(receipt.Candidates) != 0 || receipt.Descriptor != nil {
				test.Fatal("not purged")
			}
			if _, err := recorder.BindCorrelation(wrong); err == nil {
				test.Fatal("revived")
			}
			fresh, freshKey := correlationFixture(test)
			if freshKey.Generation == key.Generation {
				test.Fatal("generation reused")
			}
			if _, err := fresh.BindCorrelation(wrong); err == nil {
				test.Fatal("cross generation")
			}
			raw, _ := json.Marshal(receipt)
			for _, forbidden := range []string{"payload", "destination", "credential", "private_key", "token"} {
				if strings.Contains(string(raw), forbidden) {
					test.Fatal("privacy", forbidden)
				}
			}
		})
	}
}

func TestCorrelationBoundedOverflow(test *testing.T) {
	recorder, key := correlationFixture(test)
	for message := uint32(1); message <= CandidateLimit+1; message++ {
		correlationAttempt(recorder, message, 1)
	}
	receipt, _ := recorder.CorrelationStatus(key, false)
	if receipt.State != "OVERFLOW" || len(receipt.Candidates) != 0 {
		test.Fatal("unbounded capture")
	}
}

func TestCorrelationConcurrentDirectionAndCopies(test *testing.T) {
	recorder, key := correlationFixture(test)
	var workers sync.WaitGroup
	workers.Add(2)
	go func() {
		defer workers.Done()
		for index := 0; index < 200; index++ {
			recorder.CorrelationStatus(key, false)
		}
	}()
	go func() {
		defer workers.Done()
		for index := 0; index < 200; index++ {
			recorder.CorrelationMedia(Boundary{Direction: "tx", Stage: "rtp_correlated", Result: "ok", DataKnown: true, DataSequence: 19, MessageKnown: true, Sender: 7, Message: 11, Total: 1})
		}
	}()
	correlationAttempt(recorder, 11, 1)
	workers.Wait()
	descriptor := correlationDescriptor(key, 11, 1)
	receipt, err := recorder.BindCorrelation(descriptor)
	if err != nil || receipt.State != "COMPLETE" || len(receipt.Candidates) != 1 {
		test.Fatal("reverse direction interference")
	}
	delete(receipt.Candidates[0].Media, 0)
	receipt.Descriptor.Media[0].Picture++
	retained, _ := recorder.CorrelationStatus(key, false)
	if len(retained.Candidates[0].Media) != 1 || retained.Descriptor.Media[0] != descriptor.Media[0] {
		test.Fatal("export alias")
	}
}

func TestCorrelationAutomaticExpiry(test *testing.T) {
	recorder, key := correlationFixture(test)
	correlationAttempt(recorder, 11, 1)
	recorder.BindCorrelation(correlationDescriptor(key, 11, 1))
	recorder.mu.Lock()
	watch := recorder.correlation.watches[key.Direction]
	watch.deadline = time.Now().Add(time.Millisecond)
	watch.timer.Reset(time.Millisecond)
	recorder.mu.Unlock()
	deadline := time.Now().Add(time.Second)
	for time.Now().Before(deadline) {
		recorder.mu.Lock()
		purged := watch.value.State == "EXPIRED" && len(watch.value.Candidates) == 0 && watch.value.Descriptor == nil
		recorder.mu.Unlock()
		if purged {
			return
		}
		time.Sleep(time.Millisecond)
	}
	test.Fatal("idle timer did not purge selected proof without a status query")
}

func TestCorrelationWriterBeforeQueueReceipt(test *testing.T) {
	recorder := New(strings.Repeat("a", 64), nil)
	key := CorrelationKey{Session: recorder.Snapshot().SessionTag, Direction: "client_to_gateway", Sequence: 19, Attempt: 1, Generation: strings.Repeat("b", 32)}
	if _, err := recorder.PrearmCorrelation(key, "tx"); err != nil {
		test.Fatal(err)
	}
	point := Boundary{Direction: "tx", Stage: "carrier_written", Result: "incomplete", DataKnown: true, DataSequence: 19, AttemptKnown: true, Attempt: 1, MessageKnown: true, Sender: 7, Message: 11, Total: 1}
	recorder.Boundary(point)
	point.Stage, point.Result = "rtp_written", "ok"
	point.FrameKnown, point.PictureKnown = true, true
	point.PictureID, point.Timestamp, point.FirstRTP, point.LastRTP, point.Packets = 3, 4, 5, 5, 1
	recorder.Boundary(point)
	receipt, _ := recorder.CorrelationStatus(key, false)
	if receipt.State != "COMPLETE" || receipt.Descriptor == nil {
		test.Fatal("writer callback raced queue receipt", receipt)
	}
	if !recorder.EnableEvidenceWatch(WatchTarget{Direction: "tx", Sequence: 19, Attempt: 1}) {
		test.Fatal("legacy sender fixture")
	}
	recorder.CorrelationStatus(key, true)
	if recorder.Snapshot().Watch != nil {
		test.Fatal("legacy selected sender proof survived cleanup")
	}
}
