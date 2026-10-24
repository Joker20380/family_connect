package desktopmesh

import (
	"context"
	"strings"
	"testing"
	"time"
)

func sample(received, sent uint64, seconds int) *HealthSample {
	return &HealthSample{Session: strings.Repeat("a", 64), Received: received, Sent: sent, At: time.Duration(seconds) * time.Second, Ready: true}
}

func TestHealth102RequiresAuthenticatedBidirectionalProgress(test *testing.T) {
	for _, scenario := range []struct {
		name     string
		next     *HealthSample
		progress bool
	}{
		{"both", sample(11, 21, 35), true},
		{"receive_only", sample(11, 20, 35), false},
		{"send_only", sample(10, 21, 35), false},
		{"stale", sample(11, 21, 46), false},
		{"counter_reset", sample(1, 2, 35), false},
		{"same_time", sample(11, 21, 0), false},
		{"missing", nil, false},
		{"other_session", &HealthSample{Session: strings.Repeat("b", 64), Received: 11, Sent: 21, At: 35 * time.Second, Ready: true}, false},
		{"not_ready", &HealthSample{Session: strings.Repeat("a", 64), Received: 11, Sent: 21, At: 35 * time.Second}, false},
	} {
		test.Run(scenario.name, func(test *testing.T) {
			var policy HealthPolicy
			policy.Begin(sample(10, 20, 0))
			if policy.Observe(false, scenario.next).Progress != scenario.progress {
				test.Fatal("health102 progress mismatch")
			}
		})
	}
}

func TestHealthFailureBoundAndProbeReset(test *testing.T) {
	var policy HealthPolicy
	for attempt := 1; attempt <= 100; attempt++ {
		decision := policy.Observe(false, nil)
		if decision.Failures != min(3, attempt) || decision.Recover != (attempt >= 3) {
			test.Fatal(decision)
		}
	}
	if decision := policy.Observe(true, nil); decision.Recover || decision.Failures != 0 {
		test.Fatal(decision)
	}
}

func TestHealthDoesNotRetainCallerOwnedSamples(test *testing.T) {
	initial := sample(10, 20, 0)
	var policy HealthPolicy
	policy.Begin(initial)
	initial.Received = 999
	if !policy.Observe(false, sample(11, 21, 35)).Progress {
		test.Fatal("caller mutation changed health history")
	}
}

func TestReadiness103CancellationPrecedesDeadline(test *testing.T) {
	now := time.Unix(100, 0)
	if ReadinessStop(true, now, now) != context.Canceled || ReadinessStop(false, now, now) != context.DeadlineExceeded || ReadinessStop(false, now, now.Add(time.Second)) != nil {
		test.Fatal("readiness103 cancellation/deadline distinction lost")
	}
}
