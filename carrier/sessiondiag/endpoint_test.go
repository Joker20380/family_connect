package sessiondiag

import (
	"context"
	"strings"
	"testing"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func TestFinalDeliverySampleAndIdempotentStop(test *testing.T) {
	trace := sessiontrace.New(strings.Repeat("ab", 32), nil)
	stop := Sample(context.Background(), trace, func() (uint64, uint64) { return 3, 4 }, func() *sessiontrace.Delivery {
		return &sessiontrace.Delivery{Flow: &sessiontrace.Flow{SendNext: 8, Pending: 8}}
	})
	stop()
	stop()
	value := trace.Snapshot()
	if len(value.Events) != 1 || value.FirstFailure != nil || value.Events[0].State != "COMPLETED" || value.Events[0].Delivery.Flow.Pending != 8 {
		test.Fatal("terminal sample lost or became failure")
	}
}
