package bootstrap

import (
	"context"
	"errors"
	"testing"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func TestObservedSeedReadKeepsLegacyErrorAndFirstClose(test *testing.T) {
	primary := errors.New("SECRET underlying error")
	trace := newSeedTrace()
	endpoint := &observedSeed{PacketEndpoint: observationEndpoint{primary}, trace: trace}
	if endpoint.SeedCloseSource() != "" {
		test.Fatal("no close yet")
	}
	trace.Record(sessiontrace.Event{Stage: "CARRIER", State: "CLOSED", Reason: "CARRIER_ERROR", CloseSource: "SIGNAL_READ"})
	_, err := endpoint.Recv(context.Background())
	if err != primary {
		test.Fatal("changed original error")
	}
	endpoint.Close()
	trace.Record(sessiontrace.Event{Stage: "CARRIER", State: "CLOSED", Reason: "NONE", CloseSource: "UPPER_CLOSE"})
	if endpoint.SeedCloseSource() != "SIGNAL_READ" {
		test.Fatal("cleanup replaced first close")
	}
}
