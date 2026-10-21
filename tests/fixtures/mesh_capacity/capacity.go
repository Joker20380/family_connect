package main

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/reliablestream"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
	"github.com/Joker20380/family_connect/carrier/telemost"
)

type capacityConfig struct {
	Mode          string
	Run           uint64
	Count         int
	Sizes         []int
	Rate          int
	Seconds       int
	SendWindow    int
	ReceiveWindow int
	Reverse       bool
}

func (config capacityConfig) size(index int) int { return config.Sizes[index%len(config.Sizes)] }

func (config capacityConfig) validate() error {
	if config.Run == 0 || config.Count < 1 || config.Count > 8192 || config.Rate < 0 || config.Rate > 1000000 || config.Seconds < 0 || config.Seconds > 30 || len(config.Sizes) < 1 || len(config.Sizes) > 16 {
		return errors.New("capacity bounds")
	}
	if config.Mode != "C" && config.Mode != "R" && config.Mode != "T" && config.Mode != "P" {
		return errors.New("capacity mode")
	}
	for _, size := range config.Sizes {
		if size < 64 || size > 16448 {
			return errors.New("capacity size")
		}
	}
	if config.SendWindow != 8 && config.SendWindow != 16 && config.SendWindow != 32 {
		return errors.New("capacity window")
	}
	if config.ReceiveWindow != 16 && config.ReceiveWindow != 32 {
		return errors.New("capacity receive window")
	}
	if config.Mode == "C" && (config.Rate == 0 || config.Seconds == 0) {
		return errors.New("raw must be rate bounded")
	}
	return nil
}

func capacityTemplate(run uint64) []byte {
	data := make([]byte, 65536)
	state := run ^ 0x9e3779b97f4a7c15
	for index := range data {
		state ^= state << 13
		state ^= state >> 7
		state ^= state << 17
		data[index] = byte(state >> 24)
	}
	return data
}

func capacityPacket(buffer, template []byte, run uint64, index, size int, kind byte) []byte {
	packet := buffer[:size]
	copy(packet, "FCAP")
	packet[4] = kind
	clear(packet[5:8])
	binary.BigEndian.PutUint64(packet[8:], run)
	binary.BigEndian.PutUint64(packet[16:], uint64(index))
	binary.BigEndian.PutUint64(packet[24:], uint64(size))
	copy(packet[32:], template[:size-32])
	return packet
}

func capacityValid(packet, template []byte, run uint64) bool {
	return len(packet) >= 32 && string(packet[:4]) == "FCAP" && binary.BigEndian.Uint64(packet[8:]) == run && binary.BigEndian.Uint64(packet[24:]) == uint64(len(packet)) && bytes.Equal(packet[32:], template[:len(packet)-32])
}

type capacityEndpoint struct {
	familysession.PacketEndpoint
	sendMutex sync.Mutex
	mutex     sync.Mutex
	Messages  map[int]uint64
	Data      map[int]uint64
	Records   map[int]uint64
	TLS       bool
	next      uint64
	pending   []byte
	EnqueueNS int64
}

func (endpoint *capacityEndpoint) SendContext(ctx context.Context, data []byte) error {
	endpoint.sendMutex.Lock()
	defer endpoint.sendMutex.Unlock()
	started := time.Now()
	err := endpoint.PacketEndpoint.SendContext(ctx, data)
	endpoint.mutex.Lock()
	defer endpoint.mutex.Unlock()
	endpoint.EnqueueNS += time.Since(started).Nanoseconds()
	if err != nil {
		return err
	}
	endpoint.Messages[len(data)]++
	if len(data) >= 64 && string(data[:4]) == "FRS1" && data[4] == 2 {
		endpoint.Data[len(data)-64]++
		sequence := binary.BigEndian.Uint64(data[40:])
		if endpoint.TLS && sequence == endpoint.next {
			endpoint.next++
			endpoint.pending = append(endpoint.pending, data[64:]...)
			for len(endpoint.pending) >= 5 {
				size := int(binary.BigEndian.Uint16(endpoint.pending[3:5])) + 5
				if size > 18437 {
					break
				}
				if len(endpoint.pending) < size {
					break
				}
				endpoint.Records[size]++
				endpoint.pending = endpoint.pending[size:]
			}
		}
	}
	return nil
}

