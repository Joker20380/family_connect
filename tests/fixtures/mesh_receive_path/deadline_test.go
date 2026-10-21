package telemost

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sync"
	"testing"
	"time"

	"github.com/pion/interceptor"
	"github.com/pion/rtp"
	"github.com/pion/rtp/codecs"
	"github.com/pion/transport/v4/packetio"
)

type deadlineEvent struct {
	at     time.Time
	packet *rtp.Packet
}

type finiteResult struct {
	lateOutput
	PendingAssemblies          int
	PartialCarrierBytes        int
	PartialVP8Bytes            int
	PendingAfterExistingExpiry int
}

type deadlineTimeout struct{}

func (deadlineTimeout) Error() string   { return "deadline" }
func (deadlineTimeout) Timeout() bool   { return true }
func (deadlineTimeout) Temporary() bool { return true }

type deadlineReader struct {
	now     time.Time
	due     time.Time
	events  []deadlineEvent
	wakes   []time.Time
	sets    []time.Time
	inspect func()
}

func (reader *deadlineReader) SetReadDeadline(due time.Time) error {
	reader.due = due
	reader.sets = append(reader.sets, due)
	return nil
}

func TestDeadlineNoExtensionAndTimerCleared(test *testing.T) {
	origin := time.Now()
	reader := &deadlineReader{now: origin}
	reader.events = append(reader.events, deadlineEvent{origin, deadlinePacket(1, 1, true, true)})
	for sequence := uint16(3); sequence < 103; sequence++ {
		reader.events = append(reader.events, deadlineEvent{origin.Add(time.Duration(sequence-3) * time.Millisecond), deadlinePacket(sequence, uint32(sequence), true, true)})
	}
	buffer := newReorderBuffer()
	buffer.now = func() time.Time { return reader.now }
	if err := readReorderedRTP(reader, buffer, nil, func(*rtp.Packet) {}, func(*rtp.Packet) {}); err != io.EOF {
		test.Fatal(err)
	}
	if len(reader.wakes) != 1 || !reader.wakes[0].Equal(origin.Add(125*time.Millisecond)) || len(reader.sets) != 4 || !reader.due.IsZero() {
		test.Fatal("deadline reset per packet or left active", reader.sets, reader.wakes)
	}
}

func TestDeadlineCloseAtExpiryAndReplacement(test *testing.T) {
	for _, closeAt := range []string{"arrival", "deadline"} {
		test.Run(closeAt, func(test *testing.T) {
			origin := time.Now()
			reader := &deadlineReader{now: origin, events: []deadlineEvent{{origin, deadlinePacket(1, 1, true, true)}, {origin, deadlinePacket(3, 3, true, true)}}}
			closed := make(chan struct{})
			buffer := newReorderBuffer()
			buffer.now = func() time.Time { return reader.now }
			var ordered []uint16
			reader.inspect = func() {
				if !buffer.deadline().IsZero() {
					close(closed)
					reader.inspect = nil
				}
			}
			if closeAt == "arrival" {
				reader.events = append(reader.events, deadlineEvent{origin.Add(125 * time.Millisecond), deadlinePacket(2, 2, true, true)})
			}
			err := readReorderedRTP(reader, buffer, closed, func(*rtp.Packet) {}, func(packet *rtp.Packet) { ordered = append(ordered, packet.SequenceNumber) })
			if err != ErrClosed || len(ordered) != 1 || !reader.due.IsZero() {
				test.Fatal("closed epoch mutated", err, ordered)
			}
			fresh := newReorderBuffer()
			fresh.now = buffer.now
			fresh.push(deadlinePacket(1, 1, true, true), func(packet *rtp.Packet) { ordered = append(ordered, packet.SequenceNumber) })
			if len(ordered) != 2 || !fresh.deadline().IsZero() {
				test.Fatal("old deadline reached replacement")
			}
		})
	}
}

func (reader *deadlineReader) Read(buffer []byte) (int, interceptor.Attributes, error) {
	if reader.inspect != nil {
		reader.inspect()
	}
	if !reader.due.IsZero() && (len(reader.events) == 0 || !reader.events[0].at.Before(reader.due)) {
		reader.now = reader.due
		reader.wakes = append(reader.wakes, reader.due)
		return 0, nil, deadlineTimeout{}
	}
	if len(reader.events) == 0 {
		return 0, nil, io.EOF
	}
	event := reader.events[0]
	reader.events = reader.events[1:]
	reader.now = event.at
	encoded, err := event.packet.Marshal()
	if err != nil {
		return 0, nil, err
	}
	return copy(buffer, encoded), nil, nil
}

