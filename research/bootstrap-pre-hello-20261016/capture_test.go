package main

import (
	"context"
	"encoding/json"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"testing"
	"time"

	"fixture.invalid/gateway/roombroker"
)

func TestCorrelationCaptureLifecycle(test *testing.T) {
	for _, mode := range []string{"disabled", "normal", "output_failure", "expired", "limited"} {
		test.Run(mode, func(test *testing.T) {
			broker, err := roombroker.New(ownershipProvider{}, roombroker.TelemostGateway{}, roombroker.DefaultLimits(), nil)
			if err != nil {
				test.Fatal(err)
			}
			defer broker.Close()
			path := filepath.Join(test.TempDir(), "capture.jsonl")
			stop := func() {}
			if mode == "disabled" {
				stop, err = startOwnershipEvidence(broker, "")
			} else if mode == "output_failure" {
				if err = os.Mkdir(path, 0700); err != nil {
					test.Fatal(err)
				}
				_, err = startOwnershipEvidence(broker, path)
				if err == nil {
					test.Fatal("output failure hidden")
				}
				err = nil
			} else if mode == "expired" {
				until := time.Now().Add(5 * time.Millisecond)
				err = broker.CaptureOwnership(4, until)
				time.Sleep(time.Until(until) + time.Millisecond)
			} else if mode == "limited" {
				err = broker.CaptureOwnership(1, time.Now().Add(time.Minute))
			} else {
				stop, err = startOwnershipEvidence(broker, path)
			}
			if err != nil {
				test.Fatal(err)
			}
			broker.ExchangeEvent(context.Background(), "authenticated", "ok")
			broker.ExchangeEvent(context.Background(), "hello_sent", "ok")
			stop()
			snapshot := broker.OwnershipSnapshot()
			identity := roombroker.Identity{Family: strings.Repeat("a", 32), Device: strings.Repeat("b", 32)}
			if _, err := broker.Challenge(context.Background(), func(context.Context) (roombroker.Identity, error) { return identity, nil }); err != nil {
				test.Fatal("capture changed admission", err)
			}
			if mode == "limited" && !snapshot.Limited {
				test.Fatal("lost limit")
			}
			if mode == "disabled" || mode == "expired" || mode == "output_failure" {
				if len(snapshot.Events) != 0 {
					test.Fatal("capture unexpectedly present")
				}
			}
			if mode == "normal" {
				file, err := os.Open(path)
				if err != nil {
					test.Fatal(err)
				}
				defer file.Close()
				decoder := json.NewDecoder(file)
				var header, event, footer map[string]any
				if decoder.Decode(&header) != nil || decoder.Decode(&event) != nil || decoder.Decode(&event) != nil || decoder.Decode(&footer) != nil {
					test.Fatal("incomplete normal capture")
				}
				if header["enabled"] != true || header["event_limit"] != float64(512) || footer["stopped"] != true || footer["written"] != float64(2) {
					test.Fatal("capture readiness/footer")
				}
			}
		})
	}
}

func TestCorrelationCaptureWriteFailure(test *testing.T) {
	path := os.Getenv("CORRELATION_OUTPUT_FAILURE_CHILD")
	if path == "" {
		path = filepath.Join(test.TempDir(), "capture.jsonl")
		command := exec.Command(os.Args[0], "-test.run=^TestCorrelationCaptureWriteFailure$")
		command.Env = append(os.Environ(), "CORRELATION_OUTPUT_FAILURE_CHILD="+path)
		if output, err := command.CombinedOutput(); err != nil {
			test.Fatalf("child failed: %v %s", err, output)
		}
		raw, err := os.ReadFile(path)
		if err != nil {
			test.Fatal(err)
		}
		if strings.Contains(string(raw), "\"stopped\"") {
			test.Fatal("false complete output")
		}
		var header map[string]any
		if json.Unmarshal(raw, &header) != nil || header["enabled"] != true {
			test.Fatal("missing original header")
		}
		return
	}
	broker, err := roombroker.New(ownershipProvider{}, roombroker.TelemostGateway{}, roombroker.DefaultLimits(), nil)
	if err != nil {
		test.Fatal(err)
	}
	defer broker.Close()
	stop, err := startOwnershipEvidence(broker, path)
	if err != nil {
		test.Fatal(err)
	}
	info, err := os.Stat(path)
	if err != nil {
		test.Fatal(err)
	}
	signal.Ignore(syscall.SIGXFSZ)
	if err := syscall.Setrlimit(syscall.RLIMIT_FSIZE, &syscall.Rlimit{Cur: uint64(info.Size()), Max: uint64(info.Size())}); err != nil {
		test.Fatal(err)
	}
	broker.ExchangeEvent(context.Background(), "authenticated", "ok")
	stop()
	if len(broker.OwnershipSnapshot().Events) != 1 {
		test.Fatal("write failure changed in-memory capture")
	}
	identity := roombroker.Identity{Family: strings.Repeat("a", 32), Device: strings.Repeat("b", 32)}
	if _, err := broker.Challenge(context.Background(), func(context.Context) (roombroker.Identity, error) { return identity, nil }); err != nil {
		test.Fatal("write failure changed admission", err)
	}
}
