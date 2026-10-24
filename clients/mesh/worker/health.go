package worker

import (
	"context"
	"io"
	"time"

	"github.com/Joker20380/family_connect/carrier/desktopmesh"
)

type healthReport struct {
	State             string `json:"state"`
	Probes            uint64 `json:"probes"`
	ProbeOK           bool   `json:"probe_ok"`
	TrafficProgress   bool   `json:"traffic_progress"`
	ProgressOverrides uint64 `json:"progress_overrides"`
	Failures          int    `json:"failures"`
	LastElapsedMS     int64  `json:"last_elapsed_ms"`
	ProbeDurationMS   int64  `json:"probe_duration_ms"`
}

func (server *Server) observeHealth(core connection, policy *desktopmesh.HealthPolicy, started time.Time) error {
	if server.ctx.Err() != nil {
		return context.Canceled
	}
	if core.State() != "CONNECTED" {
		return io.EOF
	}
	policy.Begin(core.HealthSample(time.Since(started)))
	before := time.Now()
	good := server.platform.Probe(server.ctx)
	if server.ctx.Err() != nil {
		return context.Canceled
	}
	if core.State() != "CONNECTED" {
		return io.EOF
	}
	decision := policy.Observe(good, core.HealthSample(time.Since(started)))
	server.mu.Lock()
	server.health.Probes++
	server.health.ProbeOK, server.health.TrafficProgress, server.health.Failures = good, decision.Progress, decision.Failures
	server.health.LastElapsedMS, server.health.ProbeDurationMS = time.Since(started).Milliseconds(), time.Since(before).Milliseconds()
	server.health.State = "unavailable"
	if good || decision.Progress {
		server.health.State = "ok"
	}
	if !good && decision.Progress {
		server.health.ProgressOverrides++
	}
	server.mu.Unlock()
	if decision.Recover {
		return errHealth
	}
	return nil
}
