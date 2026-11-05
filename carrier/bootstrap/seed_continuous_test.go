package bootstrap

import (
	"context"
	"fmt"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

func TestContinuousSeedLifecycleAndRetirement(test *testing.T) {
	clock := &seedTestClock{now: time.Now().UTC(), armed: make(chan struct{}, 1)}
	publications, clients := make(chan Directory, 1), make(chan *pipe, 1)
	manager := &SeedManager{RotateAfter: 30 * time.Minute, ContinueRotation: true,
		now: clock.read, lifetime: clock.lifetime, after: clock.after,
		Publish: func(directory Directory) error { publications <- directory; return nil }}
	var creations atomic.Int32
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	done := make(chan error, 1)
	go func() {
		done <- manager.Run(ctx, providerFunc(func(context.Context) (roombroker.Room, error) {
			index := creations.Add(1)
			return roombroker.Room{ID: fmt.Sprint(index), JoinURL: fmt.Sprintf("https://telemost.yandex.ru/j/continuous-%d", index)}, nil
		}), func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
			client, server := pair()
			clients <- client
			return server, nil
		}, testFamily, testGateway, time.Hour, func(ctx context.Context, endpoint familysession.PacketEndpoint) {
			for {
				raw, err := endpoint.Recv(ctx)
				if err != nil || endpoint.SendContext(ctx, raw) != nil {
					return
				}
			}
		})
	}()
	var directories []Directory
	var endpoints []*pipe
	for generation := 0; generation < 5; generation++ {
		directory := seedWait(test, publications)
		client := seedWait(test, clients)
		seedWait(test, clock.armed)
		if !directory.ExpiresAt.Equal(clock.read().Add(time.Hour)) {
			test.Fatal("seed lifetime changed")
		}
		if generation > 0 && (!directory.IssuedAt.After(directories[generation-1].IssuedAt) || directory.Seeds[0].JoinURL == directories[generation-1].Seeds[0].JoinURL) {
			test.Fatal("nonmonotonic publication or reused endpoint")
		}
		directories = append(directories, directory)
		endpoints = append(endpoints, client)
		if generation >= 2 {
			seedWait(test, endpoints[generation-2].done)
			if _, err := ParseDirectory(encode(directories[generation-2]), testFamily, testGateway, clock.read()); err == nil {
				test.Fatal("expired seed still admitted")
			}
		}
		exchange, err := connectLease(bounded(test), client)
		if err != nil {
			test.Fatal(err)
		}
		go readLease(ctx, exchange)
		payload := fmt.Sprintf("generation-%d", generation)
		if err := exchange.SendContext(bounded(test), []byte(payload)); err != nil {
			test.Fatal(err)
		}
		raw, err := exchange.Recv(bounded(test))
		if err != nil || string(raw) != payload {
			test.Fatal("new seed did not carry checked traffic", err)
		}
		exchange.Close()
		if generation < 4 {
			clock.advance(30 * time.Minute)
		}
	}
	cancel()
	seedWait(test, done)
	for _, endpoint := range endpoints {
		seedWait(test, endpoint.done)
	}
	clock.advance(time.Hour)
	if creations.Load() != 5 || manager.running || manager.directory != nil {
		test.Fatal("rotation or publication survived cleanup")
	}
}

func TestContinuousSeedFailedThirdGeneration(test *testing.T) {
	for _, publicationFailure := range []bool{false, true} {
		test.Run(fmt.Sprint(publicationFailure), func(test *testing.T) {
			clock := &seedTestClock{now: time.Now().UTC(), armed: make(chan struct{}, 1)}
			published, events := make(chan Directory, 1), make(chan string, 16)
			var creations atomic.Int32
			manager := &SeedManager{RotateAfter: 30 * time.Minute, ContinueRotation: true,
				now: clock.read, lifetime: clock.lifetime, after: clock.after,
				Event: func(event string) { events <- event }, Publish: func(directory Directory) error {
					if creations.Load() == 3 {
						return roombroker.Code("seed_publication_rejected")
					}
					published <- directory
					return nil
				}}
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			done := make(chan error, 1)
			go func() {
				done <- manager.Run(ctx, providerFunc(func(context.Context) (roombroker.Room, error) {
					index := creations.Add(1)
					if index == 3 && !publicationFailure {
						return roombroker.Room{}, roombroker.Code("provider_unavailable")
					}
					return roombroker.Room{ID: fmt.Sprint(index), JoinURL: fmt.Sprintf("https://telemost.yandex.ru/j/failure-%d", index)}, nil
				}), func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
					_, server := pair()
					return server, nil
				}, testFamily, testGateway, time.Hour, func(context.Context, familysession.PacketEndpoint) {})
			}()
			for generation := 0; generation < 2; generation++ {
				seedWait(test, published)
				seedWait(test, clock.armed)
				clock.advance(30 * time.Minute)
			}
			if !publicationFailure {
				for event := seedWait(test, events); event != "bootstrap_seed_rotation_failed"; event = seedWait(test, events) {
				}
				clock.advance(30 * time.Minute)
			}
			seedWait(test, done)
			clock.advance(time.Hour)
			if creations.Load() != 3 || manager.running || manager.directory != nil {
				test.Fatal("failed rotation retried or retained stale publication")
			}
		})
	}
}

func TestContinuousSeedRejectsUnboundedOverlap(test *testing.T) {
	for _, rotation := range []time.Duration{0, time.Minute, 29 * time.Minute, time.Hour} {
		manager := &SeedManager{ContinueRotation: true, RotateAfter: rotation}
		err := manager.Run(context.Background(), providerFunc(func(context.Context) (roombroker.Room, error) {
			test.Fatal("invalid continuous configuration reached provider")
			return roombroker.Room{}, nil
		}), func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
			return nil, nil
		}, testFamily, testGateway, time.Hour, func(context.Context, familysession.PacketEndpoint) {})
		if err != roombroker.Code("seed_configuration") {
			test.Fatal("invalid rotation accepted", rotation, err)
		}
	}
}