func deadlinePacket(sequence uint16, timestamp uint32, marker, start bool) *rtp.Packet {
	flag := byte(0)
	if start {
		flag = 0x10
	}
	return &rtp.Packet{Header: rtp.Header{Version: 2, SequenceNumber: sequence, Timestamp: timestamp, Marker: marker}, Payload: append([]byte{flag}, bytes.Repeat([]byte{byte(sequence)}, 32)...)}
}

func TestDeadlineRecorded(test *testing.T) {
	encoded, err := os.ReadFile("late-arrival-input.json")
	if err != nil {
		test.Fatal(err)
	}
	var input struct {
		Episodes []lateEpisode `json:"episodes"`
	}
	if err := json.Unmarshal(encoded, &input); err != nil {
		test.Fatal(err)
	}
	var outputs []finiteResult
	for _, episode := range input.Episodes {
		for _, budget := range []int{100, 125} {
			test.Run(fmt.Sprintf("%d/%d", episode.Sequence, budget), func(test *testing.T) {
				packets, payloads := latePackets(test, episode)
				reader := &deadlineReader{now: time.Unix(0, episode.Arrivals[0].NS-1_000_000)}
				if episode.Sequence == 1294 {
					for sequence := uint16(9903); sequence <= 9908; sequence++ {
						reader.events = append(reader.events, deadlineEvent{reader.now, packets[sequence]})
					}
				}
				for _, point := range episode.Arrivals {
					reader.events = append(reader.events, deadlineEvent{time.Unix(0, point.NS), packets[point.First]})
				}
				buffer := newReorderBuffer()
				buffer.gapBudget, buffer.now = time.Duration(budget)*time.Millisecond, func() time.Time { return reader.now }
				state := vp8FrameState{}
				result := lateOutput{Sequence: episode.Sequence, BudgetMS: budget, Frames: map[uint32]int64{}, Messages: map[uint32]int64{}, ByteExactSynthetic: true}
				inspect := func(inflight *rtp.Packet) {
					count, size, capacity := len(buffer.pkts), 0, 0
					for _, packet := range buffer.pkts {
						size += len(packet.Payload)
						capacity += cap(packet.Payload)
					}
					for _, packet := range buffer.free {
						capacity += cap(packet.Payload)
					}
					pool := count + len(buffer.free)
					if inflight != nil {
						count++
						pool++
						size += len(inflight.Payload)
						capacity += cap(inflight.Payload)
					}
					result.PeakPackets = max(result.PeakPackets, count)
					result.PeakPayloadBytes = max(result.PeakPayloadBytes, size)
					result.PeakPayloadCapacity = max(result.PeakPayloadCapacity, capacity)
					result.PeakPoolPackets = max(result.PeakPoolPackets, pool)
					if pool > 256 || capacity > 256*2048 {
						test.Fatal("unbounded resources")
					}
				}
				reader.inspect = func() { inspect(nil) }
				assembler := newReassembler(99, func(data []byte) {
					for message, expected := range payloads {
						if bytes.Equal(data, expected) {
							result.Messages[message] = reader.now.UnixNano()
							return
						}
					}
					test.Fatal("corrupted synthetic message")
				})
				assembler.now = buffer.now
				err := readReorderedRTP(reader, buffer, nil, func(packet *rtp.Packet) {
					if buffer.started && seqLess(packet.SequenceNumber, buffer.nextSeq) {
						result.Old = append(result.Old, packet.SequenceNumber)
					}
				}, func(packet *rtp.Packet) {
					inspect(packet)
					if state.frameValid && (state.haveLastSeq && packet.SequenceNumber != state.lastSeq+1 || packet.Timestamp != state.timestamp) {
						result.FrameDiscards++
					}
					frame := state.process(packet)
					if frame != nil {
						result.Frames[packet.Timestamp] = reader.now.UnixNano()
						if fragment, ok := decodeVP8Frame(frame); ok {
							assembler.ingest(fragment)
						}
					}
				})
				if err != io.EOF {
					test.Fatal(err)
				}
				result.PendingPackets = len(buffer.pkts)
				if result.PendingPackets != 0 || !buffer.deadline().IsZero() {
					test.Fatal("silent gap retained")
				}
				_, rescued := result.Messages[2969335140]
				if episode.Sequence == 1294 && rescued != (budget == 125) {
					test.Fatal("unexpected 1294 result", rescued)
				}
				finite := finiteResult{lateOutput: result, PendingAssemblies: len(assembler.builds), PartialVP8Bytes: len(state.frameBuf)}
				for _, builder := range assembler.builds {
					for _, fragment := range builder.received {
						finite.PartialCarrierBytes += len(fragment)
					}
				}
				reader.now = reader.now.Add(reassemblyTimeout + time.Second)
				assembler.prune()
				finite.PendingAfterExistingExpiry = len(assembler.builds)
				if finite.PendingAfterExistingExpiry != 0 {
					test.Fatal("existing carrier expiry failed")
				}
				outputs = append(outputs, finite)
			})
		}
	}
	if output := os.Getenv("REPLAY_OUTPUT"); output != "" {
		encoded, err := json.MarshalIndent(outputs, "", "  ")
		if err != nil {
			test.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(output, "deadline-results.json"), encoded, 0600); err != nil {
			test.Fatal(err)
		}
	}
}

