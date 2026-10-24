package desktopmesh

import (
	"bytes"
	"encoding/json"
	"strings"
	"testing"
)

func TestExport106SmallRecordsAreByteIdentical(test *testing.T) {
	input := []byte("{\n\"support_id\":\"FC-TEST-TEST\",\"counter\":18446744073709551615}\n")
	result, err := BoundedExport(input)
	if err != nil || !bytes.Equal(input, result) {
		test.Fatal("small snapshot changed", err)
	}
	result[0] = '['
	if input[0] != '{' {
		test.Fatal("snapshot aliases live caller memory")
	}
}

func TestExport106KeepsBoundariesFirstCauseAndCounters(test *testing.T) {
	trace := []any{"FIRST"}
	for index := 0; index < 100; index++ {
		trace = append(trace, strings.Repeat("д", 1400))
	}
	trace = append(trace, "LAST")
	input, err := json.Marshal(map[string]any{"events": []string{"START", "END"}, "restricted_history": []any{
		map[string]any{"first_reason": "IO_CLOSED", "received_bytes": uint64(18446744073709551615), "lifecycle": map[string]any{"trace": trace}},
	}, "restricted_session": map[string]any{"terminal_reason": "NONE"}})
	if err != nil || len(input) <= ExportLimit {
		test.Fatal("invalid overflow fixture")
	}
	original := bytes.Clone(input)
	result, err := BoundedExport(input)
	if err != nil || len(result) > ExportLimit || !bytes.Equal(input, original) {
		test.Fatal("export overflow/non-mutation", err)
	}
	for _, retained := range []string{"FIRST", "LAST", "IO_CLOSED", "18446744073709551615", "omitted_detail_items", "restricted_history[0].lifecycle.trace"} {
		if !bytes.Contains(result, []byte(retained)) {
			test.Fatal("lost required evidence", retained)
		}
	}
	var exported map[string]any
	if json.Unmarshal(result, &exported) != nil {
		test.Fatal("truncated JSON")
	}
	budget := exported["record_budget"].(map[string]any)
	removed := int(budget["omitted_detail_items"].(map[string]any)["restricted_history[0].lifecycle.trace"].(float64))
	remaining := exported["restricted_history"].([]any)[0].(map[string]any)["lifecycle"].(map[string]any)["trace"].([]any)
	if len(remaining)+removed != len(trace) || removed < 1 {
		test.Fatal("omission accounting mismatch")
	}
}

func TestExport106NeverReturnsPartialOrInventedSummary(test *testing.T) {
	oversize, _ := json.Marshal(map[string]any{"required_summary": strings.Repeat("a", ExportLimit)})
	for _, input := range [][]byte{oversize, []byte("{} {}"), []byte("null"), []byte("[1]"), bytes.Repeat([]byte("a"), ExportInputLimit+1)} {
		if result, err := BoundedExport(input); err == nil || result != nil {
			test.Fatal("unrepresentable snapshot falsely exported")
		}
	}
}
