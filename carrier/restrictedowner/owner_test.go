package restrictedowner

import (
	"context"
	"errors"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

type testSession struct {
	closed atomic.Int32
	close  func()
}

func (session *testSession) Close() {
	if session.closed.Add(1) != 1 {
		panic("duplicate session close")
	}
	if session.close != nil {
		session.close()
	}
}
func (session *testSession) Failed() bool { return session.closed.Load() != 0 }

func bounded(test *testing.T) context.Context {
	test.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	test.Cleanup(cancel)
	return ctx
}

func await(test *testing.T, ctx context.Context, ready <-chan struct{}) {
	test.Helper()
	select {
	case <-ready:
	case <-ctx.Done():
		test.Fatal("bounded synchronization failed")
	}
}

func acquire(test *testing.T, manager *Coordinator, profile byte, open OpenChat, dispose func()) *Chat {
	test.Helper()
	lease, err := manager.AcquireChat(time.Now().Add(time.Minute), [32]byte{profile}, open, dispose)
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(lease.Release)
	return lease
}

func forbidden(context.Context) (Session, func(), error) { panic("independent open forbidden") }
func nothing()                                           {}

func TestChatFirstCleanupGate(test *testing.T) {
	ctx := bounded(test)
	var manager Coordinator
	closing, allowClose, disposed := make(chan struct{}), make(chan struct{}), make(chan struct{})
	permitClose := sync.OnceFunc(func() { close(allowClose) })
	defer permitClose()
	var order atomic.Int32
	old := &testSession{close: func() { close(closing); <-allowClose; order.Store(1) }}
	chat := acquire(test, &manager, 1, func(context.Context) (Session, func(), error) {
		return old, func() {
			if order.Load() != 1 {
				panic("underlay before session cleanup")
			}
			order.Store(2)
		}, nil
	}, func() {
		if order.Load() != 2 {
			panic("JNI before underlay cleanup")
		}
		order.Store(3)
		close(disposed)
	})
	if _, err := chat.Session(ctx); err != nil {
		test.Fatal(err)
	}
	workerDone, err := chat.Work()
	if err != nil {
		test.Fatal(err)
	}
	vpn, err := manager.ReserveVPN(ctx)
	if err != nil {
		test.Fatal(err)
	}
	defer vpn.Release()
	await(test, ctx, closing)
	if chat.State() != -1 {
		test.Fatal("stale chat remains usable")
	}
	if lease, err := manager.AcquireChat(time.Now().Add(time.Minute), [32]byte{2}, forbidden, nothing); err == nil || lease != nil {
		test.Fatal("new profile bypassed VPN reservation")
	}
	if vpn.Publish(&testSession{}, [32]byte{1}) == nil {
		test.Fatal("READY before cleanup")
	}
	permitClose()
	select {
	case <-disposed:
		test.Fatal("JNI released with worker alive")
	default:
	}
	workerDone()
	workerDone()
	if err := vpn.Wait(ctx); err != nil {
		test.Fatal(err)
	}
	await(test, ctx, disposed)
	if order.Load() != 3 {
		test.Fatal("gate passed before full cleanup")
	}
	active := &testSession{}
	if err := vpn.Publish(active, [32]byte{1}); err != nil {
		test.Fatal(err)
	}
	borrowed := acquire(test, &manager, 1, forbidden, nothing)
	if borrowed.State() != 2 {
		test.Fatal("not borrowed")
	}
	chat.Release()
	chat.Release()
	borrowed.Release()
	if active.Failed() || old.closed.Load() != 1 {
		test.Fatal("incorrect resource ownership")
	}
	vpn.Release()
	active.Close()
	await(test, ctx, chat.owner.done)
}

func TestVPNFirstDisconnectStaleGeneration(test *testing.T) {
	ctx := bounded(test)
	var manager Coordinator
	vpn, err := manager.ReserveVPN(ctx)
	if err != nil {
		test.Fatal(err)
	}
	active := &testSession{}
	if vpn.Wait(ctx) != nil || vpn.Publish(active, [32]byte{1}) != nil {
		test.Fatal("VPN readiness")
	}
	first := acquire(test, &manager, 1, forbidden, nothing)
	second := acquire(test, &manager, 1, forbidden, nothing)
	first.Release()
	first.Release()
	if active.Failed() || second.State() != 2 {
		test.Fatal("borrow release closed VPN")
	}
	work, err := second.Work()
	if err != nil {
		test.Fatal(err)
	}
	drainDone := make(chan struct{})
	go func() { vpn.Release(); close(drainDone) }()
	await(test, ctx, second.ctx.Done())
	select {
	case <-drainDone:
		test.Fatal("release before borrowed worker cleanup")
	default:
	}
	work()
	await(test, ctx, drainDone)
	active.Close()
	newVPN, err := manager.ReserveVPN(ctx)
	if err != nil {
		test.Fatal(err)
	}
	defer newVPN.Release()
	newSession := &testSession{}
	if newVPN.Publish(newSession, [32]byte{1}) != nil {
		test.Fatal("new generation not ready")
	}
	second.Release()
	vpn.Release()
	if vpn.Publish(&testSession{}, [32]byte{1}) == nil {
		test.Fatal("stale publish")
	}
	third := acquire(test, &manager, 1, forbidden, nothing)
	if third.State() != 2 || newSession.Failed() {
		test.Fatal("stale release affected new generation")
	}
	third.Release()
	newVPN.Release()
	newSession.Close()
}

func TestOpeningLatePublication(test *testing.T) {
	ctx := bounded(test)
	var manager Coordinator
	entered, returnOpen := make(chan struct{}), make(chan struct{})
	permit := sync.OnceFunc(func() { close(returnOpen) })
	defer permit()
	late := &testSession{}
	chat := acquire(test, &manager, 1, func(parent context.Context) (Session, func(), error) {
		close(entered)
		<-parent.Done()
		<-returnOpen
		return late, nothing, nil
	}, nothing)
	await(test, ctx, entered)
	vpn, err := manager.ReserveVPN(ctx)
	if err != nil {
		test.Fatal(err)
	}
	defer vpn.Release()
	if chat.State() != -1 {
		test.Fatal("opening handle not invalidated")
	}
	if vpn.Publish(&testSession{}, [32]byte{1}) == nil {
		test.Fatal("published before opener returned")
	}
	permit()
	if vpn.Wait(ctx) != nil || late.closed.Load() != 1 || chat.State() != -1 {
		test.Fatal("late publication or leaked late session")
	}
}

func TestCancellationAndStartupFailure(test *testing.T) {
	for _, stage := range []string{"before_reserve", "during_cleanup", "after_cleanup", "startup_failure", "budget"} {
		test.Run(stage, func(test *testing.T) {
			ctx := bounded(test)
			var manager Coordinator
			closing, allow := make(chan struct{}), make(chan struct{})
			permit := sync.OnceFunc(func() { close(allow) })
			defer permit()
			old := &testSession{close: func() { close(closing); <-allow }}
			chat := acquire(test, &manager, 1, func(context.Context) (Session, func(), error) { return old, nothing, nil }, nothing)
			if _, err := chat.Session(ctx); err != nil {
				test.Fatal(err)
			}
			attempt, cancel := context.WithCancel(ctx)
			defer cancel()
			if stage == "before_reserve" {
				cancel()
			}
			vpn, err := manager.ReserveVPN(attempt)
			if stage == "before_reserve" {
				if err == nil || chat.State() != 1 {
					test.Fatal("pre-cancel changed chat")
				}
				chat.Release()
				permit()
				await(test, ctx, chat.owner.done)
				return
			}
			if err != nil {
				test.Fatal(err)
			}
			await(test, ctx, closing)
			if stage == "after_cleanup" || stage == "startup_failure" {
				permit()
				if vpn.Wait(ctx) != nil {
					test.Fatal("cleanup wait")
				}
			}
			if stage == "budget" {
				budget, finish := context.WithTimeout(ctx, 10*time.Millisecond)
				if !errors.Is(vpn.Wait(budget), context.DeadlineExceeded) {
					test.Fatal("budget not bounded")
				}
				finish()
			}
			cancel()
			if vpn.Publish(&testSession{}, [32]byte{1}) == nil {
				test.Fatal("cancelled READY")
			}
			vpn.Release()
			if stage == "during_cleanup" || stage == "budget" {
				if _, err := manager.AcquireChat(time.Now().Add(time.Minute), [32]byte{1}, forbidden, nothing); err == nil {
					test.Fatal("reopened over draining chat")
				}
			}
			permit()
			await(test, ctx, chat.owner.done)
			fresh := &testSession{}
			recovered := acquire(test, &manager, 1, func(context.Context) (Session, func(), error) { return fresh, nothing, nil }, nothing)
			if _, err := recovered.Session(ctx); err != nil {
				test.Fatal(err)
			}
			chat.Release()
			recovered.Release()
			await(test, ctx, recovered.owner.done)
			if old.closed.Load() != 1 || fresh.closed.Load() != 1 {
				test.Fatal("cleanup count")
			}
		})
	}
}

func TestSimultaneousAcquireReserve(test *testing.T) {
	for iteration := 0; iteration < 40; iteration++ {
		ctx := bounded(test)
		var manager Coordinator
		start := make(chan struct{})
		chatResult := make(chan *Chat, 1)
		vpnResult := make(chan *VPN, 1)
		var live atomic.Int32
		go func() {
			<-start
			chat, _ := manager.AcquireChat(time.Now().Add(time.Minute), [32]byte{1}, func(context.Context) (Session, func(), error) {
				if live.Add(1) != 1 {
					panic("overlapping independent open")
				}
				return &testSession{close: func() { live.Add(-1) }}, nothing, nil
			}, nothing)
			chatResult <- chat
		}()
		go func() { <-start; vpn, _ := manager.ReserveVPN(ctx); vpnResult <- vpn }()
		close(start)
		vpn := <-vpnResult
		chat := <-chatResult
		if vpn == nil || vpn.Wait(ctx) != nil || live.Load() != 0 {
			test.Fatal("concurrent handoff failed")
		}
		if chat != nil {
			chat.Release()
		}
		vpn.Release()
	}
}

func TestCompatibilityExpiryAndFailure(test *testing.T) {
	ctx := bounded(test)
	var manager Coordinator
	vpn, _ := manager.ReserveVPN(ctx)
	defer vpn.Release()
	active := &testSession{}
	if vpn.Publish(active, [32]byte{1}) != nil {
		test.Fatal("publish")
	}
	for _, profile := range [][32]byte{{2}, {3}, {4}, {5}, {}} {
		if _, err := manager.AcquireChat(time.Now().Add(time.Minute), profile, forbidden, nothing); err == nil {
			test.Fatal("incompatible profile borrowed")
		}
	}
	if _, err := manager.AcquireChat(time.Now().Add(-time.Second), [32]byte{1}, forbidden, nothing); err == nil {
		test.Fatal("expired delivery borrowed")
	}
	lease, err := manager.AcquireChat(time.Now().Add(10*time.Millisecond), [32]byte{1}, forbidden, nothing)
	if err != nil {
		test.Fatal(err)
	}
	await(test, ctx, lease.ctx.Done())
	if lease.State() != -1 {
		test.Fatal("deadline extended")
	}
	lease.Release()
	active.Close()
	if _, err := manager.AcquireChat(time.Now().Add(time.Minute), [32]byte{1}, forbidden, nothing); err == nil {
		test.Fatal("failed VPN borrowed")
	}
	vpn.Release()
	var disposed atomic.Int32
	failed := acquire(test, &manager, 1, func(context.Context) (Session, func(), error) { return nil, nothing, errors.New("startup failure") }, func() { disposed.Add(1) })
	await(test, ctx, failed.owner.done)
	if failed.State() != -1 || disposed.Load() != 1 {
		test.Fatal("failed chat cleanup")
	}
}
