package familysession

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/Joker20380/family_connect/carrier/reliablestream"
	"io"
	"net"
	"os"
	"sync"
	"testing"
	"time"
)

type packingCapture struct {
	PacketEndpoint
	mu     sync.Mutex
	unique map[uint64][]byte
}

func (endpoint *packingCapture) SendContext(ctx context.Context, data []byte) error {
	if len(data) >= 64 && data[4] == 2 {
		endpoint.mu.Lock()
		sequence := binary.BigEndian.Uint64(data[40:])
		if _, exists := endpoint.unique[sequence]; !exists {
			endpoint.unique[sequence] = bytes.Clone(data[64:])
		}
		endpoint.mu.Unlock()
	}
	return endpoint.PacketEndpoint.SendContext(ctx, data)
}
func (endpoint *packingCapture) flattened() ([]byte, map[int]int) {
	endpoint.mu.Lock()
	defer endpoint.mu.Unlock()
	var data []byte
	hist := map[int]int{}
	for sequence := uint64(0); sequence < uint64(len(endpoint.unique)); sequence++ {
		block := endpoint.unique[sequence]
		data = append(data, block...)
		hist[len(block)]++
	}
	return data, hist
}

func TestPackingFamilyMatrix(test *testing.T) {
	for _, window := range []int{8, 32} {
		for _, policy := range []string{"A", "B0", "B2"} {
			for _, legacy := range []bool{false, true} {
				if legacy && policy != "B2" {
					continue
				}
				test.Run(fmt.Sprintf("%s%d/legacy%t", policy, window, legacy), func(test *testing.T) {
					ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
					defer cancel()
					clientProfile, serverProfile := profiles(test)
					left, right := pair()
					captureLeft := &packingCapture{PacketEndpoint: left, unique: map[uint64][]byte{}}
					captureRight := &packingCapture{PacketEndpoint: right, unique: map[uint64][]byte{}}
					config := reliablestream.DefaultConfig()
					config.SendWindow = window
					if window == 32 {
						config.ReceiveWindow = 32
					}
					peerPolicy := policy
					if legacy {
						peerPolicy = "A"
					}
					ready := make(chan *Session, 1)
					failures := make(chan error, 1)
					go func() {
						session, err := OpenReliable(WithLabPacking(ctx, peerPolicy), captureRight, encoded(serverProfile), true, config)
						ready <- session
						failures <- err
					}()
					client, err := OpenReliable(WithLabPacking(ctx, policy), captureLeft, encoded(clientProfile), false, config)
					if err != nil {
						test.Fatal(err)
					}
					defer client.Close()
					server := <-ready
					if err = <-failures; err != nil {
						test.Fatal(err)
					}
					defer server.Close()
					for _, direction := range []int{0, 1} {
						sender, receiver := client, server
						if direction == 1 {
							sender, receiver = server, client
						}
						sizes := []int{}
						for index := 0; index < 200; index++ {
							sizes = append(sizes, 16384)
						}
						sizes = append(sizes, 1, 22, 34, 16383, 16384, 16385, 32768, 65536, 7)
						completed := make(chan error, 1)
						go func() {
							for index, size := range sizes {
								data := bytes.Repeat([]byte{byte(index)}, size)
								if err := sender.SendContext(ctx, data); err != nil {
									completed <- err
									return
								}
							}
							completed <- nil
						}()
						expectedHash, actualHash := sha256.New(), sha256.New()
						for index, size := range sizes {
							if index%23 == 0 {
								time.Sleep(time.Millisecond)
							}
							actual, err := receiver.Recv(ctx)
							expected := bytes.Repeat([]byte{byte(index)}, size)
							if err != nil || !bytes.Equal(actual, expected) {
								test.Fatal(index, err)
							}
							expectedHash.Write(expected)
							actualHash.Write(actual)
						}
						if err = <-completed; err != nil {
							test.Fatal(err)
						}
						if !bytes.Equal(expectedHash.Sum(nil), actualHash.Sum(nil)) {
							test.Fatal("body hash")
						}
						if err = sender.LabDrain(ctx); err != nil {
							test.Fatal(err)
						}
					}
					for index, session := range []*Session{client, server} {
						capture, peer := captureLeft, server
						if index == 1 {
							capture, peer = captureRight, client
						}
						raw, hist := capture.flattened()
						digest := sha256.Sum256(raw)
						stats := session.LabPackingStats()
						if fmt.Sprintf("%x", digest) != stats.InputSHA256 || stats.InputSHA256 != peer.LabPackingStats().ReceiveSHA256 {
							test.Fatal("ciphertext concat", stats)
						}
						encoded, _ := json.Marshal(map[string]any{"policy": policy, "window": window, "legacy": legacy, "direction": index, "packing": stats, "unique_data": hist, "body_exact": true, "ciphertext_exact": true, "rs": session.ReliabilityStats()})
						test.Log(string(encoded))
					}
				})
			}
		}
	}
}

