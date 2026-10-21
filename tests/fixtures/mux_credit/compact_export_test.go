package roombroker

import (
	"encoding/json"
	"io"
	"os"
	"strings"
	"testing"

	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

func TestCreditCompactExport(test *testing.T) {
	reader, writer, err := os.Pipe()
	if err != nil {
		test.Fatal(err)
	}
	defer reader.Close()
	previous := os.Stdout
	os.Stdout = writer
	defer func() { os.Stdout = previous }()
	value := &sessiontrace.TransportPerformance{Window: &sessiontrace.WindowPerformance{}, Mux: &sessiontrace.MuxPerformance{}, Media: &sessiontrace.MediaPerformance{}}
	recordPerformance(sessiontrace.New(strings.Repeat("1", 64), nil), value)
	writer.Close()
	encoded, err := io.ReadAll(reader)
	if err != nil {
		test.Fatal(err)
	}
	var record map[string]any
	if err := json.Unmarshal(encoded, &record); err != nil {
		test.Fatal(err)
	}
	performance := record["performance"].(map[string]any)
	if _, ok := performance["Media"]; ok {
		test.Fatal("media trace exported")
	}
	if _, ok := performance["Window"].(map[string]any)["Events"]; ok {
		test.Fatal("RS event ring exported")
	}
	if len(performance["Mux"].(map[string]any)["Retired"].([]any)) != 0 {
		test.Fatal("empty retired entries")
	}
}
