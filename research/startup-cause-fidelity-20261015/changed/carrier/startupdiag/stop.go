package startupdiag

import (
	"context"
	"time"
)

func Stop(ctx context.Context, source string) {
	switch source {
	case "STARTUP_BUDGET", "CONNECT_CANCEL", "CLEANUP":
	default:
		return
	}
	if record := get(ctx); record != nil {
		record.mu.Lock()
		defer record.mu.Unlock()
		if record.result.LocalStop == nil {
			record.result.LocalStop = &LocalStop{Source: source, ElapsedMS: time.Since(record.started).Milliseconds()}
		}
	}
}

func StartBudget(ctx context.Context, duration time.Duration, cancel context.CancelFunc) func() bool {
	timer := time.AfterFunc(duration, func() {
		Stop(ctx, "STARTUP_BUDGET")
		cancel()
	})
	return timer.Stop
}