func TestPackingFamilyFaults(test *testing.T) {
	for _, window := range []int{8, 32} {
		test.Run(fmt.Sprint(window), func(test *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 35*time.Second)
			defer cancel()
			left, right := pair()
			senderPoint := &lossEndpoint{endpoint: left, seen: map[uint64]int{}}
			receiverPoint := &lossEndpoint{endpoint: right, seen: map[uint64]int{}}
			senderProfile, receiverProfile := profiles(test)
			config := reliablestream.DefaultConfig()
			config.SendWindow = window
			if window == 32 {
				config.ReceiveWindow = 32
			}
			ready := make(chan *Session, 1)
			go func() {
				session, _ := OpenReliable(WithLabPacking(ctx, "B2"), receiverPoint, encoded(receiverProfile), true, config)
				ready <- session
			}()
			sender, err := OpenReliable(WithLabPacking(ctx, "B2"), senderPoint, encoded(senderProfile), false, config)
			if err != nil {
				test.Fatal(err)
			}
			defer sender.Close()
			receiver := <-ready
			if receiver == nil {
				test.Fatal("handshake")
			}
			defer receiver.Close()
			senderPoint.armed.Store(true)
			receiverPoint.armed.Store(true)
			complete := make(chan error, 1)
			go func() {
				for index := 0; index < 40; index++ {
					if err := sender.SendContext(ctx, bytes.Repeat([]byte{byte(index)}, 16384)); err != nil {
						complete <- err
						return
					}
				}
				complete <- nil
			}()
			time.Sleep(300 * time.Millisecond)
			for index := 0; index < 40; index++ {
				actual, err := receiver.Recv(ctx)
				if err != nil || !bytes.Equal(actual, bytes.Repeat([]byte{byte(index)}, 16384)) {
					test.Fatal(index, err)
				}
			}
			if err = <-complete; err != nil {
				test.Fatal(err)
			}
			test.Logf("fault window=%d retries=%d queue=%d", window, sender.ReliabilityStats().Retransmissions, sender.LabPackingStats().MaxQueueBytes)
			if sender.ReliabilityStats().Retransmissions == 0 || sender.LabPackingStats().MaxQueueBytes > 65536 {
				test.Fatal("fault/bound evidence")
			}
		})
	}
}

type packingSink struct {
	send func(context.Context, []byte) error
}

func (sink packingSink) SendContext(ctx context.Context, data []byte) error {
	return sink.send(ctx, data)
}
func (sink packingSink) Recv(ctx context.Context) ([]byte, error) {
	<-ctx.Done()
	return nil, ctx.Err()
}
func (sink packingSink) Close() error { return nil }

