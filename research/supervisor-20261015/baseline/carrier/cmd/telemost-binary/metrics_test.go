package main

import (
	"context"
	"errors"
	"testing"
	"time"
)

func TestMetricsCancelAndOutputFailure(t *testing.T) {
	for _, outputFails := range []bool{false, true} {
		emitted := make(chan struct{}, 1)
		stop := startMetrics(context.Background(), time.Millisecond, func(event map[string]any) error {
			if event["event"] != "resources" || event["heap_bytes"] == nil {
				t.Error("missing resource fields")
			}
			select {
			case emitted <- struct{}{}:
			default:
			}
			if outputFails {
				return errors.New("closed output")
			}
			return nil
		})
		select {
		case <-emitted:
		case <-time.After(time.Second):
			t.Fatal("metrics did not start")
		}
		stop()
		stop()
	}
}

func TestMetricsDisabled(t *testing.T) {
	startMetrics(context.Background(), 0, func(map[string]any) error {
		t.Fatal("disabled metrics emitted")
		return nil
	})()
}
