package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
)

func interactionPressure(session *familysession.Session) map[string]any {
	stats := session.ReliabilityStats()
	perf := stats.Performance
	return map[string]any{"depth": stats.SendDepth, "terminal": stats.Terminal, "ready": perf.Ready,
		"retained": perf.RetainedBytes, "sacked": perf.SACKedBytes, "unconfirmed": perf.UnconfirmedBytes,
		"full_ns": perf.ReadyFullNS, "head_sacked_ns": perf.HeadSACKedBlockedNS,
		"head_unconfirmed_ns": perf.HeadUnconfirmedLaterSACKedBlockedNS,
		"local_busy":          perf.LocalWriterBusy, "local_queued": perf.LocalQueuedFrames}
}

func interactionMuxPressure(mux *tcpforward.Mux) map[string]any {
	perf := mux.PerformanceSnapshot()
	return map[string]any{"Profile": perf.Profile, "Window": perf.Window, "ActiveStreams": perf.ActiveStreams,
		"Streams": perf.Streams, "RetainedBytes": perf.RetainedBytes, "RetainedHighWater": perf.RetainedHighWater,
		"Batches": perf.Batches, "BatchMessages": perf.BatchMessages, "RetiredCount": perf.RetiredCount}
}

func interactionComplete(ctx context.Context, path string, mux *tcpforward.Mux, session *familysession.Session, server bool, emit func(map[string]any) error) error {
	waitFile := func(name string) error {
		ticker := time.NewTicker(50 * time.Millisecond)
		defer ticker.Stop()
		for {
			if _, err := os.Stat(filepath.Join(filepath.Dir(path), name)); err == nil {
				return nil
			}
			if err, _ := mux.Terminal(); err != nil {
				return err
			}
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-ticker.C:
			}
		}
	}
	if err := waitFile("drain.input"); err != nil {
		return err
	}
	deadline, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()
	for mux.Stats().ActiveStreams != 0 {
		select {
		case <-deadline.Done():
			return deadline.Err()
		case <-time.After(20 * time.Millisecond):
		}
	}
	err := session.LabDrain(deadline)
	stats := session.ReliabilityStats()
	if err == nil && (stats.Terminal != "" || stats.SendDepth != 0 || stats.Performance.ReleasedBlocks != stats.DataSent) {
		err = fmt.Errorf("unconfirmed final DATA")
	}
	_ = emit(map[string]any{"event": "p_drained", "server": server, "error": fmt.Sprint(err), "packing": session.LabPackingStats(), "reliability": stats, "mux": mux.Stats()})
	if err != nil {
		return err
	}
	return waitFile("finish.input")
}
