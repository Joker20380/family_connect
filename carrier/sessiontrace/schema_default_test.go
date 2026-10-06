//go:build !fc_owner_diagnostic

package sessiontrace

import (
	"bytes"
	"context"
	"encoding/json"
	"os"
	"reflect"
	"sort"
	"strings"
	"testing"
)

func TestPublicSchemaGolden(test *testing.T) {
	actual := map[string][]string{"BoundaryStages": strings.Split(BoundaryStages, "|")}
	for name, value := range map[string]any{"Boundary": Boundary{}, "Snapshot": Snapshot{}, "Delivery": Delivery{}, "Event": Event{}, "Flow": Flow{}, "Fragment": Fragment{}, "Assembly": Assembly{}, "Boundaries": Boundaries{}} {
		kind := reflect.TypeOf(value)
		for index := 0; index < kind.NumField(); index++ {
			actual[name] = append(actual[name], kind.Field(index).Tag.Get("json"))
		}
		sort.Strings(actual[name])
	}
	sort.Strings(actual["BoundaryStages"])
	raw, err := os.ReadFile("testdata/public-schema-beta66.json")
	if err != nil {
		test.Fatal(err)
	}
	var expected map[string][]string
	if err := json.Unmarshal(raw, &expected); err != nil {
		test.Fatal(err)
	}
	if !reflect.DeepEqual(actual, expected) {
		test.Fatalf("public schema differs from sealed beta66: got %v want %v", actual, expected)
	}
}

func TestPublicForensicsCannotEnterExport(test *testing.T) {
	var exported Event
	recorder := New(strings.Repeat("a", 64), func(event Event) bool { exported = event; return true })
	var point Boundary
	if err := json.Unmarshal([]byte(`{"direction":"rx","stage":"rtp_received","result":"ok","picture_known":true,"picture_id":123,"generation":"secret","descriptor":{},"candidates":[]}`), &point); err != nil {
		test.Fatal(err)
	}
	point.RecordPicture(true, 123)
	recorder.Boundary(point)
	before, _ := json.Marshal(recorder.Snapshot())
	for index := 0; index < 2100; index++ {
		recorder.ReceiverAccepted(ReceiveIdentity{}, 19, "ok", ReceiveState{}, ReceiveState{})
		recorder.ReceiverConsumed(19, ReceiveState{}, ReceiveState{}, StampACK(), 20, 0)
		recorder.ReceiverACKSent(StampACK(), 20, 0, true)
		point.CaptureACK(WithACKObservation(context.Background(), StampACK(), 20, 0))
		recorder.RecordConsumed(19, 20, 127)
		recorder.RecordBaseAdvanced(20, 127)
		for _, stage := range []string{"reliable_consumed", "base_advanced", "rtp_correlated"} {
			recorder.Boundary(Boundary{Direction: "rx", Stage: stage, Result: "ok"})
		}
	}
	after, _ := json.Marshal(recorder.Snapshot())
	if !bytes.Equal(before, after) {
		test.Fatal("forensic callbacks changed public ring, counters or snapshot")
	}
	var delivery Delivery
	if err := json.Unmarshal([]byte(`{"evidence_watch":{"state":"ACTIVE"},"generation":"secret","descriptor":{},"candidates":[]}`), &delivery); err != nil {
		test.Fatal(err)
	}
	recorder.Record(Event{Stage: "CARRIER_ACTIVITY", State: "ESTABLISHED", Reason: "NONE", Delivery: &delivery})
	for _, value := range []any{recorder.Snapshot(), exported, CloneDelivery(exported.Delivery), point, delivery} {
		raw, err := json.Marshal(value)
		if err != nil {
			test.Fatal(err)
		}
		for _, forbidden := range []string{"reliable_consumed", "base_advanced", "picture_known", "picture_id", "evidence_watch", "descriptor", "generation", "nonce", "candidates", "prearm", "secret", "created_ns", "sent_ns", "accepted", "media_complete"} {
			if strings.Contains(string(raw), forbidden) {
				test.Fatal("forensic metadata in public export", forbidden)
			}
		}
	}
	if exported.Delivery.Boundaries.Dropped != 0 || len(exported.Delivery.Boundaries.Events) != 1 {
		test.Fatal("public boundary retention changed")
	}
}
