package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func TestStartupEvidenceFirstFailurePrivacyAndStop(test *testing.T) {
	directory := test.TempDir()
	_, observe, stop, err := startPeerEvidence(directory, time.Millisecond, time.Second)
	if err != nil {
		test.Fatal(err)
	}
	observe("bootstrap_family_open", "", "")
	observe("bootstrap_exchange_rejected", "family_open", "context_deadline")
	for index := 0; index < 10000; index++ {
		observe("bootstrap_exchange_rejected", "private stage", "secret token")
	}
	stop()
	data, err := os.ReadFile(filepath.Join(directory, "startup.first.json"))
	if err != nil {
		test.Fatal(err)
	}
	var value struct {
		First  startupEvidence   `json:"first_failure"`
		Events []startupEvidence `json:"events"`
	}
	if json.Unmarshal(data, &value) != nil || value.First.Stage != "family_open" || value.First.Reason != "context_deadline" || len(value.Events) > 16 || len(data) > 16384 {
		test.Fatal("first startup failure not bounded/preserved")
	}
	if bytes.Contains(data, []byte("private")) || bytes.Contains(data, []byte("secret")) {
		test.Fatal("private error leaked")
	}
	observe("bootstrap_exchange_rejected", "authorize", "unauthorized")
	stop()
	after, _ := os.ReadFile(filepath.Join(directory, "startup.first.json"))
	if !bytes.Equal(data, after) {
		test.Fatal("stop/recovery replaced first startup failure")
	}
}

func TestPeerEvidenceFirstFailureAndBoundedSelection(test *testing.T) {
	directory := test.TempDir()
	tag := strings.Repeat("a", 64)
	other := strings.Repeat("b", 64)
	if err := os.WriteFile(filepath.Join(directory, "allow-tags"), []byte(tag), 0600); err != nil {
		test.Fatal(err)
	}
	sink, _, stop, err := startPeerEvidence(directory, time.Millisecond, 5*time.Second)
	if err != nil {
		test.Fatal(err)
	}
	defer stop()
	path := filepath.Join(directory, tag+".latest.json")
	until := time.Now().Add(time.Second)
	for {
		sink(sessiontrace.Event{SessionTag: tag, Stage: "CARRIER_ACTIVITY", State: "ESTABLISHED", Reason: "NONE"})
		if _, err := os.Stat(path); err == nil {
			break
		}
		if time.Now().After(until) {
			test.Fatal("collector not ready")
		}
		time.Sleep(time.Millisecond)
	}
	sink(sessiontrace.Event{SessionTag: tag, Stage: "CARRIER", State: "FAILED", Reason: "RELIABLE_RETRY_EXHAUSTED", Sequence: 42})
	for index := 0; index < 10000; index++ {
		sink(sessiontrace.Event{SessionTag: tag, Stage: "CARRIER", State: "FAILED", Reason: "FAMILY_TLS_ERROR", Sequence: 43})
		sink(sessiontrace.Event{SessionTag: other, Stage: "CARRIER", State: "FAILED", Reason: "CARRIER_ERROR", Sequence: 99})
	}
	stop()
	first, err := os.ReadFile(filepath.Join(directory, tag+".first.json"))
	if err != nil {
		test.Fatal(err)
	}
	var snapshot peerEvidenceSnapshot
	if err := json.Unmarshal(first, &snapshot); err != nil {
		test.Fatal(err)
	}
	if snapshot.FirstFailure == nil || snapshot.FirstFailure.Sequence != 42 || len(snapshot.Events) > 32 {
		test.Fatal("first failure overwritten or unbounded")
	}
	if _, err := os.Stat(filepath.Join(directory, other+".first.json")); !os.IsNotExist(err) {
		test.Fatal("unselected session exported")
	}
	sink(sessiontrace.Event{SessionTag: tag, Stage: "CARRIER", State: "FAILED", Sequence: 55})
	again, _ := os.ReadFile(filepath.Join(directory, tag+".first.json"))
	if string(again) != string(first) {
		test.Fatal("late callback replaced first snapshot")
	}
}

func TestPeerEvidenceDisabledAndUnsafePath(test *testing.T) {
	sink, _, stop, err := newPeerEvidence("")
	if err != nil {
		test.Fatal(err)
	}
	sink(sessiontrace.Event{})
	stop()
	if _, _, _, err := newPeerEvidence("relative"); err == nil {
		test.Fatal("relative accepted")
	}
	directory := test.TempDir()
	if err := os.Chmod(directory, 0755); err != nil {
		test.Fatal(err)
	}
	if _, _, _, err := newPeerEvidence(directory); err == nil {
		test.Fatal("public directory accepted")
	}
}

func TestPeerEvidenceLifetimeAndResources(test *testing.T) {
	directory := test.TempDir()
	sink, _, stop, err := startPeerEvidence(directory, time.Millisecond, 5*time.Millisecond)
	if err != nil {
		test.Fatal(err)
	}
	time.Sleep(15 * time.Millisecond)
	stop()
	stop()
	sink(sessiontrace.Event{})
	entries, err := os.ReadDir(directory)
	if err != nil || len(entries) != 1 || entries[0].Name() != "status.json" {
		test.Fatal("inactive unselected resources", err)
	}
}

func TestPeerEvidenceStopRequest(test *testing.T) {
	directory := test.TempDir()
	_, _, stop, err := startPeerEvidence(directory, time.Millisecond, time.Minute)
	if err != nil {
		test.Fatal(err)
	}
	defer stop()
	if err := os.WriteFile(filepath.Join(directory, "stop-request"), nil, 0600); err != nil {
		test.Fatal(err)
	}
	until := time.Now().Add(time.Second)
	for {
		data, err := os.ReadFile(filepath.Join(directory, "status.json"))
		var status struct {
			Stopped bool `json:"stopped"`
		}
		if err == nil && json.Unmarshal(data, &status) == nil && status.Stopped {
			return
		}
		if time.Now().After(until) {
			test.Fatal("stop request did not terminate worker")
		}
		time.Sleep(time.Millisecond)
	}
}
