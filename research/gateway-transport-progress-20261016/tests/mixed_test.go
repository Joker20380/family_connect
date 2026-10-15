package mixed

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"sync"
	"testing"
	"time"

	candidatefamily "fixture.invalid/candidate/familysession"
	candidatereliable "fixture.invalid/candidate/reliablestream"
	candidatecarrier "fixture.invalid/candidate/telemost"
	clientfamily "fixture.invalid/oldclient/familysession"
	clientreliable "fixture.invalid/oldclient/reliablestream"
	clientcarrier "fixture.invalid/oldclient/telemost"
	oldfamily "fixture.invalid/oldgateway/familysession"
	oldreliable "fixture.invalid/oldgateway/reliablestream"
	oldcarrier "fixture.invalid/oldgateway/telemost"
	newfamily "github.com/Joker20380/family_connect/carrier/familysession"
	newreliable "github.com/Joker20380/family_connect/carrier/reliablestream"
	newcarrier "github.com/Joker20380/family_connect/carrier/telemost"
)

type packet interface {
	SendContext(context.Context, []byte) error
	Recv(context.Context) ([]byte, error)
	Close() error
}

type carrier interface {
	packet
	Deliver([]byte) bool
	Snapshot() map[string]any
	SetReadGate(<-chan struct{})
	SetCloseGate(<-chan struct{}, chan struct{})
}

type reliable struct {
	packet
	stats func() map[string]any
}

func asMap(value any) map[string]any {
	raw, _ := json.Marshal(value)
	result := map[string]any{}
	_ = json.Unmarshal(raw, &result)
	return result
}

type wire struct {
	mu      sync.Mutex
	target  carrier
	held    bool
	frames  [][]byte
	gate    <-chan struct{}
	entered chan struct{}
	maxHeld int
}

func (link *wire) send(ctx context.Context, payload []byte) error {
	link.mu.Lock()
	gate := link.gate
	if gate != nil && link.entered != nil {
		close(link.entered)
		link.entered = nil
	}
	link.mu.Unlock()
	if gate != nil {
		select {
		case <-gate:
		case <-ctx.Done():
			return ctx.Err()
		}
	}
	link.mu.Lock()
	defer link.mu.Unlock()
	if link.held {
		if len(link.frames) == 64 {
			return errors.New("fixture capture bound")
		}
		link.frames = append(link.frames, bytes.Clone(payload))
		if len(link.frames) > link.maxHeld {
			link.maxHeld = len(link.frames)
		}
	} else {
		link.target.Deliver(bytes.Clone(payload))
	}
	return nil
}

func (link *wire) count() int { link.mu.Lock(); defer link.mu.Unlock(); return len(link.frames) }
func (link *wire) hold()      { link.mu.Lock(); link.held = true; link.mu.Unlock() }

func (link *wire) release(count int, final bool) map[string]any {
	link.mu.Lock()
	defer link.mu.Unlock()
	count = min(count, len(link.frames))
	selected := link.frames[:count]
	composition := map[string]int{}
	sequences := map[uint64]bool{}
	epochs := map[string]bool{}
	for _, frame := range selected {
		if len(frame) < 64 || string(frame[:4]) != "FRS1" {
			panic("not a real Reliable frame")
		}
		composition[fmt.Sprint(frame[4])]++
		epochs[string(frame[8:40])] = true
		if frame[4] == 2 {
			sequence := binary.BigEndian.Uint64(frame[40:48])
			if sequences[sequence] {
				composition["repeated_data"]++
			}
			sequences[sequence] = true
		}
	}
	before := link.target.Snapshot()
	started := time.Now()
	accepted := 0
	for _, frame := range selected {
		if link.target.Deliver(frame) {
			accepted++
		}
	}
	elapsed := time.Since(started)
	link.frames = append([][]byte(nil), link.frames[count:]...)
	if final {
		link.held = false
	}
	return map[string]any{"count": count, "composition_kind_1_open_2_data_3_ack_4_reset": composition, "unique_data": len(sequences), "epoch_pairs": len(epochs), "duration_ns": elapsed.Nanoseconds(), "enqueue_returned_live": accepted, "before": before, "after": link.target.Snapshot(), "capture_high_water": link.maxHeld}
}

