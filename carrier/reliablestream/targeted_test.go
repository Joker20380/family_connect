//go:build fc_owner_diagnostic

package reliablestream

import (
	"context"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func TestTargetedRealAllocationOrders(test *testing.T) {
	for _, before := range []bool{true, false} {
		test.Run(map[bool]string{true: "writer_before_arm", false: "writer_after_arm"}[before], func(test *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			trace := sessiontrace.New(strings.Repeat("a", 64), nil)
			receiver := sessiontrace.New(strings.Repeat("a", 64), nil)
			leftEndpoint, rightEndpoint := endpoints()
			left, err := New(sessiontrace.With(ctx, trace), leftEndpoint, DefaultConfig())
			if err != nil {
				test.Fatal(err)
			}
			defer left.Close()
			right, err := New(sessiontrace.With(ctx, receiver), rightEndpoint, DefaultConfig())
			if err != nil {
				test.Fatal(err)
			}
			defer right.Close()
			select {
			case <-left.ready:
			case <-ctx.Done():
				test.Fatal(ctx.Err())
			}
			select {
			case <-right.ready:
			case <-ctx.Done():
				test.Fatal(ctx.Err())
			}
			trace.Add("FAMILY_TLS", "ESTABLISHED", "NONE")
			trace.Add("GATEWAY_SESSION", "ESTABLISHED", "NONE")
			prearm, err := receiver.PrearmCorrelation(sessiontrace.CorrelationKey{Session: trace.Snapshot().SessionTag, Direction: "client_to_gateway", Sequence: 0, Attempt: 1}, "rx")
			if err != nil {
				test.Fatal(err)
			}
			if _, err = trace.PrearmCorrelation(prearm.Key, "tx"); err != nil {
				test.Fatal(err)
			}
			if err = right.SendContext(ctx, []byte("reverse while operator prepares")); err != nil {
				test.Fatal(err)
			}
			if _, err = left.Recv(ctx); err != nil {
				test.Fatal(err)
			}
			if before {
				if err = left.SendContext(ctx, []byte("competing queued write")); err != nil {
					test.Fatal(err)
				}
				if receipt := trace.TargetedArm(prearm); receipt.Result != "PREPARATION_ABORTED" || receipt.Reason != "HEAD_NOT_FREE" {
					test.Fatal(receipt)
				}
			} else {
				if receipt := trace.TargetedArm(prearm); receipt.Result != "ARMED" {
					test.Fatal(receipt)
				}
				if err = left.SendContext(ctx, []byte("any normal writer")); err != nil {
					test.Fatal(err)
				}
			}
			if _, err = right.Recv(ctx); err != nil {
				test.Fatal(err)
			}
			fault := trace.FaultCommand("status")
			want := uint32(1)
			if before {
				want = 0
			}
			if fault.Count != want || fault.Armed || fault.Sequence != 0 {
				test.Fatal(fault)
			}
		})
	}
}
