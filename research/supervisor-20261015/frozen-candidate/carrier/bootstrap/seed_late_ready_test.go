package bootstrap

import (
	"context"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

func TestSupervisorLateReadyExpiry(test *testing.T) {
	for _, directoryExpiry := range []bool{false, true} {
		parent, cancel := context.WithCancel(context.Background())
		deadline := time.Now().Add(1200 * time.Millisecond)
		securityDeadline := time.Now().Add(time.Hour)
		if directoryExpiry {
			parent, cancel = context.WithDeadline(parent, deadline)
		} else {
			securityDeadline = deadline
		}
		previous := newSeedGeneration(parent, 1)
		previous.carrier = newSupervisorEndpoint()
		late := newSupervisorEndpoint()
		manager := &SeedManager{current: previous, RecoveryCheck: func(context.Context) (time.Time, error) { return securityDeadline, nil }}
		attempts := 0
		next, err := manager.recoverSeed(parent, roombroker.Room{ID: "room"}, previous, func(lifetime, ready context.Context, room roombroker.Room) (familysession.PacketEndpoint, error) {
			<-ready.Done()
			return late, nil
		}, recoveryFailure(), &attempts)
		cancel()
		previous.close()
		if err == nil || next != nil || manager.current != previous || late.closed.Load() != 1 {
			test.Fatal("late expired ready promoted")
		}
	}
}