func TestDeadlineOrderAndSilence(test *testing.T) {
	for _, budget := range []time.Duration{100 * time.Millisecond, 125 * time.Millisecond} {
		for _, arrival := range []time.Duration{-1, 1 * time.Millisecond, budget - time.Nanosecond, budget, budget + time.Nanosecond} {
			test.Run(fmt.Sprintf("%s/%s", budget, arrival), func(test *testing.T) {
				origin := time.Now()
				reader := &deadlineReader{now: origin, events: []deadlineEvent{
					{origin, deadlinePacket(1, 1, false, true)},
					{origin, deadlinePacket(3, 1, true, false)},
				}}
				if arrival >= 0 {
					reader.events = append(reader.events, deadlineEvent{origin.Add(arrival), deadlinePacket(2, 1, false, false)})
				}
				buffer := newReorderBuffer()
				buffer.now, buffer.gapBudget = func() time.Time { return reader.now }, budget
				state := vp8FrameState{}
				var frames [][]byte
				err := readReorderedRTP(reader, buffer, nil, func(*rtp.Packet) {}, func(packet *rtp.Packet) {
					if frame := state.process(packet); frame != nil {
						frames = append(frames, append([]byte(nil), frame...))
					}
				})
				if err != io.EOF || len(buffer.pkts) != 0 {
					test.Fatal(err, len(buffer.pkts))
				}
				if arrival >= 0 && arrival < budget {
					expected := append(append(bytes.Repeat([]byte{1}, 32), bytes.Repeat([]byte{2}, 32)...), bytes.Repeat([]byte{3}, 32)...)
					if len(frames) != 1 || !bytes.Equal(frames[0], expected) {
						test.Fatal(frames)
					}
					if len(reader.wakes) != 0 {
						test.Fatal("stale deadline")
					}
				} else if len(frames) != 0 || len(reader.wakes) != 1 {
					test.Fatal("invalid frame or no finite wake")
				}
			})
		}
	}
}

