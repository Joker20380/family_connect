package main

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/Joker20380/family_connect/carrier/roombroker"
)

type ownershipProvider struct{}

func (ownershipProvider) CreateRoom(context.Context) (roombroker.Room, error) {
	return roombroker.Room{}, roombroker.Code("unused")
}

func TestOwnershipFileLoadedAndBounded(test *testing.T) {
	broker, err := roombroker.New(ownershipProvider{}, roombroker.TelemostGateway{}, roombroker.DefaultLimits(), nil)
	if err != nil {
		test.Fatal(err)
	}
	defer broker.Close()
	path := filepath.Join(test.TempDir(), "ownership.jsonl")
	stop, err := startOwnershipEvidence(broker, path)
	if err != nil {
		test.Fatal(err)
	}
	ctx := roombroker.WithExchange(context.Background(), strings.Repeat("a", 64))
	broker.ExchangeEvent(ctx, "authenticated", "ok")
	stop()
	stop()
	info, _ := os.Stat(path)
	if info.Mode().Perm() != 0600 {
		test.Fatal("capture permissions")
	}
	file, _ := os.Open(path)
	defer file.Close()
	decoder := json.NewDecoder(file)
	var header, event, footer map[string]any
	if decoder.Decode(&header) != nil || decoder.Decode(&event) != nil || decoder.Decode(&footer) != nil {
		test.Fatal("capture missing")
	}
	if header["pid"] != float64(os.Getpid()) || header["schema"] != "admission-ownership-v1" || event["action"] != "authenticated" || footer["written"] != float64(1) || footer["stopped"] != true {
		test.Fatal("loaded marker/event/final flush missing")
	}
	if _, err := startOwnershipEvidence(broker, path); err == nil {
		test.Fatal("old capture overwritten")
	}
}
