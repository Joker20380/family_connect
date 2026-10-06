//go:build !fc_owner_diagnostic

package sessiontrace

import (
	"context"
	"encoding/json"
	"os"
	"strings"
	"testing"
)

func TestEvidenceWatchDisabledInProduct(test *testing.T) {
	recorder := New(strings.Repeat("a", 64), nil)
	if recorder.EnableEvidenceWatch(WatchTarget{Direction: "tx", Sequence: 19, Attempt: 1}) {
		test.Fatal("product watch enabled")
	}
}

func TestCorrelationNoDefaultEndpoint(test *testing.T) {
	recorder := New(strings.Repeat("a", 64), nil)
	before, _ := json.Marshal(recorder.Snapshot())
	recorder.CorrelationMedia(Boundary{Direction: "rx", Stage: "rtp_correlated", Result: "ok", MessageKnown: true, Sender: 1, Message: 2})
	after, _ := json.Marshal(recorder.Snapshot())
	if string(before) != string(after) {
		test.Fatal("expanded default telemetry")
	}
	if New(strings.Repeat("a", 64), nil).CorrelationCommand(`{"operation":"prearm"}`, "client") != `{"error":"disabled"}` {
		test.Fatal("default command enabled")
	}
	directory := test.TempDir()
	test.Setenv("FC_DIAGNOSTIC_CONTROL_DIR", directory)
	StartDiagnosticControl(context.Background(), New(strings.Repeat("a", 64), nil), "gateway")
	entries, err := os.ReadDir(directory)
	if err != nil || len(entries) != 0 {
		test.Fatal("default control endpoint available")
	}
}
