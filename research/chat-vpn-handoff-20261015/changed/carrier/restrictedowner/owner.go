package restrictedowner

import (
	"context"
	"errors"
	"sync"
	"time"
)

var ErrBusy = errors.New("restricted ownership unavailable")

type Session interface {
	Close()
	Failed() bool
}

type OpenChat func(context.Context) (Session, func(), error)

type Coordinator struct {
	mu   sync.Mutex
	chat *chatOwner
	vpn  *VPN
}

type chatOwner struct {
	ctx     context.Context
	cancel  context.CancelFunc
	ready   chan struct{}
	done    chan struct{}
	profile [32]byte
	session Session
	refs    int
	workers sync.WaitGroup
	closing bool
}

type Chat struct {
	manager  *Coordinator
	owner    *chatOwner
	ctx      context.Context
	cancel   context.CancelFunc
	borrowed Session
	vpn      *VPN
	released bool
}

type VPN struct {
	manager *Coordinator
	ctx     context.Context
	cancel  context.CancelFunc
	drained <-chan struct{}
	session Session
	profile [32]byte
	workers sync.WaitGroup
}

func (manager *Coordinator) AcquireChat(expiry time.Time, profile [32]byte, open OpenChat, dispose func()) (*Chat, error) {
	manager.mu.Lock()
	if !time.Now().Before(expiry) {
		manager.mu.Unlock()
		dispose()
		return nil, ErrBusy
	}
	if vpn := manager.vpn; vpn != nil {
		if vpn.ctx.Err() != nil || vpn.session == nil || vpn.session.Failed() || vpn.profile != profile || profile == [32]byte{} {
			manager.mu.Unlock()
			dispose()
			return nil, ErrBusy
		}
		ctx, cancel := context.WithDeadline(vpn.ctx, expiry)
		lease := &Chat{manager: manager, ctx: ctx, cancel: cancel, borrowed: vpn.session, vpn: vpn}
		manager.mu.Unlock()
		dispose()
		return lease, nil
	}
	owned := manager.chat
	if owned != nil && (owned.ctx.Err() != nil || owned.profile != profile || (owned.session != nil && owned.session.Failed())) {
		manager.mu.Unlock()
		dispose()
		return nil, ErrBusy
	}
	created := owned == nil
	if created {
		ctx, cancel := context.WithDeadline(context.Background(), expiry)
		owned = &chatOwner{ctx: ctx, cancel: cancel, ready: make(chan struct{}), done: make(chan struct{}), profile: profile}
		manager.chat = owned
	}
	owned.refs++
	ctx, cancel := context.WithDeadline(owned.ctx, expiry)
	lease := &Chat{manager: manager, owner: owned, ctx: ctx, cancel: cancel}
	manager.mu.Unlock()
	if created {
		go manager.runChat(owned, open, dispose)
	} else {
		dispose()
	}
	return lease, nil
}

func (manager *Coordinator) runChat(owned *chatOwner, open OpenChat, dispose func()) {
	var session Session
	var cleanup func()
	var err error
	if owned.ctx.Err() == nil {
		session, cleanup, err = open(owned.ctx)
	}
	manager.mu.Lock()
	if err != nil || session == nil || owned.ctx.Err() != nil {
		owned.cancel()
	} else {
		owned.session = session
	}
	close(owned.ready)
	manager.mu.Unlock()
	<-owned.ctx.Done()
	manager.mu.Lock()
	owned.closing = true
	manager.mu.Unlock()
	if session != nil {
		session.Close()
	}
	owned.workers.Wait()
	if cleanup != nil {
		cleanup()
	}
	dispose()
	manager.mu.Lock()
	if manager.chat == owned {
		manager.chat = nil
	}
	close(owned.done)
	manager.mu.Unlock()
}

func (lease *Chat) Context() context.Context { return lease.ctx }

