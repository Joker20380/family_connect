//go:build fc_owner_diagnostic

package reliablestream

import (
	"bytes"
	"context"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func TestOperationalFaultRetriesThroughRuntime(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	trace := sessiontrace.New(strings.Repeat("a", 64), nil)
	leftEndpoint, rightEndpoint := endpoints()
	left, err := New(sessiontrace.With(ctx, trace), leftEndpoint, DefaultConfig())
	if err != nil {
		test.Fatal(err)
	}
	defer left.Close()
	right, err := New(ctx, rightEndpoint, DefaultConfig())
	if err != nil {
		test.Fatal(err)
	}
	defer right.Close()
	trace.Add("FAMILY_TLS", "ESTABLISHED", "NONE")
	trace.Add("GATEWAY_SESSION", "ESTABLISHED", "NONE")
	if !trace.FaultCommand("arm").Armed {
		test.Fatal("not armed")
	}
	payload := []byte("operational-one-shot-test")
	if err = left.SendContext(ctx, payload); err != nil {
		test.Fatal(err)
	}
	data, err := right.Recv(ctx)
	if err != nil || !bytes.Equal(data, payload) {
		test.Fatal("retry recovery", err)
	}
	receipt := trace.FaultCommand("status")
	if receipt.Count != 1 || !receipt.Consumed || receipt.Armed {
		test.Fatal("fault receipt", receipt)
	}
	watch := trace.Snapshot().Watch
	if watch == nil || watch.Target.Direction != "tx" || watch.Target.Sequence != receipt.Sequence || watch.Target.Attempt != 1 {
		test.Fatal("selected retry not pinned automatically", watch)
	}
	seenRetry := false
	for _, point := range trace.Snapshot().Boundaries.Events {
		if point.Stage == "reliable_send" && point.DataSequence == receipt.Sequence && point.Attempt == 1 {
			seenRetry = true
		}
	}
	if !seenRetry {
		test.Fatal("runtime retry not observed")
	}
	if err = left.SendContext(ctx, payload); err != nil {
		test.Fatal(err)
	}
	data, err = right.Recv(ctx)
	if err != nil || !bytes.Equal(data, payload) || trace.FaultCommand("status").Count != 1 {
		test.Fatal("unrelated next DATA", err)
	}
}
