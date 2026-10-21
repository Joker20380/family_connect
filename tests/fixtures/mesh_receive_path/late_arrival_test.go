package telemost

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"testing"
	"time"

	"github.com/pion/rtp"
	"github.com/pion/rtp/codecs"
)

var replayNow time.Time
var replayBudget = 100 * time.Millisecond
var replayQueued func(*reorderBuffer)

type latePoint struct {
	Index      int    `json:"i"`
	NS         int64  `json:"ns"`
	Timestamp  uint32 `json:"ts"`
	First      uint16 `json:"first"`
	Last       uint16 `json:"last"`
	Next       uint16 `json:"next"`
	Buffered   int    `json:"buffered"`
	Wait       int64  `json:"wait_ns"`
	Sender     uint32 `json:"sender"`
	Message    uint32 `json:"message"`
	Fragment   int    `json:"fragment"`
	Total      int    `json:"total"`
	Stage      string `json:"stage"`
	Result     string `json:"result"`
	Provenance string `json:"provenance"`
}

type lateEpisode struct {
	Sequence int         `json:"sequence"`
	Points   []latePoint `json:"points"`
	Arrivals []latePoint `json:"arrivals"`
}

type lateFrame struct {
	Timestamp uint32
	First     uint16
	Last      uint16
	Identity  latePoint
}

type lateOutput struct {
	Sequence            int
	BudgetMS            int
	Frames              map[uint32]int64
	Messages            map[uint32]int64
	Skips               []lateSkip
	Old                 []uint16
	PeakPackets         int
	PeakPayloadBytes    int
	PeakPayloadCapacity int
	PeakPoolPackets     int
	PendingPackets      int
	FrameDiscards       int
	ByteExactSynthetic  bool
}

type lateSkip struct {
	AtNS     int64
	GapAgeNS int64
	From     uint16
	To       uint16
	Trigger  string
}

func latePackets(test *testing.T, episode lateEpisode) (map[uint16]*rtp.Packet, map[uint32][]byte) {
	test.Helper()
	frames := map[uint32]*lateFrame{}
	for _, point := range episode.Arrivals {
		if point.Total > 0 {
			frames[point.Timestamp] = &lateFrame{Timestamp: point.Timestamp, First: point.First, Identity: point}
		}
	}
	if episode.Sequence == 1294 {
		frames[13593723] = &lateFrame{Timestamp: 13593723, First: 9903,
			Identity: latePoint{Sender: 1327879969, Message: 2969335140, Total: 3}}
	}
	for _, point := range episode.Points {
		if frame := frames[point.Timestamp]; frame != nil && point.Stage == "vp8_reassembled" && point.Result == "ok" {
			frame.Last = point.Last
		}
	}
	payloads := map[uint32][]byte{}
	for _, frame := range frames {
		identity := frame.Identity
		length := (identity.Total-1)*maxFragmentPayload + 44
		if identity.Fragment == identity.Total-1 && frame.Last != 0 {
			length = (identity.Total-1)*maxFragmentPayload + min(maxFragmentPayload, int(uint16(frame.Last-frame.First))*1199+44)
		}
		if len(payloads[identity.Message]) < length {
			payloads[identity.Message] = bytes.Repeat([]byte{byte(identity.Message)}, length)
		}
	}
	packets := map[uint16]*rtp.Packet{}
	payloader := codecs.VP8Payloader{}
	for _, frame := range frames {
		identity := frame.Identity
		fragments, err := encodeFragments(identity.Sender, identity.Message, payloads[identity.Message])
		if err != nil || len(fragments) != identity.Total {
			test.Fatal("fragment shape", err)
		}
		encoded := payloader.Payload(1200, encodeVP8DataFrame(fragments[identity.Fragment]))
		if frame.Last != 0 && uint16(len(encoded)-1) != frame.Last-frame.First {
			test.Fatalf("packet shape ts=%d count=%d first=%d last=%d", frame.Timestamp, len(encoded), frame.First, frame.Last)
		}
		for index, data := range encoded {
			sequence := frame.First + uint16(index)
			packets[sequence] = &rtp.Packet{Header: rtp.Header{SequenceNumber: sequence, Timestamp: frame.Timestamp, Marker: index == len(encoded)-1}, Payload: data}
		}
	}
	for _, point := range episode.Arrivals {
		if packets[point.First] == nil {
			packets[point.First] = &rtp.Packet{Header: rtp.Header{SequenceNumber: point.First, Timestamp: point.Timestamp, Marker: true}, Payload: []byte{0, 1}}
		}
		if packets[point.First].Timestamp != point.Timestamp {
			test.Fatal("timestamp conflict", point.First)
		}
	}
	return packets, payloads
}

