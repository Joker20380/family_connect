package reliablestream

import (
	"bytes"
	"context"
	"errors"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func TestFreshACKWithoutProgressDoesNotResetRetryBudget(test *testing.T) {
	for _, recoverGap := range []bool{false, true} {
		name := "persistent_gap"
		if recoverGap {
			name = "recovered_gap"
		}
		test.Run(name, func(test *testing.T) {
			states := connectedEngines()
			sender, receiver := states[0], states[1]
			now := sender.started
			payload := []byte("bounded-test-block")
			for index := 0; index < sender.config.SendWindow; index++ {
				packet, err := sender.send(payload, now)
				if err != nil {
					test.Fatal(err)
				}
				if index > 0 {
					if _, err = receiver.input(packet, now); err != nil {
						test.Fatal(err)
					}
				}
			}
			for attempt := 1; attempt <= sender.config.MaxRetries+1; attempt++ {
				tickAt := now.Add(time.Duration(attempt) * sender.config.RTO)
				if _, err := sender.input(receiver.ack(), tickAt.Add(-200*time.Millisecond)); err != nil {
					test.Fatal(err)
				}
				packets, err := sender.tick(tickAt)
				if attempt > sender.config.MaxRetries {
					trace := sender.failureTrace
					if !errors.Is(err, ErrExhausted) || trace.Reason != "RELIABLE_RETRY_EXHAUSTED" || trace.ReliableRetries != 8 || trace.ReliablePending != 8 || trace.ReliableSacked != 0 || trace.ReliableACKAgeMS != 200 || trace.ReliableProgressAgeMS != 9000 {
						test.Fatal("fresh ACK hid persistent missing DATA", err, trace)
					}
					return
				}
				if err != nil {
					test.Fatal(err)
				}
				retries := 0
				for _, packet := range packets {
					if packet.kind != dataFrame {
						continue
					}
					retries++
					if packet.seq != 0 {
						test.Fatal("retransmitted SACKed block")
					}
					if recoverGap && attempt == 4 {
						if _, err = receiver.input(packet, tickAt); err != nil {
							test.Fatal(err)
						}
					}
				}
				if retries != 1 {
					test.Fatal("missing selective retry", retries)
				}
				if recoverGap && attempt == 4 {
					for index := 0; index < sender.config.SendWindow; index++ {
						data, ack := receiver.consume()
						if !bytes.Equal(data, payload) {
							test.Fatal("gap recovery lost ordered data")
						}
						if _, err = sender.input(ack, tickAt); err != nil {
							test.Fatal(err)
						}
					}
					if len(sender.sent) != 0 || !sender.writable() || sender.failureTrace.Reason != "" {
						test.Fatal("recovered stream did not release its window")
					}
					return
				}
			}
		})
	}
}

func TestExhaustionBranchesRetainBoundedEvidence(test *testing.T) {
	for _, kind := range []string{"handshake", "frame", "retry", "sacked"} {
		test.Run(kind, func(test *testing.T) {
			state := connectedEngines()[0]
			now := state.started
			expected := "RELIABLE_FRAME_TIMEOUT"
			if kind == "handshake" {
				state.remote = epoch{}
				expected = "RELIABLE_HANDSHAKE_TIMEOUT"
			} else {
				if _, err := state.send([]byte("private-payload-not-in-trace"), now); err != nil {
					test.Fatal(err)
				}
				state.lastACK = now.Add(time.Second)
				state.lastProgress = now.Add(500 * time.Millisecond)
				state.stats.ACKReceived = 3
				if kind == "retry" {
					state.sent[0].retries = state.config.MaxRetries
					expected = "RELIABLE_RETRY_EXHAUSTED"
				}
				state.sent[0].sacked = kind == "sacked"
			}
			elapsed := state.config.MaxAge
			if kind == "retry" {
				elapsed = 2 * time.Second
			}
			if _, err := state.tick(now.Add(elapsed)); !errors.Is(err, ErrExhausted) {
				test.Fatal("terminal behavior changed", err)
			}
			trace := state.failureTrace
			if trace.Reason != expected || trace.Stage != "CARRIER" || trace.State != "FAILED" {
				test.Fatal("wrong failure branch", trace)
			}
			if kind != "handshake" && (trace.ReliablePending != 1 || trace.ReliableAgeMS != uint64(elapsed.Milliseconds()) || trace.ReliableACKReceived != 3 || trace.ReliableACKAgeMS != uint64((elapsed-time.Second).Milliseconds()) || trace.ReliableProgressAgeMS != uint64((elapsed-500*time.Millisecond).Milliseconds())) {
				test.Fatal("lost failure evidence", trace)
			}
			if (trace.ReliableSacked == 1) != (kind == "sacked") || (kind == "retry" && trace.ReliableRetries != uint64(state.config.MaxRetries)) {
				test.Fatal("lost SACK or retry evidence", trace)
			}
		})
	}
}

type tracedEndpoint struct {
	*testEndpoint
	trace *sessiontrace.Recorder
}

func (endpoint *tracedEndpoint) Close() error {
	endpoint.trace.Add("LOCAL_CLOSE", "STARTED", "NONE")
	return endpoint.testEndpoint.Close()
}

func TestExhaustionRecordedBeforeCarrierCleanup(test *testing.T) {
	trace := sessiontrace.New(strings.Repeat("ab", 32), nil)
	point, _ := endpoints()
	point.drop = func([]byte) bool { return true }
	config := DefaultConfig()
	config.RTO, config.MaxAge = 10*time.Millisecond, 50*time.Millisecond
	ctx, cancel := context.WithTimeout(sessiontrace.With(context.Background(), trace), time.Second)
	defer cancel()
	stream, err := New(ctx, &tracedEndpoint{point, trace}, config)
	if err != nil {
		test.Fatal(err)
	}
	defer stream.Close()
	select {
	case <-stream.done:
	case <-ctx.Done():
		test.Fatal("stream failed to terminate")
	}
	value := trace.Snapshot()
	if !errors.Is(stream.failure(), ErrExhausted) || value.FirstFailure == nil || value.FirstFailure.Reason != "RELIABLE_HANDSHAKE_TIMEOUT" {
		test.Fatal("cause lost before cleanup", value)
	}
	if len(value.Events) != 2 || value.Events[0].Reason != "RELIABLE_HANDSHAKE_TIMEOUT" || value.Events[1].Stage != "LOCAL_CLOSE" {
		test.Fatal("wrong causal order", value.Events)
	}
	trace.Add("FAMILY_TLS", "FAILED", "FAMILY_TLS_ERROR")
	if trace.Snapshot().FirstFailure.Reason != value.FirstFailure.Reason {
		test.Fatal("cleanup replaced the cause")
	}
}

func TestEstablishedRetryFailurePrecedesCleanup(test *testing.T) {
	trace := sessiontrace.New(strings.Repeat("cd", 32), nil)
	leftPoint, rightPoint := endpoints()
	leftPoint.drop = func(raw []byte) bool { return raw[4] == dataFrame }
	config := DefaultConfig()
	config.RTO, config.MaxRetries, config.MaxAge = 20*time.Millisecond, 2, time.Second
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	left, err := New(sessiontrace.With(ctx, trace), &tracedEndpoint{leftPoint, trace}, config)
	if err != nil {
		test.Fatal(err)
	}
	defer left.Close()
	right, err := New(ctx, rightPoint, config)
	if err != nil {
		test.Fatal(err)
	}
	defer right.Close()
	if err := left.SendContext(ctx, []byte("private-data")); err != nil {
		test.Fatal(err)
	}
	select {
	case <-left.done:
	case <-ctx.Done():
		test.Fatal("retry loop did not stop")
	}
	value := trace.Snapshot()
	if value.FirstFailure == nil || value.FirstFailure.Reason != "RELIABLE_RETRY_EXHAUSTED" || value.FirstFailure.ReliableRetries != 2 || value.FirstFailure.ReliablePending != 1 {
		test.Fatal("established-stream cause missing", value)
	}
	if len(value.Events) != 2 || value.Events[0].Reason != value.FirstFailure.Reason || value.Events[1].Stage != "LOCAL_CLOSE" || left.Stats().Terminal != "recovery_exhausted" {
		test.Fatal("terminal behavior or cause ordering changed", value)
	}
}
