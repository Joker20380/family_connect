//go:build fc_owner_diagnostic

package sessiontrace

import (
	"encoding/json"
	"strings"
	"sync"
	"testing"
	"time"
)

func TestWatchPinnedAcrossEvictionExportCleanupAndCopies(test *testing.T) {
	var exported Event
	recorder := New(strings.Repeat("a", 64), func(event Event) bool { exported = event; return false })
	if !recorder.EnableEvidenceWatch(WatchTarget{Direction: "tx", Sequence: 19, Attempt: 1}) {
		test.Fatal("watch refused")
	}
	point := Boundary{Direction: "tx", Result: "ok", DataKnown: true, DataSequence: 19, AttemptKnown: true, Attempt: 1}
	for _, stage := range []string{"reliable_send", "carrier_queued", "rtp_written"} {
		point.Stage = stage
		if stage != "reliable_send" {
			point.MessageKnown, point.Sender, point.Message = true, 3220232525, 842410499
		}
		recorder.Boundary(point)
	}
	for index := 0; index < 1606; index++ {
		recorder.Boundary(Boundary{Direction: "rx", Stage: "rtp_received", Result: "ok"})
	}
	correlated := recorder.MessageAttempt(Boundary{MessageKnown: true, Sender: 3220232525, Message: 842410499})
	if !correlated.AttemptKnown || correlated.Attempt != 1 || correlated.DataSequence != 19 {
		test.Fatal("pinned correlation evicted")
	}
	for _, stage := range []string{"ack_received", "base_advanced"} {
		recorder.Boundary(Boundary{Direction: "rx", Stage: stage, Result: "ok", ACKBase: 20, ACKMask: 127})
	}
	recorder.Add("CARRIER_ACTIVITY", "ESTABLISHED", "NONE")
	if exported.Delivery.Watch.State != "COMPLETE" || len(exported.Delivery.Watch.Events) != 5 {
		test.Fatal("watch incomplete", exported)
	}
	delete(exported.Delivery.Watch.Events, "rtp_written")
	recorder.Add("CLEANUP", "COMPLETED", "NONE")
	if _, exists := exported.Delivery.Watch.Events["rtp_written"]; !exists {
		test.Fatal("export alias or cleanup loss")
	}
	if recorder.Snapshot().ExportDropped != 2 {
		test.Fatal("failed exports not counted")
	}
	copy := recorder.Snapshot()
	delete(copy.Watch.Events, "reliable_send")
	if len(recorder.Snapshot().Watch.Events) != 5 {
		test.Fatal("snapshot alias")
	}
	if recorder.EnableEvidenceWatch(WatchTarget{Direction: "rx", Sequence: 20, Attempt: 1}) {
		test.Fatal("rearmed")
	}
	encoded, err := json.Marshal(recorder.Snapshot().Watch)
	if err != nil || strings.Contains(string(encoded), "payload") || strings.Contains(string(encoded), "private_key") {
		test.Fatal("privacy", err)
	}
}

func TestWatchWrongAttemptDirectionIdentityAndTimeout(test *testing.T) {
	recorder := New(strings.Repeat("b", 64), nil)
	if recorder.EnableEvidenceWatch(WatchTarget{Direction: "bad", Sequence: 19, Attempt: 1}) || recorder.EnableEvidenceWatch(WatchTarget{Direction: "tx", Sequence: 19}) {
		test.Fatal("invalid watch accepted")
	}
	recorder.EnableEvidenceWatch(WatchTarget{Direction: "tx", Sequence: 19, Attempt: 1})
	for _, point := range []Boundary{
		{Direction: "tx", Stage: "reliable_send", Result: "ok", DataKnown: true, DataSequence: 19, AttemptKnown: true},
		{Direction: "rx", Stage: "rtp_received", Result: "ok", DataKnown: true, DataSequence: 19},
		{Direction: "tx", Stage: "reliable_send", Result: "ok", DataKnown: true, DataSequence: 20, AttemptKnown: true, Attempt: 1},
		{Direction: "rx", Stage: "ack_received", Result: "ok", ACKBase: 19, ACKMask: 255},
		{Direction: "rx", Stage: "ack_received", Result: "stale", ACKBase: 20},
	} {
		recorder.Boundary(point)
	}
	if len(recorder.Snapshot().Watch.Events) != 0 {
		test.Fatal("unrelated proof accepted")
	}
	recorder.mu.Lock()
	recorder.watch.deadline = time.Now().Add(-time.Second)
	recorder.mu.Unlock()
	if recorder.Snapshot().Watch.State != "TIMEOUT" {
		test.Fatal("timeout")
	}
	recorder.Boundary(Boundary{Direction: "rx", Stage: "ack_received", Result: "ok", ACKBase: 20})
	if len(recorder.Snapshot().Watch.Events) != 0 {
		test.Fatal("post-timeout collection")
	}
}

func TestLegacyReceiverWatchRejected(test *testing.T) {
	recorder := New(strings.Repeat("c", 64), nil)
	if recorder.EnableEvidenceWatch(WatchTarget{Direction: "rx", Sequence: 19, Attempt: 1}) {
		test.Fatal("ambiguous legacy receiver API accepted")
	}
}

func TestWatchConcurrentAndClosed(test *testing.T) {
	recorder := New(strings.Repeat("d", 64), nil)
	recorder.EnableEvidenceWatch(WatchTarget{Direction: "tx", Sequence: 19, Attempt: 1})
	var workers sync.WaitGroup
	for worker := 0; worker < 8; worker++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			for index := 0; index < 200; index++ {
				recorder.Boundary(Boundary{Direction: "rx", Stage: "rtp_received", Result: "ok", DataKnown: true, DataSequence: 19})
				recorder.Snapshot()
			}
		}()
	}
	workers.Wait()
	recorder.Add("LOCAL_CLOSE", "STARTED", "NONE")
	if recorder.Snapshot().Watch.State != "CLOSED" {
		test.Fatal("collection not closed")
	}
}