func lateRun(test *testing.T, episode lateEpisode, budget int) lateOutput {
	test.Helper()
	packets, payloads := latePackets(test, episode)
	replayBudget = time.Duration(budget) * time.Millisecond
	buffer := newReorderBuffer()
	state := vp8FrameState{}
	result := lateOutput{Sequence: episode.Sequence, BudgetMS: budget, Frames: map[uint32]int64{}, Messages: map[uint32]int64{}, ByteExactSynthetic: true}
	replayQueued = func(queued *reorderBuffer) {
		payloadBytes, capacity := 0, 0
		for _, packet := range queued.pkts {
			payloadBytes += len(packet.Payload)
			capacity += cap(packet.Payload)
		}
		for _, packet := range queued.free {
			capacity += cap(packet.Payload)
		}
		result.PeakPackets = max(result.PeakPackets, len(queued.pkts))
		result.PeakPayloadBytes = max(result.PeakPayloadBytes, payloadBytes)
		result.PeakPayloadCapacity = max(result.PeakPayloadCapacity, capacity)
		result.PeakPoolPackets = max(result.PeakPoolPackets, len(queued.pkts)+len(queued.free))
		if len(queued.pkts)+len(queued.free) > 256 || capacity > 256*2048 {
			test.Fatal("unbounded packet pool")
		}
	}
	defer func() { replayQueued = nil }()
	assembler := newReassembler(99, func(data []byte) {
		for message, expected := range payloads {
			if bytes.Equal(expected, data) {
				result.Messages[message] = replayNow.UnixNano()
				return
			}
		}
		test.Fatal("non-byte-exact synthetic delivery")
	})
	assembler.now = func() time.Time { return replayNow }
	deliver := func(packet *rtp.Packet) {
		if state.frameValid && (state.haveLastSeq && packet.SequenceNumber != state.lastSeq+1 || packet.Timestamp != state.timestamp) {
			result.FrameDiscards++
		}
		frame := state.process(packet)
		if frame == nil {
			return
		}
		result.Frames[packet.Timestamp] = replayNow.UnixNano()
		if fragment, valid := decodeVP8Frame(frame); valid {
			assembler.ingest(fragment)
		}
	}
	if episode.Sequence == 1294 {
		replayNow = time.Unix(0, episode.Arrivals[0].NS-1_000_000)
		for sequence := uint16(9903); sequence <= 9908; sequence++ {
			buffer.push(packets[sequence], deliver)
		}
	}
	for _, point := range episode.Arrivals {
		replayNow = time.Unix(0, point.NS)
		packet := packets[point.First]
		if buffer.started && seqLess(packet.SequenceNumber, buffer.nextSeq) {
			result.Old = append(result.Old, packet.SequenceNumber)
		}
		before, gap, started := buffer.nextSeq, buffer.gapSince, buffer.started
		trigger := ""
		if buffer.started && !seqLess(packet.SequenceNumber, before) {
			if uint16(packet.SequenceNumber-before) >= reorderWindow {
				trigger = "sequence_distance"
			} else if len(buffer.pkts) == reorderWindow-1 && buffer.pkts[packet.SequenceNumber] == nil {
				trigger = "packet_count"
			} else if !gap.IsZero() && replayNow.Sub(gap) > replayBudget {
				trigger = "time"
			}
		}
		first := true
		buffer.push(packet, func(ordered *rtp.Packet) {
			if first && started && ordered.SequenceNumber != before {
				result.Skips = append(result.Skips, lateSkip{AtNS: point.NS, GapAgeNS: replayNow.Sub(gap).Nanoseconds(), From: before, To: ordered.SequenceNumber, Trigger: trigger})
			}
			first = false
			deliver(ordered)
		})
		result.PeakPackets = max(result.PeakPackets, len(buffer.pkts))
		payloadBytes := 0
		for _, queued := range buffer.pkts {
			payloadBytes += len(queued.Payload)
		}
		result.PeakPayloadBytes = max(result.PeakPayloadBytes, payloadBytes)
		if len(buffer.pkts) > 256 || len(buffer.pkts)+len(buffer.free) > 256 || payloadBytes > 256*2048 {
			test.Fatal("unbounded reorder")
		}
	}
	result.PendingPackets = len(buffer.pkts)
	return result
}

