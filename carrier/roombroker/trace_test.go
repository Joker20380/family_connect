package roombroker

import (
	"context"
	"encoding/hex"
	"encoding/json"
	"strings"
	"sync"
	"testing"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func TestProductionSetupLifecycleCorrelation(test *testing.T) {
	var mutex sync.Mutex
	var events []sessiontrace.Event
	broker, err := New(providerFunc(fresh), gatewayFunc(func(lifetime, ready context.Context, room Room, identifier string, identity Identity) (Gateway, error) {
		tag, status := sessiontrace.Tag(identifier)
		if status != "VALID" || sessiontrace.From(lifetime).Snapshot().SessionTag != tag {
			test.Error("gateway context lost correlation")
		}
		return &fakeGateway{run: waiting}, nil
	}), shortLimits(), func(State, Code) {}, func(event sessiontrace.Event) bool {
		mutex.Lock()
		defer mutex.Unlock()
		events = append(events, event)
		return true
	})
	if err != nil {
		test.Fatal(err)
	}
	defer broker.Close()
	identifier, err := broker.Challenge(context.Background(), allow)
	if err != nil {
		test.Fatal(err)
	}
	raw, err := hex.DecodeString(identifier)
	if err != nil || len(raw) != 32 {
		test.Fatal("authoritative producer format changed")
	}
	tag, _ := sessiontrace.Tag(identifier)
	if _, err := broker.Create(context.Background(), identifier, allow); err != nil {
		test.Fatal(err)
	}
	if err := broker.Claim(context.Background(), identifier, allow); err != nil {
		test.Fatal(err)
	}
	if err := broker.Cancel(context.Background(), identifier, allow); err != nil {
		test.Fatal(err)
	}
	waitEmpty(test, broker)
	mutex.Lock()
	defer mutex.Unlock()
	stages := map[string]bool{}
	for index, event := range events {
		if event.SessionTag != tag || event.Sequence != uint64(index+1) {
			test.Fatal("ambiguous lifecycle")
		}
		stages[event.Stage+"/"+event.State] = true
	}
	for _, expected := range []string{"AUTHORIZED/ESTABLISHED", "ROOM_CREATION/STARTED", "ROOM_CREATION/ESTABLISHED", "GATEWAY_JOIN/STARTED", "GATEWAY_JOIN/ESTABLISHED", "DESCRIPTOR/ISSUED", "LOCAL_CLOSE/STARTED", "CLEANUP/COMPLETED"} {
		if !stages[expected] {
			test.Fatalf("missing stage %s", expected)
		}
	}
	encoded, _ := json.Marshal(events)
	for _, secret := range []string{identifier, "telemost.yandex", testIdentity.Device, testIdentity.Family} {
		if strings.Contains(string(encoded), secret) {
			test.Fatal("raw identifier or room leaked")
		}
	}
}
