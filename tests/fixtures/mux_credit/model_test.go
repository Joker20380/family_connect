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
	"strconv"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
)

type creditFaultLink struct {
	*meshPerfEndpoint
	bulk      atomic.Bool
	lock      sync.Mutex
	seen      map[uint64]bool
	every     int
	unique    int
	dropped   int
	reordered int
	held      []byte
}

func (link *creditFaultLink) SendContext(ctx context.Context, data []byte) error {
	link.lock.Lock()
	defer link.lock.Unlock()
	if link.bulk.Load() && link.every > 0 && len(data) >= 64 && string(data[:4]) == "FRS1" && data[4] == 2 {
		sequence := binary.BigEndian.Uint64(data[40:48])
		if !link.seen[sequence] {
			link.seen[sequence] = true
			link.unique++
			if link.unique%link.every == 1 {
				link.dropped++
				return nil
			}
			if link.unique%link.every == 2 && link.held == nil {
				link.held = bytes.Clone(data)
				return nil
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

func TestCreditMeasuredModel(test *testing.T) {
	if os.Getenv("MUX_CREDIT_MODEL") != "1" {
		test.Skip("explicit calibrated local model only")
	}
	delayNS, err := strconv.ParseInt(os.Getenv("MUX_CREDIT_DELAY_NS"), 10, 64)
	if err != nil {
		test.Fatal(err)
	}
	every, err := strconv.Atoi(os.Getenv("MUX_CREDIT_LOSS_EVERY"))
	if err != nil || every < 3 {
		test.Fatal("missing measured loss-density proxy")
	}
	for _, faults := range []bool{false, true} {
		for _, flows := range []int{1, 4} {
			for _, slow := range []bool{false, true} {
				test.Run(fmt.Sprintf("faults=%t/flows=%d/slow=%t", faults, flows, slow), func(test *testing.T) {
					ctx, cancel := context.WithTimeout(context.Background(), 45*time.Second)
					defer cancel()
					forward, reverse := make(chan meshPerfPacket, 256), make(chan meshPerfPacket, 256)
					left := &meshPerfEndpoint{ctx: ctx, incoming: reverse, outgoing: forward, delay: time.Duration(delayNS)}
					right := &creditFaultLink{meshPerfEndpoint: &meshPerfEndpoint{ctx: ctx, incoming: forward, outgoing: reverse, delay: time.Duration(delayNS)}, seen: make(map[uint64]bool)}
					if faults {
						right.every = every
					}
					clientProfile, serverProfile := testCredentials(test)
					type opened struct {
						session *familysession.Session
						err     error
					}
					ready := make(chan opened, 1)
					serverContext := sessiontrace.With(ctx, sessiontrace.New("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef", nil))
					go func() {
						session, err := familysession.Open(serverContext, right, serverProfile, true)
						ready <- opened{session, err}
					}()
					clientSession, err := familysession.Open(ctx, left, clientProfile, false)
					if err != nil {
						test.Fatal(err)
					}
					serverSession := <-ready
					if serverSession.err != nil {
						test.Fatal(serverSession.err)
					}
					payload := meshPerfPayload((512 << 10) / flows)
					port := muxFixture(test, func(connection *net.TCPConn) {
						connection.SetDeadline(time.Now().Add(40 * time.Second))
						var trigger [1]byte
						if _, err := io.ReadFull(connection, trigger[:]); err != nil {
							return
						}
						io.Copy(connection, bytes.NewReader(payload))
						connection.CloseWrite()
					})
					client, err := NewMux(ctx, clientSession, false, MuxConfig{})
					if err != nil {
						test.Fatal(err)
					}
					server, err := NewMux(ctx, serverSession.session, true, MuxConfig{Policy: Policy{TestOnlyLoopbackPort: port}})
					if err != nil {
						test.Fatal(err)
					}
					test.Cleanup(func() {
						client.Close()
						server.Close()
						if client.Stats().RetainedBytes != 0 || server.Stats().RetainedBytes != 0 {
							test.Error("retained after close")
						}
					})
					streams := make([]*MuxStream, flows)
					for index := range streams {
						streams[index] = muxOpen(test, ctx, client, port)
					}
					right.bulk.Store(true)
					done := make(chan error, flows)
					started := time.Now()
					for _, stream := range streams {
						go func() {
							if _, err := stream.Write([]byte{1}); err != nil {
								done <- err
								return
							}
							body := make([]byte, 0, len(payload))
							buffer := make([]byte, MaxData)
							for len(body) < len(payload) {
								count, err := stream.Read(buffer)
								body = append(body, buffer[:count]...)
								if err != nil {
									done <- err
									return
								}
								if slow {
									timer := time.NewTimer(time.Duration(delayNS))
									select {
									case <-timer.C:
									case <-ctx.Done():
										timer.Stop()
										done <- ctx.Err()
										return
									}
								}
							}
							if !bytes.Equal(body, payload) {
								done <- fmt.Errorf("byte mismatch")
								return
							}
							done <- nil
						}()
					}
					for range streams {
						if err := <-done; err != nil {
							test.Fatal(err)
						}
					}
					elapsed := time.Since(started)
					right.lock.Lock()
					dropped, reordered := right.dropped, right.reordered
					right.lock.Unlock()
					stats := serverSession.session.ReliabilityStats()
					encoded, _ := json.Marshal(map[string]any{"window": MuxWindow, "flows": flows, "faults": faults, "slow": slow, "bytes": 512 << 10, "seconds": elapsed.Seconds(), "mbit_s": float64(512<<10) * 8 / elapsed.Seconds() / 1e6, "mux_server": server.PerformanceSnapshot(), "server_bounds": server.Stats(), "client_bounds": client.Stats(), "rs": stats, "dropped": dropped, "reordered": reordered, "byte_exact": true})
					test.Log("CREDIT_MODEL " + string(encoded))
				})
			}
		}
	}
}
