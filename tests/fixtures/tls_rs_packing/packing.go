package familysession

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"hash"
	"net"
	"os"
	"sync"
	"time"
)

const packingBlock = 16384
const packingSlots = 4

type packingKey struct{}

func WithLabPacking(ctx context.Context, policy string) context.Context {
	if policy != "A" && policy != "B0" && policy != "B2" {
		panic("invalid lab packing policy")
	}
	return context.WithValue(ctx, packingKey{}, policy)
}

type packingStats struct {
	Policy                                                                                                                  string
	Writes, Accepted, Sent, Received                                                                                        uint64
	InputSHA256, OutputSHA256, ReceiveSHA256                                                                                string
	InputSizes, DataSizes, Records                                                                                          map[int]uint64
	Flush                                                                                                                   map[string]uint64
	QueueBytes, MaxQueueBytes                                                                                               int
	MaxAgeNS, CoalescingWaitNS, DeadlineOvershootNS, RSWaitNS, WriteCallNS, WriteBackpressureNS, MaxEligibleDispatchDelayNS int64
	Terminal                                                                                                                string
}

type labPackingConn struct {
	net.Conn
	ctx                         context.Context
	cancel                      context.CancelFunc
	endpoint                    PacketEndpoint
	policy                      string
	mu                          sync.Mutex
	gate                        chan struct{}
	changed                     chan struct{}
	blocks                      *[packingSlots][packingBlock]byte
	sizes                       [packingSlots]int
	born                        [packingSlots]time.Time
	fullAt                      [packingSlots]time.Time
	head, used                  int
	deadline                    time.Time
	terminal                    error
	flushing                    int
	input, output, received     hash.Hash
	stats                       packingStats
	recordHeader                [5]byte
	recordHave, recordRemaining int
}

func newLabPackingConn(ctx context.Context, connection net.Conn, endpoint PacketEndpoint) *labPackingConn {
	policy, _ := ctx.Value(packingKey{}).(string)
	if policy == "" {
		policy = "A"
	}
	ctx, cancel := context.WithCancel(ctx)
	result := &labPackingConn{Conn: connection, ctx: ctx, cancel: cancel, endpoint: endpoint, policy: policy, gate: make(chan struct{}, 1), changed: make(chan struct{}), input: sha256.New(), output: sha256.New(), received: sha256.New(), stats: packingStats{Policy: policy, InputSizes: map[int]uint64{}, DataSizes: map[int]uint64{}, Records: map[int]uint64{}, Flush: map[string]uint64{}}}
	if policy != "A" {
		result.blocks = new([packingSlots][packingBlock]byte)
	}
	return result
}

func (connection *labPackingConn) notify() {
	close(connection.changed)
	connection.changed = make(chan struct{})
}

func packingCount(histogram map[int]uint64, size int) {
	if _, exists := histogram[size]; !exists && len(histogram) >= 256 {
		size = -1
	}
	histogram[size]++
}

func (connection *labPackingConn) accept(data []byte) {
	connection.input.Write(data)
	connection.stats.Accepted += uint64(len(data))
	for len(data) > 0 {
		if connection.recordRemaining > 0 {
			size := min(len(data), connection.recordRemaining)
			connection.recordRemaining -= size
			data = data[size:]
			continue
		}
		size := copy(connection.recordHeader[connection.recordHave:], data)
		connection.recordHave += size
		data = data[size:]
		if connection.recordHave == 5 {
			connection.recordRemaining = int(connection.recordHeader[3])<<8 | int(connection.recordHeader[4])
			packingCount(connection.stats.Records, connection.recordRemaining+5)
			connection.recordHave = 0
		}
	}
}

