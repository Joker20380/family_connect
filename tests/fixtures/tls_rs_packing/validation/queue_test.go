package familysession

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"github.com/Joker20380/family_connect/carrier/reliablestream"
	"net"
	"reflect"
	"runtime"
	"sync"
	"testing"
	"time"
	"unsafe"
)

type packingStalledCarrier struct {
	PacketEndpoint
	ctx              context.Context
	cancel           context.CancelFunc
	queue            chan []byte
	done             chan struct{}
	mu               sync.Mutex
	armed, stalled   bool
	entered, release chan struct{}
}

func (endpoint *packingStalledCarrier) SendContext(ctx context.Context, data []byte) error {
	select {
	case endpoint.queue <- bytes.Clone(data):
		return nil
	case <-ctx.Done():
		return ctx.Err()
	case <-endpoint.ctx.Done():
		return endpoint.ctx.Err()
	}
}
func (endpoint *packingStalledCarrier) run() {
	defer close(endpoint.done)
	for {
		select {
		case <-endpoint.ctx.Done():
			return
		case data := <-endpoint.queue:
			endpoint.mu.Lock()
			stall := endpoint.armed && !endpoint.stalled && len(data) >= 64 && data[4] == 2
			if stall {
				endpoint.stalled = true
				close(endpoint.entered)
			}
			endpoint.mu.Unlock()
			if stall {
				select {
				case <-endpoint.release:
				case <-endpoint.ctx.Done():
					return
				}
			}
			if endpoint.PacketEndpoint.SendContext(endpoint.ctx, data) != nil {
				return
			}
		}
	}
}
func (endpoint *packingStalledCarrier) Close() error {
	endpoint.cancel()
	err := endpoint.PacketEndpoint.Close()
	<-endpoint.done
	return err
}
func TestPackingPreWriteRetryControl(test *testing.T) {
	for _, window := range []int{8, 32} {
		for _, policy := range []string{"A", "B2"} {
			test.Run(fmt.Sprintf("%s%d", policy, window), func(test *testing.T) {
				ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
				defer cancel()
				left, right := pair()
				carrierContext, carrierCancel := context.WithCancel(ctx)
				carrier := &packingStalledCarrier{PacketEndpoint: left, ctx: carrierContext, cancel: carrierCancel, queue: make(chan []byte, 256), done: make(chan struct{}), entered: make(chan struct{}), release: make(chan struct{})}
				go carrier.run()
				clientProfile, serverProfile := profiles(test)
				config := reliablestream.DefaultConfig()
				config.SendWindow = window
				if window == 32 {
					config.ReceiveWindow = 32
				}
				ready := make(chan *Session, 1)
				go func() {
					session, _ := OpenReliable(WithLabPacking(ctx, policy), right, encoded(serverProfile), true, config)
					ready <- session
				}()
				sender, err := OpenReliable(WithLabPacking(ctx, policy), carrier, encoded(clientProfile), false, config)
				if err != nil {
					test.Fatal(err)
				}
				defer sender.Close()
				receiver := <-ready
				if receiver == nil {
					test.Fatal("handshake")
				}
				defer receiver.Close()
				if err = sender.LabDrain(ctx); err != nil {
					test.Fatal(err)
				}
				carrier.mu.Lock()
				carrier.armed = true
				carrier.mu.Unlock()
				complete := make(chan error, 1)
				go func() {
					for index := 0; index < 64; index++ {
						if err := sender.SendContext(ctx, bytes.Repeat([]byte{byte(index)}, 16384)); err != nil {
							complete <- err
							return
						}
					}
					complete <- nil
				}()
				<-carrier.entered
				time.Sleep(2200 * time.Millisecond)
				before := sender.ReliabilityStats()
				packing := sender.LabPackingStats()
				close(carrier.release)
				for index := 0; index < 64; index++ {
					actual, err := receiver.Recv(ctx)
					if err != nil || !bytes.Equal(actual, bytes.Repeat([]byte{byte(index)}, 16384)) {
						test.Fatal(index, err)
					}
				}
				if err = <-complete; err != nil {
					test.Fatal(err)
				}
				result, _ := json.Marshal(map[string]any{"policy": policy, "window": window, "before_first_actual_carrier_write": before, "packing": packing, "complete": true, "coalescer_struct_bytes": unsafe.Sizeof(labPackingConn{}), "owned_data_buffer_bytes_B": 5 * 16384, "old_reader_buffer_bytes_A": 65536})
				test.Log(string(result))
				if before.Retransmissions > uint64(3*window) || packing.MaxQueueBytes > 65536 {
					test.Fatal("unbounded pre-write accumulation")
				}
			})
		}
	}
}

