package telemost

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/hex"
	"errors"
	"hash/crc32"
	"sync"
	"time"

	"github.com/klauspost/reedsolomon"
)

const labSymbol = 1024
const labHeader = 64
const labSources = 8
const labRepairs = 2
const labHeldLimit = 16 * 80 * labSymbol

type labFragmentConfig struct {
	Mode      string
	Epoch     [16]byte
	Direction byte
}

var labFragmentSettings labFragmentConfig
var labCeilingOriginal bool

func ConfigureLabCeiling(original bool) error {
	if original && labFragmentSettings.Mode != "L" {
		return errors.New("original ceiling only for L bridge")
	}
	labCeilingOriginal = original
	return nil
}

func ConfigureLabFragments(mode, epoch string, server bool) error {
	if mode != "L" && mode != "S" && mode != "SF" {
		return errors.New("lab fragment mode")
	}
	decoded, err := hex.DecodeString(epoch)
	if err != nil || len(decoded) != 16 {
		return errors.New("lab fragment epoch")
	}
	labFragmentSettings = labFragmentConfig{Mode: mode}
	copy(labFragmentSettings.Epoch[:], decoded)
	if server {
		labFragmentSettings.Direction = 1
	}
	return nil
}

type labFragmentMetrics struct {
	SourceBytes, HeaderBytes, RepairBytes, PaddingBytes                                  uint64
	PartsSent, PartsReceived, MessagesSent, MessagesCompleted                            uint64
	Duplicates, Conflicts, Malformed, Foreign, Recent, Expired, Capacity                 uint64
	RawMissingAtRecovery, RecoveredSymbols, RecoveredGroups, DecodeFailures, CRCFailures uint64
	ResidualMissingAtExpiry, EncodeNS, DecodeNS, PeakHeld, Held, Pending                 uint64
	QueueAgeMaxNS, QueueSamples, QueueAgeNS                                              uint64
	Closed                                                                               bool
}

type labFragmentGroup struct {
	shards   [10][]byte
	complete bool
}
type labFragmentMessage struct {
	length, checksum uint32
	groups           [8]labFragmentGroup
	deadline         time.Time
}
type labFragmentCodec struct {
	config   labFragmentConfig
	mutex    sync.Mutex
	builds   map[[2]uint32]*labFragmentMessage
	recent   map[[2]uint32]time.Time
	metrics  labFragmentMetrics
	encoders [9]reedsolomon.Encoder
	now      func() time.Time
}

func newLabFragmentCodec(config labFragmentConfig) *labFragmentCodec {
	codec := &labFragmentCodec{config: config, builds: make(map[[2]uint32]*labFragmentMessage), recent: make(map[[2]uint32]time.Time), now: time.Now}
	for count := 1; count <= 8; count++ {
		codec.encoders[count], _ = reedsolomon.New(count, labRepairs, reedsolomon.WithMaxGoroutines(1))
	}
	return codec
}

func labPartCRC(part []byte) uint32 {
	checksum := crc32.Update(0, crc32.IEEETable, part[:48])
	return crc32.Update(checksum, crc32.IEEETable, part[52:])
}

func (codec *labFragmentCodec) encode(ctx context.Context, sender, message uint32, payload []byte) ([][]byte, error) {
	if len(payload) > MaxMessageSize || message == 0 {
		return nil, ErrMessageTooLarge
	}
	started := time.Now()
	codec.mutex.Lock()
	defer codec.mutex.Unlock()
	if codec.metrics.Closed {
		return nil, ErrClosed
	}
	var parts [][]byte
	checksum := crc32.ChecksumIEEE(payload)
	sources := max(1, (len(payload)+labSymbol-1)/labSymbol)
	protected := codec.config.Mode == "SF" && len(payload) > labSymbol
	for group := 0; group*labSources < sources; group++ {
		if err := ctx.Err(); err != nil {
			return nil, err
		}
		count := min(labSources, sources-group*labSources)
		shards := make([][]byte, count+labRepairs)
		for index := 0; index < count; index++ {
			start := (group*labSources + index) * labSymbol
			length := min(labSymbol, len(payload)-start)
			shards[index] = make([]byte, labSymbol)
			copy(shards[index], payload[start:start+length])
		}
		total := count
		if protected {
			for index := count; index < count+labRepairs; index++ {
				shards[index] = make([]byte, labSymbol)
			}
			if err := codec.encoders[count].Encode(shards); err != nil {
				return nil, err
			}
			total += labRepairs
			codec.metrics.PaddingBytes += uint64(count*labSymbol - min(count*labSymbol, len(payload)-group*labSources*labSymbol))
		}
		for index := 0; index < total; index++ {
			length := labSymbol
			if index < count {
				length = min(labSymbol, len(payload)-(group*labSources+index)*labSymbol)
			}
			part := make([]byte, labHeader+length)
			copy(part, "FCF2")
			part[4] = 1
			part[6] = codec.config.Direction
			if codec.config.Mode == "SF" {
				part[5] = 1
			}
			copy(part[8:24], codec.config.Epoch[:])
			binary.BigEndian.PutUint32(part[24:], sender)
			binary.BigEndian.PutUint32(part[28:], message)
			binary.BigEndian.PutUint32(part[32:], uint32(len(payload)))
			binary.BigEndian.PutUint32(part[36:], checksum)
			binary.BigEndian.PutUint16(part[40:], uint16(group))
			part[42] = byte(index)
			part[43] = byte(count)
			binary.BigEndian.PutUint16(part[44:], labSymbol)
			binary.BigEndian.PutUint16(part[46:], uint16(length))
			copy(part[labHeader:], shards[index][:length])
			binary.BigEndian.PutUint32(part[48:], labPartCRC(part))
			parts = append(parts, part)
			codec.metrics.HeaderBytes += labHeader
			if index >= count {
				codec.metrics.RepairBytes += uint64(length)
			}
		}
	}
	codec.metrics.SourceBytes += uint64(len(payload))
	codec.metrics.PartsSent += uint64(len(parts))
	codec.metrics.MessagesSent++
	codec.metrics.EncodeNS += uint64(time.Since(started))
	return parts, nil
}

