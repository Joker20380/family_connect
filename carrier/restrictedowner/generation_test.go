package restrictedowner

import (
	"context"
	"errors"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func TestPinnedAcquisitionCannotReplaceFailedGeneration(test *testing.T) {
	ctx := bounded(test)
	var manager Coordinator
	var opens atomic.Int32
	entered, fail, cleanup, drained := make(chan struct{}), make(chan struct{}), make(chan struct{}), make(chan struct{})
	resume := sync.OnceFunc(func() { close(fail) })
	unblock := sync.OnceFunc(func() { close(drained) })
	defer unblock()
	defer resume()
	expiry, profile := time.Now().Add(time.Minute), [32]byte{1}
	open := func(context.Context) (Session, func(), error) {
		opens.Add(1)
		close(entered)
		<-fail
		return nil, func() { close(cleanup); <-drained }, errors.New("bootstrap failed")
	}
	generation := acquire(test, &manager, 1, open, func() {})
	await(test, ctx, entered)
	operation, err := manager.RetainChat(generation, expiry, profile)
	if err != nil || operation.State() != 0 || opens.Load() != 1 {
		test.Fatal("CONNECTING must permit a pinned operation", err)
	}
	operation.Release()
	resume()
	await(test, ctx, cleanup)
	if generation.State() != -1 {
		test.Fatal("failed bootstrap is terminal")
	}
	for _, stage := range []string{"cleanup-held", "drained"} {
		if stage == "drained" {
			unblock()
			await(test, ctx, generation.owner.done)
		}
		if lease, err := manager.RetainChat(generation, expiry, profile); lease != nil || err != ErrBusy {
			test.Fatal(stage, "stale lease created a replacement", err)
		}
		if opens.Load() != 1 {
			test.Fatal("stale operation started another bootstrap")
		}
	}
	generation.Release()
	fresh := acquire(test, &manager, 1, func(context.Context) (Session, func(), error) {
		opens.Add(1)
		return &testSession{}, nil, nil
	}, func() {})
	await(test, ctx, fresh.owner.ready)
	if fresh.State() != 1 || opens.Load() != 2 {
		test.Fatal("fresh generation cannot recover")
	}
	if lease, err := manager.RetainChat(generation, expiry, profile); lease != nil || err != ErrBusy {
		test.Fatal("late generation affected new owner")
	}
}

func TestPinnedAcquisitionPreservesAdmission(test *testing.T) {
	ctx := bounded(test)
	var manager, foreign Coordinator
	profile, expiry := [32]byte{1}, time.Now().Add(time.Minute)
	session := &testSession{}
	open := func(context.Context) (Session, func(), error) { return session, nil, nil }
	generation := acquire(test, &manager, 1, open, func() {})
	await(test, ctx, generation.owner.ready)
	for _, attempt := range []struct {
		manager *Coordinator
		profile [32]byte
		expiry  time.Time
	}{{&foreign, profile, expiry}, {&manager, [32]byte{2}, expiry}, {&manager, profile, time.Now().Add(-time.Second)}} {
		if lease, err := attempt.manager.RetainChat(generation, attempt.expiry, attempt.profile); lease != nil || err != ErrBusy {
			test.Fatal("pin bypassed material/owner admission")
		}
	}
	reservation, err := manager.ReserveVPN(ctx)
	if err != nil {
		test.Fatal(err)
	}
	defer reservation.Release()
	if lease, err := manager.RetainChat(generation, expiry, profile); lease != nil || err != ErrBusy {
		test.Fatal("pin bypassed VPN reservation")
	}
	if err := reservation.Wait(ctx); err != nil {
		test.Fatal(err)
	}
}

func TestPinnedBorrowingKeepsVerifiedVPNContext(test *testing.T) {
	ctx := bounded(test)
	var manager Coordinator
	profile, expiry := [32]byte{1}, time.Now().Add(time.Minute)
	reservation, err := manager.ReserveVPN(ctx)
	if err != nil {
		test.Fatal(err)
	}
	defer reservation.Release()
	if err := reservation.Publish(&testSession{}, profile); err != nil {
		test.Fatal(err)
	}
	generation := acquire(test, &manager, 1, func(context.Context) (Session, func(), error) {
		test.Error("borrowed operation must not open a transport")
		return nil, nil, ErrBusy
	}, func() {})
	if lease, err := manager.RetainChat(generation, expiry, [32]byte{2}); lease != nil || err != ErrBusy {
		test.Fatal("borrowed profile mismatch accepted")
	}
	operation, err := manager.RetainChat(generation, expiry, profile)
	if err != nil || operation.State() != 2 {
		test.Fatal("matching VPN context lost", err)
	}
	operation.Release()
	generation.Release()
	if lease, err := manager.RetainChat(generation, expiry, profile); lease != nil || err != ErrBusy {
		test.Fatal("released generation retained")
	}
}
