package sessiontrace

import (
	"strings"
	"testing"
)

func TestDeliveryRetentionAndDeepCopies(test *testing.T) {
	value := &Delivery{Flow: &Flow{SendNext: 1}, Assembly: &Assembly{Fragments: 3}, Pending: &Fragment{Total: 2}, Queued: &Fragment{Total: 2}, Written: &Fragment{Total: 2}, Received: &Fragment{Total: 2}}
	trace := New(strings.Repeat("ab", 32), func(event Event) bool {
		if event.Delivery != nil {
			event.Delivery.Flow.SendNext = 999
			event.Delivery.Pending.Total = 999
		}
		return true
	})
	trace.Record(Event{Stage: "CARRIER", State: "FAILED", Reason: "RELIABLE_RETRY_EXHAUSTED", Delivery: value})
	for index := 0; index < 20; index++ {
		trace.Record(Event{Stage: "CARRIER_ACTIVITY", State: "ESTABLISHED", Reason: "NONE", Delivery: value})
	}
	value.Flow.SendNext = 998
	snapshot := trace.Snapshot()
	count := 0
	for _, event := range snapshot.Events {
		if event.Delivery != nil {
			count++
			if event.Delivery.Flow.SendNext != 1 || event.Delivery.Pending.Total != 2 {
				test.Fatal("input/sink alias")
			}
			event.Delivery.Flow.SendNext = 997
		}
	}
	if count != DeliveryLimit || snapshot.DeliveryDropped != 13 || snapshot.FirstFailure.Delivery.Flow.SendNext != 1 {
		test.Fatal("delivery bound lost first failure", count, snapshot.DeliveryDropped)
	}
	snapshot.FirstFailure.Delivery.Assembly.Fragments = 999
	if trace.Snapshot().FirstFailure.Delivery.Assembly.Fragments != 3 || trace.Snapshot().Events[20].Delivery.Flow.SendNext != 1 {
		test.Fatal("snapshot alias")
	}
}