func (connection *labPackingConn) Write(data []byte) (int, error) {
	if connection.policy == "A" {
		select {
		case connection.gate <- struct{}{}:
		case <-connection.ctx.Done():
			return 0, connection.ctx.Err()
		}
		defer func() { <-connection.gate }()
		count, err := connection.Conn.Write(data)
		connection.mu.Lock()
		connection.stats.Writes++
		packingCount(connection.stats.InputSizes, count)
		connection.accept(data[:count])
		connection.mu.Unlock()
		return count, err
	}
	started := time.Now()
	for {
		connection.mu.Lock()
		deadline, changed, failure := connection.deadline, connection.changed, connection.terminal
		connection.mu.Unlock()
		if failure != nil {
			return 0, failure
		}
		if !deadline.IsZero() && !time.Now().Before(deadline) {
			return 0, os.ErrDeadlineExceeded
		}
		timer := packingTimer(deadline)
		acquired := false
		select {
		case connection.gate <- struct{}{}:
			acquired = true
		case <-changed:
		case <-timer.C:
			timer.Stop()
			return 0, os.ErrDeadlineExceeded
		case <-connection.ctx.Done():
			timer.Stop()
			return 0, connection.ctx.Err()
		}
		timer.Stop()
		if acquired {
			break
		}
	}
	defer func() { <-connection.gate }()
	count := 0
	connection.mu.Lock()
	defer func() {
		connection.stats.Writes++
		packingCount(connection.stats.InputSizes, count)
		connection.stats.WriteCallNS += time.Since(started).Nanoseconds()
		connection.mu.Unlock()
	}()
	for count < len(data) {
		if connection.terminal != nil {
			return count, connection.terminal
		}
		if connection.ctx.Err() != nil {
			return count, connection.ctx.Err()
		}
		if !connection.deadline.IsZero() && !time.Now().Before(connection.deadline) {
			return count, os.ErrDeadlineExceeded
		}
		tail := (connection.head + connection.used - 1 + packingSlots) % packingSlots
		if connection.used == 0 || connection.sizes[tail] == packingBlock {
			if connection.used == packingSlots {
				changed, deadline := connection.changed, connection.deadline
				waited := time.Now()
				connection.mu.Unlock()
				timer := packingTimer(deadline)
				select {
				case <-changed:
				case <-timer.C:
				case <-connection.ctx.Done():
				}
				timer.Stop()
				connection.mu.Lock()
				connection.stats.WriteBackpressureNS += time.Since(waited).Nanoseconds()
				continue
			}
			tail = (connection.head + connection.used) % packingSlots
			connection.used++
			connection.born[tail] = time.Now()
		}
		copied := copy(connection.blocks[tail][connection.sizes[tail]:], data[count:])
		connection.sizes[tail] += copied
		if connection.sizes[tail] == packingBlock {
			connection.fullAt[tail] = time.Now()
		}
		connection.accept(data[count : count+copied])
		count += copied
		connection.stats.QueueBytes += copied
		connection.stats.MaxQueueBytes = max(connection.stats.MaxQueueBytes, connection.stats.QueueBytes)
		connection.notify()
	}
	return count, nil
}

func packingTimer(deadline time.Time) *time.Timer {
	if deadline.IsZero() {
		return time.NewTimer(24 * time.Hour)
	}
	return time.NewTimer(max(0, time.Until(deadline)))
}

func (connection *labPackingConn) run() {
	buffer := make([]byte, packingBlock)
	workerReady := time.Now()
	for {
		connection.mu.Lock()
		if connection.terminal != nil {
			connection.mu.Unlock()
			return
		}
		if connection.used == 0 {
			changed := connection.changed
			connection.mu.Unlock()
			select {
			case <-changed:
			case <-connection.ctx.Done():
				connection.fail(connection.ctx.Err())
				return
			}
			continue
		}
		head := connection.head
		age := time.Since(connection.born[head])
		reason := "full"
		if connection.sizes[head] < packingBlock {
			delay := time.Duration(0)
			if connection.policy == "B2" {
				delay = 2 * time.Millisecond
			}
			if connection.flushing > 0 {
				reason = "explicit"
			} else if age >= delay {
				reason = "deadline"
			} else {
				deadline := connection.born[head].Add(delay)
				changed := connection.changed
				connection.mu.Unlock()
				started := time.Now()
				timer := packingTimer(deadline)
				select {
				case <-changed:
				case <-timer.C:
				case <-connection.ctx.Done():
				}
				timer.Stop()
				connection.mu.Lock()
				connection.stats.CoalescingWaitNS += time.Since(started).Nanoseconds()
				connection.mu.Unlock()
				if connection.ctx.Err() != nil {
					connection.fail(connection.ctx.Err())
					return
				}
				continue
			}
		}
		size := copy(buffer, connection.blocks[head][:connection.sizes[head]])
		eligible := connection.fullAt[head]
		if reason != "full" {
			eligible = connection.born[head]
			if connection.policy == "B2" && reason == "deadline" {
				eligible = eligible.Add(2 * time.Millisecond)
			}
		}
		if eligible.Before(workerReady) {
			eligible = workerReady
		}
		connection.stats.MaxEligibleDispatchDelayNS = max(connection.stats.MaxEligibleDispatchDelayNS, time.Since(eligible).Nanoseconds())
		connection.stats.MaxAgeNS = max(connection.stats.MaxAgeNS, age.Nanoseconds())
		if reason == "deadline" && connection.policy == "B2" {
			connection.stats.DeadlineOvershootNS = max(connection.stats.DeadlineOvershootNS, max(0, age.Nanoseconds()-int64(2*time.Millisecond)))
		}
		connection.stats.Flush[reason]++
		connection.stats.QueueBytes -= size
		connection.sizes[head] = 0
		connection.used--
		connection.head = (head + 1) % packingSlots
		connection.notify()
		connection.mu.Unlock()
		started := time.Now()
		failure := connection.endpoint.SendContext(connection.ctx, buffer[:size])
		workerReady = time.Now()
		connection.mu.Lock()
		connection.stats.RSWaitNS += time.Since(started).Nanoseconds()
		if failure == nil {
			connection.output.Write(buffer[:size])
			connection.stats.Sent += uint64(size)
			packingCount(connection.stats.DataSizes, size)
			connection.notify()
		}
		connection.mu.Unlock()
		if failure != nil {
			connection.fail(failure)
			return
		}
	}
}

