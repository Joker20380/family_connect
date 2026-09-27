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
	"sort"
	"sync"
	"syscall"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
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
	familyConfig := flag.String("family-config", "", "private isolated 5N.3 credentials file; no production identity")
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
	var data familysession.PacketEndpoint = session
	if *familyConfig != "" {
		if mode != telemost.ModeVP8 {
			return errors.New("Family gate requires VP8")
		}
		info, err := os.Lstat(*familyConfig)
		if err != nil || !info.Mode().IsRegular() || info.Mode().Perm() != 0600 || info.Size() > 48<<10 {
			return familysession.ErrRejected
		}
		credentials, err := os.ReadFile(*familyConfig)
		if err != nil {
			return familysession.ErrRejected
		}
		if *role == "probe" {
			select {
			case <-time.After(*settle):
			case <-ctx.Done():
				return ctx.Err()
			}
		}
		secured, err := familysession.Open(ctx, session, credentials, *role == "echo")
		clear(credentials)
		if err != nil {
			_ = emit(map[string]any{"event": "family_auth", "accepted": false})
			return familysession.ErrRejected
		}
		defer secured.Close()
		data = secured
		if err := emit(map[string]any{"event": "family_auth", "accepted": true, "protocol": familysession.Protocol}); err != nil {
			return err
		}
	}
	if *role == "echo" {
		for {
			payload, err := data.Recv(ctx)
			if err != nil {
				if ctx.Err() != nil {
					return nil
				}
				return err
			}
			if err := data.SendContext(ctx, payload); err != nil {
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
		if err := probe(ctx, data, session, emit, "size", size, 1, 0); err != nil {
			return err
		}
	}
	for _, size := range []int{1024, 16384} {
		if err := probe(ctx, data, session, emit, "batch", size, 100, 0); err != nil {
			return err
		}
	}
	if *sustained > 0 {
		if err := probe(ctx, data, session, emit, "sustained", 16384, 0, *sustained); err != nil {
			return err
		}
	}
	if *extended {
		if err := probe(ctx, data, session, emit, "extended", 16384, 0, 5*time.Minute); err != nil {
			return err
		}
	}
	return emit(map[string]any{"event": "suite_complete", "byte_for_byte": true, "family_authenticated": *familyConfig != "", "gate_eligible_mode": mode == telemost.ModeVP8, "note": "requires independent endpoints and recorded real Telemost room/media evidence; Android gate also requires a physical device; no automatic gate promotion"})
}

func probe(ctx context.Context, data familysession.PacketEndpoint, session *telemost.Session, emit func(map[string]any) error, phase string, size, count int, duration time.Duration) error {
	started := time.Now()
	completed := 0
	var totalRTT time.Duration
	var maximumRTT time.Duration
	minimumRTT := time.Duration(1<<63 - 1)
	samples := make([]float64, 0, 256)
	for (count > 0 && completed < count) || (duration > 0 && time.Since(started) < duration) {
		payload := make([]byte, size)
		if _, err := rand.Read(payload); err != nil {
			return errors.New("synthetic payload generation failed")
		}
		requestContext, cancel := context.WithTimeout(ctx, 10*time.Second)
		sent := time.Now()
		err := data.SendContext(requestContext, payload)
		var echoed []byte
		if err == nil {
			echoed, err = data.Recv(requestContext)
		}
		requestErr := requestContext.Err()
		cancel()
		if err != nil {
			reason := "SESSION_CLOSED"
			if errors.Is(err, context.DeadlineExceeded) || errors.Is(requestErr, context.DeadlineExceeded) || os.IsTimeout(err) {
				reason = "ECHO_TIMEOUT"
			} else if errors.Is(err, context.Canceled) {
				reason = "CANCELED"
			}
			_ = emit(map[string]any{"event": "probe_failed", "phase": phase, "payload_bytes": size, "completed": completed, "reason": reason, "carrier_mode": session.Stats().Mode, "stats": session.Stats()})
			return errors.New("binary probe failed; gate remains open")
		}
		if !bytes.Equal(payload, echoed) {
			_ = emit(map[string]any{"event": "probe_failed", "phase": phase, "completed": completed, "reason": "CORRUPTION"})
			return errors.New("binary mismatch; gate remains open")
		}
		elapsed := time.Since(sent)
		totalRTT += elapsed
		maximumRTT = max(maximumRTT, elapsed)
		minimumRTT = min(minimumRTT, elapsed)
		if len(samples) < 4096 {
			samples = append(samples, float64(elapsed.Nanoseconds())/1e6)
		}
		completed++
	}
	seconds := time.Since(started).Seconds()
	if completed == 0 {
		return errors.New("probe interval completed without samples")
	}
	result := map[string]any{"event": "probe_result", "phase": phase, "payload_bytes": size, "count": completed, "sent": completed, "received": completed, "byte_equal": true, "carrier_mode": session.Stats().Mode, "byte_for_byte": true, "elapsed_s": seconds, "mean_rtt_ms": float64(totalRTT.Nanoseconds()) / 1e6 / float64(completed), "max_rtt_ms": float64(maximumRTT.Nanoseconds()) / 1e6, "min_rtt_ms": float64(minimumRTT.Nanoseconds()) / 1e6, "useful_tx_bytes": completed * size, "useful_rx_bytes": completed * size, "useful_oneway_mbit_s": float64(completed*size*8) / seconds / 1e6, "useful_roundtrip_mbit_s": float64(completed*size*2*8) / seconds / 1e6, "stats": session.Stats(), "rtt_ms": samples, "rtt_samples_complete": len(samples) == completed}
	if len(samples) == completed {
		ordered := append([]float64(nil), samples...)
		sort.Float64s(ordered)
		for _, percentile := range []int{50, 95, 99} {
			result[fmt.Sprintf("p%d_rtt_ms", percentile)] = ordered[(percentile*len(ordered)+99)/100-1]
		}
	}
	return emit(result)
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