func TestPackingCalibration(test *testing.T) {
	for _, policy := range []string{"A", "B0", "B2"} {
		test.Run(policy, func(test *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
			defer cancel()
			connection := bridge(WithLabPacking(ctx, policy), packingSink{send: func(context.Context, []byte) error { return nil }})
			defer connection.Close()
			large, small := make([]byte, 16406), make([]byte, 34)
			large[0], small[0] = 23, 23
			binary.BigEndian.PutUint16(large[3:5], uint16(len(large)-5))
			binary.BigEndian.PutUint16(small[3:5], uint16(len(small)-5))
			started := time.Now()
			for index := 0; index < 512; index++ {
				if _, err := connection.Write(large); err != nil {
					test.Fatal(err)
				}
				if _, err := connection.Write(small); err != nil {
					test.Fatal(err)
				}
			}
			if err := connection.lab.flush(ctx); err != nil {
				test.Fatal(err)
			}
			elapsed := time.Since(started)
			stats := connection.lab.snapshot()
			if stats.InputSHA256 != stats.OutputSHA256 || stats.Accepted != stats.Sent {
				test.Fatal("calibration byte stream")
			}
			result, _ := json.Marshal(map[string]any{"policy": policy, "bytes": stats.Accepted, "seconds": elapsed.Seconds(), "mbit_s": float64(stats.Accepted) * 8 / elapsed.Seconds() / 1e6, "stats": stats})
			test.Log(string(result))
		})
	}
}

func TestPackingDrainRejectsTerminal(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	left, right := pair()
	clientProfile, serverProfile := profiles(test)
	ready := make(chan *Session, 1)
	go func() {
		session, _ := Open(WithLabPacking(ctx, "B2"), right, encoded(serverProfile), true)
		ready <- session
	}()
	client, err := Open(WithLabPacking(ctx, "B2"), left, encoded(clientProfile), false)
	if err != nil {
		test.Fatal(err)
	}
	defer client.Close()
	server := <-ready
	if server == nil {
		test.Fatal("handshake")
	}
	defer server.Close()
	cancel()
	deadline := time.Now().Add(time.Second)
	for client.ReliabilityStats().Terminal == "" && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	if client.ReliabilityStats().Terminal == "" {
		test.Fatal("missing terminal")
	}
	if err = client.LabDrain(context.Background()); err == nil {
		test.Fatal("terminal RS with zero depth incorrectly reported drained")
	}
}

func TestPackingMemoryAccounting(test *testing.T) {
	for _, policy := range []string{"A", "B2"} {
		test.Run(policy, func(test *testing.T) {
			const count = 128
			runtime.GC()
			var before, after runtime.MemStats
			runtime.ReadMemStats(&before)
			connections := make([]*labPackingConn, 0, count)
			peers := make([]net.Conn, 0, count)
			buffers := make([][]byte, 0, count)
			timers := make([]*time.Timer, 0, 2*count)
			for index := 0; index < count; index++ {
				left, right := net.Pipe()
				connection := newLabPackingConn(WithLabPacking(context.Background(), policy), left, nil)
				for size := 0; size < 258; size++ {
					packingCount(connection.stats.InputSizes, size)
					packingCount(connection.stats.DataSizes, size)
					packingCount(connection.stats.Records, size)
				}
				for _, reason := range []string{"full", "deadline", "explicit", "shutdown"} {
					connection.stats.Flush[reason] = 1
				}
				size := 65536
				if policy == "B2" {
					size = 16384
				}
				buffers = append(buffers, make([]byte, size))
				connections = append(connections, connection)
				peers = append(peers, right)
				timers = append(timers, time.NewTimer(time.Hour), time.NewTimer(time.Hour))
			}
			runtime.GC()
			runtime.ReadMemStats(&after)
			result, _ := json.Marshal(map[string]any{"memory_policy": policy, "sessions": count, "retained_heap_bytes_per_session": float64(int64(after.HeapAlloc)-int64(before.HeapAlloc)) / count, "connection_struct_bytes": unsafe.Sizeof(labPackingConn{}), "sha_state_bytes_each": reflect.TypeOf(connections[0].input).Elem().Size(), "histograms_at_cap": true, "modeled_timers_per_session": 2, "includes_both_pipe_ends": true})
			test.Log(string(result))
			runtime.KeepAlive(buffers)
			for _, timer := range timers {
				timer.Stop()
			}
			for _, connection := range connections {
				connection.Close()
			}
			for _, peer := range peers {
				peer.Close()
			}
		})
	}
}
