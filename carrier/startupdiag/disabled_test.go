//go:build !fc_owner_diagnostic

package startupdiag

import (
	"context"
	"testing"
)

func TestPublicStartupDiagnosticsDisabled(test *testing.T) {
	parent := context.Background()
	ctx := Start(parent, 1)
	Failure(ctx, "HELLO_RECEIVE", context.DeadlineExceeded)
	Cancel(ctx)
	Complete(ctx, context.DeadlineExceeded)
	if ctx != parent || Snapshot(ctx) != nil {
		test.Fatal("public diagnostics enabled")
	}
}