func newPoint(test *testing.T, ctx context.Context, version string, link *wire) carrier {
	test.Helper()
	switch version {
	case "candidate":
		point, err := candidatecarrier.NewMixedEndpoint(ctx)
		if err != nil {
			test.Fatal(err)
		}
		point.Send = link.send
		return point
	case "oldgateway":
		point, err := oldcarrier.NewMixedEndpoint(ctx)
		if err != nil {
			test.Fatal(err)
		}
		point.Send = link.send
		return point
	case "oldclient":
		point, err := clientcarrier.NewMixedEndpoint(ctx)
		if err != nil {
			test.Fatal(err)
		}
		point.Send = link.send
		return point
	default:
		point, err := newcarrier.NewMixedEndpoint(ctx)
		if err != nil {
			test.Fatal(err)
		}
		point.Send = link.send
		return point
	}
}

func newReliable(test *testing.T, ctx context.Context, version string, point carrier) reliable {
	test.Helper()
	switch version {
	case "candidate":
		stream, err := candidatereliable.New(ctx, point, candidatereliable.DefaultConfig())
		if err != nil {
			test.Fatal(err)
		}
		return reliable{stream, func() map[string]any { return asMap(stream.Stats()) }}
	case "oldgateway":
		stream, err := oldreliable.New(ctx, point, oldreliable.DefaultConfig())
		if err != nil {
			test.Fatal(err)
		}
		return reliable{stream, func() map[string]any { return asMap(stream.Stats()) }}
	case "oldclient":
		stream, err := clientreliable.New(ctx, point, clientreliable.DefaultConfig())
		if err != nil {
			test.Fatal(err)
		}
		return reliable{stream, func() map[string]any { return asMap(stream.Stats()) }}
	default:
		stream, err := newreliable.New(ctx, point, newreliable.DefaultConfig())
		if err != nil {
			test.Fatal(err)
		}
		return reliable{stream, func() map[string]any { return asMap(stream.Stats()) }}
	}
}

type pair struct {
	client, gateway           reliable
	clientPoint, gatewayPoint carrier
	forward, reverse          *wire
	ctx                       context.Context
	cancel                    context.CancelFunc
	once                      sync.Once
}

func await(test *testing.T, label string, limit time.Duration, predicate func() bool) {
	test.Helper()
	timer := time.NewTimer(limit)
	defer timer.Stop()
	ticker := time.NewTicker(time.Millisecond)
	defer ticker.Stop()
	for !predicate() {
		select {
		case <-timer.C:
			test.Fatal("gate timeout", label)
		case <-ticker.C:
		}
	}
}

func newPair(test *testing.T, clientVersion, gatewayVersion string) *pair {
	test.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	forward, reverse := &wire{}, &wire{}
	clientPoint := newPoint(test, ctx, clientVersion, forward)
	gatewayPoint := newPoint(test, ctx, gatewayVersion, reverse)
	forward.target, reverse.target = gatewayPoint, clientPoint
	result := &pair{clientPoint: clientPoint, gatewayPoint: gatewayPoint, forward: forward, reverse: reverse, ctx: ctx, cancel: cancel}
	result.client = newReliable(test, ctx, clientVersion, clientPoint)
	result.gateway = newReliable(test, ctx, gatewayVersion, gatewayPoint)
	test.Cleanup(func() { result.close(test) })
	exchange(test, ctx, result.client, result.gateway, []byte("client-ready"))
	exchange(test, ctx, result.gateway, result.client, []byte("gateway-ready"))
	await(test, "initial windows free", time.Second, func() bool {
		return result.client.stats()["SendDepth"].(float64) == 0 && result.gateway.stats()["SendDepth"].(float64) == 0
	})
	return result
}

