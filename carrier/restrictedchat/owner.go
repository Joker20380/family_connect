package restrictedchat

import (
	"context"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/restrictedowner"
	"github.com/Joker20380/family_connect/carrier/underlay"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

const MaxLeases = 8

type Config struct {
	Readiness []byte
	Identity  []byte
	Anchor    []byte
	Resolver  string
}

func (Config) Format(output fmt.State, verb rune) { fmt.Fprint(output, "[chat material redacted]") }
func (Config) MarshalJSON() ([]byte, error)       { return nil, ErrDenied }

type Owner struct {
	coordinator restrictedowner.Coordinator
	mu          sync.Mutex
	active      int
	closed      bool
	clients     map[*Client]struct{}
}

func (owner *Owner) ReserveVPN(ctx context.Context) (*restrictedowner.VPN, error) {
	owner.mu.Lock()
	defer owner.mu.Unlock()
	if owner.closed || ctx == nil {
		return nil, ErrUnavailable
	}
	return owner.coordinator.ReserveVPN(ctx)
}

func (owner *Owner) Acquire(config Config, protect func(int) bool) (*Client, error) {
	return owner.acquireMaterial(config, protect, nil)
}

func (owner *Owner) AcquireGeneration(config Config, protect func(int) bool, generation *Client) (*Client, error) {
	if generation == nil {
		return nil, ErrUnavailable
	}
	return owner.acquireMaterial(config, protect, generation)
}

func (owner *Owner) acquireMaterial(config Config, protect func(int) bool, generation *Client) (*Client, error) {
	if protect == nil || len(config.Readiness) == 0 || len(config.Readiness) > wholedevice.MaxReadiness || len(config.Identity) != 64 || len(config.Anchor) != 32 {
		return nil, ErrDenied
	}
	profile, directory, err := wholedevice.DeliveryMaterial(config.Readiness, config.Identity, config.Anchor, time.Now())
	if err != nil {
		clear(profile)
		return nil, ErrDenied
	}
	var header struct {
		ExpiresAt int64 `json:"expires_at"`
	}
	if json.Unmarshal(config.Readiness, &header) != nil || header.ExpiresAt <= time.Now().Unix() {
		clear(profile)
		return nil, ErrDenied
	}
	resolver := config.Resolver
	return owner.acquireGeneration(time.Unix(header.ExpiresAt, 0), sha256.Sum256(profile), func(parent context.Context) (restrictedowner.Session, func(), error) {
		return openSession(parent, profile, directory, resolver, protect)
	}, func() { clear(profile); clear(directory) }, generation)
}

func openSession(parent context.Context, profile, directory []byte, resolver string, protect func(int) bool) (restrictedowner.Session, func(), error) {
	ctx, cancel := context.WithCancel(parent)
	network, err := underlay.New(ctx, resolver, protect)
	if err != nil {
		cancel()
		return nil, nil, err
	}
	cleanup := func() { cancel(); network.Close() }
	timer := time.AfterFunc(MaxDuration, cancel)
	session, err := wholedevice.OpenProvisioned(ctx, profile, directory, network, func(string) {})
	timer.Stop()
	if session == nil {
		return nil, cleanup, err
	}
	return session, cleanup, err
}

func (owner *Owner) acquire(expiry time.Time, profile [32]byte, open restrictedowner.OpenChat, dispose func()) (*Client, error) {
	return owner.acquireGeneration(expiry, profile, open, dispose, nil)
}

func (owner *Owner) acquireGeneration(expiry time.Time, profile [32]byte, open restrictedowner.OpenChat, dispose func(), generation *Client) (*Client, error) {
	owner.mu.Lock()
	defer owner.mu.Unlock()
	if owner.closed || owner.active >= MaxLeases {
		dispose()
		return nil, ErrUnavailable
	}
	var lease *restrictedowner.Chat
	var err error
	if generation != nil {
		if _, present := owner.clients[generation]; !present {
			dispose()
			return nil, ErrUnavailable
		}
		lease, err = owner.coordinator.RetainChat(generation.lease, expiry, profile)
		dispose()
	} else {
		lease, err = owner.coordinator.AcquireChat(expiry, profile, open, dispose)
	}
	if err != nil {
		return nil, ErrUnavailable
	}
	client, err := New(lease)
	if err != nil {
		lease.Release()
		return nil, err
	}
	owner.active++
	if owner.clients == nil {
		owner.clients = make(map[*Client]struct{})
	}
	owner.clients[client] = struct{}{}
	client.onClose = func() {
		owner.mu.Lock()
		delete(owner.clients, client)
		owner.active--
		owner.mu.Unlock()
	}
	return client, nil
}

func (owner *Owner) Close() error {
	owner.mu.Lock()
	owner.closed = true
	clients := make([]*Client, 0, len(owner.clients))
	for client := range owner.clients {
		clients = append(clients, client)
	}
	owner.mu.Unlock()
	for _, client := range clients {
		client.Close()
	}
	reservation, err := owner.coordinator.ReserveVPN(context.Background())
	if err == nil {
		defer reservation.Release()
		return reservation.Wait(context.Background())
	}
	return nil
}
