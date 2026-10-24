package desktopauto

import (
	"encoding/json"
	"fmt"
	"os"
	"reflect"
	"strings"
	"testing"
	"time"
)

func TestAcceptedReferenceTrace(test *testing.T) {
	var actual []string
	record := func(format string, values ...any) {
		line := fmt.Sprintf(format, values...)
		actual = append(actual, line)
		test.Log(line)
	}
	for _, name := range []string{"normal", "normal-fallback", "mesh-fallback", "auth", "configuration", "internal",
		"offline", "mesh-only", "bootstrap-permanent", "bootstrap-temporary", "deadlines", "cancel-open", "cancel-wait",
		"restoration", "stable", "cleanup", "configure-denied"} {
		host := newFixture(test)
		if name == "normal-fallback" || name == "mesh-fallback" || name == "cleanup" {
			host.failures[AWG] = Rejected{Category: Network}
		}
		if name == "mesh-fallback" {
			host.failures[TCP] = Rejected{Category: Network}
		}
		for label, reason := range map[string]Failure{"auth": Auth, "configuration": Configuration, "internal": Internal} {
			if name == label {
				host.failures[AWG] = Rejected{Category: reason}
			}
		}
		if name == "configure-denied" {
			host.configureFailure = Rejected{Category: Auth}
		}
		if name == "mesh-only" || strings.HasPrefix(name, "bootstrap-") || name == "cancel-wait" {
			host.configured = nil
		}
		if strings.HasPrefix(name, "bootstrap-") {
			host.failures[Restricted] = Rejected{Category: BootstrapUnavailable, TemporaryBootstrap: name == "bootstrap-temporary"}
		}
		if name == "cancel-wait" {
			host.failures[Restricted] = Rejected{Category: Network}
		}
		host.offline = name == "offline"
		host.openUntilDeadline = name == "deadlines"
		if name == "cancel-open" {
			host.cancelCandidate = AWG
		}
		host.closeFailureWhenActive = name == "cleanup"
		host.connect(test)
		if name == "bootstrap-temporary" {
			for _, delay := range []time.Duration{30 * time.Second, 60 * time.Second, 300 * time.Second} {
				host.advance(delay)
				_ = host.controller.Retry(1)
			}
		}
		if name == "cancel-wait" {
			_ = host.controller.Interrupt(1, Cancelled)
			host.advance(MaxRecoveryBackoff)
			_ = host.controller.Retry(1)
		}
		if name == "restoration" {
			host.failures[AWG] = Rejected{Category: Network}
			_ = host.controller.Lost(1, Network)
			_ = host.controller.Lost(1, Network)
			host.advance(RecoveryBackoff)
			_ = host.controller.Retry(1)
		}
		if name == "stable" {
			_ = host.controller.Lost(1, Network)
			_ = host.controller.Healthy(1, true)
			host.advance(StableTraffic)
			_ = host.controller.Healthy(1, true)
			_ = host.controller.Lost(1, Network)
		}
		snapshot := host.controller.Snapshot()
		for _, event := range snapshot.Events {
			record("AUTO_EVENT|%s|%s|%s|%s|%s|%d", name, event.Name, event.Candidate, event.Category, event.State, event.ElapsedMS)
		}
		join := func(values []Candidate) string {
			result := make([]string, len(values))
			for index, value := range values {
				result[index] = string(value)
			}
			return strings.Join(result, ",")
		}
		record("AUTO_STATE|%s|%s|%s|%s|%s|%d|%t|%d", name, snapshot.State, snapshot.Selected,
			join(host.attempts), join(host.remembered), host.releases.Load(), host.guard.Load(), host.Now().Milliseconds())
		if host.peak > 1 {
			test.Fatal("overlapping candidate")
		}
	}
	raw, failure := os.ReadFile("testdata/android106-traces.json")
	if failure != nil {
		test.Fatal(failure)
	}
	var expected []string
	if failure := json.Unmarshal(raw, &expected); failure != nil {
		test.Fatal(failure)
	}
	if !reflect.DeepEqual(actual, expected) {
		test.Fatal("trace differs from the accepted Java reference; run scripts/check_desktop_auto_reference.py")
	}
}
