//go:build fc_owner_diagnostic && !linux

package sessiontrace

import "context"

func StartDiagnosticControl(ctx context.Context, recorder *Recorder, role string) {
	context.AfterFunc(ctx, recorder.closeCorrelation)
}
