package bootstrap

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

func TestSeedPublishedOnlyAfterReadyAndWithdrawn(test *testing.T) {
	exported := make(chan Directory, 1)
	manager := &SeedManager{Publish: func(directory Directory) error { exported <- directory; return nil }}
	ctx, cancel := context.WithCancel(bounded(test))
	defer cancel()
	started, ready := make(chan struct{}), make(chan struct{})
	client, server := pair()
	defer client.Close()
	done := make(chan error, 1)
	go func() {
		done <- manager.Run(ctx, providerFunc(func(context.Context) (roombroker.Room, error) {
			return roombroker.Room{ID: "seed", JoinURL: "https://telemost.yandex.ru/j/seed-test"}, nil
		}),
			func(ctx, bound context.Context, room roombroker.Room) (familysession.PacketEndpoint, error) {
				close(started)
				select {
				case <-ready:
					return server, nil
				case <-bound.Done():
					return nil, bound.Err()
				}
			}, testFamily, testGateway, time.Minute, func(context.Context, familysession.PacketEndpoint) {})
	}()
	<-started
	manager.mu.Lock()
	published := manager.directory != nil
	manager.mu.Unlock()
	if published {
		test.Fatal("seed published before READY")
	}
	select {
	case <-exported:
		test.Fatal("seed exported before READY")
	default:
	}
	close(ready)
	for {
		manager.mu.Lock()
		published = manager.directory != nil
		manager.mu.Unlock()
		if published {
			break
		}
		select {
		case <-ctx.Done():
			test.Fatal("seed not published")
		case <-time.After(time.Millisecond):
		}
	}
	select {
	case directory := <-exported:
		if len(directory.Seeds) != 1 || directory.Seeds[0].Gateway != testGateway {
			test.Fatal("invalid export")
		}
	case <-ctx.Done():
		test.Fatal("seed was not exported")
	}
	cancel()
	<-done
	manager.mu.Lock()
	defer manager.mu.Unlock()
	if manager.directory != nil || manager.running {
		test.Fatal("seed survived shutdown")
	}
}

func TestSeedFailureAndNotReady(test *testing.T) {
	for _, kind := range []string{"provider", "ready", "cancel"} {
		test.Run(kind, func(test *testing.T) {
			manager := &SeedManager{}
			ctx, cancel := context.WithCancel(bounded(test))
			defer cancel()
			if kind == "cancel" {
				cancel()
			}
			err := manager.Run(ctx, providerFunc(func(context.Context) (roombroker.Room, error) {
				if kind == "provider" {
					return roombroker.Room{}, errors.New("provider")
				}
				return roombroker.Room{ID: "seed", JoinURL: "https://telemost.yandex.ru/j/seed-test"}, nil
			}), func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
				return nil, errors.New("not READY")
			}, testFamily, testGateway, time.Minute, func(context.Context, familysession.PacketEndpoint) {})
			if err == nil || manager.directory != nil || manager.running {
				test.Fatal("unavailable seed published")
			}
		})
	}
}
