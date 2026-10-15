package mixed

import (
	"testing"
	"time"
)

func TestMixedSustainedRealPeerOverload(test *testing.T) {
	value := newPair(test, "new", "oldgateway")
	gate := make(chan struct{})
	defer close(gate)
	value.clientPoint.SetReadGate(gate)
	started := time.Now()
	for index := 0; index < 8; index++ {
		if err := value.gateway.SendContext(value.ctx, payload(70+index)); err != nil {
			test.Fatal(err)
		}
	}
	await(test, "persistent blocked reader has bounded terminal", 12*time.Second, func() bool {
		return value.clientPoint.Snapshot()["closed"].(bool) || value.gateway.stats()["Terminal"].(string) != ""
	})
	observation := value.clientPoint.Snapshot()
	if observation["depth"].(int) > 64 || observation["capacity"].(int) != 64 {
		test.Fatal("receive memory bound violated")
	}
	record(test, "sustained_real_peer_overload", map[string]any{"elapsed_ms": time.Since(started).Milliseconds(), "queue": observation, "client": value.client.stats(), "gateway": value.gateway.stats(), "injected_replays": 0})
	value.close(test)
}
