package sessiondiag

import (
	"context"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func Sample(ctx context.Context, trace *sessiontrace.Recorder, counters func() (uint64, uint64), delivery ...func() *sessiontrace.Delivery) func() {
	if trace == nil {
		return func() {}
	}
	stop, done := make(chan struct{}), make(chan struct{})
	var once sync.Once
	go func() {
		defer close(done)
		emit := func(state string) {
			tx, rx := counters()
			event := sessiontrace.Event{Stage: "CARRIER_ACTIVITY", State: state, Reason: "NONE", TX: tx, RX: rx}
			if len(delivery) > 0 && delivery[0] != nil {
				event.Delivery = delivery[0]()
			}
			trace.Record(event)
		}
		defer emit("COMPLETED")
		ticker := time.NewTicker(2 * time.Second)
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-stop:
				return
			case <-ticker.C:
				emit("ESTABLISHED")
			}
		}
	}()
	return func() { once.Do(func() { close(stop) }); <-done }
}
