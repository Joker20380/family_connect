//go:build !fc_owner_diagnostic

package sessiontrace

import (
	"strings"
	"testing"
)

func TestFaultDefaultBuildCannotArm(test *testing.T) {
	recorder := New(strings.Repeat("a", 64), nil)
	recorder.Add("FAMILY_TLS", "ESTABLISHED", "NONE")
	recorder.Add("GATEWAY_SESSION", "ESTABLISHED", "NONE")
	if recorder.FaultCommand("arm").State != "DISABLED" || recorder.DropDiagnostic(Boundary{Direction: "tx", DataKnown: true, AttemptKnown: true}) || recorder.Snapshot().Fault != nil {
		test.Fatal("default build exposes fault injection")
	}
}
