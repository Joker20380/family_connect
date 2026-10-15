package bootstrap

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

func TestSeedObservationPreservesLegacyReturn(test *testing.T) {
	for _, rotate := range []time.Duration{0, time.Minute} {
		var observed []SeedFailure
		manager := &SeedManager{RotateAfter: rotate, Observe: func(value SeedFailure) { observed = append(observed, value) }}
		cause := roombroker.Code("provider_forbidden")
		err := manager.Run(context.Background(), providerFunc(func(context.Context) (roombroker.Room, error) { return roombroker.Room{}, cause }), func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
			test.Fatal("connector called")
			return nil, nil
		}, testFamily, testGateway, time.Hour, func(context.Context, familysession.PacketEndpoint) {})
		if err != roombroker.Code("seed_creation_failed") || len(observed) != 1 || observed[0].Cause != cause || observed[0].Stage != "SEED_CREATE" {
			test.Fatal("return or primary changed", err, observed)
		}
		if rotate != 0 && observed[0].Generation != 1 {
			test.Fatal("generation")
		}
	}
}

type observationEndpoint struct{ cause error }

func (endpoint observationEndpoint) Recv(context.Context) ([]byte, error)      { return nil, endpoint.cause }
func (endpoint observationEndpoint) SendContext(context.Context, []byte) error { return endpoint.cause }
func (endpoint observationEndpoint) Close() error                              { return errors.New("late cleanup") }

func TestSeedReadPreservesFirstError(test *testing.T) {
	cause := errors.New("private underlying error")
	var observed []error
	err := serveCarrier(context.Background(), observationEndpoint{cause}, func(context.Context, familysession.PacketEndpoint) {}, func(stage string, err error) {
		if stage != "SEED_READ" {
			test.Fatal(stage)
		}
		observed = append(observed, err)
	})
	if err != roombroker.Code("seed_closed") || len(observed) != 1 || observed[0] != cause {
		test.Fatal("legacy/first cause changed")
	}
}