func (connection *labPackingConn) fail(failure error) {
	connection.mu.Lock()
	if connection.terminal == nil {
		connection.terminal = failure
		connection.stats.Terminal = failure.Error()
		connection.notify()
	}
	connection.mu.Unlock()
}

func (connection *labPackingConn) observeReceive(data []byte) {
	connection.mu.Lock()
	defer connection.mu.Unlock()
	connection.received.Write(data)
	connection.stats.Received += uint64(len(data))
}

func (connection *labPackingConn) baselineSend(ctx context.Context, data []byte) error {
	started := time.Now()
	err := connection.endpoint.SendContext(ctx, data)
	connection.mu.Lock()
	defer connection.mu.Unlock()
	connection.stats.RSWaitNS += time.Since(started).Nanoseconds()
	if err != nil {
		return err
	}
	connection.output.Write(data)
	connection.stats.Sent += uint64(len(data))
	packingCount(connection.stats.DataSizes, len(data))
	connection.notify()
	return nil
}

func (connection *labPackingConn) snapshot() packingStats {
	connection.mu.Lock()
	defer connection.mu.Unlock()
	result := connection.stats
	clone := func(source map[int]uint64) map[int]uint64 {
		target := map[int]uint64{}
		for size, count := range source {
			target[size] = count
		}
		return target
	}
	result.InputSizes = clone(result.InputSizes)
	result.DataSizes = clone(result.DataSizes)
	result.Records = clone(result.Records)
	result.Flush = map[string]uint64{}
	for reason, count := range connection.stats.Flush {
		result.Flush[reason] = count
	}
	result.InputSHA256 = hex.EncodeToString(connection.input.Sum(nil))
	result.OutputSHA256 = hex.EncodeToString(connection.output.Sum(nil))
	result.ReceiveSHA256 = hex.EncodeToString(connection.received.Sum(nil))
	return result
}

func (connection *labPackingConn) flush(ctx context.Context) error {
	connection.mu.Lock()
	target := connection.stats.Accepted
	connection.flushing++
	connection.notify()
	defer func() { connection.flushing--; connection.mu.Unlock() }()
	for connection.stats.Sent < target {
		if connection.terminal != nil {
			return connection.terminal
		}
		changed := connection.changed
		connection.mu.Unlock()
		select {
		case <-changed:
		case <-ctx.Done():
			connection.mu.Lock()
			return ctx.Err()
		}
		connection.mu.Lock()
	}
	return nil
}

func (connection *labPackingConn) Close() error {
	connection.mu.Lock()
	pending := connection.stats.Accepted > connection.stats.Sent && connection.policy != "A"
	connection.mu.Unlock()
	connection.fail(net.ErrClosed)
	connection.cancel()
	connection.Conn.Close()
	if pending {
		return errors.New("packing abort with locally accepted bytes; remote receipt not established")
	}
	return nil
}

func (connection *labPackingConn) SetWriteDeadline(deadline time.Time) error {
	if connection.policy == "A" {
		return connection.Conn.SetWriteDeadline(deadline)
	}
	connection.mu.Lock()
	connection.deadline = deadline
	connection.notify()
	connection.mu.Unlock()
	return nil
}
func (connection *labPackingConn) SetDeadline(deadline time.Time) error {
	if err := connection.SetReadDeadline(deadline); err != nil {
		return err
	}
	return connection.SetWriteDeadline(deadline)
}
func (session *Session) LabPackingStats() packingStats { return session.stream.lab.snapshot() }
func (session *Session) LabDrain(ctx context.Context) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	if err := session.stream.lab.flush(ctx); err != nil {
		return err
	}
	ticker := time.NewTicker(5 * time.Millisecond)
	defer ticker.Stop()
	for {
		stats := session.reliable.Stats()
		if stats.Terminal != "" {
			return errors.New(stats.Terminal)
		}
		if stats.SendDepth == 0 {
			return nil
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-ticker.C:
		}
	}
}

var _ net.Conn = (*labPackingConn)(nil)
