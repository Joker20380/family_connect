package sessiontrace

import (
	"encoding/json"
	"strings"
	"testing"
)

func TestProductionIdentifier(test *testing.T) {
	id := strings.Repeat("ab", 32)
	tag, status := Tag(id)
	upper, _ := Tag(strings.ToUpper(id))
	other, _ := Tag(strings.Repeat("ac", 32))
	if status != "VALID" || len(tag) != 64 || tag == id || tag != upper || tag == other {
		test.Fatal("production correlation contract")
	}
	if tag != "e1b8ac9f42012f22097916fece757a4f004325f58c07a9b3a24259b27f9530e3" {
		test.Fatal("diagnostic v2 domain-separated vector changed")
	}
	for _, bad := range []string{"", strings.Repeat("ab", 16), strings.Repeat("a", 63), strings.Repeat("a", 65), strings.Repeat("z", 64), " " + id} {
		value, result := Tag(bad)
		if value != "" || result == "VALID" {
			test.Fatal("invalid identifier correlated")
		}
	}
}

func TestFirstFailureBoundPrivacyAndSnapshots(test *testing.T) {
	recorder := New(strings.Repeat("ab", 32), func(Event) bool { return false })
	recorder.Add("WEBSOCKET", "CLOSED", "SIGNAL_WS_CLOSE")
	recorder.Add("CLEANUP", "FAILED", "RECOVERY_CLEANUP_FAILED")
	for index := 0; index < Limit+2; index++ {
		recorder.Add("HEARTBEAT", "TX", "NONE")
	}
	recorder.Add("secret room", "FAILED", "secret token")
	value := recorder.Snapshot()
	if len(value.Events) != Limit || value.Dropped != 5 || value.ExportDropped != Limit+4 || value.FirstFailure.Reason != "SIGNAL_WS_CLOSE" {
		test.Fatal("bounded first failure")
	}
	value.Events[0].Stage = "secret"
	value.FirstFailure.Reason = "secret"
	raw, _ := json.Marshal(recorder.Snapshot())
	if strings.Contains(string(raw), "secret") {
		test.Fatal("privacy or alias")
	}
	closed := New(strings.Repeat("cd", 32), nil)
	closed.Add("LOCAL_CLOSE", "STARTED", "NONE")
	closed.Add("FAMILY_TLS", "CLOSED", "FAMILY_TLS_EOF")
	if closed.Snapshot().FirstFailure != nil {
		test.Fatal("local cleanup became primary failure")
	}
}
