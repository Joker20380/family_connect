package familysession

import (
	"context"
	"errors"
	"io"
	"strings"
	"testing"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func TestTLSFailureDiagnosticClassification(test *testing.T) {
	for _, item := range []struct {
		failure error
		reason  string
	}{{io.EOF, "FAMILY_TLS_EOF"}, {io.ErrUnexpectedEOF, "FAMILY_TLS_EOF"}, {errors.New("secret credential"), "FAMILY_TLS_ERROR"}} {
		trace := sessiontrace.New(strings.Repeat("ab", 32), nil)
		ctx := sessiontrace.With(context.Background(), trace)
		traceFailure(ctx, trace, item.failure)
		if trace.Snapshot().FirstFailure.Reason != item.reason {
			test.Fatal("TLS reason")
		}
	}
	trace := sessiontrace.New(strings.Repeat("ab", 32), nil)
	ctx, cancel := context.WithCancel(sessiontrace.With(context.Background(), trace))
	cancel()
	traceFailure(ctx, trace, io.EOF)
	if trace.Snapshot().FirstFailure != nil {
		test.Fatal("local cancellation promoted to causal failure")
	}
}
