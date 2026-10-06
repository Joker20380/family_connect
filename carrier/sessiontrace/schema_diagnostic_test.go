//go:build fc_owner_diagnostic

package sessiontrace

import (
	"encoding/json"
	"strings"
	"testing"
)

func TestDiagnosticSchemaAndExport(test *testing.T) {
	var exported Event
	recorder := New(strings.Repeat("a", 64), func(event Event) bool { exported = event; return true })
	if !recorder.EnableEvidenceWatch(WatchTarget{Direction: "tx", Sequence: 19, Attempt: 1}) {
		test.Fatal("watch disabled")
	}
	point := Boundary{Direction: "tx", Stage: "rtp_written", Result: "ok", DataKnown: true, DataSequence: 19, AttemptKnown: true, Attempt: 1}
	point.RecordPicture(true, 123)
	recorder.Boundary(point)
	recorder.RecordConsumed(19, 20, 127)
	recorder.RecordBaseAdvanced(20, 127)
	recorder.Record(Event{Stage: "CARRIER_ACTIVITY", State: "ESTABLISHED", Reason: "NONE"})
	for _, value := range []any{recorder.Snapshot(), exported, CloneDelivery(exported.Delivery)} {
		raw, err := json.Marshal(value)
		if err != nil {
			test.Fatal(err)
		}
		for _, required := range []string{`"picture_known":true`, `"picture_id":123`, `"reliable_consumed"`, `"base_advanced"`, `"evidence_watch"`} {
			if !strings.Contains(string(raw), required) {
				test.Fatal("diagnostic export missing", required)
			}
		}
	}
}
