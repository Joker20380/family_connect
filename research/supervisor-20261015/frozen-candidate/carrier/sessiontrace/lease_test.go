package sessiontrace

import (
	"strings"
	"testing"
)

func TestLeaseReceiptProjection(test *testing.T) {
	var published Event
	trace := New(strings.Repeat("a", 64), func(event Event) bool { published = event; return true })
	for _, action := range []string{"offer", "request", "accepted", "applied", "confirmed"} {
		trace.Record(Event{Stage: "GATEWAY_SESSION", State: "ESTABLISHED", Reason: "NONE", LeaseAction: action, LeaseSequence: 2, LeaseDeadlineMS: 1791705374000})
		if published.LeaseAction != action || published.LeaseSequence != 2 || published.LeaseDeadlineMS != 1791705374000 {
			test.Fatal("lease receipt lost")
		}
	}
	trace.Record(Event{Stage: "GATEWAY_SESSION", State: "ESTABLISHED", Reason: "NONE", LeaseAction: "untrusted", LeaseSequence: 2})
	if published.LeaseAction != "" || published.LeaseSequence != 0 {
		test.Fatal("unbounded lease metadata")
	}
}
