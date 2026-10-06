//go:build fc_owner_diagnostic && linux

package sessiontrace

import (
	"context"
	"encoding/json"
	"net"
	"os"
	"strings"
	"testing"
	"time"
)

func controlExchange(test *testing.T, path string, request correlationRequest) CorrelationReceipt {
	test.Helper()
	connection, err := net.DialUnix("unix", nil, &net.UnixAddr{Name: path, Net: "unix"})
	if err != nil {
		test.Fatal(err)
	}
	defer connection.Close()
	if err := json.NewEncoder(connection).Encode(request); err != nil {
		test.Fatal(err)
	}
	connection.CloseWrite()
	var receipt CorrelationReceipt
	if err := json.NewDecoder(connection).Decode(&receipt); err != nil {
		test.Fatal(err)
	}
	return receipt
}

func TestCorrelationAuthenticatedRuntime(test *testing.T) {
	directory, err := os.MkdirTemp("/tmp", "fc-corr-")
	if err != nil {
		test.Fatal(err)
	}
	defer os.RemoveAll(directory)
	recorder := New(strings.Repeat("a", 64), nil)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	path, err := recorder.serveCorrelation(ctx, directory, "gateway")
	if err != nil {
		test.Fatal(err)
	}
	key := CorrelationKey{Session: recorder.Snapshot().SessionTag, Direction: "client_to_gateway", Sequence: 19, Attempt: 1}
	armed := controlExchange(test, path, correlationRequest{Operation: "prearm", Key: key})
	if armed.State != "ARMED" || !validGeneration(armed.Key.Generation) {
		test.Fatal("runtime not armed", armed)
	}
	correlationAttempt(recorder, 10, 2)
	descriptor := correlationDescriptor(armed.Key, 11, 2)
	bound := controlExchange(test, path, correlationRequest{Operation: "bind", Key: armed.Key, Descriptor: &descriptor})
	if bound.State != "BOUND" {
		test.Fatal("late original completed watch", bound)
	}
	correlationAttempt(recorder, 11, 2)
	complete := controlExchange(test, path, correlationRequest{Operation: "status", Key: armed.Key})
	if complete.State != "COMPLETE" {
		test.Fatal(complete)
	}
	replay := controlExchange(test, path, correlationRequest{Operation: "bind", Key: armed.Key, Descriptor: &descriptor})
	if replay.State != "" {
		test.Fatal("replay accepted")
	}
	cleaned := controlExchange(test, path, correlationRequest{Operation: "cleanup", Key: armed.Key})
	if cleaned.State != "CLEANED" || len(cleaned.Candidates) != 0 || cleaned.Descriptor != nil {
		test.Fatal("cleanup failed")
	}
	if err := os.Chmod(directory, 0755); err != nil {
		test.Fatal(err)
	}
	if _, err := recorder.serveCorrelation(ctx, directory, "gateway"); err == nil {
		test.Fatal("insecure directory accepted")
	}
}

func TestCorrelationSessionContextCleanupWithoutSocket(test *testing.T) {
	test.Setenv("FC_DIAGNOSTIC_CONTROL_DIR", "")
	recorder, key := correlationFixture(test)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	StartDiagnosticControl(ctx, recorder, "client")
	request, finish := context.WithCancel(ctx)
	finish()
	<-request.Done()
	receipt, _ := recorder.CorrelationStatus(key, false)
	if receipt.State != "ARMED" {
		test.Fatal("request cancellation closed session control")
	}
	correlationAttempt(recorder, 10, 1)
	cancel()
	deadline := time.Now().Add(time.Second)
	for time.Now().Before(deadline) {
		receipt, _ = recorder.CorrelationStatus(key, false)
		if receipt.State == "CLOSED" && len(receipt.Candidates) == 0 {
			return
		}
		time.Sleep(time.Millisecond)
	}
	test.Fatal("session cancellation did not purge evidence")
}
