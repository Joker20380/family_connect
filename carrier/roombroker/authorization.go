package roombroker

import (
	"context"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
)

type authorizationAccess func(context.Context, func(Identity, time.Time) error) error

type activeAuthorization struct {
	mu     sync.Mutex
	access authorizationAccess
}

func sessionAccess(path string, secured *familysession.Session) authorizationAccess {
	return func(ctx context.Context, use func(Identity, time.Time) error) error {
		return secured.WithAuthorization(ctx, func(snapshot familysession.Authorization) error {
			raw, err := LoadCredentials(path)
			if err != nil {
				return err
			}
			defer clear(raw)
			if snapshot.CheckPolicy(raw, true) != nil {
				return Code("unauthorized")
			}
			identity, err := profileIdentity(ctx, raw, &snapshot.State, false)
			if err != nil {
				return err
			}
			return use(identity, snapshot.Deadline)
		})
	}
}

func (binding *leaseBinding) configure(ctx context.Context, path string, secured *familysession.Session, config *tcpforward.MuxConfig) error {
	current, broker := binding.current, binding.broker
	current.authorization.mu.Lock()
	defer current.authorization.mu.Unlock()
	access := sessionAccess(path, secured)
	err := access(ctx, func(identity Identity, deadline time.Time) error {
		broker.mu.Lock()
		defer broker.unlock()
		if broker.closed || broker.setups[current.id] != current || current.state != Active || current.ctx.Err() != nil || identity != current.identity || !time.Now().Before(deadline) {
			return Code("unauthorized")
		}
		current.authorization.access = access
		return nil
	})
	if err != nil {
		return err
	}
	config.LeaseRenewal = binding.dynamicHandler(access)
	config.CredentialRenewal = binding.credentialHandler(path, secured)
	return nil
}

func (binding *leaseBinding) credentialGuard(ctx context.Context, path string) familysession.RenewalGuard {
	return func(next familysession.Authorization, commit func() error) error {
		raw, err := LoadCredentials(path)
		if err != nil {
			return err
		}
		defer clear(raw)
		if next.CheckPolicy(raw, true) != nil {
			return Code("unauthorized")
		}
		identity, err := profileIdentity(ctx, raw, &next.State, false)
		if err != nil {
			return err
		}
		current, broker := binding.current, binding.broker
		broker.mu.Lock()
		defer broker.unlock()
		current.lease.mu.Lock()
		defer current.lease.mu.Unlock()
		if broker.closed || broker.setups[current.id] != current || current.state != Active || current.ctx.Err() != nil || ctx.Err() != nil || identity != current.identity || !current.lease.now().Before(current.lease.until) {
			return Code("unauthorized")
		}
		return commit()
	}
}

func (broker *Broker) reauthorize(current *setup) {
	current.authorization.mu.Lock()
	defer current.authorization.mu.Unlock()
	access := current.authorization.access
	check := func(identity Identity, _ time.Time) error {
		broker.mu.Lock()
		defer broker.unlock()
		if terminal(current.state) || current.ctx.Err() != nil {
			return nil
		}
		if identity != current.identity {
			return Code("unauthorized")
		}
		if current.state != Active && time.Now().After(current.deadline) {
			return Code("unused_expired")
		}
		return nil
	}
	var err error
	if access != nil {
		err = access(current.ctx, check)
	} else {
		var identity Identity
		identity, err = authorized(current.ctx, current.authorize)
		if err == nil {
			err = check(identity, time.Time{})
		}
	}
	if err == Code("unused_expired") {
		broker.terminate(current, Expired, "unused_expired")
	} else if err != nil {
		broker.terminate(current, Failed, "authorization_changed")
	}
}
