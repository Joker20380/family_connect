package bootstrap

import (
	"context"
	"errors"
	"io"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/telemost"
)

func recoveryFailure() SeedFailure {
	return SeedFailure{Stage: "SEED_READ", Cause: io.EOF, CloseSource: "SIGNAL_READ", SignalingRead: telemost.SignalingReadFailure{Kind: "WS_CLOSE", CloseCode: 1011, ContextState: "ACTIVE"}}
}

func TestSupervisorClassification(test *testing.T) {
	for _, name := range []string{"1011", "1002", "1007", "1008", "unknown", "json", "cancel", "deadline", "local_close", "admission", "source"} {
		test.Run(name, func(test *testing.T) {
			failure := recoveryFailure()
			switch name {
			case "1002":
				failure.SignalingRead.CloseCode = 1002
			case "1007":
				failure.SignalingRead.CloseCode = 1007
			case "1008":
				failure.SignalingRead.CloseCode = 1008
			case "unknown":
				failure.SignalingRead.Kind = "UNKNOWN"
			case "json":
				failure.SignalingRead.Kind = "JSON_SYNTAX"
			case "cancel":
				failure.ParentError = context.Canceled
			case "deadline":
				failure.SignalingRead.ContextState = "DEADLINE"
			case "local_close":
				failure.SignalingRead.CarrierClosed = true
			case "admission":
				failure.Stage = "SEED_ADMISSION"
			case "source":
				failure.CloseSource = "PUBLISHER_DISCONNECTED"
			}
			if recoverableSeed(failure) != (name == "1011") {
				test.Fatal("classification", name)
			}
		})
	}
}

type supervisorEndpoint struct {
	stop   chan struct{}
	once   sync.Once
	closed atomic.Int64
}

func newSupervisorEndpoint() *supervisorEndpoint {
	return &supervisorEndpoint{stop: make(chan struct{})}
}
func (endpoint *supervisorEndpoint) Recv(ctx context.Context) ([]byte, error) {
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	case <-endpoint.stop:
		return nil, io.EOF
	}
}
func (endpoint *supervisorEndpoint) SendContext(ctx context.Context, raw []byte) error {
	return ctx.Err()
}
func (endpoint *supervisorEndpoint) Close() error {
	endpoint.once.Do(func() { endpoint.closed.Add(1); close(endpoint.stop) })
	return nil
}
func (endpoint *supervisorEndpoint) SeedCloseSource() string { return "SIGNAL_READ" }
func (endpoint *supervisorEndpoint) SeedSignalingReadFailure() telemost.SignalingReadFailure {
	return recoveryFailure().SignalingRead
}

func TestSupervisorLifetimeBudgetAndDirectory(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	var creates, joins, publications atomic.Int64
	ready := make(chan *supervisorEndpoint, 4)
	events := make(chan SeedRecovery, 32)
	fatal := make(chan SeedFailure, 2)
	manager := &SeedManager{RecoveryCheck: func(context.Context) (time.Time, error) { return time.Now().Add(time.Hour), nil }, Recovery: func(event SeedRecovery) { events <- event }, Observe: func(failure SeedFailure) { fatal <- failure }, Publish: func(Directory) error { publications.Add(1); return nil }}
	done := make(chan error, 1)
	go func() {
		done <- manager.Run(ctx, providerFunc(func(context.Context) (roombroker.Room, error) {
			creates.Add(1)
			return roombroker.Room{ID: "same-room", JoinURL: "https://telemost.yandex.ru/j/12345678901234"}, nil
		}), func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
			joins.Add(1)
			endpoint := newSupervisorEndpoint()
			ready <- endpoint
			return endpoint, nil
		}, testFamily, testGateway, time.Hour, func(context.Context, familysession.PacketEndpoint) {})
	}()
	for generation := 0; generation < 4; generation++ {
		select {
		case endpoint := <-ready:
			endpoint.Close()
		case <-ctx.Done():
			test.Fatal("join timeout")
		}
	}
	select {
	case err := <-done:
		if err == nil {
			test.Fatal("budget must terminate")
		}
	case <-ctx.Done():
		test.Fatal("unbounded recovery")
	}
	if creates.Load() != 1 || joins.Load() != 4 || publications.Load() != 1 {
		test.Fatal("room/publication/budget changed", creates.Load(), joins.Load(), publications.Load())
	}
	if failure := <-fatal; failure.Cause != io.EOF || failure.SignalingRead.CloseCode != 1011 {
		test.Fatal("first cause lost")
	}
	if len(fatal) != 0 {
		test.Fatal("recovered close reported fatal")
	}
	lastGeneration := uint64(1)
	close(events)
	for event := range events {
		if event.State == "SEED_ACTIVE" {
			if event.NewGeneration <= lastGeneration {
				test.Fatal("generation reuse")
			}
			lastGeneration = event.NewGeneration
		}
	}
	if lastGeneration != 4 || manager.current != nil {
		test.Fatal("generation ownership")
	}
}

