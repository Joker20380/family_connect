package reliablestream

import (
	"errors"
	"testing"
	"time"
)

func TestRTTEstimatorUsesOnlyNewUnambiguousAcknowledgements(test *testing.T) {
	states := connectedEngines()
	sender, receiver := states[0], states[1]
	for index := 0; index < 2; index++ {
		packet, err := sender.send([]byte{byte(index)}, sender.started)
		if err != nil {
			test.Fatal(err)
		}
		if _, err := receiver.input(packet, sender.started); err != nil {
			test.Fatal(err)
		}
	}
	sender.sent[1].retries = 1
	acknowledgement := receiver.ack()
	if _, err := sender.input(acknowledgement, sender.started.Add(2*time.Second)); err != nil {
		test.Fatal(err)
	}
	if sender.smoothedRTT != 2*time.Second || sender.rttVariation != time.Second || sender.retryInterval(sender.sent[0]) != 6*time.Second {
		test.Fatal("first fresh ACK did not set a bounded RTT estimate")
	}
	for _, elapsed := range []time.Duration{3 * time.Second, 8 * time.Second, 19 * time.Second} {
		if _, err := sender.input(acknowledgement, sender.started.Add(elapsed)); err != nil {
			test.Fatal(err)
		}
	}
	for range 2 {
		_, acknowledgement = receiver.consume()
		if _, err := sender.input(acknowledgement, sender.started.Add(19*time.Second)); err != nil {
			test.Fatal(err)
		}
	}
	if sender.smoothedRTT != 2*time.Second || sender.rttVariation != time.Second {
		test.Fatal("duplicate, already-SACKed or retransmitted data changed RTT")
	}
}

func TestInvalidAndStaleACKCannotTrainRecovery(test *testing.T) {
	states := connectedEngines()
	sender, receiver := states[0], states[1]
	if _, err := sender.send([]byte{1}, sender.started); err != nil {
		test.Fatal(err)
	}
	acknowledgement := receiver.ack()
	acknowledgement.ack = 2
	if _, err := sender.input(acknowledgement, sender.started.Add(time.Second)); !errors.Is(err, ErrProtocol) {
		test.Fatal("impossible cumulative ACK accepted")
	}
	acknowledgement.ack, acknowledgement.source = 1, epoch{9}
	if _, err := sender.input(acknowledgement, sender.started.Add(time.Second)); err != nil {
		test.Fatal(err)
	}
	if sender.smoothedRTT != 0 || sender.ackCredit != 0 || len(sender.sent) != 1 {
		test.Fatal("invalid or stale acknowledgement changed recovery state")
	}
}

func TestInitialNegotiationRTTSkipsRetransmissionAmbiguity(test *testing.T) {
	for _, retried := range []bool{false, true} {
		state := newEngine(DefaultConfig(), epoch{1}, time.Unix(100, 0))
		if _, err := state.tick(state.started); err != nil {
			test.Fatal(err)
		}
		elapsed := 600 * time.Millisecond
		if retried {
			elapsed += state.config.RTO
			if _, err := state.tick(state.started.Add(state.config.RTO)); err != nil {
				test.Fatal(err)
			}
		}
		packet := state.opening(state.local)
		packet.source = epoch{2}
		if _, err := state.input(packet, state.started.Add(elapsed)); err != nil {
			test.Fatal(err)
		}
		if retried && state.smoothedRTT != 0 || !retried && state.smoothedRTT != elapsed {
			test.Fatal("ambiguous negotiation trained the RTT estimate")
		}
	}
}

func TestSendAllowanceGrowsOnlyOnConsumptionAndCutsOncePerFlight(test *testing.T) {
	config := DefaultConfig()
	config.SendWindow, config.ReceiveWindow = 32, 32
	sender := newEngine(config, epoch{1}, time.Unix(100, 0))
	receiver := newEngine(config, epoch{2}, sender.started)
	sender.remote, sender.remoteWindow, sender.remoteSize = receiver.local, 32, config.Payload
	receiver.remote, receiver.remoteWindow, receiver.remoteSize = sender.local, 32, config.Payload
	for index := 0; index < 4; index++ {
		packet, err := sender.send([]byte{byte(index)}, sender.started)
		if err != nil {
			test.Fatal(err)
		}
		if _, err := receiver.input(packet, sender.started); err != nil {
			test.Fatal(err)
		}
	}
	if sender.writable() {
		test.Fatal("new large-window session flooded the unmeasured link")
	}
	for range 32 {
		if _, err := sender.input(receiver.ack(), sender.started); err != nil {
			test.Fatal(err)
		}
	}
	if sender.sendAllowance != 4 || sender.writable() {
		test.Fatal("SACK inflated the sender or released unconsumed bytes")
	}
	for range 4 {
		_, acknowledgement := receiver.consume()
		if _, err := sender.input(acknowledgement, sender.started); err != nil {
			test.Fatal(err)
		}
	}
	if sender.sendAllowance != 5 || !sender.writable() {
		test.Fatal("completed flight did not grow the allowance gradually")
	}
	for sender.writable() {
		if _, err := sender.send([]byte{1}, sender.started); err != nil {
			test.Fatal(err)
		}
	}
	if _, err := sender.tick(sender.started.Add(time.Second)); err != nil {
		test.Fatal(err)
	}
	if sender.sendAllowance != 2 || len(sender.sent) != 5 || sender.writable() {
		test.Fatal("timeout cut repeatedly or discarded outstanding bytes")
	}
	if _, err := sender.tick(sender.started.Add(3 * time.Second)); err != nil || sender.sendAllowance != 2 {
		test.Fatal("the same stalled flight cut the allowance again", err)
	}
}

func TestRTTBackoffStaysWithinConfiguredBounds(test *testing.T) {
	state := connectedEngines()[0]
	for _, sample := range []time.Duration{-time.Second, 0, time.Nanosecond, time.Hour} {
		state.observeRTT(sample)
		for attempt := 0; attempt <= 32; attempt++ {
			interval := state.retryInterval(&pending{timeouts: attempt})
			if interval < state.config.RTO || interval > 10*time.Second || interval > state.config.MaxAge {
				test.Fatal("unbounded retry interval", interval)
			}
		}
	}
}

func TestColdStartKeepsOrdinaryThroughputBounded(test *testing.T) {
	warm := throughputSimulation(test, throughputCase{name: "warm"})
	cold := throughputSimulation(test, throughputCase{name: "cold", coldStart: true})
	if !cold.BytesIdentical || cold.Retransmits != 0 || cold.VirtualMS > 2*warm.VirtualMS || cold.SendHighWater != DefaultConfig().SendWindow {
		test.Fatalf("cold start stayed throttled or lost bytes: warm=%+v cold=%+v", warm, cold)
	}
	test.Logf("1MiB ordinary model: cold=%dms warm=%dms; zero retransmissions, final window=%d", cold.VirtualMS, warm.VirtualMS, cold.SendHighWater)
}