func (endpoint *capacityEndpoint) snapshot() map[string]any {
	endpoint.mutex.Lock()
	defer endpoint.mutex.Unlock()
	clone := func(source map[int]uint64) map[int]uint64 {
		result := map[int]uint64{}
		for size, count := range source {
			result[size] = count
		}
		return result
	}
	return map[string]any{"carrier_messages": clone(endpoint.Messages), "rs_data_attempts": clone(endpoint.Data), "tls_records_unique": clone(endpoint.Records), "enqueue_wait_ns": endpoint.EnqueueNS}
}

func capacityRun(ctx context.Context, session *telemost.Session, path, credentialsPath string, server bool, emit func(map[string]any) error) error {
	raw, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	var config capacityConfig
	if err = json.Unmarshal(raw, &config); err != nil {
		return err
	}
	if err = config.validate(); err != nil {
		return err
	}
	endpoint := &capacityEndpoint{PacketEndpoint: session, Messages: map[int]uint64{}, Data: map[int]uint64{}, Records: map[int]uint64{}, TLS: config.Mode == "T" || config.Mode == "P"}
	var data familysession.PacketEndpoint = endpoint
	reliability := reliablestream.DefaultConfig()
	reliability.SendWindow, reliability.ReceiveWindow = config.SendWindow, config.ReceiveWindow
	var reliableStats func() any = func() any { return nil }
	if config.Mode == "R" {
		stream, openErr := reliablestream.New(ctx, endpoint, reliability)
		if openErr != nil {
			return openErr
		}
		defer stream.Close()
		data = stream
		reliableStats = func() any { return stream.Stats() }
	} else if config.Mode == "T" || config.Mode == "P" {
		credentials, readErr := os.ReadFile(credentialsPath)
		if readErr != nil {
			return readErr
		}
		secured, openErr := familysession.OpenReliable(ctx, endpoint, credentials, server, reliability)
		clear(credentials)
		if openErr != nil {
			return openErr
		}
		defer secured.Close()
		data = secured
		reliableStats = func() any { return secured.ReliabilityStats() }
	}
	snapshot := func() map[string]any {
		result := session.PerformanceSnapshot()
		result["reliability"] = reliableStats()
		result["histograms"] = endpoint.snapshot()
		return result
	}
	_ = emit(map[string]any{"event": "capacity_config", "config": config, "reliability_config": reliability, "server": server})
	sampleContext, stop := context.WithCancel(ctx)
	var samples sync.WaitGroup
	samples.Add(1)
	go func() {
		defer samples.Done()
		ticker := time.NewTicker(time.Second)
		defer ticker.Stop()
		for {
			select {
			case <-sampleContext.Done():
				return
			case <-ticker.C:
				_ = emit(map[string]any{"event": "capacity_sample", "transport": snapshot()})
			}
		}
	}()
	defer func() {
		stop()
		samples.Wait()
		_ = emit(map[string]any{"event": "capacity_final", "transport": snapshot()})
	}()
	if config.Mode == "P" {
		mux, openErr := tcpforward.NewMux(ctx, data.(*familysession.Session), server, tcpforward.MuxConfig{Policy: tcpforward.Policy{TestOnlyLoopbackPort: 18764}})
		if openErr != nil {
			return openErr
		}
		defer mux.Close()
		if server {
			return mux.Wait()
		}
		return muxHostCompare(ctx, mux, 18764, snapshot, emit)
	}
	transferContext, cancel := context.WithTimeout(ctx, 180*time.Second)
	defer cancel()
	if server != config.Reverse {
		return capacitySend(transferContext, data, session, config, emit)
	}
	return capacityReceive(transferContext, data, config, emit)
}