func TestSupervisorStopExpiryAndJoinFailure(test *testing.T) {
	for _, name := range []string{"stop_backoff", "directory_expiry", "credential_expiry", "security_reject", "metadata", "sdp", "ice", "media_timeout", "1011_during_recovery", "stale_swap"} {
		test.Run(name, func(test *testing.T) {
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			if name == "directory_expiry" {
				var stop context.CancelFunc
				ctx, stop = context.WithTimeout(ctx, 30*time.Millisecond)
				defer stop()
			}
			previous := newSeedGeneration(ctx, 1)
			previous.carrier = newSupervisorEndpoint()
			manager := &SeedManager{current: previous, RecoveryCheck: func(context.Context) (time.Time, error) {
				if name == "security_reject" {
					return time.Time{}, errors.New("private")
				}
				if name == "credential_expiry" {
					return time.Now().Add(30 * time.Millisecond), nil
				}
				return time.Now().Add(time.Hour), nil
			}}
			if name == "stop_backoff" {
				manager.Recovery = func(event SeedRecovery) {
					if event.Outcome == "BACKOFF" {
						cancel()
					}
				}
			}
			if name == "stale_swap" {
				manager.current = newSeedGeneration(ctx, 99)
				defer manager.current.close()
			}
			joins := 0
			attempts := 0
			start := time.Now()
			next, err := manager.recoverSeed(ctx, roombroker.Room{ID: "room"}, previous, func(lifetime, ready context.Context, room roombroker.Room) (familysession.PacketEndpoint, error) {
				joins++
				if name == "stale_swap" {
					return newSupervisorEndpoint(), nil
				}
				if name == "1011_during_recovery" && joins == 1 {
					return nil, &seedConnectFailure{source: "SIGNAL_READ", signaling: recoveryFailure().SignalingRead, cause: io.EOF}
				}
				return nil, errors.New("private join rejection")
			}, recoveryFailure(), &attempts)
			if err == nil || next != nil {
				test.Fatal("failure accepted")
			}
			if name == "1011_during_recovery" {
				if joins != 2 {
					test.Fatal("narrow retry missing", joins)
				}
			} else if joins > 1 {
				test.Fatal("blind retry")
			}
			if name == "stop_backoff" && time.Since(start) > 300*time.Millisecond {
				test.Fatal("shutdown not immediate")
			}
			if previous.closedForTest() != 1 {
				test.Fatal("old cleanup")
			}
		})
	}
}

func (generation *seedGeneration) closedForTest() int64 {
	return generation.carrier.(*supervisorEndpoint).closed.Load()
}

func TestSupervisorGenerationIsolation(test *testing.T) {
	parent, cancel := context.WithCancel(context.Background())
	defer cancel()
	old := newSeedGeneration(parent, 1)
	old.carrier = newSupervisorEndpoint()
	next := newSeedGeneration(parent, 2)
	next.carrier = newSupervisorEndpoint()
	defer next.close()
	manager := &SeedManager{current: old}
	if !manager.swapGeneration(old, next) {
		test.Fatal("swap")
	}
	var workers sync.WaitGroup
	for index := 0; index < 32; index++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			old.close()
			if manager.swapGeneration(old, nil) {
				test.Error("stale callback accepted")
			}
		}()
	}
	workers.Wait()
	if next.ctx.Err() != nil || old.closedForTest() != 1 || next.closedForTest() != 0 || manager.current != next {
		test.Fatal("generation leaked ownership")
	}
	cancel()
	if next.ctx.Err() != context.Canceled {
		test.Fatal("service stop detached")
	}
}
