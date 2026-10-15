package main

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/telemost"
)

type signalingMatrixEndpoint struct {
	matrixEndpoint
	read telemost.SignalingReadFailure
}

func (endpoint *signalingMatrixEndpoint) SeedSignalingReadFailure() telemost.SignalingReadFailure {
	return endpoint.read
}

func TestSignalReadReceiptBridge(test *testing.T) {
	directory := os.Getenv("FC_SIGNAL_MATRIX_DIR")
	if directory == "" {
		test.Skip("local real WebSocket matrix not supplied")
	}
	files, err := filepath.Glob(filepath.Join(directory, "*.json"))
	if err != nil || len(files) != 16 {
		test.Fatal("matrix incomplete")
	}
	for _, path := range files {
		raw, err := os.ReadFile(path)
		if err != nil {
			test.Fatal(err)
		}
		var fixture struct {
			Name     string                        `json:"case"`
			LowLevel telemost.SignalingReadFailure `json:"low_level"`
			Close    string                        `json:"first_close"`
		}
		if json.Unmarshal(raw, &fixture) != nil {
			test.Fatal("bad matrix")
		}
		if fixture.Name == "normal_json" {
			continue
		}
		test.Run(fixture.Name, func(test *testing.T) {
			observer := fixtureObserver(test)
			endpoint := &signalingMatrixEndpoint{matrixEndpoint: matrixEndpoint{cause: errors.New("SECRET discarded read"), source: fixture.Close}, read: fixture.LowLevel}
			manager := &bootstrap.SeedManager{RotateAfter: 3 * time.Hour, Observe: observer.failure}
			err := manager.Run(context.Background(), matrixProvider{}, func(context.Context, context.Context, roombroker.Room) (familysession.PacketEndpoint, error) {
				return endpoint, nil
			}, strings.Repeat("a", 32), strings.Repeat("b", 32), 4*time.Hour, func(context.Context, familysession.PacketEndpoint) { test.Error("unexpected peer") })
			if err != roombroker.Code("seed_closed") || endpoint.closed.Load() == 0 {
				test.Fatal("behavior changed")
			}
			observer.failure(bootstrap.SeedFailure{Stage: "RUN", Cause: context.Canceled, CloseSource: "SIGNAL_READ", SignalingRead: telemost.SignalingReadFailure{Kind: "EOF"}})
			observer.cleanup()
			observer.finish(err, "", false)
			record := readFatal(test, observer)
			if record.Stage != "SEED_READ" || record.Cause != fixture.Close || !record.Fatal {
				test.Fatal("wrong exit contract")
			}
			if fixture.Close == "SIGNAL_READ" && (record.SignalingRead == nil || *record.SignalingRead != fixture.LowLevel) {
				test.Fatal("lost low-level cause")
			}
			if fixture.Close != "SIGNAL_READ" && record.SignalingRead != nil {
				test.Fatal("unrelated cause attached")
			}
			encoded, _ := json.Marshal(record)
			if strings.Contains(string(encoded), "SECRET") {
				test.Fatal("raw error leaked")
			}
			test.Log("SIGNAL_FATAL " + string(encoded))
		})
	}
}

func TestSignalReadReceiptSanitizesExternalValues(test *testing.T) {
	observer := fixtureObserver(test)
	observer.failure(bootstrap.SeedFailure{Stage: "SEED_READ", Cause: errors.New("SECRET"), CloseSource: "SIGNAL_READ", SignalingRead: telemost.SignalingReadFailure{Kind: "SECRET", ContextState: "SECRET", CloseCode: 9000}})
	observer.finish(errors.New("SECRET cleanup"), "", false)
	record := readFatal(test, observer)
	if record.SignalingRead == nil || record.SignalingRead.Kind != "UNKNOWN" || record.SignalingRead.CloseCode != 0 {
		test.Fatal("unsafe nested receipt")
	}
	encoded, _ := json.Marshal(record)
	if strings.Contains(string(encoded), "SECRET") {
		test.Fatal("leak")
	}
}
