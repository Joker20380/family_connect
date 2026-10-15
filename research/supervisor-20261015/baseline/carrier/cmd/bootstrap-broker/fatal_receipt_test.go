package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"strings"
	"sync"
	"syscall"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/telemost"
)

func fixtureObserver(test *testing.T) *fatalObserver {
	test.Helper()
	directory := test.TempDir()
	if err := os.Chmod(directory, 0700); err != nil {
		test.Fatal(err)
	}
	return &fatalObserver{started: time.Now(), dir: directory, value: fatalRecord{Schema: 1, Invocation: strings.Repeat("a", 32), LastStage: "RUN"}}
}

func readFatal(test *testing.T, observer *fatalObserver) fatalRecord {
	test.Helper()
	raw, err := os.ReadFile(filepath.Join(observer.dir, "application-"+observer.value.Invocation+".json"))
	if err != nil {
		test.Fatal(err)
	}
	var value fatalRecord
	if err := json.Unmarshal(raw, &value); err != nil {
		test.Fatal(err)
	}
	return value
}

func TestFatalClassification(test *testing.T) {
	for _, item := range []struct {
		name   string
		err    error
		parent error
		cause  string
		fatal  bool
	}{
		{"typed", roombroker.Code("provider_timeout"), nil, "provider_timeout", true},
		{"wrapped", fmt.Errorf("SECRET %w", roombroker.Code("seed_closed")), nil, "seed_closed", true},
		{"unknown", errors.New("SECRET token https://private/j/room"), nil, "UNKNOWN", true},
		{"deadline", context.DeadlineExceeded, nil, "DEADLINE", true},
		{"lifetime", context.DeadlineExceeded, context.DeadlineExceeded, "DEADLINE", false},
		{"cancel", context.Canceled, nil, "CANCELLED", false},
		{"parent_cancel", telemost.ErrClosed, context.Canceled, "CARRIER_CLOSED", false},
		{"provider", telemost.ErrAPI, nil, "PROVIDER_API", true},
		{"broker", roombroker.Code("seed_creation_failed"), nil, "seed_creation_failed", true},
		{"unlisted_code", roombroker.Code("SECRET"), nil, "UNKNOWN", true},
	} {
		test.Run(item.name, func(test *testing.T) {
			observer := fixtureObserver(test)
			observer.failure(bootstrap.SeedFailure{Stage: "SEED_READ", Cause: item.err, ParentError: item.parent, Generation: 2})
			observer.cleanup()
			observer.finish(item.err, "", false)
			value := readFatal(test, observer)
			if value.Cause != item.cause || value.Fatal != item.fatal || value.Stage != "SEED_READ" || value.Generation != 2 || !value.CleanupCompleted {
				test.Fatalf("%+v", value)
			}
			raw, _ := json.Marshal(value)
			if strings.Contains(string(raw), "SECRET") || strings.Contains(string(raw), "https:") {
				test.Fatal("privacy")
			}
		})
	}
}

func TestFatalNormalPanicAndWriteFailure(test *testing.T) {
	observer := fixtureObserver(test)
	observer.cleanup()
	observer.finish(nil, "", false)
	if value := readFatal(test, observer); value.Fatal || value.ExitPath != "normal_stop" {
		test.Fatal(value)
	}
	observer = fixtureObserver(test)
	observer.finish(nil, "", true)
	if value := readFatal(test, observer); !value.Fatal || value.ExitPath != "panic" || value.Cause != "PANIC" || value.CleanupCompleted {
		test.Fatal(value)
	}
	observer = fixtureObserver(test)
	observer.dir = filepath.Join(observer.dir, "absent")
	original := roombroker.Code("seed_closed")
	observer.finish(original, "", false)
	if !observer.sealed || observer.value.Cause != "seed_closed" {
		test.Fatal("write failure changed cause")
	}
}

