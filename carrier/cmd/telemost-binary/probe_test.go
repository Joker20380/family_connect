package main

import (
	"context"
	"testing"

	"github.com/Joker20380/family_connect/carrier/telemost"
)

type immediateEcho struct {
	payload []byte
	corrupt bool
}

func (echo *immediateEcho) SendContext(_ context.Context, payload []byte) error {
	echo.payload = append([]byte(nil), payload...)
	if echo.corrupt {
		echo.payload = append(echo.payload, 0)
	}
	return nil
}
func (echo *immediateEcho) Recv(context.Context) ([]byte, error) { return echo.payload, nil }
func (echo *immediateEcho) Close() error                         { return nil }

func TestProbeMeasurementAndEquality(t *testing.T) {
	for _, corrupt := range []bool{false, true} {
		var result map[string]any
		err := probe(context.Background(), &immediateEcho{corrupt: corrupt}, &telemost.Session{}, func(event map[string]any) error { result = event; return nil }, "batch", 1024, 100, 0)
		if corrupt {
			if err == nil || result["reason"] != "CORRUPTION" {
				t.Fatal("corruption must fail")
			}
			continue
		}
		if err != nil {
			t.Fatal(err)
		}
		if result["count"] != 100 || result["useful_tx_bytes"] != 102400 || result["useful_rx_bytes"] != 102400 {
			t.Fatal("incorrect useful byte counts")
		}
		if result["useful_roundtrip_mbit_s"].(float64) != 2*result["useful_oneway_mbit_s"].(float64) {
			t.Fatal("inconsistent rate definitions")
		}
		if len(result["rtt_ms"].([]float64)) != 100 || result["rtt_samples_complete"] != true {
			t.Fatal("missing samples")
		}
		if result["min_rtt_ms"].(float64) > result["p50_rtt_ms"].(float64) || result["p50_rtt_ms"].(float64) > result["p95_rtt_ms"].(float64) || result["p95_rtt_ms"].(float64) > result["p99_rtt_ms"].(float64) || result["p99_rtt_ms"].(float64) > result["max_rtt_ms"].(float64) {
			t.Fatal("invalid nearest-rank quantiles")
		}
	}
}
