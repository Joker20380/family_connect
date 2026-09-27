package main

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"os"
	"sort"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

type performanceConfig struct {
	Window        int     `json:"window"`
	Payload       int     `json:"payload"`
	Seconds       int     `json:"seconds"`
	WarmupSeconds int     `json:"warmup_seconds"`
	Rate          float64 `json:"rate_mbit_s"`
}

func readPerformanceConfig(path string) (performanceConfig, error) {
	var config performanceConfig
	file, err := os.Open(path)
	if err != nil {
		return config, errors.New("performance input unavailable")
	}
	defer file.Close()
	info, err := file.Stat()
	if err != nil || info.Size() > 4096 {
		return config, errors.New("performance input exceeds bound")
	}
	decoder := json.NewDecoder(io.LimitReader(file, 4097))
	decoder.DisallowUnknownFields()
	if decoder.Decode(&config) != nil || decoder.Decode(new(any)) != io.EOF || config.Window < 1 || config.Window > 128 || config.Payload < 1024 || config.Payload > familysession.MaxPayload || config.Seconds < 1 || config.Seconds > 300 || config.WarmupSeconds < 1 || config.WarmupSeconds > 30 || math.IsNaN(config.Rate) || math.IsInf(config.Rate, 0) || config.Rate < 0 || config.Rate > 4 || (config.Rate > 0 && config.Rate < 0.01) {
		return config, errors.New("invalid bounded performance input")
	}
	return config, nil
}

type performanceBlock struct {
	sequence uint64
	payload  []byte
	created  time.Time
	begin    time.Time
	end      time.Time
	received time.Time
}

type performanceEvent struct {
	sequence uint64
	payload  []byte
	begin    time.Time
	end      time.Time
	err      error
	sending  bool
}

