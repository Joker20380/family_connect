package main

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"runtime"
	"runtime/debug"
	"sync"
	"syscall"
	"time"

	"github.com/Joker20380/family_connect/carrier/telemost"
)

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func run() error {
	role := flag.String("role", "probe", "probe or echo; synthetic traffic only")
	modeName := flag.String("mode", "vp8", "vp8 or datachannel (diagnostic only)")
	duration := flag.Duration("duration", 10*time.Minute, "hard session deadline, maximum one hour")
	sustained := flag.Duration("sustained", 30*time.Second, "sustained probe duration after size/batch checks")
	extended := flag.Bool("extended", false, "run another five minutes after successful sustained check")
	settle := flag.Duration("settle", 3*time.Second, "wait for remote media slots before probing")
	metricsInterval := flag.Duration("metrics-interval", 0, "optional memory/CPU sample interval (1s to 1m; zero disables)")
	flag.Parse()
	if *metricsInterval != 0 && (*metricsInterval < time.Second || *metricsInterval > time.Minute) {
		return errors.New("invalid metrics interval")
	}
	if (*role != "probe" && *role != "echo") || (*modeName != "vp8" && *modeName != "datachannel") || *duration <= 0 || *duration > time.Hour || *sustained < 0 || *sustained > 5*time.Minute || *settle < 0 || *settle > time.Minute {
		return errors.New("invalid harness options")
	}
	mode := telemost.ModeVP8
	if *modeName == "datachannel" {
		mode = telemost.ModeDataChannel
	}
	signalContext, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	ctx, cancel := context.WithTimeout(signalContext, *duration)
	defer cancel()
	session, err := telemost.New(ctx, telemost.Config{RoomURL: os.Getenv("FC_TELEMOST_ROOM"), DisplayName: "FC synthetic " + *role, Mode: mode})
	if err != nil {
		return err
	}
	defer session.Close()
	encoder := json.NewEncoder(os.Stdout)
	var outputMu sync.Mutex
	emit := func(event map[string]any) error {
		outputMu.Lock()
		defer outputMu.Unlock()
		event["utc"] = time.Now().UTC().Format(time.RFC3339Nano)
		return encoder.Encode(event)
	}
	stopMetrics := startMetrics(ctx, *metricsInterval, emit)
	defer stopMetrics()
	defer func() {
		_ = session.Close()
		stopMetrics()
		var usage syscall.Rusage
		_ = syscall.Getrusage(syscall.RUSAGE_SELF, &usage)
		var memory runtime.MemStats
		runtime.ReadMemStats(&memory)
		_ = emit(map[string]any{"event": "summary", "stats": session.Stats(), "cpu_user_s": float64(usage.Utime.Sec) + float64(usage.Utime.Usec)/1e6, "cpu_system_s": float64(usage.Stime.Sec) + float64(usage.Stime.Usec)/1e6, "max_rss_kib": usage.Maxrss, "heap_bytes": memory.HeapAlloc, "goroutines": runtime.NumGoroutine()})
	}()
	metadata := buildMetadata()
	metadata["event"] = "start"
	metadata["role"] = *role
	metadata["mode"] = *modeName
	metadata["room_method"] = "operator-provided disposable room"
	if err := emit(metadata); err != nil {
		return errors.New("metrics output failed")
	}
	if err := session.Connect(ctx); err != nil {
		return err
	}
	if err := emit(map[string]any{"event": "connected", "stats": session.Stats()}); err != nil {
		return err
	}
	if *role == "echo" {
		for {
			payload, err := session.Recv(ctx)
			if err != nil {
				if ctx.Err() != nil {
					return nil
				}
				return err
			}
			if err := session.Send(payload); err != nil {
				return err
			}
		}
	}
	select {
	case <-time.After(*settle):
	case <-ctx.Done():
		return ctx.Err()
	}
	for _, size := range []int{1, 32, 256, 1024, 4096, 16384, 65536} {
		if err := probe(ctx, session, emit, "size", size, 1, 0); err != nil {
			return err
		}
	}
	for _, size := range []int{1024, 16384} {
		if err := probe(ctx, session, emit, "batch", size, 100, 0); err != nil {
			return err
		}
	}
	if *sustained > 0 {
		if err := probe(ctx, session, emit, "sustained", 16384, 0, *sustained); err != nil {
			return err
		}
	}
	if *extended {
		if err := probe(ctx, session, emit, "extended", 16384, 0, 5*time.Minute); err != nil {
			return err
		}
	}
	return emit(map[string]any{"event": "suite_complete", "byte_for_byte": true, "gate_eligible_mode": mode == telemost.ModeVP8, "note": "requires independent endpoints and recorded real Telemost room/media evidence; Android gate also requires a physical device; no automatic gate promotion"})
}

func probe(ctx context.Context, session *telemost.Session, emit func(map[string]any) error, phase string, size, count int, duration time.Duration) error {
	started := time.Now()
	completed := 0
	var totalRTT time.Duration
	var maximumRTT time.Duration
	for (count > 0 && completed < count) || (duration > 0 && time.Since(started) < duration) {
		payload := make([]byte, size)
		if _, err := rand.Read(payload); err != nil {
			return errors.New("synthetic payload generation failed")
		}
		requestContext, cancel := context.WithTimeout(ctx, 10*time.Second)
		sent := time.Now()
		err := session.SendContext(requestContext, payload)
		var echoed []byte
		if err == nil {
			echoed, err = session.Recv(requestContext)
		}
		cancel()
		if err != nil {
			reason := "SESSION_CLOSED"
			if errors.Is(err, context.DeadlineExceeded) {
				reason = "ECHO_TIMEOUT"
			} else if errors.Is(err, context.Canceled) {
				reason = "CANCELED"
			}
			_ = emit(map[string]any{"event": "probe_failed", "phase": phase, "payload_bytes": size, "completed": completed, "reason": reason, "carrier_mode": session.Stats().Mode, "stats": session.Stats()})
			return errors.New("binary probe failed; gate remains open")
		}
		if !bytes.Equal(payload, echoed) {
			return errors.New("binary mismatch; gate remains open")
		}
		elapsed := time.Since(sent)
		totalRTT += elapsed
		maximumRTT = max(maximumRTT, elapsed)
		completed++
	}
	seconds := time.Since(started).Seconds()
	if completed == 0 {
		return errors.New("probe interval completed without samples")
	}
	return emit(map[string]any{"event": "probe_result", "phase": phase, "payload_bytes": size, "count": completed, "sent": completed, "received": completed, "byte_equal": true, "carrier_mode": session.Stats().Mode, "byte_for_byte": true, "elapsed_s": seconds, "mean_rtt_ms": float64(totalRTT.Microseconds()) / 1000 / float64(completed), "max_rtt_ms": float64(maximumRTT.Microseconds()) / 1000, "useful_roundtrip_mbit_s": float64(completed*size*2*8) / seconds / 1e6, "stats": session.Stats()})
}

func buildMetadata() map[string]any {
	metadata := map[string]any{"os": runtime.GOOS, "arch": runtime.GOARCH, "go": runtime.Version(), "pid": os.Getpid(), "parent_pid": os.Getppid()}
	if info, ok := debug.ReadBuildInfo(); ok {
		for _, dependency := range info.Deps {
			if dependency.Path == "github.com/pion/webrtc/v4" {
				metadata["pion"] = dependency.Version
			}
		}
		for _, setting := range info.Settings {
			if setting.Key == "vcs.revision" || setting.Key == "vcs.modified" {
				metadata[setting.Key] = setting.Value
			}
		}
	}
	return metadata
}
