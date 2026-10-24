package worker

import (
	"context"
	"errors"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/desktopmesh"
)

type healthPlatform struct {
	fakePlatform
	probe func(context.Context) bool
}

func (platform healthPlatform) Probe(ctx context.Context) bool { return platform.probe(ctx) }

type healthConnection struct {
	fakeConnection
	sample func(time.Duration) *desktopmesh.HealthSample
}

func (connection *healthConnection) HealthSample(at time.Duration) *desktopmesh.HealthSample {
	return connection.sample(at)
}

func TestHealthRecoveryRequiresThreeFailures(test *testing.T) {
	server := New(context.Background(), healthPlatform{probe: func(context.Context) bool { return false }})
	defer server.Close()
	core := &fakeConnection{state: "CONNECTED"}
	policy := new(desktopmesh.HealthPolicy)
	for attempt := 1; attempt <= 3; attempt++ {
		err := server.observeHealth(core, policy, time.Now())
		if (attempt == 3) != errors.Is(err, errHealth) || server.health.Failures != attempt || server.health.Probes != uint64(attempt) {
			test.Fatal("health recovery threshold changed")
		}
	}
	server.platform = healthPlatform{probe: func(context.Context) bool { return true }}
	if server.observeHealth(core, policy, time.Now()) != nil || server.health.Failures != 0 || server.health.State != "ok" {
		test.Fatal("successful health did not reset failures")
	}
}

func TestAuthenticatedBidirectionalProgressOverridesFailedProbe(test *testing.T) {
	server := New(context.Background(), healthPlatform{probe: func(context.Context) bool { return false }})
	defer server.Close()
	for _, kind := range []string{"bidirectional", "one-way", "new-session", "stale", "not-ready"} {
		count := 0
		core := &healthConnection{fakeConnection: fakeConnection{state: "CONNECTED"}, sample: func(at time.Duration) *desktopmesh.HealthSample {
			count++
			sample := &desktopmesh.HealthSample{Session: strings.Repeat("a", 64), Received: uint64(count), Sent: uint64(count),
				At: time.Duration(count) * time.Second, Ready: true}
			switch kind {
			case "one-way":
				sample.Sent = 0
			case "new-session":
				if count == 2 {
					sample.Session = strings.Repeat("b", 64)
				}
			case "stale":
				sample.At *= 46
			case "not-ready":
				sample.Ready = false
			}
			return sample
		}}
		if server.observeHealth(core, new(desktopmesh.HealthPolicy), time.Now()) != nil ||
			server.health.TrafficProgress != (kind == "bidirectional") || (server.health.State == "ok") != (kind == "bidirectional") {
			test.Fatal("health102 progress gate changed", kind)
		}
	}
}

func TestHealthCancelOrSessionLossCannotBecomePositiveSample(test *testing.T) {
	for _, cancelled := range []bool{true, false} {
		server := New(context.Background(), fakePlatform{})
		core := &fakeConnection{state: "CONNECTED"}
		server.platform = healthPlatform{probe: func(context.Context) bool {
			if cancelled {
				server.cancel()
			} else {
				core.state = "FAILED"
			}
			return true
		}}
		if server.observeHealth(core, new(desktopmesh.HealthPolicy), time.Now()) == nil || server.health.Probes != 0 {
			test.Fatal("late probe became success after cancel/session loss")
		}
		server.Close()
	}
}
