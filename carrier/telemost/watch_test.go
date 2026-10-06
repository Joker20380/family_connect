//go:build fc_owner_diagnostic

package telemost

import (
	"bytes"
	"context"
	"fmt"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/reliablestream"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func TestSelectedRetryPinnedAcrossBoundPionAndRingFlood(test *testing.T) {
	for _, size := range []int{1, reliablestream.DefaultConfig().Payload} {
		test.Run(fmt.Sprint(size), func(test *testing.T) { selectedRetryPinned(test, size) })
	}
}

func selectedRetryPinned(test *testing.T, size int) {
	test.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 12*time.Second)
	defer cancel()
	leftEndpoint, rightEndpoint := headLossPair(test, ctx, 19, "none")
	rightEndpoint.configureReceiveObservation()
	leftTrace, rightTrace := leftEndpoint.cfg.Trace, rightEndpoint.cfg.Trace
	left, err := reliablestream.New(sessiontrace.With(ctx, leftTrace), leftEndpoint, reliablestream.DefaultConfig())
	if err != nil {
		test.Fatal(err)
	}
	defer left.Close()
	right, err := reliablestream.New(sessiontrace.With(ctx, rightTrace), rightEndpoint, reliablestream.DefaultConfig())
	if err != nil {
		test.Fatal(err)
	}
	defer right.Close()
	for sequence := 0; sequence < 19; sequence++ {
		if err := left.SendContext(ctx, []byte("warmup")); err != nil {
			test.Fatal(err)
		}
		if _, err := right.Recv(ctx); err != nil {
			test.Fatal(err)
		}
	}
	waitHeadState(test, ctx, func() bool { return left.Stats().Flow.SendBase == 19 })
	if !leftTrace.EnableEvidenceWatch(sessiontrace.WatchTarget{Direction: "tx", Sequence: 19, Attempt: 1}) {
		test.Fatal("paired watch not active")
	}
	armed, err := rightTrace.PrearmCorrelation(sessiontrace.CorrelationKey{Session: rightTrace.Snapshot().SessionTag, Direction: "client_to_gateway", Sequence: 19, Attempt: 1}, "rx")
	if err != nil {
		test.Fatal(err)
	}
	if _, err := leftTrace.PrearmCorrelation(armed.Key, "tx"); err != nil {
		test.Fatal(err)
	}
	leftTrace.Add("FAMILY_TLS", "ESTABLISHED", "NONE")
	leftTrace.Add("GATEWAY_SESSION", "ESTABLISHED", "NONE")
	if !leftTrace.FaultCommand("arm").Armed {
		test.Fatal("fault not armed")
	}
	for offset := 0; offset < 8; offset++ {
		if err := left.SendContext(ctx, bytes.Repeat([]byte{byte(offset + 1)}, size)); err != nil {
			test.Fatal(err)
		}
	}
	for offset := 0; offset < 8; offset++ {
		data, err := right.Recv(ctx)
		if err != nil || !bytes.Equal(data, bytes.Repeat([]byte{byte(offset + 1)}, size)) {
			test.Fatal("ordered recovery", err)
		}
	}
	waitHeadState(test, ctx, func() bool { return left.Stats().Flow.SendBase == 27 })
	for _, trace := range []*sessiontrace.Recorder{leftTrace, rightTrace} {
		for index := 0; index < 2000; index++ {
			trace.Boundary(sessiontrace.Boundary{Direction: "rx", Stage: "rtp_received", Result: "ok"})
		}
	}
	sent, err := leftTrace.CorrelationStatus(armed.Key, false)
	if err != nil || sent.State != "COMPLETE" || sent.Descriptor == nil {
		test.Fatalf("sender descriptor incomplete: %+v %v", sent, err)
	}
	before, _ := rightTrace.CorrelationStatus(armed.Key, false)
	if before.State != "ARMED" {
		test.Fatalf("finalized before descriptor: %+v", before)
	}
	received, err := rightTrace.BindCorrelation(*sent.Descriptor)
	if err != nil || received.State != "COMPLETE" {
		test.Fatalf("receiver incomplete: %+v %v", received, err)
	}
	proof := received.Reliable
	if proof == nil || proof.Accepted == nil || proof.Consumed == nil || proof.ACK == nil || proof.Accepted.Sequence != 19 || proof.Consumed.Sequence != 19 || proof.Consumed.Before.Next != 19 || proof.Consumed.After.Next != 20 || proof.ACK.Base != 20 || proof.ACK.Result != "ok" || proof.ACK.SentNS == 0 {
		test.Fatalf("exact Reliable/ACK callbacks not retained: %+v", proof)
	}
	if len(sent.Descriptor.Media) < 1 || (size > 8192 && len(sent.Descriptor.Media) < 2) {
		test.Fatal("fragments missing")
	}
	if leftTrace.FaultCommand("status").Count != 1 {
		test.Fatal("multiple faults")
	}
	test.Logf("seq19 attempt1 pinned through actual local Pion packetization/receive, VP8, carrier, DATA, consume, ACK and base despite 2000 later boundaries; no external network")
}