func TestLateRecordedSweep(test *testing.T) {
	defer func() { replayBudget = 100 * time.Millisecond }()
	input, err := os.ReadFile("late-arrival-input.json")
	if err != nil {
		test.Fatal(err)
	}
	var decoded struct {
		Episodes []lateEpisode `json:"episodes"`
	}
	if err := json.Unmarshal(input, &decoded); err != nil {
		test.Fatal(err)
	}
	var results []lateOutput
	for _, episode := range decoded.Episodes {
		for _, budget := range []int{100, 110, 125, 200, 350, 500} {
			result := lateRun(test, episode, budget)
			if budget == 100 {
				if len(result.Skips) != 1 || result.Skips[0].Trigger != "time" || result.FrameDiscards != 1 {
					test.Fatalf("baseline did not reproduce %+v", result)
				}
				var discardNS int64
				for _, point := range episode.Points {
					if point.Stage == "frame_discard" {
						discardNS = point.NS
						break
					}
				}
				if delay := discardNS - result.Skips[0].AtNS; delay < 0 || delay > 50_000 {
					test.Fatal("baseline skip differs from saved discard", delay)
				}
			}
			results = append(results, result)
			test.Logf("DATA%d budget=%d complete_messages=%d frames=%d discard=%d old=%v pending=%d peak=%d/%d", episode.Sequence, budget, len(result.Messages), len(result.Frames), result.FrameDiscards, result.Old, result.PendingPackets, result.PeakPackets, result.PeakPayloadBytes)
		}
	}
	encoded, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		test.Fatal(err)
	}
	if directory := os.Getenv("REPLAY_OUTPUT"); directory != "" {
		if err := os.WriteFile(filepath.Join(directory, "sweep.json"), encoded, 0600); err != nil {
			test.Fatal(err)
		}
	}
}

func TestLateSyntheticMatrix(test *testing.T) {
	for _, budget := range []int{100, 200, 350, 500} {
		for _, scenario := range []string{"small_reorder", "late", "lost", "two_holes", "distance", "wrap", "duplicate", "silence"} {
			test.Run(fmt.Sprintf("%d/%s", budget, scenario), func(test *testing.T) {
				replayBudget = time.Duration(budget) * time.Millisecond
				replayNow = time.Unix(1, 0)
				buffer := newReorderBuffer()
				var delivered []uint16
				deliver := func(packet *rtp.Packet) { delivered = append(delivered, packet.SequenceNumber) }
				push := func(sequence uint16, milliseconds int) {
					replayNow = time.Unix(1, int64(milliseconds)*1_000_000)
					buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: sequence}, Payload: []byte{1}}, deliver)
				}
				if scenario == "wrap" {
					push(65534, 0)
					push(0, 10)
					push(65535, 20)
					if fmt.Sprint(delivered) != "[65534 65535 0]" {
						test.Fatal(delivered)
					}
					return
				}
				push(100, 0)
				push(102, 10)
				switch scenario {
				case "small_reorder":
					push(101, 20)
				case "late":
					push(103, 120)
					push(101, 150)
					if (len(delivered) == 4) != (budget > 100) {
						test.Fatal(delivered)
					}
				case "lost":
					push(103, budget+11)
					if len(delivered) != 3 || len(buffer.pkts) != 0 {
						test.Fatal(delivered)
					}
				case "two_holes":
					push(104, 20)
					push(105, budget+11)
					push(106, 2*budget+12)
					if len(buffer.pkts) != 0 {
						test.Fatal("second gap stuck")
					}
				case "distance":
					push(357, 11)
					if len(buffer.pkts) != 0 || buffer.nextSeq != 358 {
						test.Fatal("distance did not win")
					}
				case "duplicate":
					push(102, 20)
					push(101, 30)
					push(102, 40)
					if len(delivered) != 3 {
						test.Fatal(delivered)
					}
				case "silence":
					replayNow = time.Unix(10, 0)
					if len(delivered) != 1 || len(buffer.pkts) != 1 {
						test.Fatal("baseline silence changed")
					}
					push(103, 10000)
				}
				if !sort.SliceIsSorted(delivered, func(left, right int) bool { return delivered[left] < delivered[right] }) {
					test.Fatal("order", delivered)
				}
			})
		}
	}
	replayBudget = 100 * time.Millisecond
}

