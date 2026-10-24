package reliablestream

import (
	"bytes"
	"errors"
	"testing"
	"time"
)

func fastRecoveryWindow(test *testing.T) (*engine, *engine, []frame) {
	test.Helper()
	states := connectedEngines()
	sender, receiver := states[0], states[1]
	var packets []frame
	for index := 0; index < sender.config.SendWindow; index++ {
		packet, err := sender.send([]byte{byte(index)}, sender.started)
		if err != nil {
			test.Fatal(err)
		}
		packets = append(packets, packet)
	}
	return sender, receiver, packets
}

func fastRecoveryDeliver(test *testing.T, sender, receiver *engine, packet frame, now time.Time) {
	test.Helper()
	responses, err := receiver.input(packet, now)
	if err != nil {
		test.Fatal(err)
	}
	for _, response := range responses {
		if _, err = sender.input(response, now); err != nil {
			test.Fatal(err)
		}
	}
}

func fastRecoveryData(test *testing.T, sender *engine, elapsed time.Duration) []frame {
	test.Helper()
	packets, err := sender.tick(sender.started.Add(elapsed))
	if err != nil {
		test.Fatal(err)
	}
	var data []frame
	for _, packet := range packets {
		if packet.kind == dataFrame {
			data = append(data, packet)
		}
	}
	return data
}

func TestFastRecoveryDistinctSACKThreshold(test *testing.T) {
	for confirmations := 0; confirmations <= 3; confirmations++ {
		sender, receiver, packets := fastRecoveryWindow(test)
		for index := 1; index <= confirmations; index++ {
			fastRecoveryDeliver(test, sender, receiver, packets[index], sender.started)
		}
		for duplicate := 0; duplicate < 40; duplicate++ {
			if _, err := sender.input(receiver.ack(), sender.started); err != nil {
				test.Fatal(err)
			}
		}
		got := fastRecoveryData(test, sender, sender.config.RTO/4)
		if confirmations < 3 && len(got) != 0 {
			test.Fatal("duplicate ACKs must not create distinct SACK evidence", confirmations)
		}
		if confirmations == 3 && (len(got) != 1 || got[0].seq != 0) {
			test.Fatal("three later SACKed blocks must recover only the head", got)
		}
	}
}

func TestFastRecoveryGraceSingleShotAndFallback(test *testing.T) {
	sender, receiver, packets := fastRecoveryWindow(test)
	for _, packet := range packets[1:] {
		fastRecoveryDeliver(test, sender, receiver, packet, sender.started)
	}
	grace := sender.config.RTO / 4
	if len(fastRecoveryData(test, sender, grace-time.Nanosecond)) != 0 {
		test.Fatal("reordering grace shortened")
	}
	retries := fastRecoveryData(test, sender, grace)
	if len(retries) != 1 || !bytes.Equal(encode(retries[0]), encode(packets[0])) {
		test.Fatal("retransmission changed wire identity/payload")
	}
	if sender.stats.Timeouts != 0 || sender.stats.Retransmissions != 1 || sender.sent[0].retries != 1 {
		test.Fatal("early recovery must not invent an RTO timeout")
	}
	for step := 1; step <= 9; step++ {
		now := grace + time.Duration(step)*sender.config.RTO/10
		if _, err := sender.input(receiver.ack(), sender.started.Add(now)); err != nil {
			test.Fatal(err)
		}
		if len(fastRecoveryData(test, sender, now)) != 0 {
			test.Fatal("unchanged SACK repeatedly triggered fast retry")
		}
	}
	retries = fastRecoveryData(test, sender, grace+sender.config.RTO)
	if len(retries) != 1 || sender.sent[0].retries != 2 || sender.stats.Timeouts != 1 {
		test.Fatal("lost fast retry did not fall back to ordinary RTO")
	}
}

func TestFastRecoveryReorderingAndSlowConsumer(test *testing.T) {
	for _, consume := range []bool{false, true} {
		sender, receiver, packets := fastRecoveryWindow(test)
		for _, packet := range packets[1:] {
			fastRecoveryDeliver(test, sender, receiver, packet, sender.started)
		}
		fastRecoveryDeliver(test, sender, receiver, packets[0], sender.started.Add(200*time.Millisecond))
		if consume {
			for index := range packets {
				data, ack := receiver.consume()
				if !bytes.Equal(data, []byte{byte(index)}) {
					test.Fatal("ordered bytes changed")
				}
				if _, err := sender.input(ack, sender.started.Add(200*time.Millisecond)); err != nil {
					test.Fatal(err)
				}
			}
		}
		if len(fastRecoveryData(test, sender, 900*time.Millisecond)) != 0 {
			test.Fatal("delayed original or SACKed unconsumed head retransmitted")
		}
	}
}

func TestFastRecoveryStaleAndCumulativeACK(test *testing.T) {
	sender, receiver, packets := fastRecoveryWindow(test)
	for _, packet := range packets[1:] {
		if _, err := receiver.input(packet, sender.started); err != nil {
			test.Fatal(err)
		}
	}
	stale := receiver.ack()
	stale.source = epoch{3}
	if _, err := sender.input(stale, sender.started); err != nil {
		test.Fatal(err)
	}
	if len(fastRecoveryData(test, sender, 500*time.Millisecond)) != 0 {
		test.Fatal("foreign epoch provided fast-recovery evidence")
	}
	if _, err := sender.input(receiver.ack(), sender.started); err != nil {
		test.Fatal(err)
	}
	fastRecoveryDeliver(test, sender, receiver, packets[0], sender.started)
	_, ack := receiver.consume()
	if _, err := sender.input(ack, sender.started); err != nil {
		test.Fatal(err)
	}
	if sender.base != 1 || len(fastRecoveryData(test, sender, 500*time.Millisecond)) != 0 {
		test.Fatal("consumed head or SACKed successor retransmitted")
	}
}

func TestFastRecoveryExhaustionBounds(test *testing.T) {
	for _, expired := range []bool{false, true} {
		sender, receiver, packets := fastRecoveryWindow(test)
		for _, packet := range packets[1:] {
			fastRecoveryDeliver(test, sender, receiver, packet, sender.started)
		}
		reason := "RELIABLE_RETRY_EXHAUSTED"
		elapsed := sender.config.RTO
		sender.sent[0].retries = sender.config.MaxRetries
		if expired {
			reason, elapsed = "RELIABLE_FRAME_TIMEOUT", sender.config.MaxAge
		}
		if _, err := sender.tick(sender.started.Add(elapsed)); !errors.Is(err, ErrExhausted) || sender.failureTrace.Reason != reason {
			test.Fatal("exhaustion identity or age bound changed", err, sender.failureTrace)
		}
		if sender.stats.Retransmissions != 0 {
			test.Fatal("retry budget bypassed")
		}
	}
}
