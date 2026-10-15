package telemost

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"os"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/reliablestream"
)

type liveLoss struct {
	*Session
	armed   atomic.Bool
	dropped atomic.Uint64
}

func (point *liveLoss) SendContext(ctx context.Context, data []byte) error {
	if len(data) >= reliablestream.HeaderSize && string(data[:4]) == "FRS1" && data[4] == 2 && point.armed.CompareAndSwap(true, false) {
		point.dropped.Store(binary.BigEndian.Uint64(data[40:]) + 1)
		return nil
	}
	return point.Session.SendContext(ctx, data)
}

func TestLiveReliableGap(test *testing.T) {
	if os.Getenv("FC_TEST_LIVE_RELIABLE_GAP") != "1" {
		test.Skip("explicit physical live gap opt-in")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()
	raw, err := os.ReadFile(os.Getenv("FC_FAMILY_TEST_PROFILE"))
	if err != nil {
		test.Fatal("profile unavailable")
	}
	defer clear(raw)
	carrier, err := New(ctx, Config{RoomURL: os.Getenv("FC_TELEMOST_ROOM"), DisplayName: "FC synthetic reliability", Mode: ModeVP8})
	if err != nil {
		test.Fatal("carrier unavailable")
	}
	defer carrier.Close()
	if carrier.Connect(ctx) != nil {
		test.Fatal("join failed")
	}
	select {
	case <-time.After(3 * time.Second):
	case <-ctx.Done():
		test.Fatal("settle timeout")
	}
	point := &liveLoss{Session: carrier}
	secured, err := familysession.Open(ctx, point, raw, false)
	if err != nil {
		test.Fatal("Family handshake failed")
	}
	defer secured.Close()
	point.armed.Store(true)
	completed := make(chan error, 1)
	go func() {
		for index := 0; index < 8; index++ {
			payload := bytes.Repeat([]byte{byte(index)}, 16384)
			if err := secured.SendContext(ctx, payload); err != nil {
				completed <- err
				return
			}
		}
		completed <- nil
	}()
	for index := 0; index < 8; index++ {
		payload, err := secured.Recv(ctx)
		if err != nil || !bytes.Equal(payload, bytes.Repeat([]byte{byte(index)}, 16384)) {
			test.Fatal("exact authenticated recovery failed")
		}
	}
	if err := <-completed; err != nil {
		test.Fatal("send failed")
	}
	stats := secured.ReliabilityStats()
	if point.dropped.Load() == 0 || stats.Retransmissions == 0 {
		test.Fatal("controlled loss not exercised")
	}
	evidence, _ := json.Marshal(map[string]any{"injected_sequence": point.dropped.Load() - 1, "exact_echoes": 8, "tls_survived": true, "reliability": stats, "carrier": carrier.Stats()})
	test.Log("RELIABLE_GAP_EVIDENCE", string(evidence))
}