func TestLateControlBehindData(test *testing.T) {
	for _, budget := range []int{100, 110, 125, 200, 350, 500} {
		for _, missing := range []bool{false, true} {
			test.Run(fmt.Sprintf("%d/lost=%t", budget, missing), func(test *testing.T) {
				replayBudget = time.Duration(budget) * time.Millisecond
				replayNow = time.Unix(1, 0)
				buffer := newReorderBuffer()
				state := vp8FrameState{}
				data := bytes.Repeat([]byte{0x24}, 2000)
				control := []byte("synthetic ACK/control; no physical ACK timestamp")
				var output [][]byte
				var deliveredAt []time.Time
				assembler := newReassembler(2, func(payload []byte) {
					output = append(output, bytes.Clone(payload))
					deliveredAt = append(deliveredAt, replayNow)
				})
				deliver := func(packet *rtp.Packet) {
					if fragment, ok := decodeVP8Frame(state.process(packet)); ok {
						assembler.ingest(fragment)
					}
				}
				packetize := func(message uint32, sequence uint16, timestamp uint32, payload []byte) []*rtp.Packet {
					fragments, err := encodeFragments(1, message, payload)
					if err != nil {
						test.Fatal(err)
					}
					payloader := codecs.VP8Payloader{}
					encoded := payloader.Payload(1200, encodeVP8DataFrame(fragments[0]))
					var result []*rtp.Packet
					for index, part := range encoded {
						result = append(result, &rtp.Packet{Header: rtp.Header{SequenceNumber: sequence + uint16(index), Timestamp: timestamp, Marker: index == len(encoded)-1}, Payload: part})
					}
					return result
				}
				dataPackets := packetize(1, 65534, ^uint32(0)-100, data)
				controlPackets := packetize(2, 0, 50, control)
				if len(dataPackets) != 2 || len(controlPackets) != 1 {
					test.Fatal("fixture shape")
				}
				buffer.push(dataPackets[0], deliver)
				replayNow = time.Unix(1, 10_000_000)
				buffer.push(controlPackets[0], deliver)
				replayNow = time.Unix(1, 111_000_000)
				buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: 1, Timestamp: 51, Marker: true}, Payload: []byte{0x10, 1}}, deliver)
				if !missing {
					replayNow = time.Unix(1, 119_000_000)
					buffer.push(dataPackets[1], deliver)
				}
				if missing {
					replayNow = time.Unix(2, 0)
					buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: 2, Timestamp: 52, Marker: true}, Payload: []byte{0x10, 1}}, deliver)
				}
				expectData := !missing && budget > 100
				if len(output) != 1+map[bool]int{true: 1, false: 0}[expectData] {
					test.Fatal("delivery count", len(output))
				}
				if !bytes.Equal(output[len(output)-1], control) {
					test.Fatal("control corrupted")
				}
				if expectData && !bytes.Equal(output[0], data) {
					test.Fatal("DATA corrupted")
				}
				if len(buffer.pkts) != 0 {
					test.Fatal("following traffic held indefinitely")
				}
				test.Logf("control_wait_ns=%d data_recovered=%t", deliveredAt[len(deliveredAt)-1].Sub(time.Unix(1, 10_000_000)).Nanoseconds(), expectData)
			})
		}
	}
	replayBudget = 100 * time.Millisecond
}