func (value *pair) close(test *testing.T) {
	value.once.Do(func() {
		value.cancel()
		done := make(chan struct{})
		go func() { value.client.Close(); value.gateway.Close(); close(done) }()
		select {
		case <-done:
		case <-time.After(3 * time.Second):
			test.Error("cleanup did not finish")
		}
		await(test, "adapter workers joined", time.Second, func() bool {
			return value.clientPoint.Snapshot()["active_calls"].(int64) == 0 && value.gatewayPoint.Snapshot()["active_calls"].(int64) == 0
		})
	})
}

func exchange(test *testing.T, ctx context.Context, sender, receiver packet, payload []byte) {
	test.Helper()
	sent := make(chan error, 1)
	go func() { sent <- sender.SendContext(ctx, payload) }()
	actual, err := receiver.Recv(ctx)
	if err != nil || !bytes.Equal(actual, payload) {
		test.Fatalf("byte exact/order: error=%v got=%d expected=%d", err, len(actual), len(payload))
	}
	if err := <-sent; err != nil {
		test.Fatal("send failed", err)
	}
}

func payload(index int) []byte { return bytes.Repeat([]byte{byte(index + 1)}, 1024+index) }

func collect(test *testing.T, value *pair, count int) {
	test.Helper()
	value.reverse.hold()
	for index := 0; index < 8; index++ {
		exchange(test, value.ctx, value.client, value.gateway, payload(index))
		if err := value.gateway.SendContext(value.ctx, payload(index)); err != nil {
			test.Fatal(err)
		}
	}
	await(test, "bounded real-peer accumulation", 6*time.Second, func() bool { return value.reverse.count() >= count })
	if value.gateway.stats()["SendHighWater"].(float64) > 8 {
		test.Fatal("peer exceeded default window")
	}
}

func record(test *testing.T, kind string, value any) {
	test.Helper()
	raw, _ := json.Marshal(value)
	test.Log("MIXED", kind, string(raw))
}

var versionPairs = []struct{ name, client, gateway string }{
	{"C_NEW_RECEIVES_G_CANDIDATE", "new", "candidate"},
	{"G_CANDIDATE_RECEIVES_C_NEW", "candidate", "new"},
	{"C_INSTALLED_RECEIVES_G_CANDIDATE", "oldclient", "candidate"},
	{"G_CANDIDATE_RECEIVES_C_INSTALLED", "candidate", "oldclient"},
}

func burstCase(test *testing.T, versions struct{ name, client, gateway string }, count int, stall bool, stale ...carrier) {
	value := newPair(test, versions.client, versions.gateway)
	for _, previous := range stale {
		if previous.Deliver([]byte("late A callback while B ready")) {
			test.Fatal("old carrier accepted late delivery")
		}
	}
	if count == 0 {
		for index := 0; index < 16; index++ {
			exchange(test, value.ctx, value.client, value.gateway, payload(index))
			exchange(test, value.ctx, value.gateway, value.client, payload(index))
		}
		record(test, "normal", map[string]any{"client": value.client.stats(), "gateway": value.gateway.stats()})
		return
	}
	deliveredBefore := value.client.stats()["DeliveredBytes"]
	collect(test, value, count)
	var releaseGate chan struct{}
	var entered chan struct{}
	if stall {
		releaseGate, entered = make(chan struct{}), make(chan struct{})
		value.forward.mu.Lock()
		value.forward.gate, value.forward.entered = releaseGate, entered
		value.forward.mu.Unlock()
		defer func() {
			if releaseGate != nil {
				close(releaseGate)
			}
		}()
	}
	observation := value.reverse.release(count, false)
	record(test, "burst", observation)
	if value.clientPoint.Snapshot()["closed"].(bool) {
		record(test, "supported_burst_failure", value.clientPoint.Snapshot())
		if versions.client == "oldclient" {
			record(test, "KNOWN_OLD_RECEIVER_LIMIT", value.clientPoint.Snapshot())
		}
		if versions.client == "oldclient" && count > 16 {
			return
		}
		test.Fatal("supported real-peer burst closed carrier")
	}
	await(test, "prefix dequeued", time.Second, func() bool { return value.clientPoint.Snapshot()["depth"].(int) == 0 })
	record(test, "remainder", value.reverse.release(64, true))
	await(test, "slow upper consumer accepted full window", time.Second, func() bool { return value.client.stats()["DataReceived"].(float64) >= 9 })
	if value.client.stats()["DeliveredBytes"] != deliveredBefore {
		test.Fatal("payload consumed without upper reader")
	}
	record(test, "slow_upper_consumer_before_resume", value.client.stats())
	if stall {
		select {
		case <-entered:
		case <-time.After(time.Second):
			test.Fatal("outbound stall not entered")
		}
		record(test, "while_outbound_gated", value.client.stats())
		close(releaseGate)
		releaseGate = nil
	}
	for index := 0; index < 8; index++ {
		actual, err := value.client.Recv(value.ctx)
		if err != nil || !bytes.Equal(actual, payload(index)) {
			test.Fatalf("burst byte exact/order index=%d error=%v", index, err)
		}
	}
	await(test, "ACK freed peer window", time.Second, func() bool {
		return value.gateway.stats()["SendDepth"].(float64) == 0 && value.client.stats()["SendDepth"].(float64) == 0
	})
	for index := 0; index < 8; index++ {
		exchange(test, value.ctx, value.gateway, value.client, payload(20+index))
		exchange(test, value.ctx, value.client, value.gateway, payload(30+index))
	}
	if value.client.stats()["Terminal"].(string) != "" || value.gateway.stats()["Terminal"].(string) != "" {
		test.Fatal("unexpected terminal")
	}
	record(test, "recovered", map[string]any{"client": value.client.stats(), "gateway": value.gateway.stats(), "queue": value.clientPoint.Snapshot()})
}