func performanceProbe(parent context.Context, endpoint familysession.PacketEndpoint, config performanceConfig, snapshot func() map[string]any, emit func(map[string]any) error) error {
	ctx, cancel := context.WithCancel(parent)
	jobs := make(chan *performanceBlock, 128)
	events := make(chan performanceEvent, 256)
	var workers sync.WaitGroup
	workers.Add(2)
	defer func() { cancel(); endpoint.Close(); workers.Wait() }()
	go func() {
		defer workers.Done()
		for {
			select {
			case <-ctx.Done():
				return
			case block := <-jobs:
				request, stop := context.WithDeadline(ctx, block.created.Add(10*time.Second))
				begin := time.Now()
				err := endpoint.SendContext(request, block.payload)
				end := time.Now()
				stop()
				select {
				case events <- performanceEvent{sequence: block.sequence, begin: begin, end: end, err: err, sending: true}:
				case <-ctx.Done():
					return
				}
				if err != nil {
					return
				}
			}
		}
	}()
	go func() {
		defer workers.Done()
		for {
			payload, err := endpoint.Recv(ctx)
			event := performanceEvent{payload: payload, end: time.Now(), err: err}
			if len(payload) >= 8 {
				event.sequence = binary.BigEndian.Uint64(payload)
			}
			select {
			case events <- event:
			case <-ctx.Done():
				return
			}
			if err != nil {
				return
			}
		}
	}()
	started := time.Now()
	warmup := true
	interval := time.Duration(config.WarmupSeconds) * time.Second
	deadline := started.Add(interval)
	nextOffer := started
	offerInterval := time.Duration(0)
	if config.Rate > 0 {
		offerInterval = time.Duration(float64(config.Payload*8) / config.Rate * 1000)
	}
	pending := map[uint64]*performanceBlock{}
	sequence, expected := uint64(1), uint64(1)
	sent, received, deliveredInInterval, sentInInterval := 0, 0, 0, 0
	maximumOutstanding := 0
	integral := float64(0)
	lastIntegral := started
	samples := make([]float64, 0, 512)
	stages := make([][]float64, 0, 512)
	counters := map[string]int{"corruption": 0, "missing": 0, "duplicate": 0, "reordered": 0, "unexpected_frames": 0, "timeout": 0, "disconnect": 0, "recovery": 0}
	reason := ""
	status := "PASS"
	accumulate := func(now time.Time) {
		bound := now
		if bound.After(deadline) {
			bound = deadline
		}
		if bound.After(lastIntegral) {
			integral += bound.Sub(lastIntegral).Seconds() * float64(len(pending))
			lastIntegral = bound
		}
	}
	tick := time.NewTicker(time.Millisecond)
	defer tick.Stop()
	nextSnapshot := started.Add(5 * time.Second)
	for {
		now := time.Now()
		accumulate(now)
		if !now.Before(deadline) && len(pending) == 0 {
			if !warmup {
				break
			}
			if err := emit(map[string]any{"event": "perf_warmup", "sent": sent, "received": received, "elapsed_s": now.Sub(started).Seconds()}); err != nil {
				return err
			}
			warmup = false
			started = now
			interval = time.Duration(config.Seconds) * time.Second
			deadline = started.Add(interval)
			nextOffer = started
			sent = 0
			received = 0
			sentInInterval = 0
			deliveredInInterval = 0
			maximumOutstanding = 0
			integral = 0
			lastIntegral = started
			samples = samples[:0]
			stages = stages[:0]
			nextSnapshot = started.Add(5 * time.Second)
		}
		for _, block := range pending {
			if now.Sub(block.created) >= 10*time.Second {
				reason = "timeout"
				break
			}
		}
		if reason != "" {
			break
		}
		if !now.Before(nextSnapshot) {
			if err := emit(map[string]any{"event": "perf_sample", "warmup": warmup, "elapsed_s": now.Sub(started).Seconds(), "sent": sent, "received": received, "outstanding": len(pending), "application_send_queue": len(jobs), "snapshot": snapshot()}); err != nil {
				return err
			}
			nextSnapshot = now.Add(5 * time.Second)
		}
		if now.Before(deadline) && (config.Rate == 0 || !now.Before(nextOffer)) {
			if len(pending) < config.Window {
				payload := make([]byte, config.Payload)
				if _, err := rand.Read(payload); err != nil {
					return errors.New("performance payload generation failed")
				}
				binary.BigEndian.PutUint64(payload, sequence)
				block := &performanceBlock{sequence: sequence, payload: payload, created: time.Now()}
				pending[sequence] = block
				sequence++
				jobs <- block
				maximumOutstanding = max(maximumOutstanding, len(pending))
				if config.Rate > 0 {
					nextOffer = nextOffer.Add(offerInterval)
				}
			} else if config.Rate > 0 {
				reason = "offered_load_outstanding_bound"
				break
			}
		}
		select {
		case <-ctx.Done():
			reason = "disconnect"
		case <-tick.C:
		case event := <-events:
			if event.err != nil {
				reason = "disconnect"
				if errors.Is(event.err, context.DeadlineExceeded) || os.IsTimeout(event.err) {
					reason = "timeout"
				}
				break
			}
			block := pending[event.sequence]
			if block == nil {
				if event.sequence < expected {
					reason = "duplicate"
				} else {
					reason = "unexpected_frames"
				}
				break
			}
			if event.sending {
				block.begin = event.begin
				block.end = event.end
				sent++
				if event.end.Before(deadline) {
					sentInInterval++
				}
			} else {
				if !block.received.IsZero() {
					reason = "duplicate"
					break
				}
				if event.sequence != expected {
					reason = "reordered"
					break
				}
				if !bytes.Equal(block.payload, event.payload) {
					reason = "corruption"
					break
				}
				expected++
				block.received = event.end
				received++
				if event.end.Before(deadline) {
					deliveredInInterval++
				}
			}
			if !block.end.IsZero() && !block.received.IsZero() {
				accumulate(time.Now())
				milliseconds := func(when time.Time) float64 { return float64(when.Sub(started)) / float64(time.Millisecond) }
				samples = append(samples, float64(block.received.Sub(block.created))/float64(time.Millisecond))
				stages = append(stages, []float64{float64(block.sequence), milliseconds(block.created), milliseconds(block.begin), milliseconds(block.end), milliseconds(block.received)})
				delete(pending, block.sequence)
				if len(samples) >= 16384 {
					reason = "sample_bound"
				}
			}
		}
		if reason != "" {
			break
		}
	}
	if reason != "" {
		status = "FAIL"
		if _, ok := counters[reason]; ok {
			counters[reason]++
		}
	}
	counters["missing"] = sent - received
	if counters["missing"] < 0 {
		counters["missing"] = 0
	}
	elapsed := time.Since(started).Seconds()
	measured := math.Min(elapsed, interval.Seconds())
	for offset := 0; offset < len(stages); offset += 128 {
		if err := emit(map[string]any{"event": "perf_blocks", "warmup": warmup, "columns": []string{"sequence", "created_ms", "send_begin_ms", "send_return_ms", "echo_received_ms"}, "rows": stages[offset:min(offset+128, len(stages))]}); err != nil {
			return err
		}
	}
	result := map[string]any{"event": "perf_result", "status": status, "reason": reason, "warmup": warmup, "config": config, "measurement_s": measured, "elapsed_with_drain_s": elapsed, "blocks_sent": sent, "blocks_received": received, "useful_tx_bytes": sent * config.Payload, "useful_rx_bytes": received * config.Payload, "tx_interval_bytes": sentInInterval * config.Payload, "rx_interval_bytes": deliveredInInterval * config.Payload, "tx_mbit_s": float64(sentInInterval*config.Payload*8) / measured / 1e6, "delivered_mbit_s": float64(deliveredInInterval*config.Payload*8) / measured / 1e6, "aggregate_mbit_s": float64((sentInInterval+deliveredInInterval)*config.Payload*8) / measured / 1e6, "drain_normalized_mbit_s": float64(received*config.Payload*8) / elapsed / 1e6, "max_outstanding": maximumOutstanding, "average_outstanding": integral / measured, "errors": counters, "snapshot": snapshot()}
	if len(samples) > 0 {
		sort.Float64s(samples)
		total := float64(0)
		for _, sample := range samples {
			total += sample
		}
		result["avg_rtt_ms"] = total / float64(len(samples))
		result["min_rtt_ms"] = samples[0]
		result["max_rtt_ms"] = samples[len(samples)-1]
		for _, percentile := range []int{50, 95, 99} {
			result[fmt.Sprintf("p%d_rtt_ms", percentile)] = samples[(percentile*len(samples)+99)/100-1]
		}
	}
	if err := emit(result); err != nil {
		return err
	}
	if reason != "" {
		return errors.New("bounded performance point failed; no retry")
	}
	return nil
}

