package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"sort"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
	"golang.org/x/net/dns/dnsmessage"
)

type muxProbeConfig struct {
	Mode    string `json:"mode"`
	Seconds int    `json:"seconds"`
	Port    int    `json:"port"`
}

func muxSamples(ctx context.Context, mux *tcpforward.Mux, snapshot func() map[string]any, emit func(map[string]any) error) func() {
	ctx, cancel := context.WithCancel(ctx)
	done := make(chan struct{})
	go func() {
		defer close(done)
		ticker := time.NewTicker(5 * time.Second)
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				_ = emit(map[string]any{"event": "mux_sample", "stats": mux.Stats(), "transport": snapshot()})
			}
		}
	}()
	return func() { cancel(); <-done }
}

func muxProbe(ctx context.Context, session *familysession.Session, path string, guard bool, snapshot func() map[string]any, emit func(map[string]any) error) error {
	info, err := os.Stat(path)
	if err != nil || !info.Mode().IsRegular() || info.Size() > 1024 {
		return errors.New("invalid mux configuration")
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	var config muxProbeConfig
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if decoder.Decode(&config) != nil || decoder.Decode(new(any)) != io.EOF || (config.Mode != "public" && config.Mode != "mixed") || config.Seconds < 0 || config.Seconds > 600 || config.Mode == "mixed" && (config.Seconds < 300 || config.Port < 1 || config.Port > 65535) {
		return errors.New("invalid mux configuration")
	}
	mux, err := tcpforward.NewMux(ctx, session, false, tcpforward.MuxConfig{})
	if err != nil {
		return err
	}
	defer mux.Close()
	stop := muxSamples(ctx, mux, snapshot, emit)
	defer stop()
	started := time.Now()
	if config.Mode == "public" {
		err = muxPublic(ctx, mux, emit)
	} else {
		err = muxMixed(ctx, mux, config, emit)
	}
	status := "PASS"
	if guard && dnsGuardCount() != 0 {
		err = errors.New("native DNS attempted after admission")
	}
	if err != nil {
		status = "FAIL"
	}
	_ = emit(map[string]any{"event": "mux_result", "status": status, "mode": config.Mode, "seconds": time.Since(started).Seconds(), "stats": mux.Stats(), "transport": snapshot()})
	return err
}

func muxPublic(ctx context.Context, mux *tcpforward.Mux, emit func(map[string]any) error) error {
	streams := make([]*tcpforward.MuxStream, 4)
	configs := []tcpConfig{{Host: "example.com", Port: 443, Path: "/"}, {Host: "speed.cloudflare.com", Port: 443, Path: "/__down?bytes=1024"}, {Host: "example.com", Port: 443, Path: "/"}, {Host: "speed.cloudflare.com", Port: 443, Path: "/__down?bytes=2048"}}
	for index, config := range configs {
		stream, err := mux.OpenTCP(ctx, tcpforward.OpenRequest{Host: config.Host, Port: config.Port})
		if err != nil {
			return err
		}
		streams[index] = stream
		defer stream.Close()
	}
	_ = emit(map[string]any{"event": "mux_open", "simultaneous": 4, "stats": mux.Stats()})
	results := make(chan error, 4)
	for index, stream := range streams {
		go func() {
			result := map[string]any{"event": "mux_https", "host": configs[index].Host, "stream_id": stream.Stats().ID}
			err := tcpHTTPS(ctx, stream, configs[index], result)
			if err == nil {
				err = stream.Close()
			}
			result["passed"] = err == nil
			result["stream"] = stream.Stats()
			_ = emit(result)
			results <- err
		}()
	}
	var failure error
	for range streams {
		if err := <-results; err != nil {
			failure = err
		}
	}
	if failure != nil {
		return failure
	}
	return muxDNSProof(ctx, mux, emit)
}

func muxQuery(name string, kind dnsmessage.Type) ([]byte, error) {
	domain, err := dnsmessage.NewName(name)
	if err != nil {
		return nil, err
	}
	return (&dnsmessage.Message{Header: dnsmessage.Header{ID: 7, RecursionDesired: true}, Questions: []dnsmessage.Question{{Name: domain, Type: kind, Class: dnsmessage.ClassINET}}}).Pack()
}

func muxDNSProof(ctx context.Context, mux *tcpforward.Mux, emit func(map[string]any) error) error {
	results := make(chan error, 3)
	for index, kind := range []dnsmessage.Type{dnsmessage.TypeA, dnsmessage.TypeAAAA, dnsmessage.TypeA} {
		name := muxDNSName(index)
		go func() {
			query, err := muxQuery(name, kind)
			if err != nil {
				results <- err
				return
			}
			started := time.Now()
			response, err := mux.QueryDNS(ctx, query)
			var message dnsmessage.Message
			if err == nil {
				err = message.Unpack(response)
			}
			if err == nil && (index == 2 && message.RCode != dnsmessage.RCodeNameError || index != 2 && (message.RCode != 0 || len(message.Answers) == 0)) {
				err = errors.New("DNS answer mismatch")
			}
			_ = emit(map[string]any{"event": "mux_dns", "query_type": int(kind), "nxdomain": index == 2, "passed": err == nil, "rcode": int(message.RCode), "answers": len(message.Answers), "latency_ms": float64(time.Since(started)) / float64(time.Millisecond)})
			results <- err
		}()
	}
	var failure error
	for range 3 {
		if err := <-results; err != nil {
			failure = err
		}
	}
	return failure
}

func muxDNSName(index int) string {
	if index == 2 {
		return fmt.Sprintf("fc-mux-%d.invalid.", time.Now().UnixNano())
	}
	return "example.com."
}

func muxFill(payload []byte, id uint32, offset int64) {
	for index := range payload {
		position := offset + int64(index)
		payload[index] = byte(position*31 + position/251 + int64(id)*73)
	}
}

func muxBulk(ctx context.Context, stream *tcpforward.MuxStream, seconds int, emit func(map[string]any) error) error {
	id := stream.Stats().ID
	started := time.Now()
	until := started.Add(time.Duration(seconds) * time.Second)
	written := make(chan error, 1)
	go func() {
		buffer := make([]byte, 8192)
		offset := int64(0)
		for time.Now().Before(until) {
			muxFill(buffer, id, offset)
			count, err := stream.Write(buffer)
			offset += int64(count)
			if err != nil {
				written <- err
				return
			}
			next := started.Add(time.Duration(float64(offset) * 8 / 500000 * float64(time.Second)))
			timer := time.NewTimer(max(time.Duration(0), time.Until(next)))
			select {
			case <-timer.C:
			case <-ctx.Done():
				timer.Stop()
				written <- ctx.Err()
				return
			}
		}
		written <- stream.CloseWrite()
	}()
	buffer, expected := make([]byte, 8192), make([]byte, 8192)
	total := int64(0)
	digest := sha256.New()
	var failure error
	for {
		count, err := stream.Read(buffer)
		if count > 0 {
			muxFill(expected[:count], id, total)
			if !bytes.Equal(buffer[:count], expected[:count]) {
				failure = errors.New("bulk byte mismatch")
				break
			}
			total += int64(count)
			digest.Write(buffer[:count])
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			failure = err
			break
		}
	}
	if failure != nil {
		stream.Reset()
	}
	if err := <-written; err != nil {
		failure = err
	}
	if failure == nil && (total < 10<<20 || total != int64(stream.Stats().Sent)) {
		failure = errors.New("bulk below ten MiB")
	}
	if failure == nil {
		failure = stream.Close()
	}
	elapsed := time.Since(started).Seconds()
	_ = emit(map[string]any{"event": "mux_bulk", "passed": failure == nil, "bytes_each_direction": total, "sha256": hex.EncodeToString(digest.Sum(nil)), "seconds": elapsed, "aggregate_mbit": float64(total) * 16 / elapsed / 1e6, "stream": stream.Stats()})
	return failure
}

func muxPercentiles(samples []float64) map[string]any {
	if len(samples) == 0 {
		return map[string]any{"count": 0}
	}
	sort.Float64s(samples)
	sum := 0.0
	for _, sample := range samples {
		sum += sample
	}
	return map[string]any{"count": len(samples), "avg_ms": sum / float64(len(samples)), "p50_ms": samples[(len(samples)-1)*50/100], "p95_ms": samples[(len(samples)-1)*95/100], "p99_ms": samples[(len(samples)-1)*99/100], "max_ms": samples[len(samples)-1]}
}

func muxMixed(ctx context.Context, mux *tcpforward.Mux, config muxProbeConfig, emit func(map[string]any) error) error {
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	streams := make([]*tcpforward.MuxStream, 5)
	for index := range streams {
		stream, err := mux.OpenTCP(ctx, tcpforward.OpenRequest{Host: "127.0.0.1", Port: config.Port})
		if err != nil {
			return err
		}
		streams[index] = stream
		defer stream.Close()
	}
	_ = emit(map[string]any{"event": "mux_open", "simultaneous": 5, "stats": mux.Stats()})
	started := time.Now()
	until := started.Add(time.Duration(config.Seconds) * time.Second)
	results := make(chan error, 7)
	go func() { results <- muxBulk(ctx, streams[0], config.Seconds, emit) }()
	go func() {
		timer := time.NewTimer(10 * time.Second)
		defer timer.Stop()
		select {
		case <-timer.C:
		case <-ctx.Done():
			results <- ctx.Err()
			return
		}
		for _, mode := range []string{"reset", "cancel"} {
			local, stop := context.WithCancel(ctx)
			stream, err := mux.OpenTCP(local, tcpforward.OpenRequest{Host: "127.0.0.1", Port: config.Port})
			if err != nil {
				stop()
				results <- err
				return
			}
			payload, response := make([]byte, 128), make([]byte, 128)
			muxFill(payload, stream.Stats().ID, 0)
			_, err = stream.Write(payload)
			if err == nil {
				_, err = io.ReadFull(stream, response)
			}
			if err == nil && !bytes.Equal(payload, response) {
				err = errors.New("isolation identity mismatch")
			}
			if mode == "reset" {
				stream.Reset()
			}
			stop()
			_, terminal := stream.Read(response)
			if terminal == nil || terminal == io.EOF {
				err = errors.New("isolated cancellation did not reset")
			}
			_ = emit(map[string]any{"event": "mux_isolation", "mode": mode, "passed": err == nil, "stream": stream.Stats()})
			if err != nil {
				results <- err
				return
			}
		}
		_, err := mux.OpenTCP(ctx, tcpforward.OpenRequest{Host: "169.254.169.254", Port: 80})
		var refusal *tcpforward.OpenError
		passed := errors.As(err, &refusal) && refusal.Code == "policy_rejected"
		_ = emit(map[string]any{"event": "mux_isolation", "mode": "policy_error", "passed": passed})
		if !passed {
			results <- errors.New("policy isolation failed")
			return
		}
		results <- nil
	}()
	var lock sync.Mutex
	var rtts []float64
	for _, stream := range streams[1:] {
		go func() {
			payload, response := make([]byte, 128), make([]byte, 128)
			offset := int64(0)
			for time.Now().Before(until) {
				muxFill(payload, stream.Stats().ID, offset)
				offset += 128
				begin := time.Now()
				if _, err := stream.Write(payload); err != nil {
					results <- err
					return
				}
				if _, err := io.ReadFull(stream, response); err != nil {
					results <- err
					return
				}
				if !bytes.Equal(payload, response) {
					results <- errors.New("cross-stream interactive mismatch")
					return
				}
				lock.Lock()
				if len(rtts) < 4096 {
					rtts = append(rtts, float64(time.Since(begin))/float64(time.Millisecond))
				}
				lock.Unlock()
				timer := time.NewTimer(time.Second)
				select {
				case <-timer.C:
				case <-ctx.Done():
					timer.Stop()
					results <- ctx.Err()
					return
				}
			}
			if err := stream.CloseWrite(); err != nil {
				results <- err
				return
			}
			count, err := stream.Read(response)
			if count != 0 || err != io.EOF {
				results <- errors.New("interactive final EOF mismatch")
				return
			}
			err = stream.Close()
			_ = emit(map[string]any{"event": "mux_stream", "stream": stream.Stats(), "passed": err == nil})
			results <- err
		}()
	}
	go func() {
		for time.Now().Before(until) {
			if err := muxDNSProof(ctx, mux, emit); err != nil {
				results <- err
				return
			}
			timer := time.NewTimer(5 * time.Second)
			select {
			case <-timer.C:
			case <-ctx.Done():
				timer.Stop()
				results <- ctx.Err()
				return
			}
		}
		results <- nil
	}()
	var failure error
	for range 7 {
		if err := <-results; err != nil {
			failure = err
			cancel()
		}
	}
	_ = emit(map[string]any{"event": "mux_interactive", "latency": muxPercentiles(rtts), "seconds": time.Since(started).Seconds(), "passed": failure == nil})
	return failure
}