func TestDeadlineGapsWindowWrapAndEpoch(test *testing.T) {
	for _, budget := range []time.Duration{100 * time.Millisecond, 125 * time.Millisecond} {
		test.Run(budget.String(), func(test *testing.T) {
			origin := time.Now()
			reader := &deadlineReader{now: origin, events: []deadlineEvent{
				{origin, deadlinePacket(65533, 0xfffffff0, false, true)},
				{origin, deadlinePacket(65535, 0xfffffff0, true, false)},
				{origin.Add(time.Millisecond), deadlinePacket(65534, 0xfffffff0, false, false)},
				{origin.Add(2 * time.Millisecond), deadlinePacket(1, 10, false, true)},
				{origin.Add(3 * time.Millisecond), deadlinePacket(3, 10, true, false)},
				{origin.Add(4 * time.Millisecond), deadlinePacket(5, 20, true, true)},
			}}
			buffer := newReorderBuffer()
			buffer.gapBudget, buffer.now = budget, func() time.Time { return reader.now }
			var completed []uint32
			state := vp8FrameState{}
			if err := readReorderedRTP(reader, buffer, nil, func(*rtp.Packet) {}, func(packet *rtp.Packet) {
				if state.process(packet) != nil {
					completed = append(completed, packet.Timestamp)
				}
			}); err != io.EOF {
				test.Fatal(err)
			}
			if len(completed) != 2 || completed[0] != 0xfffffff0 || completed[1] != 20 {
				test.Fatal(completed)
			}
			if len(reader.wakes) != 3 || !reader.wakes[0].Equal(origin.Add(2*time.Millisecond+budget)) {
				test.Fatal(reader.wakes)
			}
			if !reader.now.Equal(origin.Add(2*time.Millisecond+3*budget)) || len(buffer.pkts) != 0 {
				test.Fatal("nonfinite gaps")
			}
			buffer = newReorderBuffer()
			buffer.now = func() time.Time { return origin }
			var ordered []uint16
			deliver := func(packet *rtp.Packet) { ordered = append(ordered, packet.SequenceNumber) }
			buffer.push(deadlinePacket(1, 1, true, true), deliver)
			buffer.push(deadlinePacket(3, 2, true, true), deliver)
			buffer.push(deadlinePacket(258, 3, true, true), deliver)
			if len(ordered) != 2 || ordered[1] != 258 || len(buffer.pkts) != 0 {
				test.Fatal("distance window")
			}
			fresh := newReorderBuffer()
			fresh.now = buffer.now
			fresh.push(deadlinePacket(1, 1, true, true), deliver)
			if ordered[len(ordered)-1] != 1 || fresh.nextSeq != 2 {
				test.Fatal("epoch mixed")
			}
		})
	}
}

func TestDeadlineByteOwnershipDuplicateAndCorruption(test *testing.T) {
	origin := time.Now()
	buffer := newReorderBuffer()
	buffer.now = func() time.Time { return origin }
	var ordered [][]byte
	deliver := func(packet *rtp.Packet) { ordered = append(ordered, append([]byte(nil), packet.Payload...)) }
	buffer.push(deadlinePacket(1, 1, true, true), deliver)
	packet := deadlinePacket(3, 3, true, true)
	buffer.push(packet, deliver)
	packet.Payload[1] = 99
	buffer.push(deadlinePacket(3, 3, true, true), deliver)
	buffer.push(deadlinePacket(2, 2, true, true), deliver)
	if len(ordered) != 3 || ordered[2][1] != 3 {
		test.Fatal(ordered)
	}
	buffer.push(deadlinePacket(2, 2, true, true), deliver)
	if len(ordered) != 3 {
		test.Fatal("old duplicate delivered")
	}
	data := bytes.Repeat([]byte{44}, 9000)
	fragments, err := encodeFragments(1, 7, data)
	if err != nil {
		test.Fatal(err)
	}
	var messages [][]byte
	assembler := newReassembler(99, func(value []byte) { messages = append(messages, value) })
	assembler.ingest(fragments[0])
	bad := append([]byte(nil), fragments[1]...)
	bad[len(bad)-1] ^= 1
	assembler.ingest(bad)
	if len(messages) != 0 {
		test.Fatal("CRC bypass")
	}
	assembler.ingest(fragments[0])
	assembler.ingest(fragments[1])
	if len(messages) != 0 {
		test.Fatal("corrupt identity reused")
	}
	fragments, err = encodeFragments(1, 8, data)
	if err != nil {
		test.Fatal(err)
	}
	assembler.ingest(fragments[0])
	assembler.ingest(fragments[1])
	if len(messages) != 1 || !bytes.Equal(data, messages[0]) {
		test.Fatal("CRC recovery")
	}
}

