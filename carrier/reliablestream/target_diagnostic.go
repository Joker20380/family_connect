//go:build fc_owner_diagnostic

package reliablestream

import (
	"context"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func (stream *Stream) bindDiagnosticAllocation(ctx context.Context) {
	trace := sessiontrace.From(ctx)
	trace.BindFaultAllocation(func(check func(sessiontrace.Flow)) {
		stream.mu.Lock()
		defer stream.mu.Unlock()
		if ctx.Err() == nil && stream.err == nil && stream.state.remote != (epoch{}) {
			check(stream.state.flow())
		}
	}, func() bool { return ctx.Err() == nil })
}
