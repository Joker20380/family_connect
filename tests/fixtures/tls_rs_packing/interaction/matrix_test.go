package tcpforward

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"os"
	"path/filepath"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/reliablestream"
)

type interactionLink struct {
	*meshPerfEndpoint
	lock                                                     sync.Mutex
	armed, faults                                            bool
	seen                                                     map[uint64]bool
	offset                                                   uint64
	held                                                     []byte
	drops, reordered, retryAttempts, retryBytes, uniqueBytes uint64
	repeated                                                 map[uint64]int
	droppedRanges                                            [][2]uint64
}

func (link *interactionLink) SendContext(ctx context.Context, data []byte) error {
	link.lock.Lock()
	defer link.lock.Unlock()
	if len(data) >= 64 && string(data[:4]) == "FRS1" && data[4] == 2 {
		sequence := binary.BigEndian.Uint64(data[40:48])
		if link.seen[sequence] {
			link.retryAttempts++
			link.retryBytes += uint64(len(data) - 64)
			link.repeated[sequence] = len(data) - 64
		} else {
			link.seen[sequence] = true
			link.uniqueBytes += uint64(len(data) - 64)
			if link.armed {
				start := link.offset
				link.offset += uint64(len(data) - 64)
				if link.faults {
					for marker := uint64(64 << 10); marker < link.offset; marker += 128 << 10 {
						if marker+16<<10 > start {
							link.drops++
							link.droppedRanges = append(link.droppedRanges, [2]uint64{start, link.offset})
							return nil
						}
					}
					if start < 32<<10 && link.offset >= 32<<10 && link.held == nil {
						link.held = bytes.Clone(data)
						return nil
					}
				}
			}
		}
	}
	if err := link.meshPerfEndpoint.SendContext(ctx, data); err != nil {
		return err
	}
	if link.held != nil {
		pending := link.held
		link.held = nil
		link.reordered++
		return link.meshPerfEndpoint.SendContext(ctx, pending)
	}
	return nil
}

func (link *interactionLink) report() map[string]any {
	link.lock.Lock()
	defer link.lock.Unlock()
	return map[string]any{"drops": link.drops, "dropped_byte_ranges": link.droppedRanges, "reordered": link.reordered,
		"retry_attempts": link.retryAttempts, "retry_bytes": link.retryBytes, "unique_ciphertext_bytes": link.uniqueBytes,
		"unique_repeated": len(link.repeated), "repeated_sizes": link.repeated, "carrier": link.snapshot(false)}
}