func TestDeadlineACKAfterIncompleteData(test *testing.T) {
	for _, budget := range []time.Duration{100 * time.Millisecond, 125 * time.Millisecond} {
		test.Run(budget.String(), func(test *testing.T) {
			origin := time.Now()
			reader := &deadlineReader{now: origin}
			payloads := [][]byte{bytes.Repeat([]byte{41}, 8000), []byte("ACK-control-byte-exact")}
			payloader := codecs.VP8Payloader{}
			sequence := uint16(1)
			for index, payload := range payloads {
				fragments, err := encodeFragments(1, uint32(index+1), payload)
				if err != nil {
					test.Fatal(err)
				}
				packets := payloader.Payload(1200, encodeVP8DataFrame(fragments[0]))
				for part, data := range packets {
					if sequence != 2 {
						reader.events = append(reader.events, deadlineEvent{origin, &rtp.Packet{Header: rtp.Header{Version: 2, SequenceNumber: sequence, Timestamp: uint32(index + 1), Marker: part == len(packets)-1}, Payload: data}})
					}
					sequence++
				}
			}
			buffer := newReorderBuffer()
			buffer.gapBudget, buffer.now = budget, func() time.Time { return reader.now }
			var output [][]byte
			assembler := newReassembler(99, func(data []byte) { output = append(output, data) })
			state := vp8FrameState{}
			err := readReorderedRTP(reader, buffer, nil, func(*rtp.Packet) {}, func(packet *rtp.Packet) {
				if frame := state.process(packet); frame != nil {
					if fragment, ok := decodeVP8Frame(frame); ok {
						assembler.ingest(fragment)
					}
				}
			})
			if err != io.EOF || len(output) != 1 || !bytes.Equal(output[0], payloads[1]) || !reader.now.Equal(origin.Add(budget)) {
				test.Fatal("control blocked/corrupted", err)
			}
		})
	}
}

func TestDeadlineBoundedWindowAndConsumer(test *testing.T) {
	origin := time.Now()
	buffer := newReorderBuffer()
	buffer.now = func() time.Time { return origin }
	buffer.push(deadlinePacket(0, 0, true, true), func(*rtp.Packet) {})
	for sequence := uint16(2); sequence <= 256; sequence++ {
		buffer.push(deadlinePacket(sequence, 1, true, true), func(*rtp.Packet) {})
	}
	if len(buffer.pkts) != 255 || len(buffer.pkts)+len(buffer.free) > 256 {
		test.Fatal("packet bound")
	}
	first := buffer.deadline()
	buffer.push(deadlinePacket(257, 2, true, true), func(*rtp.Packet) {})
	if len(buffer.pkts) != 0 || buffer.nextSeq != 258 || !buffer.deadline().IsZero() || !origin.Before(first) {
		test.Fatal("window did not precede deadline")
	}
	session := testSession(test)
	for count := 0; count <= cap(session.recvQueue); count++ {
		fragments, err := encodeFragments(session.senderID+1, uint32(count), []byte("bounded upper consumer"))
		if err != nil {
			test.Fatal(err)
		}
		session.reassembler.ingest(fragments[0])
	}
	if !session.closed.Load() || len(session.recvQueue) != cap(session.recvQueue) {
		test.Fatal("slow consumer did not fail closed at existing bound")
	}
	if err := session.Close(); err != nil {
		test.Fatal(err)
	}
}

func TestDeadlineConflictingFragment(test *testing.T) {
	first, _ := encodeFragments(1, 1, bytes.Repeat([]byte{3}, 9000))
	other, _ := encodeFragments(1, 1, bytes.Repeat([]byte{4}, 9000))
	deliveries := 0
	assembler := newReassembler(99, func([]byte) { deliveries++ })
	assembler.ingest(first[0])
	assembler.ingest(other[1])
	assembler.ingest(first[1])
	if deliveries != 0 || assembler.metrics.Conflict != 1 {
		test.Fatal("conflict not rejected")
	}
}

type deadlinePacketIO struct{ *packetio.Buffer }

func (reader deadlinePacketIO) Read(buffer []byte) (int, interceptor.Attributes, error) {
	length, err := reader.Buffer.Read(buffer)
	return length, nil, err
}

type deadlineArmedReader struct {
	deadlinePacketIO
	armed chan time.Time
	once  sync.Once
	last  time.Time
}

func (reader *deadlineArmedReader) SetReadDeadline(due time.Time) error {
	reader.last = due
	err := reader.Buffer.SetReadDeadline(due)
	if !due.IsZero() {
		reader.once.Do(func() { reader.armed <- due })
	}
	return err
}