func TestPackingTailFailureDeadlinesRaces(test *testing.T) {
	for _, policy := range []string{"B0", "B2"} {
		test.Run(policy, func(test *testing.T) {
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			local, peer := net.Pipe()
			defer peer.Close()
			received := make(chan []byte, 32)
			connection := newLabPackingConn(WithLabPacking(ctx, policy), local, packingSink{send: func(ctx context.Context, data []byte) error { received <- bytes.Clone(data); return nil }})
			done := make(chan struct{})
			go func() { connection.run(); close(done) }()
			payload := []byte("tail-owner-copy")
			started := time.Now()
			if count, err := connection.Write(payload); count != len(payload) || err != nil {
				test.Fatal(count, err)
			}
			clear(payload)
			select {
			case actual := <-received:
				if string(actual) != "tail-owner-copy" {
					test.Fatal("copy")
				}
			case <-time.After(250 * time.Millisecond):
				test.Fatal("tail requires future write")
			}
			test.Log("tail", time.Since(started))
			connection.Close()
			select {
			case <-done:
			case <-time.After(time.Second):
				test.Fatal("worker leak")
			}
		})
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	local, peer := net.Pipe()
	defer peer.Close()
	release := make(chan struct{})
	failure := errors.New("injected underlying failure")
	connection := newLabPackingConn(WithLabPacking(ctx, "B2"), local, packingSink{send: func(ctx context.Context, data []byte) error {
		select {
		case <-release:
			return failure
		case <-ctx.Done():
			return ctx.Err()
		}
	}})
	done := make(chan struct{})
	go func() { connection.run(); close(done) }()
	connection.SetWriteDeadline(time.Now().Add(50 * time.Millisecond))
	count, err := connection.Write(make([]byte, 6*packingBlock))
	if count == 0 || count > 5*packingBlock || !errors.Is(err, os.ErrDeadlineExceeded) {
		test.Fatal(count, err)
	}
	close(release)
	<-done
	connection.SetWriteDeadline(time.Time{})
	if _, err = connection.Write([]byte{1}); !errors.Is(err, failure) {
		test.Fatal("lost terminal error", err)
	}
	flushCtx, stop := context.WithTimeout(ctx, time.Second)
	defer stop()
	if !errors.Is(connection.flush(flushCtx), failure) {
		test.Fatal("flush lost failure")
	}
	connection.Close()
	for iteration := 0; iteration < 30; iteration++ {
		child, abort := context.WithCancel(context.Background())
		local, peer := net.Pipe()
		current := newLabPackingConn(WithLabPacking(child, "B2"), local, packingSink{send: func(ctx context.Context, data []byte) error {
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(time.Millisecond):
				return nil
			}
		}})
		var workers sync.WaitGroup
		workers.Add(4)
		go func() { defer workers.Done(); current.run() }()
		go func() { defer workers.Done(); current.Write(make([]byte, 100000)) }()
		go func() {
			defer workers.Done()
			current.SetWriteDeadline(time.Now().Add(time.Millisecond))
			current.flush(child)
		}()
		go func() { defer workers.Done(); time.Sleep(time.Millisecond); abort(); current.Close() }()
		workers.Wait()
		peer.Close()
	}
}

func TestPackingSmallRequestAndHandshakeFailure(test *testing.T) {
	for _, policy := range []string{"A", "B0", "B2"} {
		test.Run(policy, func(test *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
			defer cancel()
			left, right := pair()
			clientProfile, serverProfile := profiles(test)
			ready := make(chan *Session, 1)
			go func() {
				session, _ := Open(WithLabPacking(ctx, policy), right, encoded(serverProfile), true)
				ready <- session
			}()
			client, err := Open(WithLabPacking(ctx, policy), left, encoded(clientProfile), false)
			if err != nil {
				test.Fatal(err)
			}
			defer client.Close()
			server := <-ready
			if server == nil {
				test.Fatal("handshake")
			}
			defer server.Close()
			complete := make(chan error, 1)
			go func() {
				for index := 0; index < 8; index++ {
					data, err := server.Recv(ctx)
					if err == nil {
						err = server.SendContext(ctx, data)
					}
					if err != nil {
						complete <- err
						return
					}
				}
				complete <- nil
			}()
			var latencies []float64
			for index := 0; index < 8; index++ {
				time.Sleep(3 * time.Millisecond)
				started := time.Now()
				if err = client.SendContext(ctx, []byte("request")); err != nil {
					test.Fatal(err)
				}
				data, err := client.Recv(ctx)
				if err != nil || string(data) != "request" {
					test.Fatal(err)
				}
				latencies = append(latencies, time.Since(started).Seconds())
			}
			if err = <-complete; err != nil {
				test.Fatal(err)
			}
			test.Log("small_idle_rtt_seconds", latencies)
			if err = client.connection.CloseWrite(); err != nil {
				test.Fatal(err)
			}
			if _, err = server.connection.Read(make([]byte, 1)); err != io.EOF {
				test.Fatal("close_notify stalled", err)
			}
			if err = server.connection.CloseWrite(); err != nil {
				test.Fatal(err)
			}
			if _, err = client.connection.Read(make([]byte, 1)); err != io.EOF {
				test.Fatal("reverse close_notify", err)
			}
		})
	}
	ctx, cancel := context.WithTimeout(context.Background(), 40*time.Millisecond)
	defer cancel()
	left, right := pair()
	defer right.Close()
	profile, _ := profiles(test)
	if session, err := Open(WithLabPacking(ctx, "B2"), left, encoded(profile), false); err == nil || session != nil {
		test.Fatal("handshake must fail finitely")
	}
}

