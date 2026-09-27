package telemost

import (
	"bytes"
	"context"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

type handshakeCapture struct {
	*Session
	mu      sync.Mutex
	packets [][]byte
	bytes   int
}

func (capture *handshakeCapture) SendContext(ctx context.Context, payload []byte) error {
	capture.mu.Lock()
	if len(capture.packets) >= 16 || capture.bytes+len(payload) > 1<<20 {
		capture.mu.Unlock()
		return familysession.ErrRejected
	}
	capture.packets = append(capture.packets, bytes.Clone(payload))
	capture.bytes += len(payload)
	capture.mu.Unlock()
	return capture.Session.SendContext(ctx, payload)
}

func TestLiveFamilyHandshakeReplay(test *testing.T) {
	if os.Getenv("FC_TEST_LIVE_FAMILY_REPLAY") != "1" {
		test.Skip("explicit opt-in, Family echo and orchestrated fresh server required")
	}
	raw, err := os.ReadFile(os.Getenv("FC_FAMILY_TEST_PROFILE"))
	if err != nil {
		test.Fatal("test credentials unavailable")
	}
	defer clear(raw)
	ctx, cancel := context.WithTimeout(context.Background(), 110*time.Second)
	defer cancel()
	join := func() *Session {
		carrier, err := New(ctx, Config{RoomURL: os.Getenv("FC_TELEMOST_ROOM"), DisplayName: "FC synthetic replay check", Mode: ModeVP8})
		if err != nil {
			test.Fatal("carrier creation failed")
		}
		test.Cleanup(func() { carrier.Close() })
		if carrier.Connect(ctx) != nil {
			test.Fatal("carrier join failed")
		}
		select {
		case <-time.After(3 * time.Second):
		case <-ctx.Done():
			test.Fatal("settle deadline")
		}
		return carrier
	}
	capture := &handshakeCapture{Session: join()}
	secured, err := familysession.Open(ctx, capture, raw, false)
	if err != nil {
		test.Fatal("initial authentication failed")
	}
	request, stop := context.WithTimeout(ctx, 10*time.Second)
	payload := []byte("synthetic authenticated replay prerequisite")
	err = secured.SendContext(request, payload)
	echo, receiveErr := secured.Recv(request)
	stop()
	capture.mu.Lock()
	transcript := append([][]byte(nil), capture.packets...)
	capture.mu.Unlock()
	if err != nil || receiveErr != nil || !bytes.Equal(payload, echo) || len(transcript) < 2 {
		test.Fatal("authenticated echo prerequisite failed")
	}
	secured.Close()
	test.Log("FAMILY_REPLAY_CAPTURE_READY")
	marker := os.Getenv("FC_FAMILY_REPLAY_READY")
	if marker == "" {
		test.Fatal("restart coordination unavailable")
	}
	deadline := time.NewTimer(45 * time.Second)
	defer deadline.Stop()
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()
	for {
		if _, err := os.Stat(marker); err == nil {
			break
		}
		select {
		case <-ticker.C:
		case <-deadline.C:
			test.Fatal("fresh server not confirmed")
		case <-ctx.Done():
			test.Fatal("replay deadline")
		}
	}
	fresh := join()
	for _, record := range transcript {
		if fresh.SendContext(ctx, record) != nil {
			test.Fatal("replay delivery failed")
		}
	}
	test.Log("FAMILY_REPLAY_SENT; requires fresh B auth rejection evidence, not a standalone gate PASS")
	select {
	case <-time.After(8 * time.Second):
	case <-ctx.Done():
		test.Fatal("observation deadline")
	}
	if fresh.Stats().MessagesSent != uint64(len(transcript)) {
		test.Fatal("replay count mismatch")
	}
}