func TestLateEpochAndConflictingFragment(test *testing.T) {
	replayBudget = 125 * time.Millisecond
	replayNow = time.Unix(1, 0)
	previous, current := newReorderBuffer(), newReorderBuffer()
	var oldOutput, newOutput []uint16
	oldDeliver := func(packet *rtp.Packet) { oldOutput = append(oldOutput, packet.SequenceNumber) }
	newDeliver := func(packet *rtp.Packet) { newOutput = append(newOutput, packet.SequenceNumber) }
	previous.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: 400}}, oldDeliver)
	previous.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: 402}}, oldDeliver)
	current.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: 7}}, newDeliver)
	previous.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: 401}}, oldDeliver)
	if fmt.Sprint(newOutput) != "[7]" || fmt.Sprint(oldOutput) != "[400 401 402]" {
		test.Fatal("epoch mixed")
	}
	deliveries := 0
	assembler := newReassembler(2, func([]byte) { deliveries++ })
	original, _ := encodeFragments(1, 9, bytes.Repeat([]byte{3}, 16384))
	conflicting, _ := encodeFragments(1, 9, bytes.Repeat([]byte{4}, 16384))
	assembler.ingest(original[0])
	assembler.ingest(conflicting[0])
	assembler.ingest(original[1])
	if deliveries != 0 {
		test.Fatal("conflict accepted")
	}
	replayBudget = 100 * time.Millisecond
}

func TestLateBudgetOnlyHasNoFiniteSilenceDeadline(test *testing.T) {
	for _, budget := range []int{100, 110, 125, 200, 350, 500} {
		replayBudget = time.Duration(budget) * time.Millisecond
		replayNow = time.Unix(1, 0)
		buffer := newReorderBuffer()
		delivered := 0
		consume := func(*rtp.Packet) { delivered++ }
		buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: 0}}, consume)
		buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: 2}}, consume)
		replayNow = replayNow.Add(time.Hour)
		if delivered != 1 || len(buffer.pkts) != 1 {
			test.Fatal("clock alone unexpectedly services deadline")
		}
		test.Logf("budget=%d silence=1h held=1: NOT_A_WALL_CLOCK_RETENTION_BOUND", budget)
		buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: 3}}, consume)
		if delivered != 3 || len(buffer.pkts) != 0 {
			test.Fatal("arrival fails to recover genuine loss")
		}
	}
	replayBudget = 100 * time.Millisecond
}

func TestLateHolesInConsecutiveFrames(test *testing.T) {
	for _, budget := range []int{100, 125, 200, 350, 500} {
		replayBudget = time.Duration(budget) * time.Millisecond
		replayNow = time.Unix(1, 0)
		buffer := newReorderBuffer()
		state := vp8FrameState{}
		var output [][]byte
		assembler := newReassembler(2, func(payload []byte) { output = append(output, bytes.Clone(payload)) })
		deliver := func(packet *rtp.Packet) {
			if fragment, valid := decodeVP8Frame(state.process(packet)); valid {
				assembler.ingest(fragment)
			}
		}
		sequence := uint16(100)
		for message := uint32(1); message <= 3; message++ {
			payload := bytes.Repeat([]byte{byte(message)}, 8100)
			if message == 3 {
				payload = []byte("control after two broken DATA frames")
			}
			fragments, err := encodeFragments(1, message, payload)
			if err != nil {
				test.Fatal(err)
			}
			payloader := codecs.VP8Payloader{}
			encoded := payloader.Payload(1200, encodeVP8DataFrame(fragments[0]))
			for index, part := range encoded {
				packet := &rtp.Packet{Header: rtp.Header{SequenceNumber: sequence, Timestamp: message, Marker: index == len(encoded)-1}, Payload: part}
				sequence++
				if packet.SequenceNumber == 101 || packet.SequenceNumber == 104 || packet.SequenceNumber == 108 {
					continue
				}
				buffer.push(packet, deliver)
			}
		}
		for step := 1; step <= 3; step++ {
			replayNow = time.Unix(1, int64(step*(budget+1))*1_000_000)
			buffer.push(&rtp.Packet{Header: rtp.Header{SequenceNumber: sequence, Timestamp: 10, Marker: true}, Payload: []byte{0x10, 1}}, deliver)
			sequence++
		}
		if len(output) != 1 || !bytes.Equal(output[0], []byte("control after two broken DATA frames")) || len(buffer.pkts) != 0 {
			test.Fatal("incomplete frame escaped or following control stuck")
		}
	}
	replayBudget = 100 * time.Millisecond
}
