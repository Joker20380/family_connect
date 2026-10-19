//go:build linux

package tcpforward

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"os"
	"runtime"
	"sort"
	"strconv"
	"sync"
	"syscall"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/reliablestream"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

type meshPerfPacket struct {
	data          []byte
	queued, ready time.Time
}

type meshPerfEndpoint struct {
	ctx                                   context.Context
	incoming, outgoing                    chan meshPerfPacket
	delay                                 time.Duration
	mu                                    sync.Mutex
	next                                  time.Time
	bytes, frames, segments, segmentBytes uint64
	highWater                             int
	residence, ackIntervals               []float64
	lastACK                               time.Time
}

func (endpoint *meshPerfEndpoint) SendContext(ctx context.Context, data []byte) error {
	endpoint.mu.Lock()
	defer endpoint.mu.Unlock()
	now := time.Now()
	if endpoint.next.Before(now) {
		endpoint.next = now
	}
	fragments := (len(data) + 8191) / 8192
	ready := endpoint.next.Add(time.Duration(fragments-1) * 2 * time.Millisecond)
	endpoint.next = ready.Add(2 * time.Millisecond)
	select {
	case endpoint.outgoing <- meshPerfPacket{bytes.Clone(data), now, ready.Add(endpoint.delay)}:
		endpoint.bytes += uint64(len(data))
		endpoint.frames += uint64(fragments)
		endpoint.highWater = max(endpoint.highWater, len(endpoint.outgoing))
		if len(endpoint.residence) < 4096 {
			endpoint.residence = append(endpoint.residence, ready.Sub(now).Seconds()*1000)
		}
		if len(data) >= 64 && string(data[:4]) == "FRS1" && data[4] == 2 {
			endpoint.segments++
			endpoint.segmentBytes += uint64(len(data) - 64)
		}
		return nil
	case <-ctx.Done():
		return ctx.Err()
	case <-endpoint.ctx.Done():
		return endpoint.ctx.Err()
	}
}

func (endpoint *meshPerfEndpoint) Recv(ctx context.Context) ([]byte, error) {
	select {
	case packet := <-endpoint.incoming:
		timer := time.NewTimer(time.Until(packet.ready))
		defer timer.Stop()
		select {
		case <-timer.C:
			if len(packet.data) >= 64 && string(packet.data[:4]) == "FRS1" && packet.data[4] == 3 {
				endpoint.mu.Lock()
				if !endpoint.lastACK.IsZero() && len(endpoint.ackIntervals) < 4096 {
					endpoint.ackIntervals = append(endpoint.ackIntervals, time.Since(endpoint.lastACK).Seconds()*1000)
				}
				endpoint.lastACK = time.Now()
				endpoint.mu.Unlock()
			}
			return packet.data, nil
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-endpoint.ctx.Done():
			return nil, endpoint.ctx.Err()
		}
	case <-ctx.Done():
		return nil, ctx.Err()
	case <-endpoint.ctx.Done():
		return nil, endpoint.ctx.Err()
	}
}

func (endpoint *meshPerfEndpoint) Close() error { return nil }

func meshPerfQuantiles(samples []float64) []float64 {
	if len(samples) == 0 {
		return nil
	}
	values := append([]float64(nil), samples...)
	sort.Float64s(values)
	return []float64{values[(len(values)-1)*50/100], values[(len(values)-1)*95/100], values[(len(values)-1)*99/100]}
}

func (endpoint *meshPerfEndpoint) snapshot(reset bool) map[string]any {
	endpoint.mu.Lock()
	defer endpoint.mu.Unlock()
	result := map[string]any{"endpoint_bytes": endpoint.bytes, "modeled_frames": endpoint.frames, "data_segments": endpoint.segments, "segment_bytes": endpoint.segmentBytes, "queue_high_water_messages": endpoint.highWater, "modeled_queue_ms_p50_p95_p99": meshPerfQuantiles(endpoint.residence), "ack_interval_ms_p50_p95_p99": meshPerfQuantiles(endpoint.ackIntervals)}
	if reset {
		endpoint.bytes, endpoint.frames, endpoint.segments, endpoint.segmentBytes = 0, 0, 0, 0
		endpoint.highWater, endpoint.residence, endpoint.ackIntervals, endpoint.lastACK = 0, nil, nil, time.Time{}
	}
	return result
}

