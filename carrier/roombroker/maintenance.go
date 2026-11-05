package roombroker

import (
	"bytes"
	"context"
	"sync"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
)

type SessionMaintenance struct {
	mu           sync.Mutex
	closed       bool
	run          sync.Once
	seen         map[[32]byte]bool
	updates      chan Maintenance
	secured      *familysession.Session
	mux          *tcpforward.Mux
	ctx          context.Context
	setupID      string
	closeSession func()
}

func NewSessionMaintenance(ctx context.Context, mux *tcpforward.Mux, secured *familysession.Session, setupID string, closeSession func()) *SessionMaintenance {
	return &SessionMaintenance{seen: make(map[[32]byte]bool), updates: make(chan Maintenance, 1), secured: secured, mux: mux, ctx: ctx, setupID: setupID, closeSession: closeSession}
}

func (owner *SessionMaintenance) Run() {
	owner.run.Do(func() {
		defer func() {
			cancelled, cancel := context.WithCancel(owner.ctx)
			cancel()
			owner.mu.Lock()
			defer owner.mu.Unlock()
			owner.closed = true
			for {
				select {
				case update := <-owner.updates:
					update(cancelled)
				default:
					return
				}
			}
		}()
		MaintainSession(owner.ctx, owner.mux, owner.setupID, owner.closeSession, owner.updates)
	})
}

func (owner *SessionMaintenance) Offer(raw []byte, committed func()) bool {
	owner.mu.Lock()
	defer owner.mu.Unlock()
	if owner.closed || owner.ctx.Err() != nil || len(owner.seen) >= 32 {
		return false
	}
	candidate, err := owner.secured.Candidate(raw)
	if err != nil || owner.seen[candidate.Fingerprint] {
		return false
	}
	material := bytes.Clone(raw)
	update := func(ctx context.Context) (bool, error) {
		defer clear(material)
		if ctx.Err() != nil || owner.ctx.Err() != nil {
			return false, Code("cancelled")
		}
		changed, err := ExchangeCredentials(ctx, owner.mux, owner.secured, material)
		if changed && err == nil && ctx.Err() == nil && owner.ctx.Err() == nil && committed != nil {
			committed()
		}
		return changed, err
	}
	select {
	case owner.updates <- update:
		owner.seen[candidate.Fingerprint] = true
		return true
	default:
		clear(material)
		return false
	}
}