func TestGatewaySupported(test *testing.T) {
	for _, versions := range versionPairs {
		test.Run(versions.name, func(test *testing.T) {
			for _, count := range []int{0, 8, 16, 19, 20, 40} {
				test.Run(fmt.Sprint(count), func(test *testing.T) { burstCase(test, versions, count, false) })
			}
		})
	}
}

func TestGatewayOutboundStall(test *testing.T) {
	for _, versions := range versionPairs {
		test.Run(versions.name, func(test *testing.T) {
			count := 20
			if versions.client == "oldclient" {
				count = 16
			}
			burstCase(test, versions, count, true)
		})
	}
}

func TestGatewayLifecycle(test *testing.T) {
	for _, versions := range versionPairs {
		test.Run(versions.name, func(test *testing.T) {
			for _, held := range []bool{false, true} {
				test.Run(fmt.Sprint(held), func(test *testing.T) {
					previous := newPair(test, versions.client, versions.gateway)
					gate, entered := make(chan struct{}), make(chan struct{})
					if held {
						previous.clientPoint.SetCloseGate(gate, entered)
					}
					previous.cancel()
					done := make(chan struct{})
					go func() { previous.client.Close(); previous.gateway.Close(); close(done) }()
					if held {
						select {
						case <-entered:
						case <-time.After(time.Second):
							test.Fatal("old cleanup gate not entered")
						}
					} else {
						<-done
					}
					await(test, "old carrier closed", time.Second, func() bool { return previous.clientPoint.Snapshot()["closed"].(bool) })
					test.Run("B", func(test *testing.T) {
						count := 20
						if versions.client == "oldclient" {
							count = 16
						}
						burstCase(test, versions, count, false, previous.clientPoint)
					})
					close(gate)
					select {
					case <-done:
					case <-time.After(time.Second):
						test.Fatal("held A cleanup did not complete")
					}
					previous.close(test)
				})
			}
		})
	}
}

