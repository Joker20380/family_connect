//go:build !fc_owner_diagnostic

package sessiontrace

type faultControl struct{}

func evidenceWatchEnabled() bool { return false }

func (recorder *Recorder) FaultCommand(command string) FaultReceipt {
	return FaultReceipt{Schema: 1, State: "DISABLED", Target: "outbound_data_attempt0_after_established"}
}

func (recorder *Recorder) DropDiagnostic(point Boundary) bool { return false }

func (recorder *Recorder) faultEvent(event Event) {}

func (recorder *Recorder) faultSnapshot() *FaultReceipt { return nil }
