package main

import (
	"context"
	"encoding/binary"
	"errors"
	"os"
	"path/filepath"
	"sync/atomic"
	"testing"
	"time"
)

type pipelineEcho struct {
	queue        chan []byte
	sent         atomic.Int64
	firstReceive atomic.Int64
	fault        string
}

func (echo *pipelineEcho) SendContext(ctx context.Context, payload []byte) error {
	copyPayload := append([]byte(nil), payload...)
	select {
	case echo.queue <- copyPayload:
		echo.sent.Add(1)
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}
func (echo *pipelineEcho) Recv(ctx context.Context) ([]byte, error) {
	select {
	case <-time.After(20 * time.Millisecond):
	case <-ctx.Done():
		return nil, ctx.Err()
	}
	echo.firstReceive.CompareAndSwap(0, echo.sent.Load())
	select {
	case payload := <-echo.queue:
		switch echo.fault {
		case "corruption":
			payload[len(payload)-1] ^= 1
		case "reordered":
			binary.BigEndian.PutUint64(payload, 2)
		case "duplicate":
			binary.BigEndian.PutUint64(payload, 0)
		case "unexpected_frames":
			binary.BigEndian.PutUint64(payload, 999)
		case "disconnect":
			return nil, errors.New("disconnected")
		case "timeout":
			return nil, context.DeadlineExceeded
		}
		return payload, nil
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}
func (echo *pipelineEcho) Close() error { return nil }

func TestPerformancePipelineAndBounds(test *testing.T) {
	for _, rate := range []float64{0, 0.25} {
		echo := &pipelineEcho{queue: make(chan []byte, 128)}
		var result map[string]any
		emit := func(event map[string]any) error {
			if event["event"] == "perf_result" {
				result = event
			}
			return nil
		}
		config := performanceConfig{Window: 8, Payload: 1024, Seconds: 1, WarmupSeconds: 1, Rate: rate}
		if err := performanceProbe(context.Background(), echo, config, func() map[string]any { return nil }, emit); err != nil {
			test.Fatal(err)
		}
		if rate == 0 && echo.firstReceive.Load() < 2 {
			test.Fatal("producer still waits for first echo")
		}
		if result["blocks_sent"] != result["blocks_received"] || result["max_outstanding"].(int) > 8 || result["measurement_s"] != float64(1) {
			test.Fatal(result)
		}
		if result["errors"].(map[string]int)["missing"] != 0 {
			test.Fatal("lost blocks")
		}
	}
}

func TestPerformanceFaultsNeverPass(test *testing.T) {
	for _, fault := range []string{"corruption", "reordered", "duplicate", "unexpected_frames", "timeout", "disconnect"} {
		test.Run(fault, func(test *testing.T) {
			echo := &pipelineEcho{queue: make(chan []byte, 128), fault: fault}
			var result map[string]any
			err := performanceProbe(context.Background(), echo, performanceConfig{Window: 4, Payload: 1024, Seconds: 1, WarmupSeconds: 1}, func() map[string]any { return nil }, func(event map[string]any) error {
				if event["event"] == "perf_result" {
					result = event
				}
				return nil
			})
			if err == nil || result["status"] != "FAIL" || result["errors"].(map[string]int)[fault] != 1 {
				test.Fatal(result, err)
			}
		})
	}
}

func TestPerformanceOfferedLoadStopsInsteadOfBlocking(test *testing.T) {
	echo := &pipelineEcho{queue: make(chan []byte, 128)}
	var result map[string]any
	err := performanceProbe(context.Background(), echo, performanceConfig{Window: 2, Payload: 1024, Seconds: 1, WarmupSeconds: 1, Rate: 4}, func() map[string]any { return nil }, func(event map[string]any) error {
		if event["event"] == "perf_result" {
			result = event
		}
		return nil
	})
	if err == nil || result["reason"] != "offered_load_outstanding_bound" {
		test.Fatal(result, err)
	}
}

func TestPerformanceConfigRejectsUnboundedAndUnknown(test *testing.T) {
	path := filepath.Join(test.TempDir(), "performance.json")
	for _, input := range []string{`{}`, `{"window":129,"payload":1024,"seconds":60,"warmup_seconds":5}`, `{"window":1,"payload":65537,"seconds":60,"warmup_seconds":5}`, `{"window":1,"payload":1024,"seconds":301,"warmup_seconds":5}`, `{"window":1,"payload":1024,"seconds":60,"warmup_seconds":5,"unknown":1}`} {
		if err := os.WriteFile(path, []byte(input), 0600); err != nil {
			test.Fatal(err)
		}
		if _, err := readPerformanceConfig(path); err == nil {
			test.Fatal("accepted invalid configuration")
		}
	}
	if err := os.WriteFile(path, []byte(`{"window":64,"payload":16384,"seconds":60,"warmup_seconds":5}`), 0600); err != nil {
		test.Fatal(err)
	}
	if _, err := readPerformanceConfig(path); err != nil {
		test.Fatal(err)
	}
}

func TestPerformanceErrorClassNeverLeaksRawError(test *testing.T) {
	if performanceErrorClass(errors.New("sensitive arbitrary server response")) != "other_redacted" || performanceErrorClass(errors.New("tls: bad record MAC")) != "tls_bad_record_mac" {
		test.Fatal("unsafe error classification")
	}
}
