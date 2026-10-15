package bootstrap

import (
	"testing"

	"github.com/Joker20380/family_connect/carrier/telemost"
)

type signalingObservationEndpoint struct {
	observationEndpoint
	failure telemost.SignalingReadFailure
}

func (endpoint signalingObservationEndpoint) SignalingReadFailure() telemost.SignalingReadFailure {
	return endpoint.failure
}

func TestObservedSeedForwardsSignalingSnapshot(test *testing.T) {
	value := telemost.SignalingReadFailure{Kind: "WS_CLOSE", CloseCode: 1008, ContextState: "ACTIVE"}
	endpoint := &observedSeed{PacketEndpoint: signalingObservationEndpoint{failure: value}, trace: newSeedTrace()}
	if endpoint.SeedSignalingReadFailure() != value {
		test.Fatal("snapshot dropped")
	}
	endpoint.PacketEndpoint = observationEndpoint{}
	if endpoint.SeedSignalingReadFailure().Kind != "" {
		test.Fatal("fabricated failure")
	}
}