func (codec *labFragmentCodec) releaseLocked(key [2]uint32, now time.Time) {
	if message := codec.builds[key]; message != nil {
		for _, group := range message.groups {
			for _, shard := range group.shards {
				codec.metrics.Held -= uint64(len(shard))
			}
		}
		delete(codec.builds, key)
	}
	codec.recent[key] = now.Add(reassemblyTimeout)
}

func (codec *labFragmentCodec) pruneLocked(now time.Time) {
	for key, deadline := range codec.recent {
		if !now.Before(deadline) {
			delete(codec.recent, key)
		}
	}
	for key, message := range codec.builds {
		if now.Before(message.deadline) {
			continue
		}
		sources := max(1, (int(message.length)+labSymbol-1)/labSymbol)
		for index := 0; index < sources; index++ {
			if message.groups[index/labSources].shards[index%labSources] == nil {
				codec.metrics.ResidualMissingAtExpiry++
			}
		}
		codec.metrics.Expired++
		codec.releaseLocked(key, now)
	}
}

func (codec *labFragmentCodec) ingest(part []byte) []byte {
	codec.mutex.Lock()
	defer codec.mutex.Unlock()
	if codec.metrics.Closed {
		return nil
	}
	bad := func() []byte { codec.metrics.Malformed++; return nil }
	if len(part) < labHeader || len(part) > labHeader+labSymbol || string(part[:4]) != "FCF2" || part[4] != 1 || part[5] > 1 || part[6] > 1 || part[7] != 0 || !bytes.Equal(part[52:64], make([]byte, 12)) {
		return bad()
	}
	if !bytes.Equal(part[8:24], codec.config.Epoch[:]) || part[6] == codec.config.Direction {
		codec.metrics.Foreign++
		return nil
	}
	if (part[5] == 1) != (codec.config.Mode == "SF") {
		return bad()
	}
	length := binary.BigEndian.Uint32(part[32:])
	checksum := binary.BigEndian.Uint32(part[36:])
	group, index, count := int(binary.BigEndian.Uint16(part[40:])), int(part[42]), int(part[43])
	if length > MaxMessageSize || binary.BigEndian.Uint32(part[28:]) == 0 || binary.BigEndian.Uint16(part[44:]) != labSymbol || int(binary.BigEndian.Uint16(part[46:])) != len(part)-labHeader {
		return bad()
	}
	sources := max(1, (int(length)+labSymbol-1)/labSymbol)
	if group >= 8 || group*labSources >= sources || count != min(labSources, sources-group*labSources) {
		return bad()
	}
	protected := codec.config.Mode == "SF" && length > labSymbol
	total := count
	if protected {
		total += labRepairs
	}
	if index >= total {
		return bad()
	}
	expected := labSymbol
	if index < count {
		expected = min(labSymbol, int(length)-(group*labSources+index)*labSymbol)
	}
	if len(part) != labHeader+expected || labPartCRC(part) != binary.BigEndian.Uint32(part[48:]) {
		return bad()
	}
	codec.metrics.PartsReceived++
	now := codec.now()
	codec.pruneLocked(now)
	key := [2]uint32{binary.BigEndian.Uint32(part[24:]), binary.BigEndian.Uint32(part[28:])}
	if _, ok := codec.recent[key]; ok {
		codec.metrics.Recent++
		return nil
	}
	message := codec.builds[key]
	if message == nil {
		if len(codec.builds) >= maxPendingMessages || len(codec.recent)+len(codec.builds) >= maxRecentMessages {
			codec.metrics.Capacity++
			return nil
		}
		message = &labFragmentMessage{length: length, checksum: checksum, deadline: now.Add(reassemblyTimeout)}
		codec.builds[key] = message
	}
	if message.length != length || message.checksum != checksum {
		codec.metrics.Conflicts++
		codec.releaseLocked(key, now)
		return nil
	}
	section := &message.groups[group]
	if prior := section.shards[index]; prior != nil {
		if bytes.Equal(prior[:expected], part[labHeader:]) {
			codec.metrics.Duplicates++
		} else {
			codec.metrics.Conflicts++
			codec.releaseLocked(key, now)
		}
		return nil
	}
	if section.complete && index >= count {
		codec.metrics.Recent++
		return nil
	}
	if codec.metrics.Held+labSymbol > labHeldLimit {
		codec.metrics.Capacity++
		return nil
	}
	section.shards[index] = make([]byte, labSymbol)
	copy(section.shards[index], part[labHeader:])
	codec.metrics.Held += labSymbol
	codec.metrics.PeakHeld = max(codec.metrics.PeakHeld, codec.metrics.Held)
	present, sourcePresent := 0, 0
	for shard := 0; shard < total; shard++ {
		if section.shards[shard] != nil {
			present++
			if shard < count {
				sourcePresent++
			}
		}
	}
	if sourcePresent == count {
		section.complete = true
	} else if protected && present >= count {
		started := time.Now()
		missing := count - sourcePresent
		codec.metrics.RawMissingAtRecovery += uint64(missing)
		if codec.metrics.Held+uint64(missing*labSymbol) > labHeldLimit {
			codec.metrics.Capacity++
			return nil
		}
		if err := codec.encoders[count].ReconstructData(section.shards[:total]); err != nil {
			codec.metrics.DecodeFailures++
			codec.releaseLocked(key, now)
			return nil
		}
		codec.metrics.DecodeNS += uint64(time.Since(started))
		codec.metrics.Held += uint64(missing * labSymbol)
		codec.metrics.PeakHeld = max(codec.metrics.PeakHeld, codec.metrics.Held)
		codec.metrics.RecoveredSymbols += uint64(missing)
		codec.metrics.RecoveredGroups++
		section.complete = true
	}
	for position := 0; position*labSources < sources; position++ {
		if !message.groups[position].complete {
			return nil
		}
	}
	output := make([]byte, length)
	for position := 0; position < sources; position++ {
		copy(output[position*labSymbol:], message.groups[position/labSources].shards[position%labSources])
	}
	codec.releaseLocked(key, now)
	if crc32.ChecksumIEEE(output) != checksum {
		codec.metrics.CRCFailures++
		return nil
	}
	codec.metrics.MessagesCompleted++
	return output
}

