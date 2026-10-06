//go:build fc_owner_diagnostic

package telemost

import (
	"bytes"
	"context"
	"encoding/binary"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func TestCorrelationPionRetryDiscrimination(test *testing.T) {
	for _, mode := range []string{"none", "late_message", "late_rtp", "duplicate", "reorder"} {
		test.Run(mode, func(test *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			sender, receiver := headLossPair(test, ctx, 19, mode)
			defer sender.Close()
			defer receiver.Close()
			left, right := sender.cfg.Trace, receiver.cfg.Trace
			armed, err := right.PrearmCorrelation(sessiontrace.CorrelationKey{Session: right.Snapshot().SessionTag, Direction: "client_to_gateway", Sequence: 19, Attempt: 1}, "rx")
			if err != nil {
				test.Fatal(err)
			}
			if _, err := left.PrearmCorrelation(armed.Key, "tx"); err != nil {
				test.Fatal(err)
			}
			data := diagnosticData()
			binary.BigEndian.PutUint64(data[40:], 19)
			for attempt := uint32(0); attempt < 3; attempt++ {
				if err := sender.SendContext(sessiontrace.WithAttempt(ctx, 19, attempt), data); err != nil {
					test.Fatal(err)
				}
			}
			if mode == "duplicate" {
				receiver.receive(sender.attempts[0].packets)
				receiver.receive(sender.attempts[1].packets)
				fragments, _ := encodeFragments(sender.senderID, sender.attempts[1].message, data)
				for _, fragment := range fragments {
					receiver.reassembler.ingest(fragment)
				}
			}
			before, _ := right.CorrelationStatus(armed.Key, false)
			if before.State != "ARMED" {
				test.Fatal("premature finalization", before)
			}
			descriptor, _ := left.CorrelationStatus(armed.Key, false)
			if descriptor.Descriptor == nil || len(descriptor.Descriptor.Media) != 3 {
				test.Fatal("sender incomplete", descriptor)
			}
			selected, err := right.BindCorrelation(*descriptor.Descriptor)
			if err != nil || selected.State != "COMPLETE" {
				test.Fatalf("exact selected proof incomplete: %+v / %v", selected, err)
			}
			if selected.Descriptor.Message != sender.attempts[1].message || selected.Descriptor.Message == sender.attempts[0].message || selected.Descriptor.Message == sender.attempts[2].message {
				test.Fatal("attempt identity mixed")
			}
			observer := rtpBoundary{trace: right, stage: "rtp_correlated", direction: "rx", correlationOnly: true}
			for _, packet := range sender.attempts[1].packets {
				before, _ := packet.Marshal()
				observer.packet(&packet.Header, packet.Payload, "ok")
				after, _ := packet.Marshal()
				if !bytes.Equal(before, after) {
					test.Fatal("observer modified RTP bytes")
				}
			}
		})
	}
}