func capacitySend(ctx context.Context, endpoint familysession.PacketEndpoint, session *telemost.Session, config capacityConfig, emit func(map[string]any) error) error {
	template, buffer := capacityTemplate(config.Run), make([]byte, 65536)
	for {
		packet, err := endpoint.Recv(ctx)
		if err != nil {
			return err
		}
		if !capacityValid(packet, template, config.Run) {
			return errors.New("invalid setup")
		}
		if packet[4] == 2 {
			break
		}
		if packet[4] != 1 {
			return errors.New("invalid setup kind")
		}
		if err = endpoint.SendContext(ctx, packet); err != nil {
			return err
		}
	}
	started := time.Now()
	type receipt struct {
		packet []byte
		err    error
	}
	reports := make(chan receipt, 1)
	go func() {
		for {
			packet, err := endpoint.Recv(ctx)
			if err == nil && capacityValid(packet, template, config.Run) && packet[4] == 5 {
				if err = endpoint.SendContext(ctx, packet); err == nil {
					continue
				}
			}
			reports <- receipt{packet, err}
			return
		}
	}()
	sent, useful, offered := 0, 0, 0
	var sendErr error
	for index := 0; index < config.Count; index++ {
		size := config.size(index)
		if config.Rate > 0 {
			wait := time.Until(started.Add(time.Duration(float64(offered) / float64(config.Rate) * float64(time.Second))))
			if wait > 0 {
				select {
				case <-ctx.Done():
					sendErr = ctx.Err()
				case <-time.After(wait):
				}
				if sendErr != nil {
					break
				}
			}
		}
		if config.Mode == "C" && session.Stats().SendQueueDepth > 48 {
			sendErr = errors.New("raw queue safety stop")
			break
		}
		offered += size
		packet := capacityPacket(buffer, template, config.Run, index, size, 3)
		if sendErr = endpoint.SendContext(ctx, packet); sendErr != nil {
			break
		}
		sent++
		useful += size - 32
	}
	seconds := time.Since(started).Seconds()
	_ = emit(map[string]any{"event": "capacity_sent", "count": sent, "expected": config.Count, "useful_bytes": useful, "offered_bytes": offered, "seconds": seconds, "error": fmt.Sprint(sendErr)})
	if sendErr != nil {
		return sendErr
	}
	select {
	case <-ctx.Done():
		return ctx.Err()
	case result := <-reports:
		if result.err != nil {
			return result.err
		}
		if !capacityValid(result.packet, template, config.Run) || result.packet[4] != 4 {
			return errors.New("invalid final receipt")
		}
		count := binary.BigEndian.Uint64(result.packet[16:])
		_ = emit(map[string]any{"event": "capacity_confirmed", "count": count, "expected": config.Count, "complete_seconds": time.Since(started).Seconds()})
		if err := endpoint.SendContext(ctx, result.packet); err != nil {
			return err
		}
		select {
		case <-time.After(2 * time.Second):
		case <-ctx.Done():
		}
		if config.Mode != "C" && int(count) != config.Count {
			return errors.New("reliable incomplete")
		}
		return nil
	}
}