func (codec *labFragmentCodec) snapshot() labFragmentMetrics {
	codec.mutex.Lock()
	defer codec.mutex.Unlock()
	result := codec.metrics
	result.Pending = uint64(len(codec.builds))
	return result
}
func (codec *labFragmentCodec) prune() {
	codec.mutex.Lock()
	defer codec.mutex.Unlock()
	codec.pruneLocked(codec.now())
}
func (codec *labFragmentCodec) close() {
	codec.mutex.Lock()
	defer codec.mutex.Unlock()
	clear(codec.builds)
	clear(codec.recent)
	codec.metrics.Held = 0
	codec.metrics.Closed = true
}

func (session *Session) labEncode(ctx context.Context, message uint32, payload []byte) ([][]byte, error) {
	if session.labFragments == nil {
		return encodeFragments(session.senderID, message, payload)
	}
	return session.labFragments.encode(ctx, session.senderID, message, payload)
}
func (session *Session) labIngest(part []byte) {
	if session.labFragments == nil {
		session.reassembler.ingest(part)
		return
	}
	if output := session.labFragments.ingest(part); output != nil {
		session.deliver(output)
	}
}
func (session *Session) LabFragmentStats() any {
	if session.labFragments == nil {
		return map[string]any{"mode": "L", "assembly": session.reassembler.delivery()}
	}
	return session.labFragments.snapshot()
}

var labRate = struct {
	sync.Mutex
	next      time.Time
	WaitNS    uint64
	Bytes     uint64
	MaxPacket int
	MaxHeader int
}{}

func labMediaRate(size, header int) {
	labRate.Lock()
	defer labRate.Unlock()
	now := time.Now()
	if !labCeilingOriginal && now.Before(labRate.next) {
		duration := labRate.next.Sub(now)
		time.Sleep(duration)
		labRate.WaitNS += uint64(duration)
	}
	labRate.next = time.Now().Add(time.Duration(size) * time.Second / 1048576)
	labRate.Bytes += uint64(size)
	labRate.MaxPacket = max(labRate.MaxPacket, size-64)
	labRate.MaxHeader = max(labRate.MaxHeader, header)
}

func LabRateStats() map[string]any {
	labRate.Lock()
	defer labRate.Unlock()
	return map[string]any{"original_bridge": labCeilingOriginal, "ceiling_bytes_s": 1048576, "charged_bytes": labRate.Bytes, "wait_ns": labRate.WaitNS, "max_rtp_rtcp_bytes": labRate.MaxPacket, "max_rtp_header": labRate.MaxHeader, "fixed_frame_pause_ns": int64(vp8SendInterval), "nominal_frame_duration_ns": int64(vp8FrameDuration)}
}