type packingACKLoss struct {
	PacketEndpoint
	mu    sync.Mutex
	drops int
}

func (endpoint *packingACKLoss) SendContext(ctx context.Context, data []byte) error {
	endpoint.mu.Lock()
	drop := len(data) >= 64 && (data[4] == 3 || data[4] == 4) && endpoint.drops > 0
	if drop {
		endpoint.drops--
	}
	endpoint.mu.Unlock()
	if drop {
		return nil
	}
	return endpoint.PacketEndpoint.SendContext(ctx, data)
}
func TestPackingACKLoss(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 12*time.Second)
	defer cancel()
	left, right := pair()
	ackLoss := &packingACKLoss{PacketEndpoint: right}
	clientProfile, serverProfile := profiles(test)
	ready := make(chan *Session, 1)
	go func() {
		session, _ := Open(WithLabPacking(ctx, "B2"), ackLoss, encoded(serverProfile), true)
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
	ackLoss.mu.Lock()
	ackLoss.drops = 2
	ackLoss.mu.Unlock()
	if err = client.SendContext(ctx, []byte("one tail after ACK loss")); err != nil {
		test.Fatal(err)
	}
	actual, err := server.Recv(ctx)
	if err != nil || string(actual) != "one tail after ACK loss" {
		test.Fatal(err)
	}
	if err = client.LabDrain(ctx); err != nil {
		test.Fatal(err)
	}
	test.Log("ACK loss recovered", client.ReliabilityStats())
}
func TestPackingOldestAndCloseOnly(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	local, peer := net.Pipe()
	defer peer.Close()
	arrival := make(chan time.Time, 64)
	connection := newLabPackingConn(WithLabPacking(ctx, "B2"), local, packingSink{send: func(ctx context.Context, data []byte) error { arrival <- time.Now(); return nil }})
	done := make(chan struct{})
	go func() { connection.run(); close(done) }()
	started := time.Now()
	connection.Write([]byte{1})
	time.Sleep(time.Millisecond)
	connection.Write([]byte{2})
	select {
	case first := <-arrival:
		if first.Sub(started) > 100*time.Millisecond {
			test.Fatal("oldest postponed")
		}
	case <-time.After(100 * time.Millisecond):
		test.Fatal("no deadline")
	}
	connection.Close()
	<-done
	local2, peer2 := net.Pipe()
	defer peer2.Close()
	blocked := make(chan struct{})
	second := newLabPackingConn(WithLabPacking(ctx, "B2"), local2, packingSink{send: func(ctx context.Context, data []byte) error { close(blocked); <-ctx.Done(); return ctx.Err() }})
	stopped := make(chan struct{})
	go func() { second.run(); close(stopped) }()
	second.Write(make([]byte, 16384))
	<-blocked
	second.Close()
	select {
	case <-stopped:
	case <-time.After(time.Second):
		test.Fatal("close alone failed to cancel send")
	}
}
