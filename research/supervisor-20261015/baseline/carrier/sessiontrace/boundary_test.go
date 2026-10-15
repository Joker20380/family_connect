package sessiontrace

import (
	"encoding/json"
	"strings"
	"sync"
	"testing"
)

func TestBoundaryBoundPrivacyCopiesAndConcurrentSnapshot(test *testing.T) {
	var exported Event
	recorder := New(strings.Repeat("a", 64), func(event Event) bool { exported = event; return true })
	var workers sync.WaitGroup
	for worker := 0; worker < 4; worker++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			for index := 0; index < 100; index++ {
				recorder.Boundary(Boundary{Direction: "tx", Stage: "reliable_send", Result: "ok", DataKnown: true, DataSequence: 48, AttemptKnown: true, Attempt: 8})
				_ = recorder.Snapshot()
			}
		}()
	}
	workers.Wait()
	recorder.Boundary(Boundary{Direction: "tx", Stage: "PRIVATE KEY", Result: "ok"})
	recorder.Boundary(Boundary{Direction: "https://secret", Stage: "reliable_send", Result: "ok"})
	recorder.Boundary(Boundary{Direction: "rx", Stage: "rtp_received", Result: "token=secret"})
	value := recorder.Snapshot()
	if len(value.Boundaries.Events) != BoundaryLimit || value.Boundaries.Dropped != 400-BoundaryLimit || value.Boundaries.Events[0].Index != 337 {
		test.Fatal("ring bound or rejection failed", value.Boundaries)
	}
	value.Boundaries.Events[0].Stage = "mutated"
	recorder.Record(Event{Stage: "CARRIER_ACTIVITY", State: "ESTABLISHED", Reason: "NONE"})
	value = recorder.Snapshot()
	exported.Delivery.Boundaries.Events[0].Stage = "mutated"
	if value.Events[0].Delivery != nil {
		test.Fatal("ring must not multiply across retained native samples")
	}
	raw, err := json.Marshal(recorder.Snapshot())
	if err != nil {
		test.Fatal(err)
	}
	for _, forbidden := range []string{"secret", "PRIVATE", "mutated", "payload", "destination", "room", "epoch"} {
		if strings.Contains(string(raw), forbidden) {
			test.Fatal("diagnostic privacy/copy failure", forbidden)
		}
	}
}

func TestMessageAttemptEvictionIsUnknown(test *testing.T) {
	recorder := New(strings.Repeat("b", 64), nil)
	point := Boundary{Direction: "tx", Stage: "carrier_queued", Result: "ok", MessageKnown: true, Sender: 1, Message: 7, DataKnown: true, DataSequence: 58, AttemptKnown: true, Attempt: 1}
	recorder.Boundary(point)
	query := Boundary{MessageKnown: true, Sender: 1, Message: 7}
	if actual := recorder.MessageAttempt(query); !actual.AttemptKnown || actual.Attempt != 1 || actual.DataSequence != 58 {
		test.Fatal("lost exact message attempt")
	}
	for index := 0; index < BoundaryLimit; index++ {
		recorder.Boundary(Boundary{Direction: "tx", Stage: "ack_sent", Result: "ok"})
	}
	if recorder.MessageAttempt(query).AttemptKnown {
		test.Fatal("invented attempt after eviction")
	}
}
