package sessiontrace

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
)

func TestReceivePathBoundedIncidentExport(test *testing.T) {
	if !PerformanceEnabled { test.Skip("observation build only") }
	recorder := New(strings.Repeat("a", 64), nil)
	recorder.RecordTransport(TransportPoint{Kind:"receive", Wire:strings.Repeat("b",32), Sequence:597, Result:"new"})
	for index := 0; index < 400; index++ {
		point := ReceivePoint{Stage:"fragment_stored", Direction:"rx", Sender:752154365, Message:4260144682,
			Fragment:2, Total:3, Mask:5, Sequence:597, Known:true, Track:1, Timestamp:7466613,
			First:5987, Last:5987, Packets:1, Next:5988, Buffered:16, WaitNS:100000000}
		if index == 260 { point.Stage, point.Result = "carrier_message_completed", "capacity" }
		recorder.RecordReceive(point)
	}
	first := recorder.TransportSnapshot()
	if first.Receive.Count != 400 || first.Receive.Overwritten != 144 || len(first.Receive.Points) != 256 || len(first.Receive.Incident) != 128 || first.Receive.IncidentAt != 261 {
		test.Fatalf("incorrect coverage: %+v", first.Receive)
	}
	var workers sync.WaitGroup
	for worker := 0; worker < 4; worker++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			for index := 0; index < 100; index++ {
				recorder.RecordReceive(ReceivePoint{Stage:"rtp_reader", Direction:"rx", First:uint16(index)})
				recorder.TransportSnapshot()
			}
		}()
	}
	workers.Wait()
	if first.Receive.Points[0].Index != 145 || recorder.TransportSnapshot().Receive.Incident[0].Index != 134 { test.Fatal("snapshot aliased live ring or pinned context lost") }
	output := os.Getenv("RECEIVE_TRACE_OUTPUT")
	if output == "" { return }
	value := &TransportPerformance{Trace:first}
	raw, err := json.Marshal(map[string]any{"state":2, "packet":map[string]any{"diagnostic":map[string]any{"session_tag":recorder.PerformanceTag(), "restricted_performance_v1":value}}})
	if err != nil { test.Fatal(err) }
	if err = os.WriteFile(filepath.Join(output,"receive-native.json"), raw, 0600); err != nil { test.Fatal(err) }
	chunks, err := PerformanceExport(recorder.PerformanceTag(),value)
	if err != nil { test.Fatal(err) }
	if err = os.WriteFile(filepath.Join(output,"receive-go-chunks.jsonl"),bytes.Join(chunks,nil),0600); err != nil { test.Fatal(err) }
}

func BenchmarkReceiveObservation(bench *testing.B) {
	recorder:=New(strings.Repeat("a",64),nil)
	point:=ReceivePoint{Stage:"rtp_reader",Direction:"rx",Track:1,Timestamp:100,First:10,Last:10,Packets:1}
	bench.ReportAllocs()
	bench.ResetTimer()
	for index:=0;index<bench.N;index++{recorder.RecordReceive(point)}
}