func meshPerfStack(test *testing.T, ctx context.Context, layer string, delay time.Duration) (familysession.PacketEndpoint, familysession.PacketEndpoint, []*meshPerfEndpoint, []func() reliablestream.Stats) {
	test.Helper()
	forward, reverse := make(chan meshPerfPacket, 256), make(chan meshPerfPacket, 256)
	left := &meshPerfEndpoint{ctx: ctx, incoming: reverse, outgoing: forward, delay: delay}
	right := &meshPerfEndpoint{ctx: ctx, incoming: forward, outgoing: reverse, delay: delay}
	links := []*meshPerfEndpoint{left, right}
	clientContext, serverContext := ctx, ctx
	if os.Getenv("MESH_PERF_TRACE") == "1" {
		identifier := "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
		clientContext = sessiontrace.With(ctx, sessiontrace.New(identifier, nil))
		serverContext = sessiontrace.With(ctx, sessiontrace.New(identifier, nil))
	}
	if layer == "carrier_model" {
		return left, right, links, nil
	}
	if layer == "reliable" {
		client, err := reliablestream.New(clientContext, left, reliablestream.DefaultConfig())
		if err != nil {
			test.Fatal(err)
		}
		server, err := reliablestream.New(serverContext, right, reliablestream.DefaultConfig())
		if err != nil {
			test.Fatal(err)
		}
		return client, server, links, []func() reliablestream.Stats{client.Stats, server.Stats}
	}
	clientProfile, serverProfile := testCredentials(test)
	type opened struct {
		session *familysession.Session
		err     error
	}
	ready := make(chan opened, 1)
	go func() {
		session, err := familysession.Open(serverContext, right, serverProfile, true)
		ready <- opened{session, err}
	}()
	client, err := familysession.Open(clientContext, left, clientProfile, false)
	if err != nil {
		test.Fatal(err)
	}
	server := <-ready
	if server.err != nil {
		test.Fatal(server.err)
	}
	return client, server.session, links, []func() reliablestream.Stats{client.ReliabilityStats, server.session.ReliabilityStats}
}

func meshPerfPayload(size int) []byte {
	payload := make([]byte, size)
	for index := range payload {
		payload[index] = byte(index*31 + 17)
	}
	return payload
}

func meshPerfPackets(ctx context.Context, sender, receiver familysession.PacketEndpoint, size int) error {
	done := make(chan error, 1)
	const count = 128
	payload := meshPerfPayload(size)
	go func() {
		for range count {
			if err := sender.SendContext(ctx, payload); err != nil {
				done <- err
				return
			}
		}
		done <- nil
	}()
	expected := bytes.Repeat(payload, count)
	received := make([]byte, 0, len(expected))
	for len(received) < len(expected) {
		data, err := receiver.Recv(ctx)
		if err != nil {
			return err
		}
		received = append(received, data...)
	}
	if !bytes.Equal(received, expected) {
		return fmt.Errorf("byte mismatch")
	}
	return <-done
}

func meshPerfTCP(test *testing.T, ctx context.Context, clientSession, serverSession *familysession.Session, flows, size int, download bool) (func() error, *[]float64, *[]float64, func() any) {
	test.Helper()
	payload := meshPerfPayload(size)
	targetDone := make(chan error, flows)
	port := muxFixture(test, func(connection *net.TCPConn) {
		mode := make([]byte, 1)
		if _, err := io.ReadFull(connection, mode); err != nil {
			return
		}
		if mode[0] == 0 {
			io.Copy(connection, connection)
			return
		}
		if download {
			_, err := io.Copy(connection, bytes.NewReader(payload))
			targetDone <- err
		} else {
			body := make([]byte, len(payload))
			_, err := io.ReadFull(connection, body)
			if err == nil && !bytes.Equal(body, payload) {
				err = fmt.Errorf("target mismatch")
			}
			targetDone <- err
		}
	})
	client, err := NewMux(ctx, clientSession, false, MuxConfig{})
	if err != nil {
		test.Fatal(err)
	}
	server, err := NewMux(ctx, serverSession, true, MuxConfig{Policy: Policy{TestOnlyLoopbackPort: port}})
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() { client.Close(); server.Close() })
	probe := muxOpen(test, ctx, client, port)
	if _, err := probe.Write([]byte{0}); err != nil {
		test.Fatal(err)
	}
	ping := func() (float64, error) {
		start := time.Now()
		if _, err := probe.Write([]byte{42}); err != nil {
			return 0, err
		}
		body := make([]byte, 1)
		_, err := io.ReadFull(probe, body)
		if err == nil && body[0] != 42 {
			err = fmt.Errorf("ping mismatch")
		}
		return time.Since(start).Seconds() * 1000, err
	}
	idle, loaded := []float64{}, []float64{}
	for range 8 {
		elapsed, err := ping()
		if err != nil {
			test.Fatal(err)
		}
		idle = append(idle, elapsed)
	}
	streams := make([]*MuxStream, flows)
	for index := range streams {
		streams[index] = muxOpen(test, ctx, client, port)
	}
	work := func() error {
		done := make(chan error, flows)
		stop := make(chan struct{})
		probeDone := make(chan error, 1)
		go func() {
			for {
				select {
				case <-stop:
					probeDone <- nil
					return
				default:
				}
				elapsed, err := ping()
				if err != nil {
					probeDone <- err
					return
				}
				loaded = append(loaded, elapsed)
			}
		}()
		for _, stream := range streams {
			go func(stream *MuxStream) {
				if _, err := stream.Write([]byte{1}); err != nil {
					done <- err
					return
				}
				if download {
					body := make([]byte, len(payload))
					_, err := io.ReadFull(stream, body)
					if err == nil && !bytes.Equal(body, payload) {
						err = fmt.Errorf("client mismatch")
					}
					done <- err
				} else {
					_, err := io.Copy(stream, bytes.NewReader(payload))
					done <- err
				}
			}(stream)
		}
		var failure error
		for range flows {
			if err := <-done; err != nil {
				failure = err
			}
		}
		if failure == nil {
			for range flows {
				if err := <-targetDone; err != nil {
					failure = err
				}
			}
		}
		close(stop)
		if err := <-probeDone; err != nil {
			failure = err
		}
		return failure
	}
	return work, &idle, &loaded, func() any { return []MuxStats{client.Stats(), server.Stats()} }
}

