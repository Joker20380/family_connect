package tcpforward

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/localwrite"
	"github.com/Joker20380/family_connect/carrier/sessionprofile"
)

type speedFaultEndpoint struct {
	*lossyEndpoint
	faults     atomic.Bool
	count      int
	ackDropped bool
	held       []byte
}

func (endpoint *speedFaultEndpoint) SendContext(ctx context.Context, payload []byte) error {
	completion, err := localwrite.Register(ctx, 1)
	if err != nil {
		return err
	}
	if !completion.Begin() {
		return nil
	}
	defer func() { completion.Complete(err) }()
	if endpoint.faults.Load() && len(payload) >= 64 {
		if payload[4] == 3 && !endpoint.ackDropped {
			endpoint.ackDropped = true
			return nil
		}
		if payload[4] == 2 {
			endpoint.count++
			if endpoint.count <= 3 {
				return nil
			}
			if endpoint.count == 4 {
				endpoint.held = bytes.Clone(payload)
				return nil
			}
			if endpoint.count == 5 {
				if err = endpoint.lossyEndpoint.SendContext(ctx, payload); err != nil {
					return err
				}
				if err = endpoint.lossyEndpoint.SendContext(ctx, endpoint.held); err != nil {
					return err
				}
				endpoint.held = nil
			}
		}
	}
	err = endpoint.lossyEndpoint.SendContext(ctx, payload)
	return err
}

func speedPair(test *testing.T, ctx context.Context, profile sessionprofile.Profile) (*familysession.Session, *familysession.Session) {
	test.Helper()
	clientJSON, serverJSON := testCredentials(test)
	forward, reverse, closed := make(chan []byte, 64), make(chan []byte, 64), make(chan struct{})
	once := &sync.Once{}
	left := &speedFaultEndpoint{lossyEndpoint: &lossyEndpoint{incoming: reverse, outgoing: forward, closed: closed, once: once, seen: make(map[uint64]int)}}
	right := &speedFaultEndpoint{lossyEndpoint: &lossyEndpoint{incoming: forward, outgoing: reverse, closed: closed, once: once, seen: make(map[uint64]int)}}
	config := profile.Reliable()
	type result struct {
		session *familysession.Session
		err     error
	}
	ready := make(chan result, 1)
	go func() {
		session, err := familysession.OpenMuxReliable(profile.LocalWrite(ctx), right, serverJSON, true, profile != sessionprofile.P0, config)
		ready <- result{session, err}
	}()
	client, err := familysession.OpenMuxReliable(profile.LocalWrite(ctx), left, clientJSON, false, true, config)
	if err != nil {
		test.Fatal(err)
	}
	server := <-ready
	if server.err != nil {
		test.Fatal(server.err)
	}
	test.Cleanup(func() { client.Close(); server.session.Close() })
	left.faults.Store(true)
	right.faults.Store(true)
	return client, server.session
}

func TestSpeedProfilesIntegrated(test *testing.T) {
	for _, profile := range []sessionprofile.Profile{sessionprofile.P0, sessionprofile.P1, sessionprofile.P2} {
		test.Run(profile.Name(), func(test *testing.T) {
			test.Parallel()
			ctx, cancel := context.WithTimeout(context.Background(), 40*time.Second)
			defer cancel()
			port := muxFixture(test, muxEcho)
			clientTLS, serverTLS := speedPair(test, ctx, profile)
			client, err := NewMux(ctx, clientTLS, false, MuxConfig{MaxStreams: 32})
			if err != nil {
				test.Fatal(err)
			}
			server, err := NewMux(ctx, serverTLS, true, MuxConfig{MaxStreams: 32, Policy: Policy{TestOnlyLoopbackPort: port}})
			if err != nil {
				test.Fatal(err)
			}
			defer func() {
				client.Close()
				server.Close()
				if client.Stats().RetainedBytes != 0 || server.Stats().RetainedBytes != 0 {
					test.Error("retained after close")
				}
			}()
			expected := profile.Reliable()
			for _, secured := range []*familysession.Session{clientTLS, serverTLS} {
				limits := secured.ReliabilityStats().Limits
				if limits.LocalSend != expected.SendWindow || limits.LocalReceive != expected.ReceiveWindow || limits.PeerReceive != expected.ReceiveWindow || limits.EffectiveSend != expected.SendWindow || limits.LocalWriteCompletion != (profile == sessionprofile.P2) {
					test.Fatal(limits)
				}
			}
			window := 65536
			if profile != sessionprofile.P0 {
				window = 131072
			}
			if client.Stats().Window != window || server.Stats().Window != window {
				test.Fatal("negotiated window")
			}
			streams := make([]*MuxStream, 32)
			for index := range streams {
				streams[index] = muxOpen(test, ctx, client, port)
			}
			streams[31].Reset()
			results := make(chan error, 31)
			for index, stream := range streams[:31] {
				go func() {
					payload := bytes.Repeat([]byte{byte(index + 1)}, 192<<10)
					if index >= 2 {
						payload = payload[:1024]
					}
					writing := make(chan error, 1)
					go func() {
						_, failure := stream.Write(payload)
						if failure == nil {
							failure = stream.CloseWrite()
						}
						writing <- failure
					}()
					if index == 0 {
						time.Sleep(200 * time.Millisecond)
					}
					body := make([]byte, len(payload))
					_, failure := io.ReadFull(stream, body)
					if sent := <-writing; failure == nil {
						failure = sent
					}
					if failure == nil && sha256.Sum256(body) != sha256.Sum256(payload) {
						failure = fmt.Errorf("body mismatch")
					}
					if failure == nil {
						tail := make([]byte, 1)
						count, end := stream.Read(tail)
						if count != 0 || end != io.EOF {
							failure = fmt.Errorf("missing FIN: %v", end)
						}
					}
					stream.Close()
					results <- failure
				}()
			}
			for range 31 {
				if err := <-results; err != nil {
					test.Fatal(err)
				}
			}
			if client.Stats().ProtocolErrors != 0 || server.Stats().ProtocolErrors != 0 {
				test.Fatal("protocol error")
			}
			for _, stats := range []struct {
				name    string
				session *familysession.Session
			}{{"client", clientTLS}, {"server", serverTLS}} {
				value := stats.session.ReliabilityStats()
				if value.MaxBufferedBytes > expected.ReceiveWindow*expected.Payload || value.SendHighWater > expected.SendWindow {
					test.Fatal("unbounded RS", value)
				}
			}
			record, _ := json.Marshal(map[string]any{"profile": profile.Name(), "client": clientTLS.ReliabilityStats().Limits, "server": serverTLS.ReliabilityStats().Limits, "mux": window, "streams": 32, "reset_isolated": true, "sha256": true, "rs_client_retries": clientTLS.ReliabilityStats().Retransmissions, "rs_server_retries": serverTLS.ReliabilityStats().Retransmissions, "scope": "post-handshake RS-message burst3/reorder/duplicate/ACK-loss; not RTP loss"})
			test.Log(string(record))
		})
	}
}

func TestSpeedWireOPENBounds(test *testing.T) {
	config := sessionprofile.P1.Reliable()
	if config.Payload != 16384 || config.SendWindow != 32 || config.ReceiveWindow != 32 || config.MaxRetries != 8 || config.RTO != time.Second {
		test.Fatal(config)
	}
	raw := make([]byte, 64)
	binary.BigEndian.PutUint16(raw[60:], uint16(config.ReceiveWindow))
	if binary.BigEndian.Uint16(raw[60:]) != 32 {
		test.Fatal("OPEN window")
	}
}