func TestDeadlinePionCloseWithActiveTimer(test *testing.T) {
	for _, atExpiry := range []bool{false, true} {
		test.Run(fmt.Sprint(atExpiry), func(test *testing.T) {
			reader := &deadlineArmedReader{deadlinePacketIO: deadlinePacketIO{packetio.NewBuffer()}, armed: make(chan time.Time, 1)}
			reader.SetLimitCount(256)
			defer reader.Close()
			closed := make(chan struct{})
			done := make(chan error, 1)
			buffer := newReorderBuffer()
			go func() { done <- readReorderedRTP(reader, buffer, closed, func(*rtp.Packet) {}, func(*rtp.Packet) {}) }()
			for _, sequence := range []uint16{1, 3} {
				encoded, _ := deadlinePacket(sequence, 1, true, true).Marshal()
				reader.Write(encoded)
			}
			due := <-reader.armed
			if atExpiry {
				timer := time.NewTimer(time.Until(due))
				<-timer.C
			}
			var workers sync.WaitGroup
			workers.Add(2)
			go func() {
				defer workers.Done()
				encoded, _ := deadlinePacket(2, 1, true, true).Marshal()
				reader.Write(encoded)
			}()
			go func() { defer workers.Done(); close(closed); reader.Close() }()
			workers.Wait()
			select {
			case <-done:
			case <-time.After(3 * time.Second):
				test.Fatal("active timer or reader leaked")
			}
			if !reader.last.IsZero() {
				test.Fatal("timer not cancelled")
			}
		})
	}
}

func TestDeadlinePionSilenceAndClose(test *testing.T) {
	for _, budget := range []time.Duration{100 * time.Millisecond, 125 * time.Millisecond} {
		test.Run(budget.String(), func(test *testing.T) {
			reader := deadlinePacketIO{packetio.NewBuffer()}
			reader.SetLimitCount(256)
			defer reader.Close()
			buffer := newReorderBuffer()
			buffer.gapBudget = budget
			delivered := make(chan uint16, 3)
			wakes := make(chan time.Duration, 1)
			done := make(chan error, 1)
			go func() {
				done <- readReorderedRTP(reader, buffer, nil, func(*rtp.Packet) {}, func(packet *rtp.Packet) {
					if packet.SequenceNumber == 3 {
						wakes <- time.Since(buffer.deadline())
					}
					delivered <- packet.SequenceNumber
				})
			}()
			for _, sequence := range []uint16{1, 3} {
				packet, _ := deadlinePacket(sequence, uint32(sequence), true, true).Marshal()
				if _, err := reader.Write(packet); err != nil {
					test.Fatal(err)
				}
			}
			for _, expected := range []uint16{1, 3} {
				select {
				case actual := <-delivered:
					if actual != expected {
						test.Fatal(actual)
					}
				case <-time.After(3 * time.Second):
					test.Fatal("reader did not serve silent deadline")
				}
			}
			test.Logf("scheduler_lateness=%s budget=%s", <-wakes, budget)
			reader.Close()
			select {
			case err := <-done:
				if !errors.Is(err, io.EOF) {
					test.Fatal(err)
				}
			case <-time.After(3 * time.Second):
				test.Fatal("blocked read leaked")
			}
			if len(buffer.pkts) != 0 {
				test.Fatal("buffer retained")
			}
		})
	}
}

func TestDeadlineCloseArrivalAndSlowConsumer(test *testing.T) {
	for iteration := 0; iteration < 40; iteration++ {
		reader := deadlinePacketIO{packetio.NewBuffer()}
		reader.SetLimitCount(256)
		buffer := newReorderBuffer()
		entered, release := make(chan struct{}), make(chan struct{})
		closed := make(chan struct{})
		done := make(chan error, 1)
		go func() {
			done <- readReorderedRTP(reader, buffer, closed, func(*rtp.Packet) {}, func(packet *rtp.Packet) {
				if packet.SequenceNumber == 1 {
					close(entered)
					<-release
				}
			})
		}()
		packet, _ := deadlinePacket(1, 1, true, true).Marshal()
		reader.Write(packet)
		<-entered
		var workers sync.WaitGroup
		workers.Add(2)
		go func() {
			defer workers.Done()
			for sequence := uint16(3); sequence < 258; sequence++ {
				encoded, _ := deadlinePacket(sequence, 1, true, true).Marshal()
				reader.Write(encoded)
			}
		}()
		go func() { defer workers.Done(); close(closed); reader.Close() }()
		workers.Wait()
		close(release)
		select {
		case <-done:
		case <-time.After(3 * time.Second):
			test.Fatal("worker leak")
		}
		if reader.Count() > 256 || len(buffer.pkts)+len(buffer.free) > 256 {
			test.Fatal("backpressure unbounded")
		}
	}
}