func TestMeshPerformanceMatrix(test *testing.T) {
	if os.Getenv("MESH_PERF") != "1" {
		test.Skip("opt-in offline measurement: MESH_PERF=1")
	}
	delayMS := 40
	tcpSize := 128 << 10
	if value := os.Getenv("MESH_PERF_TCP_KIB"); value != "" {
		parsed, err := strconv.Atoi(value)
		if err != nil || parsed < 128 || parsed > 1024 {
			test.Fatal("MESH_PERF_TCP_KIB must be 128..1024")
		}
		tcpSize = parsed << 10
	}
	if value := os.Getenv("MESH_PERF_DELAY_MS"); value != "" {
		parsed, err := strconv.Atoi(value)
		if err != nil || parsed < 1 || parsed > 150 {
			test.Fatal("MESH_PERF_DELAY_MS must be 1..150")
		}
		delayMS = parsed
	}
	for _, layer := range []string{"carrier_model", "reliable", "family", "mux"} {
		for _, size := range []int{384, 1024, 16336, 16384} {
			if layer == "mux" && size != 16384 {
				continue
			}
			for _, direction := range []string{"upload", "download"} {
				flowsList := []int{1}
				if layer == "mux" {
					flowsList = []int{1, 4}
				}
				for _, flows := range flowsList {
					test.Run(fmt.Sprintf("%s/%d/%s/%d", layer, size, direction, flows), func(test *testing.T) {
						ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
						defer cancel()
						client, server, links, stats := meshPerfStack(test, ctx, layer, time.Duration(delayMS)*time.Millisecond)
						defer client.Close()
						defer server.Close()
						if err := client.SendContext(ctx, []byte{1}); err != nil {
							test.Fatal(err)
						}
						if _, err := server.Recv(ctx); err != nil {
							test.Fatal(err)
						}
						if err := server.SendContext(ctx, []byte{2}); err != nil {
							test.Fatal(err)
						}
						if _, err := client.Recv(ctx); err != nil {
							test.Fatal(err)
						}
						time.Sleep(time.Duration(2*delayMS+10) * time.Millisecond)
						var idle, loaded *[]float64
						var muxStats func() any
						payloadBytes := size * 128
						work := func() error {
							if direction == "download" {
								return meshPerfPackets(ctx, server, client, size)
							}
							return meshPerfPackets(ctx, client, server, size)
						}
						if layer == "mux" {
							work, idle, loaded, muxStats = meshPerfTCP(test, ctx, client.(*familysession.Session), server.(*familysession.Session), flows, tcpSize, direction == "download")
							payloadBytes = tcpSize * flows
						}
						before := make([]reliablestream.Stats, len(stats))
						for index, read := range stats {
							before[index] = read()
						}
						for _, link := range links {
							link.snapshot(true)
						}
						sampleStop, sampleDone := make(chan struct{}), make(chan struct{})
						windowSamples, pendingSum, fullSamples := make([]int, len(stats)), make([]int, len(stats)), make([]int, len(stats))
						go func() {
							defer close(sampleDone)
							ticker := time.NewTicker(10 * time.Millisecond)
							defer ticker.Stop()
							for {
								select {
								case <-sampleStop:
									return
								case <-ticker.C:
									for index, read := range stats {
										flow := read().Flow
										windowSamples[index]++
										pendingSum[index] += int(flow.SendNext - flow.SendBase)
										if flow.SendNext-flow.SendBase == 8 {
											fullSamples[index]++
										}
									}
								}
							}
						}()
						var cpuBefore, cpuAfter syscall.Rusage
						var memoryBefore, memoryAfter runtime.MemStats
						syscall.Getrusage(syscall.RUSAGE_SELF, &cpuBefore)
						runtime.ReadMemStats(&memoryBefore)
						start := time.Now()
						err := work()
						duration := time.Since(start)
						close(sampleStop)
						<-sampleDone
						syscall.Getrusage(syscall.RUSAGE_SELF, &cpuAfter)
						runtime.ReadMemStats(&memoryAfter)
						if err != nil {
							test.Fatal(err)
						}
						cpuSeconds := func(value syscall.Rusage) float64 {
							return float64(value.Utime.Sec+value.Stime.Sec) + float64(value.Utime.Usec+value.Stime.Usec)/1e6
						}
						row := map[string]any{"source_label": os.Getenv("MESH_PERF_SOURCE"), "case": test.Name(), "synthetic": true, "one_way_ms": delayMS, "loss_percent": 0, "payload_bytes": payloadBytes, "duration_s": duration.Seconds(), "goodput_mbps": float64(payloadBytes) * 8 / duration.Seconds() / 1e6, "wire_bitrate": nil, "trace": os.Getenv("MESH_PERF_TRACE"), "cpu_one_core_percent": 100 * (cpuSeconds(cpuAfter) - cpuSeconds(cpuBefore)) / duration.Seconds(), "allocated_bytes": memoryAfter.TotalAlloc - memoryBefore.TotalAlloc, "allocations": memoryAfter.Mallocs - memoryBefore.Mallocs, "client": links[0].snapshot(false), "gateway": links[1].snapshot(false), "byte_exact": true}
						if idle != nil {
							row["idle_rtt_ms_p50_p95_p99"] = meshPerfQuantiles(*idle)
							row["loaded_rtt_ms_p50_p95_p99"] = meshPerfQuantiles(*loaded)
							row["loaded_samples"] = len(*loaded)
							row["idle_samples"] = len(*idle)
							row["mux"] = muxStats()
						}
						for index, read := range stats {
							after := read()
							row[fmt.Sprintf("reliable_%d", index)] = map[string]any{"data_sent": after.DataSent - before[index].DataSent, "retransmissions": after.Retransmissions - before[index].Retransmissions, "send_high_water_lifetime": after.SendHighWater, "flow_at_end": after.Flow, "window_samples": windowSamples[index], "pending_sum": pendingSum[index], "full_window_samples": fullSamples[index]}
						}
						encoded, err := json.Marshal(row)
						if err != nil {
							test.Fatal(err)
						}
						test.Logf("MESH_PERF %s", encoded)
					})
				}
			}
		}
	}
}

