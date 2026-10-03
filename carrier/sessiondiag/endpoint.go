package sessiondiag

import (
	"context"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func Sample(ctx context.Context, trace *sessiontrace.Recorder, counters func() (uint64, uint64)) func() {
	if trace == nil {
		return func() {}
	}
	stop, done := make(chan struct{}), make(chan struct{})
	var once sync.Once
	go func() {
		defer close(done)
		ticker := time.NewTicker(2 * time.Second)
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-stop:
				return
			case <-ticker.C:
				tx, rx := counters()
				trace.Record(sessiontrace.Event{Stage: "CARRIER_ACTIVITY", State: "ESTABLISHED", Reason: "NONE", TX: tx, RX: rx})
			}
		}
	}()
	return func() { once.Do(func() { close(stop) }); <-done }
}