func TestFatalFirstCauseAndStaleCallbacks(test *testing.T) {
	observer := fixtureObserver(test)
	observer.failure(bootstrap.SeedFailure{Stage: "SEED_CREATE", Cause: roombroker.Code("provider_unavailable"), Generation: 1})
	var workers sync.WaitGroup
	for index := 0; index < 30; index++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			observer.failure(bootstrap.SeedFailure{Stage: "SECRET", Cause: errors.New("SECRET")})
			observer.stage("SEED_READ")
			observer.cleanup()
		}()
	}
	workers.Wait()
	observer.finish(roombroker.Code("seed_closed"), "", false)
	before, _ := os.ReadFile(filepath.Join(observer.dir, "application-"+observer.value.Invocation+".json"))
	observer.failure(bootstrap.SeedFailure{Stage: "PROFILE", Cause: context.Canceled})
	observer.finish(nil, "SIGTERM", true)
	after, _ := os.ReadFile(filepath.Join(observer.dir, "application-"+observer.value.Invocation+".json"))
	if string(before) != string(after) || readFatal(test, observer).Cause != "provider_unavailable" {
		test.Fatal("first replaced")
	}
}

func TestFatalRetentionAndPermissions(test *testing.T) {
	observer := fixtureObserver(test)
	for index := 0; index < 36; index++ {
		value := observer.value
		value.Invocation = fmt.Sprintf("%032x", index)
		if err := writeFatalReceipt(observer.dir, value); err != nil {
			test.Fatal(err)
		}
	}
	files, _ := filepath.Glob(filepath.Join(observer.dir, "application-*.json"))
	if len(files) != 32 {
		test.Fatal(len(files))
	}
	for _, name := range files {
		info, _ := os.Stat(name)
		if info.Mode().Perm() != 0600 {
			test.Fatal(info.Mode())
		}
	}
	value := observer.value
	value.Invocation = fmt.Sprintf("%032x", 35)
	if writeFatalReceipt(observer.dir, value) == nil {
		test.Fatal("invocation overwritten")
	}
	if err := os.Chmod(observer.dir, 0755); err != nil {
		test.Fatal(err)
	}
	if writeFatalReceipt(observer.dir, observer.value) == nil {
		test.Fatal("unsafe dir accepted")
	}
}

func TestFatalSubprocess(test *testing.T) {
	mode := os.Getenv("FC_RECEIPT_FIXTURE")
	if mode != "" {
		observer := newFatalObserver()
		defer receiptPanic(observer)
		if mode == "panic" {
			panic("SECRET-PANIC")
		}
		if mode == "signal" {
			ctx, cancel := signal.NotifyContext(context.Background(), syscall.SIGTERM)
			defer cancel()
			fmt.Println("ARMED")
			<-ctx.Done()
			observer.failure(bootstrap.SeedFailure{Stage: "RUN", Cause: ctx.Err(), ParentError: ctx.Err()})
			observer.cleanup()
			observer.finish(nil, "SIGTERM", false)
			return
		}
		observer.cleanup()
		observer.finish(roombroker.Code("seed_closed"), "", false)
		os.Exit(1)
	}
	for _, item := range []struct {
		mode string
		exit int
	}{{"error", 1}, {"panic", 2}, {"signal", 0}} {
		test.Run(item.mode, func(test *testing.T) {
			directory := test.TempDir()
			if err := os.Chmod(directory, 0700); err != nil {
				test.Fatal(err)
			}
			command := exec.Command(os.Args[0], "-test.run=^TestFatalSubprocess$")
			command.Env = append(os.Environ(), "FC_RECEIPT_FIXTURE="+item.mode, "FC_FATAL_RECEIPT_DIR="+directory, "INVOCATION_ID="+strings.Repeat("b", 32))
			var output []byte
			var err error
			if item.mode == "signal" {
				pipe, failure := command.StdoutPipe()
				if failure != nil {
					test.Fatal(failure)
				}
				if err := command.Start(); err != nil {
					test.Fatal(err)
				}
				buffer := make([]byte, 6)
				if _, err := pipe.Read(buffer); err != nil || string(buffer) != "ARMED\n" {
					test.Fatal("not armed")
				}
				command.Process.Signal(syscall.SIGTERM)
				err = command.Wait()
			} else {
				output, err = command.CombinedOutput()
			}
			code := 0
			if err != nil {
				var failure *exec.ExitError
				if !errors.As(err, &failure) {
					test.Fatal(err)
				}
				code = failure.ExitCode()
			}
			if code != item.exit || strings.Contains(string(output), "SECRET") {
				test.Fatalf("exit/privacy %d", code)
			}
			files, _ := filepath.Glob(filepath.Join(directory, "application-*.json"))
			if len(files) != 1 {
				test.Fatal("missing receipt")
			}
		})
	}
}
