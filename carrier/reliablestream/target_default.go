//go:build !fc_owner_diagnostic

package reliablestream

import "context"

func (stream *Stream) bindDiagnosticAllocation(context.Context) {}
