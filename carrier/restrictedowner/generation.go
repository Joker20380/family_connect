package restrictedowner

import (
	"context"
	"time"
)

func (manager *Coordinator) RetainChat(generation *Chat, expiry time.Time, profile [32]byte) (*Chat, error) {
	manager.mu.Lock()
	defer manager.mu.Unlock()
	if generation == nil || generation.manager != manager || generation.ctx.Err() != nil || !time.Now().Before(expiry) {
		return nil, ErrBusy
	}
	if owned := generation.owner; owned != nil {
		if manager.chat != owned || manager.vpn != nil || owned.closing || owned.ctx.Err() != nil || owned.profile != profile || (owned.session != nil && owned.session.Failed()) {
			return nil, ErrBusy
		}
		owned.refs++
		ctx, cancel := context.WithDeadline(owned.ctx, expiry)
		return &Chat{manager: manager, owner: owned, ctx: ctx, cancel: cancel}, nil
	}
	vpn := generation.vpn
	if vpn == nil || manager.vpn != vpn || vpn.ctx.Err() != nil || vpn.session == nil || vpn.session.Failed() || vpn.profile != profile || profile == [32]byte{} {
		return nil, ErrBusy
	}
	ctx, cancel := context.WithDeadline(vpn.ctx, expiry)
	return &Chat{manager: manager, ctx: ctx, cancel: cancel, borrowed: vpn.session, vpn: vpn}, nil
}