func TestInteractionMatrix(test *testing.T) {
	if os.Getenv("FC_INTERACTION_LOCAL") != "1" {
		test.Skip("explicit bounded local matrix")
	}
	for _, scenario := range []struct {
		name         string
		flows, size  int
		slow, faults bool
	}{
		{"single", 1, 512 << 10, false, false}, {"parallel", 2, 256 << 10, false, false},
		{"slow", 1, 256 << 10, true, false}, {"fault", 1, 256 << 10, false, true},
	} {
		for _, variant := range []struct {
			name, packing string
			credit128     bool
		}{
			{"A", "A", false}, {"B", "B2", false}, {"C", "A", true}, {"D", "B2", true},
		} {
			test.Run(scenario.name+"/"+variant.name, func(test *testing.T) {
				ctx, cancel := context.WithTimeout(context.Background(), 35*time.Second)
				defer cancel()
				ctx = familysession.WithLabPacking(ctx, variant.packing)
				forward, reverse := make(chan meshPerfPacket, 256), make(chan meshPerfPacket, 256)
				makeLink := func(incoming, outgoing chan meshPerfPacket) *interactionLink {
					return &interactionLink{meshPerfEndpoint: &meshPerfEndpoint{ctx: ctx, incoming: incoming, outgoing: outgoing, delay: 156345875 * time.Nanosecond}, seen: map[uint64]bool{}, repeated: map[uint64]int{}}
				}
				left, right := makeLink(reverse, forward), makeLink(forward, reverse)
				clientProfile, serverProfile := testCredentials(test)
				config := reliablestream.DefaultConfig()
				config.SendWindow, config.ReceiveWindow = 32, 32
				type opened struct {
					session *familysession.Session
					err     error
				}
				ready := make(chan opened, 1)
				go func() {
					session, err := familysession.LabOpenMuxReliable(ctx, right, serverProfile, true, variant.credit128, config)
					ready <- opened{session, err}
				}()
				clientSession, err := familysession.LabOpenMuxReliable(ctx, left, clientProfile, false, variant.credit128, config)
				if err != nil {
					test.Fatal(err)
				}
				defer clientSession.Close()
				serverReady := <-ready
				if serverReady.err != nil {
					test.Fatal(serverReady.err)
				}
				serverSession := serverReady.session
				defer serverSession.Close()
				payload := meshPerfPayload(scenario.size)
				port := muxFixture(test, func(connection *net.TCPConn) {
					var header [1]byte
					if _, err := io.ReadFull(connection, header[:]); err != nil {
						return
					}
					if header[0] == 'D' {
						io.Copy(connection, bytes.NewReader(payload))
					} else {
						connection.Write(bytes.Repeat([]byte{7}, 32))
					}
					connection.CloseWrite()
				})
				server, err := NewMux(ctx, serverSession, true, MuxConfig{Policy: Policy{TestOnlyLoopbackPort: port}})
				if err != nil {
					test.Fatal(err)
				}
				defer server.Close()
				client, err := NewMux(ctx, clientSession, false, MuxConfig{})
				if err != nil {
					test.Fatal(err)
				}
				defer client.Close()
				window := 65536
				if variant.credit128 {
					window = 131072
				}
				if client.Stats().Window != window || server.Stats().Window != window {
					test.Fatal("negotiation")
				}
				request := func(bulk bool) (time.Duration, error) {
					started := time.Now()
					stream, err := client.OpenTCP(ctx, OpenRequest{Host: "127.0.0.1", Port: port})
					if err != nil {
						return time.Since(started), err
					}
					defer stream.Close()
					kind, expected := byte('E'), bytes.Repeat([]byte{7}, 32)
					if bulk {
						kind, expected = 'D', payload
					}
					if _, err = stream.Write([]byte{kind}); err != nil {
						return time.Since(started), err
					}
					if err = stream.CloseWrite(); err != nil {
						return time.Since(started), err
					}
					actual := make([]byte, len(expected))
					for offset := 0; offset < len(actual); {
						count, readErr := stream.Read(actual[offset:min(offset+16384, len(actual))])
						offset += count
						if readErr != nil {
							return time.Since(started), readErr
						}
						if bulk && scenario.slow {
							time.Sleep(80 * time.Millisecond)
						}
					}
					var tail [1]byte
					if _, err = stream.Read(tail[:]); err != io.EOF {
						return time.Since(started), fmt.Errorf("tail %v", err)
					}
					if !bytes.Equal(actual, expected) || sha256.Sum256(actual) != sha256.Sum256(expected) {
						return time.Since(started), fmt.Errorf("integrity")
					}
					return time.Since(started), stream.Close()
				}
				idle := []float64{}
				for index := 0; index < 4; index++ {
					duration, err := request(false)
					if err != nil {
						test.Fatal(err)
					}
					idle = append(idle, duration.Seconds())
				}
				right.lock.Lock()
				right.armed = true
				right.faults = scenario.faults
				right.lock.Unlock()
				stopSamples := make(chan struct{})
				samplesDone := make(chan struct{})
				samples := []map[string]any{}
				started := time.Now()
				go func() {
					defer close(samplesDone)
					ticker := time.NewTicker(10 * time.Millisecond)
					defer ticker.Stop()
					for {
						select {
						case <-stopSamples:
							return
						case <-ticker.C:
							if len(samples) < 4096 {
								samples = append(samples, map[string]any{"ns": time.Since(started).Nanoseconds(), "mux": server.PerformanceSnapshot(), "rs": serverSession.ReliabilityStats().Performance, "packing": serverSession.LabPackingStats()})
							}
						}
					}
				}()
				completed := make(chan error, scenario.flows)
				for index := 0; index < scenario.flows; index++ {
					go func() { _, err := request(true); completed <- err }()
				}
				loadedDone := make(chan []float64, 1)
				go func() {
					time.Sleep(100 * time.Millisecond)
					values := []float64{}
					for index := 0; index < 4; index++ {
						duration, err := request(false)
						if err != nil {
							values = append(values, -1)
							break
						}
						values = append(values, duration.Seconds())
					}
					loadedDone <- values
				}()
				var failure error
				for index := 0; index < scenario.flows; index++ {
					if err := <-completed; err != nil {
						failure = err
					}
				}
				elapsed := time.Since(started)
				loaded := <-loadedDone
				close(stopSamples)
				<-samplesDone
				time.Sleep(400 * time.Millisecond)
				clientDrain, serverDrain := clientSession.LabDrain(ctx), serverSession.LabDrain(ctx)
				clientRS, serverRS := clientSession.ReliabilityStats(), serverSession.ReliabilityStats()
				clientPacking, serverPacking := clientSession.LabPackingStats(), serverSession.LabPackingStats()
				result := map[string]any{"scenario": scenario.name, "variant": variant.name, "seconds": elapsed.Seconds(), "mbit_s": float64(scenario.size*scenario.flows) * 8 / elapsed.Seconds() / 1e6, "source_bytes": scenario.size * scenario.flows, "idle": idle, "loaded": loaded, "error": fmt.Sprint(failure), "drains": []string{fmt.Sprint(clientDrain), fmt.Sprint(serverDrain)}, "client_mux": client.Stats(), "server_mux": server.Stats(), "client_rs": clientRS, "server_rs": serverRS, "client_packing": clientPacking, "server_packing": serverPacking, "client_link": left.report(), "server_link": right.report(), "client_events": client.LabObservation(), "server_events": server.LabObservation(), "samples": samples}
				raw, _ := json.Marshal(result)
				if directory := os.Getenv("FC_INTERACTION_OUTPUT"); directory != "" {
					if err := os.WriteFile(filepath.Join(directory, scenario.name+"-"+variant.name+".json"), raw, 0600); err != nil {
						test.Fatal(err)
					}
				}
				test.Logf("%s %s %.6fs %.6fMbit/s error=%v", scenario.name, variant.name, elapsed.Seconds(), float64(scenario.size*scenario.flows)*8/elapsed.Seconds()/1e6, failure)
				if failure != nil || clientDrain != nil || serverDrain != nil {
					test.Fatal("completion", failure, clientDrain, serverDrain)
				}
				if clientRS.Performance.ReleasedBlocks != clientRS.DataSent || serverRS.Performance.ReleasedBlocks != serverRS.DataSent {
					test.Fatal("unconfirmed")
				}
				if clientPacking.InputSHA256 != serverPacking.ReceiveSHA256 || serverPacking.InputSHA256 != clientPacking.ReceiveSHA256 {
					test.Fatal("ciphertext contract")
				}
				client.Close()
				server.Close()
				if client.Stats().ProtocolErrors != 0 || server.Stats().ProtocolErrors != 0 {
					test.Fatal("protocol through close")
				}
				if scenario.faults && (right.drops == 0 || right.reordered == 0 || right.retryAttempts == 0) {
					test.Fatal("fault not exercised")
				}
			})
		}
	}
}
