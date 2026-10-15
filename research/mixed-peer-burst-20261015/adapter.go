//go:build fc_mixed_fixture

package telemost

import (
	"context"
	"encoding/json"
	"sync"
	"sync/atomic"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

type MixedEndpoint struct {
	session      *Session
	Send         func(context.Context, []byte) error
	mu           sync.Mutex
	high         int
	enqueued     int
	readGate     <-chan struct{}
	closeGate    <-chan struct{}
	closeEntered chan struct{}
	dequeued     atomic.Int64
	active       atomic.Int64
}

func NewMixedEndpoint(ctx context.Context) (*MixedEndpoint, error) {
	session, err := New(ctx, Config{RoomURL: "mixed-fixture-no-provider", Trace: sessiontrace.New("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", nil)})
	if err != nil {
		return nil, err
	}
	return &MixedEndpoint{session: session}, nil
}

func (endpoint *MixedEndpoint) SendContext(ctx context.Context, payload []byte) error {
	endpoint.active.Add(1)
	defer endpoint.active.Add(-1)
	return endpoint.Send(ctx, payload)
}

func (endpoint *MixedEndpoint) Recv(ctx context.Context) ([]byte, error) {
	endpoint.active.Add(1)
	defer endpoint.active.Add(-1)
	endpoint.mu.Lock()
	gate := endpoint.readGate
	endpoint.mu.Unlock()
	if gate != nil {
		select {
		case <-gate:
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-endpoint.session.closeCh:
			return nil, ErrClosed
		}
	}
	payload, err := endpoint.session.Recv(ctx)
	if err == nil {
		endpoint.dequeued.Add(1)
	}
	return payload, err
}

func (endpoint *MixedEndpoint) Deliver(payload []byte) bool {
	endpoint.mu.Lock()
	defer endpoint.mu.Unlock()
	select {
	case <-endpoint.session.closeCh:
		return false
	default:
	}
	endpoint.session.deliver(payload)
	depth := len(endpoint.session.recvQueue)
	if depth > endpoint.high {
		endpoint.high = depth
	}
	select {
	case <-endpoint.session.closeCh:
		return false
	default:
	}
	endpoint.enqueued++
	return true
}

func (endpoint *MixedEndpoint) SetReadGate(gate <-chan struct{}) {
	endpoint.mu.Lock()
	endpoint.readGate = gate
	endpoint.mu.Unlock()
}

func (endpoint *MixedEndpoint) Snapshot() map[string]any {
	endpoint.mu.Lock()
	defer endpoint.mu.Unlock()
	result := map[string]any{"depth": len(endpoint.session.recvQueue), "capacity": cap(endpoint.session.recvQueue), "sampled_high_water": endpoint.high, "enqueue_returned_live": endpoint.enqueued, "dequeued": endpoint.dequeued.Load(), "active_calls": endpoint.active.Load()}
	select {
	case <-endpoint.session.closeCh:
		result["closed"] = true
	default:
		result["closed"] = false
	}
	raw, _ := json.Marshal(endpoint.session.cfg.Trace.Snapshot())
	var trace map[string]any
	_ = json.Unmarshal(raw, &trace)
	result["first_failure"] = trace["first_failure"]
	return result
}

func (endpoint *MixedEndpoint) SetCloseGate(gate <-chan struct{}, entered chan struct{}) {
	endpoint.mu.Lock()
	endpoint.closeGate, endpoint.closeEntered = gate, entered
	endpoint.mu.Unlock()
}

func (endpoint *MixedEndpoint) Close() error {
	endpoint.mu.Lock()
	gate := endpoint.closeGate
	if endpoint.closeEntered != nil {
		close(endpoint.closeEntered)
		endpoint.closeEntered = nil
	}
	endpoint.mu.Unlock()
	if gate != nil {
		<-gate
	}
	return endpoint.session.Close()
}