func TestMeshSendCompletionIsNotRemoteACK(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	client, server, _, stats := meshPerfStack(test, ctx, "reliable", time.Millisecond)
	defer client.Close()
	defer server.Close()
	for index := 0; index < 8; index++ {
		if err := client.SendContext(ctx, []byte{byte(index)}); err != nil {
			test.Fatal(err)
		}
	}
	flow := stats[0]().Flow
	if flow.SendNext-flow.SendBase != 8 {
		test.Fatal("eight unconsumed segments must remain in flight", flow)
	}
	for index := 0; index < 8; index++ {
		data, err := server.Recv(ctx)
		if err != nil || !bytes.Equal(data, []byte{byte(index)}) {
			test.Fatal("delivery", err)
		}
	}
}

func TestMeshModelFrameAccounting(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	endpoint := &meshPerfEndpoint{ctx: ctx, outgoing: make(chan meshPerfPacket, 8)}
	data := make([]byte, 64+16384)
	copy(data, "FRS1")
	data[4] = 2
	binary.BigEndian.PutUint16(data[6:], 16384)
	if err := endpoint.SendContext(ctx, data); err != nil {
		test.Fatal(err)
	}
	if endpoint.frames != 3 || endpoint.segments != 1 || endpoint.segmentBytes != 16384 {
		test.Fatal(endpoint.snapshot(false))
	}
}