func TestGatewaySACKReorder(test *testing.T) {
	for _, versions := range versionPairs {
		test.Run(versions.name, func(test *testing.T) {
			value := newPair(test, versions.client, versions.gateway)
			value.reverse.hold()
			for index := 0; index < 3; index++ {
				if err := value.gateway.SendContext(value.ctx, payload(44+index)); err != nil {
					test.Fatal(err)
				}
			}
			value.reverse.mu.Lock()
			indices := []int{}
			for index, frame := range value.reverse.frames {
				if frame[4] == 2 {
					indices = append(indices, index)
				}
			}
			if len(indices) != 3 {
				value.reverse.mu.Unlock()
				test.Fatal("real three DATA not captured")
			}
			index := indices[1]
			second := value.reverse.frames[index]
			value.reverse.frames = append(value.reverse.frames[:index], value.reverse.frames[index+1:]...)
			value.reverse.mu.Unlock()
			sacks := value.gateway.stats()["SACKReceived"].(float64)
			value.clientPoint.Deliver(second)
			await(test, "actual SACK returned to peer", time.Second, func() bool { return value.gateway.stats()["SACKReceived"].(float64) > sacks })
			record(test, "sack_gap_observed", map[string]any{"client": value.client.stats(), "gateway": value.gateway.stats()})
			value.reverse.release(64, true)
			for index := 0; index < 3; index++ {
				data, err := value.client.Recv(value.ctx)
				if err != nil || !bytes.Equal(data, payload(44+index)) {
					test.Fatal("SACK/gap delivery ordering", err)
				}
			}
			await(test, "SACK window freed after consumption", time.Second, func() bool { return value.gateway.stats()["SendDepth"].(float64) == 0 })
			exchange(test, value.ctx, value.gateway, value.client, []byte("after-sack-gap"))
		})
	}
}

func TestGatewayOverloadAndCancel(test *testing.T) {
	value := newPair(test, "candidate", "new")
	collect(test, value, 20)
	value.reverse.mu.Lock()
	replay := bytes.Clone(value.reverse.frames[0])
	value.reverse.mu.Unlock()
	gate := make(chan struct{})
	value.clientPoint.SetReadGate(gate)
	capacity := value.clientPoint.Snapshot()["capacity"].(int)
	for index := 0; index < capacity*4; index++ {
		value.clientPoint.Deliver(bytes.Clone(replay))
	}
	observation := value.clientPoint.Snapshot()
	record(test, "separate_replay_overload_guard", observation)
	if !observation["closed"].(bool) || observation["depth"].(int) > capacity {
		test.Fatal("finite observable overload guard absent")
	}
	value.close(test)
	close(gate)
}

func familyOpen(ctx context.Context, version string, point carrier, raw []byte, server bool) (packet, error) {
	switch version {
	case "candidate":
		return candidatefamily.Open(ctx, point, raw, server)
	case "oldgateway":
		return oldfamily.Open(ctx, point, raw, server)
	case "oldclient":
		return clientfamily.Open(ctx, point, raw, server)
	default:
		return newfamily.Open(ctx, point, raw, server)
	}
}

func TestGatewayFamilyTLS(test *testing.T) {
	for _, versions := range versionPairs {
		test.Run(versions.name, func(test *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
			defer cancel()
			forward, reverse := &wire{}, &wire{}
			clientPoint, gatewayPoint := newPoint(test, ctx, versions.client, forward), newPoint(test, ctx, versions.gateway, reverse)
			forward.target, reverse.target = gatewayPoint, clientPoint
			defer clientPoint.Close()
			defer gatewayPoint.Close()
			clientProfile, gatewayProfile := profiles(test)
			clientRaw, _ := json.Marshal(clientProfile)
			gatewayRaw, _ := json.Marshal(gatewayProfile)
			type result struct {
				session packet
				err     error
			}
			opened := make(chan result, 1)
			go func() {
				session, err := familyOpen(ctx, versions.gateway, gatewayPoint, gatewayRaw, true)
				opened <- result{session, err}
			}()
			client, err := familyOpen(ctx, versions.client, clientPoint, clientRaw, false)
			if err != nil {
				test.Fatal(err)
			}
			defer client.Close()
			gateway := <-opened
			if gateway.err != nil {
				test.Fatal(gateway.err)
			}
			defer gateway.session.Close()
			for _, size := range []int{1, 4096, 16384, 65536} {
				data := bytes.Repeat([]byte{byte(size % 251)}, size)
				exchange(test, ctx, client, gateway.session, data)
				exchange(test, ctx, gateway.session, client, data)
			}
			record(test, "family_tls", map[string]any{"pair": versions.name, "handshake": "PASS", "byte_exact_both_directions": "PASS"})
		})
	}
}