func capacityReceive(ctx context.Context, endpoint familysession.PacketEndpoint, config capacityConfig, emit func(map[string]any) error) error {
	template, buffer := capacityTemplate(config.Run), make([]byte, 65536)
	for index := 0; index < 3; index++ {
		started := time.Now()
		if err := endpoint.SendContext(ctx, capacityPacket(buffer, template, config.Run, index, 32, 1)); err != nil {
			return err
		}
		packet, err := endpoint.Recv(ctx)
		if err != nil {
			return err
		}
		if !capacityValid(packet, template, config.Run) || packet[4] != 1 || binary.BigEndian.Uint64(packet[16:]) != uint64(index) {
			return errors.New("probe mismatch")
		}
		_ = emit(map[string]any{"event": "capacity_probe", "bytes": 32, "rtt_seconds": time.Since(started).Seconds()})
	}
	started := time.Now()
	if err := endpoint.SendContext(ctx, capacityPacket(buffer, template, config.Run, 0, 32, 2)); err != nil {
		return err
	}
	seen := make([]bool, config.Count)
	count, useful, duplicates, corrupt, late := 0, 0, 0, 0, 0
	first, last := 0.0, 0.0
	var arrivals []float64
	var loadedRTT []float64
	probes := map[int]time.Time{}
	lastProbe := time.Now()
	receiveContext := ctx
	stop := func() {}
	if config.Mode == "C" {
		receiveContext, stop = context.WithTimeout(ctx, time.Duration(config.Seconds+12)*time.Second)
	}
	defer stop()
	var readErr error
	for {
		packet, err := endpoint.Recv(receiveContext)
		if err != nil {
			readErr = err
			break
		}
		if !capacityValid(packet, template, config.Run) {
			corrupt++
			continue
		}
		if packet[4] == 5 {
			probeID := int(binary.BigEndian.Uint64(packet[16:]))
			if sent, ok := probes[probeID]; ok {
				loadedRTT = append(loadedRTT, time.Since(sent).Seconds())
				delete(probes, probeID)
			}
			continue
		}
		if packet[4] != 3 {
			corrupt++
			continue
		}
		index := int(binary.BigEndian.Uint64(packet[16:]))
		if index < 0 || index >= config.Count || len(packet) != config.size(index) {
			corrupt++
			continue
		}
		if seen[index] {
			duplicates++
			continue
		}
		seen[index] = true
		count++
		useful += len(packet) - 32
		elapsed := time.Since(started).Seconds()
		if count == 1 {
			first = elapsed
		}
		last = elapsed
		arrivals = append(arrivals, elapsed)
		if config.Mode == "C" && elapsed > float64(config.Seconds) {
			late++
		}
		if time.Since(lastProbe) > time.Second && len(probes) < 4 {
			lastProbe = time.Now()
			probes[count] = lastProbe
			if err := endpoint.SendContext(ctx, capacityPacket(buffer, template, config.Run, count, 32, 5)); err != nil {
				readErr = err
				break
			}
		}
		if count == config.Count {
			break
		}
	}
	missing := []int{}
	for index, present := range seen {
		if !present {
			missing = append(missing, index)
		}
	}
	_ = emit(map[string]any{"event": "capacity_received", "count": count, "expected": config.Count, "useful_bytes": useful, "missing_ids": missing, "duplicates": duplicates, "corrupt": corrupt, "late_after_offer_seconds": late, "first_seconds": first, "last_seconds": last, "observation_seconds": time.Since(started).Seconds(), "arrivals_seconds": arrivals, "loaded_rtt_seconds": loadedRTT, "unanswered_probes": len(probes), "error": fmt.Sprint(readErr)})
	if corrupt > 0 {
		return errors.New("corrupt payload")
	}
	if config.Mode != "C" && count != config.Count {
		return errors.New("reliable incomplete")
	}
	if err := endpoint.SendContext(ctx, capacityPacket(buffer, template, config.Run, count, 32, 4)); err != nil {
		return err
	}
	for {
		packet, err := endpoint.Recv(ctx)
		if err != nil {
			return err
		}
		if !capacityValid(packet, template, config.Run) {
			return errors.New("confirmation corrupt")
		}
		if packet[4] == 4 {
			break
		}
		if packet[4] != 5 && packet[4] != 3 {
			return errors.New("confirmation missing")
		}
	}
	return emit(map[string]any{"event": "capacity_complete", "seconds": time.Since(started).Seconds(), "complete": count == config.Count})
}
