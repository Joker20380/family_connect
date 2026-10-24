package desktopmesh

import (
	"context"
	"time"
)

const MaxHealthSampleGap = 45 * time.Second

type HealthSample struct {
	Session  string
	Received uint64
	Sent     uint64
	At       time.Duration
	Ready    bool
}

type HealthDecision struct {
	Progress bool
	Recover  bool
	Failures int
}

type HealthPolicy struct {
	previous *HealthSample
	failures int
}

func validSample(sample *HealthSample) bool {
	if sample == nil || !sample.Ready || len(sample.Session) != 64 || sample.At < 0 {
		return false
	}
	for _, character := range sample.Session {
		if !(character >= '0' && character <= '9' || character >= 'a' && character <= 'f') {
			return false
		}
	}
	return true
}

func cloneSample(sample *HealthSample) *HealthSample {
	if !validSample(sample) {
		return nil
	}
	copy := *sample
	return &copy
}

func (policy *HealthPolicy) Begin(sample *HealthSample) {
	if policy.previous == nil {
		policy.previous = cloneSample(sample)
	}
}

func (policy *HealthPolicy) Observe(probe bool, current *HealthSample) HealthDecision {
	previous := policy.previous
	progress := validSample(current) && previous != nil && current.Session == previous.Session &&
		current.At > previous.At && current.At-previous.At <= MaxHealthSampleGap &&
		current.Received > previous.Received && current.Sent > previous.Sent
	policy.previous = cloneSample(current)
	if probe || progress {
		policy.failures = 0
	} else {
		policy.failures = min(3, policy.failures+1)
	}
	return HealthDecision{Progress: progress, Recover: policy.failures >= 3, Failures: policy.failures}
}

func ReadinessStop(cancelled bool, now, deadline time.Time) error {
	if cancelled {
		return context.Canceled
	}
	if !now.Before(deadline) {
		return context.DeadlineExceeded
	}
	return nil
}
