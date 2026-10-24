package bootstrap

import (
	"context"
	"sync"
	"sync/atomic"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
)

type seedTimer interface{ Stop() bool }

func (manager *SeedManager) timeNow() time.Time {
	if manager.now != nil {
		return manager.now()
	}
	return time.Now()
}

func (manager *SeedManager) withLifetime(ctx context.Context, ttl time.Duration) (context.Context, context.CancelFunc) {
	if manager.lifetime != nil {
		return manager.lifetime(ctx, ttl)
	}
	return context.WithTimeout(ctx, ttl)
}

func (manager *SeedManager) schedule(delay time.Duration, callback func()) seedTimer {
	if manager.after != nil {
		return manager.after(delay, callback)
	}
	return time.AfterFunc(delay, callback)
}

func (manager *SeedManager) runOverlap(ctx context.Context, provider roombroker.RoomProvider, connect SeedConnector, family, gateway string, ttl time.Duration, exchange func(context.Context, familysession.PacketEndpoint)) error {
	if manager.RotateAfter <= 0 || ttl-manager.RotateAfter <= roombroker.CreationTimeout+ConnectTimeout {
		return roombroker.Code("seed_configuration")
	}
	manager.mu.Lock()
	if manager.running {
		manager.mu.Unlock()
		return roombroker.Code("seed_busy")
	}
	manager.running = true
	manager.mu.Unlock()
	ctx, cancel := context.WithCancel(ctx)
	var workers sync.WaitGroup
	defer func() {
		cancel()
		workers.Wait()
		manager.mu.Lock()
		manager.directory = nil
		manager.running = false
		manager.mu.Unlock()
	}()
	type completion struct {
		generation int
		err        error
	}
	type publication struct {
		generation int
		directory  Directory
	}
	done, published := make(chan completion, 2), make(chan publication, 2)
	var current atomic.Int32
	start := func(generation int) {
		child := &SeedManager{Event: manager.Event, now: manager.now, lifetime: manager.lifetime, after: manager.after}
		child.Publish = func(directory Directory) error {
			if ctx.Err() != nil {
				return ctx.Err()
			}
			manager.mu.Lock()
			previous := manager.directory
			manager.mu.Unlock()
			if previous != nil && (!directory.IssuedAt.After(previous.IssuedAt) || directory.Seeds[0].JoinURL == previous.Seeds[0].JoinURL) {
				return roombroker.Code("seed_publication_rejected")
			}
			if manager.Publish != nil {
				if err := manager.Publish(directory); err != nil {
					return err
				}
			}
			manager.mu.Lock()
			manager.directory = &directory
			manager.mu.Unlock()
			current.Store(int32(generation))
			published <- publication{generation, directory}
			return nil
		}
		workers.Add(1)
		go func() {
			defer workers.Done()
			done <- completion{generation, child.Run(ctx, provider, connect, family, gateway, ttl, exchange)}
		}()
	}
	rotate := make(chan struct{}, 1)
	var timer seedTimer
	defer func() {
		if timer != nil {
			timer.Stop()
		}
	}()
	start(1)
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case publication := <-published:
			if publication.generation == 1 {
				when := publication.directory.IssuedAt.Add(manager.RotateAfter)
				if when.Before(publication.directory.ExpiresAt) {
					timer = manager.schedule(max(0, when.Sub(manager.timeNow())), func() { rotate <- struct{}{} })
				}
			}
		case <-rotate:
			if ctx.Err() != nil {
				return ctx.Err()
			}
			start(2)
		case result := <-done:
			active := int(current.Load())
			if result.generation == active || active == 0 || result.err == roombroker.Code("seed_publication_failed") {
				return result.err
			}
			if manager.Event != nil {
				if result.generation < active {
					manager.Event("bootstrap_previous_seed_retired")
				} else {
					manager.Event("bootstrap_seed_rotation_failed")
				}
			}
		}
	}
}
