package telemost

import (
	"context"
	"encoding/json"
	"strings"
	"testing"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func TestReceiveQueueFailureKeepsSourceBeforeCleanup(t *testing.T) {
	trace := sessiontrace.New(strings.Repeat("a", 64), nil)
	session, err := New(context.Background(), Config{RoomURL: "test-room", Trace: trace})
	if err != nil {
		t.Fatal(err)
	}
	defer session.Close()
	for index := 0; index <= cap(session.recvQueue); index++ {
		session.deliver([]byte{1})
	}
	if err := session.Close(); err != nil {
		t.Fatal(err)
	}
	raw, err := json.Marshal(trace.Snapshot())
	if err != nil {
		t.Fatal(err)
	}
	var snapshot struct {
		FirstFailure struct {
			Reason string `json:"reason"`
			Source string `json:"close_source"`
		} `json:"first_failure"`
	}
	if err := json.Unmarshal(raw, &snapshot); err != nil {
		t.Fatal(err)
	}
	if snapshot.FirstFailure.Reason != "CARRIER_ERROR" || snapshot.FirstFailure.Source != "RECEIVE_QUEUE_FULL" {
		t.Fatalf("first close source lost before cleanup: %+v", snapshot.FirstFailure)
	}
}