func (lease *Chat) Work() (func(), error) {
	lease.manager.mu.Lock()
	defer lease.manager.mu.Unlock()
	if lease.ctx.Err() != nil {
		return nil, ErrBusy
	}
	var workers *sync.WaitGroup
	if lease.owner != nil {
		if lease.owner.closing {
			return nil, ErrBusy
		}
		workers = &lease.owner.workers
	} else {
		workers = &lease.vpn.workers
	}
	workers.Add(1)
	return sync.OnceFunc(workers.Done), nil
}

func (lease *Chat) State() int32 {
	lease.manager.mu.Lock()
	defer lease.manager.mu.Unlock()
	if lease.ctx.Err() != nil {
		return -1
	}
	if lease.borrowed != nil {
		if lease.borrowed.Failed() {
			return -1
		}
		return 2
	}
	select {
	case <-lease.owner.ready:
		if lease.owner.session == nil || lease.owner.session.Failed() {
			return -1
		}
		return 1
	default:
		return 0
	}
}

func (lease *Chat) Session(ctx context.Context) (Session, error) {
	if lease.owner != nil {
		select {
		case <-lease.owner.ready:
		case <-lease.ctx.Done():
			return nil, lease.ctx.Err()
		case <-ctx.Done():
			return nil, ctx.Err()
		}
	}
	lease.manager.mu.Lock()
	defer lease.manager.mu.Unlock()
	if lease.ctx.Err() != nil || ctx.Err() != nil {
		return nil, ErrBusy
	}
	session := lease.borrowed
	if session == nil {
		session = lease.owner.session
	}
	if session == nil || session.Failed() {
		return nil, ErrBusy
	}
	return session, nil
}

func (lease *Chat) Release() {
	lease.manager.mu.Lock()
	defer lease.manager.mu.Unlock()
	if lease.released {
		return
	}
	lease.released = true
	lease.cancel()
	if lease.owner != nil {
		lease.owner.refs--
		if lease.owner.refs == 0 {
			lease.owner.cancel()
		}
	}
}

func (manager *Coordinator) ReserveVPN(parent context.Context) (*VPN, error) {
	manager.mu.Lock()
	defer manager.mu.Unlock()
	if manager.vpn != nil || parent.Err() != nil {
		return nil, ErrBusy
	}
	ctx, cancel := context.WithCancel(parent)
	drained := make(chan struct{})
	vpn := &VPN{manager: manager, ctx: ctx, cancel: cancel, drained: drained}
	manager.vpn = vpn
	if manager.chat != nil {
		vpn.drained = manager.chat.done
		manager.chat.cancel()
	} else {
		close(drained)
	}
	return vpn, nil
}

func (vpn *VPN) Wait(ctx context.Context) error {
	select {
	case <-vpn.drained:
	case <-ctx.Done():
		return ctx.Err()
	case <-vpn.ctx.Done():
		return vpn.ctx.Err()
	}
	vpn.manager.mu.Lock()
	defer vpn.manager.mu.Unlock()
	if vpn.manager.vpn != vpn || vpn.ctx.Err() != nil || ctx.Err() != nil {
		return ErrBusy
	}
	return nil
}

func (vpn *VPN) Publish(session Session, profile [32]byte) error {
	vpn.manager.mu.Lock()
	defer vpn.manager.mu.Unlock()
	select {
	case <-vpn.drained:
	default:
		return ErrBusy
	}
	if vpn.manager.vpn != vpn || vpn.ctx.Err() != nil || session == nil || session.Failed() || vpn.session != nil {
		return ErrBusy
	}
	vpn.session, vpn.profile = session, profile
	return nil
}

func (vpn *VPN) Drain() {
	vpn.manager.mu.Lock()
	vpn.cancel()
	vpn.manager.mu.Unlock()
	vpn.workers.Wait()
}

func (vpn *VPN) Release() {
	vpn.Drain()
	vpn.manager.mu.Lock()
	defer vpn.manager.mu.Unlock()
	if vpn.manager.vpn == vpn {
		vpn.manager.vpn = nil
	}
}