func performanceEcho(ctx context.Context, endpoint familysession.PacketEndpoint, snapshot func() map[string]any, emit func(map[string]any) error) error {
	started := time.Now()
	rows := make([][]float64, 0, 128)
	count, total := 0, 0
	flush := func() error {
		if len(rows) == 0 {
			return nil
		}
		err := emit(map[string]any{"event": "perf_echo", "columns": []string{"sequence", "application_received_ms", "echo_enqueue_ms", "echo_send_return_ms", "bytes"}, "rows": rows, "blocks_received": count, "useful_rx_bytes": total, "elapsed_s": time.Since(started).Seconds(), "snapshot": snapshot()})
		rows = rows[:0]
		return err
	}
	defer flush()
	for {
		payload, err := endpoint.Recv(ctx)
		received := time.Now()
		if err != nil {
			return err
		}
		if len(payload) < 8 {
			return errors.New("unexpected performance block")
		}
		begin := time.Now()
		request, cancel := context.WithTimeout(ctx, 10*time.Second)
		err = endpoint.SendContext(request, payload)
		end := time.Now()
		cancel()
		if err != nil {
			return err
		}
		milliseconds := func(when time.Time) float64 { return float64(when.Sub(started)) / float64(time.Millisecond) }
		rows = append(rows, []float64{float64(binary.BigEndian.Uint64(payload)), milliseconds(received), milliseconds(begin), milliseconds(end), float64(len(payload))})
		count++
		total += len(payload)
		if len(rows) == 128 {
			if err := flush(); err != nil {
				return err
			}
		}
	}
}
