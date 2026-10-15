package telemost

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/json"
	"errors"
	"os"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

func TestLiveSignalingClosure(t *testing.T) {
	if os.Getenv("FC_TEST_LIVE_SIGNALING_CLOSE") != "1" {
		t.Skip("explicit live opt-in and remote VP8 echo required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 80*time.Second)
	defer cancel()
	session, err := New(ctx, Config{RoomURL: os.Getenv("FC_TELEMOST_ROOM"), DisplayName: "FC synthetic WS closure", Mode: ModeVP8})
	if err != nil {
		t.Fatal(err)
	}
	defer session.Close()
	if err := session.Connect(ctx); err != nil {
		t.Fatal(err)
	}
	select {
	case <-time.After(3 * time.Second):
	case <-ctx.Done():
		t.Fatal("live connect/settle timeout")
	}
	var data familysession.PacketEndpoint = session
	if path := os.Getenv("FC_FAMILY_TEST_PROFILE"); path != "" {
		raw, err := os.ReadFile(path)
		if err != nil {
			t.Fatal("test credentials unavailable")
		}
		secured, err := familysession.Open(ctx, session, raw, false)
		clear(raw)
		if err != nil {
			t.Fatal("Family authentication failed")
		}
		defer secured.Close()
		data = secured
	}
	payload := make([]byte, 1024)
	if _, err := rand.Read(payload); err != nil {
		t.Fatal("random payload unavailable")
	}
	probeContext, probeCancel := context.WithTimeout(ctx, 10*time.Second)
	defer probeCancel()
	if err := data.SendContext(probeContext, payload); err != nil {
		t.Fatal("live VP8 send failed")
	}
	echo, err := data.Recv(probeContext)
	if err != nil || !bytes.Equal(payload, echo) {
		t.Fatal("live VP8 echo prerequisite failed")
	}
	started := time.Now()
	if os.Getenv("FC_TEST_LIVE_PEER_CLOSE") == "1" {
		_ = session.pcPub.Load().Close()
	} else if connection := session.wsConn(); connection != nil {
		_ = connection.Close()
	} else {
		t.Fatal("signaling already closed")
	}
	closedContext, closedCancel := context.WithTimeout(ctx, 5*time.Second)
	defer closedCancel()
	if _, err := data.Recv(closedContext); err == nil || errors.Is(err, context.DeadlineExceeded) || os.IsTimeout(err) {
		t.Fatal("signaling loss did not terminate receive promptly")
	}
	if err := data.SendContext(closedContext, payload); err == nil {
		t.Fatal("send succeeded after signaling loss")
	}
	_ = session.Close()
	encoded, err := json.Marshal(map[string]any{"event": "live_signaling_close", "family_authenticated": os.Getenv("FC_FAMILY_TEST_PROFILE") != "", "peer_close": os.Getenv("FC_TEST_LIVE_PEER_CLOSE") == "1", "echo_byte_equal": true, "shutdown_ms": time.Since(started).Milliseconds(), "stats": session.Stats()})
	if err != nil {
		t.Fatal("metrics encoding failed")
	}
	t.Log(string(encoded))
}
