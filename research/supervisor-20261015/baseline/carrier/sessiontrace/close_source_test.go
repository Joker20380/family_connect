package sessiontrace

import (
	"encoding/json"
	"strings"
	"testing"
)

func TestFirstCloseSurvivesCleanupAndRingEviction(test *testing.T) {
	recorder := New(strings.Repeat("a", 64), nil)
	recorder.Record(Event{Stage: "CARRIER", State: "CLOSED", Reason: "CARRIER_ERROR", CloseSource: "SIGNAL_READ"})
	recorder.Record(Event{Stage: "LOCAL_CLOSE", State: "STARTED", Reason: "NONE", CloseSource: "UPPER_CLOSE"})
	for index := 0; index < Limit+1; index++ {
		recorder.Add("CLEANUP", "COMPLETED", "NONE")
	}
	first := recorder.Snapshot().FirstClose
	if first == nil || first.Sequence != 1 || first.CloseSource != "SIGNAL_READ" {
		test.Fatal("first initiator lost", first)
	}
	first.CloseSource = "UNKNOWN"
	if recorder.Snapshot().FirstClose.CloseSource != "SIGNAL_READ" {
		test.Fatal("snapshot aliases retained first close")
	}
}

func TestCloseSourcePrivacyAndLeaseBounds(test *testing.T) {
	recorder := New(strings.Repeat("a", 64), nil)
	recorder.Record(Event{Stage: "AUTHORIZED", State: "STARTED", Reason: "NONE", LeaseDeadlineMS: 1791650000000})
	recorder.Record(Event{Stage: "CARRIER", State: "CLOSED", Reason: "CARRIER_ERROR", CloseSource: "secret-room", LeaseDeadlineMS: -1})
	snapshot := recorder.Snapshot()
	if snapshot.Events[0].LeaseDeadlineMS != 1791650000000 || snapshot.FirstClose.CloseSource != "UNKNOWN" || snapshot.FirstClose.LeaseDeadlineMS != 0 {
		test.Fatal("unsafe source/deadline projection")
	}
	raw, _ := json.Marshal(snapshot)
	if strings.Contains(string(raw), "secret") {
		test.Fatal("raw error leaked")
	}
}
