package telemost

import (
	"encoding/binary"
	"errors"
	"sort"
	"sync"
	"time"
)

// The carrier moves whole application messages, but each provider transport has
// a smaller safe per-frame/per-datagram limit, so messages are split into
// ordered fragments and reassembled on the receiving side.
//
// Fragment wire header (big-endian, 16 bytes):
//
//	u32be sender_id | u32be message_id | u32be seq | u32be total
//
// seq is 0-based; total is the fragment count (>= 1). sender_id is a random
// per-session value used to drop the SFU's self-view echo.
const (
	fragmentHeaderLen = 16

	// MaxMessageSize is the largest application message the carrier accepts.
	MaxMessageSize = 64 * 1024

	// maxFragmentPayload is the largest payload a single transport frame can
	// carry. It is intentionally well below the VP8 reassembly ceiling and the
	// observed Telemost data-channel message limit.
	maxFragmentPayload = 8 * 1024

	// maxFragmentsPerMessage bounds reassembly of a message spanning fragments.
	maxFragmentsPerMessage = (MaxMessageSize / maxFragmentPayload) + 2

	// reassemblyTimeout bounds how long partial messages are retained.
	reassemblyTimeout = 10 * time.Second
)

var (
	// ErrMessageTooLarge is returned when a message exceeds MaxMessageSize.
	ErrMessageTooLarge = errors.New("telemost: message too large")
	// ErrClosed is returned when a carrier operation is attempted after Close.
	ErrClosed = errors.New("telemost: carrier closed")
)

type fragment struct {
	seq  uint32
	data []byte
}

// fragmentBuilder collects the fragments of one message keyed by
// (senderID, messageID).
type fragmentBuilder struct {
	total    uint32
	received map[uint32][]byte
	deadline time.Time
}

// reassembler turns fragment streams back into application messages.
type reassembler struct {
	mu      sync.Mutex
	builds  map[[2]uint32]*fragmentBuilder
	onData  func([]byte)
	selfID  uint32
	now     func() time.Time
}

func newReassembler(selfID uint32, onData func([]byte)) *reassembler {
	return &reassembler{
		builds: make(map[[2]uint32]*fragmentBuilder),
		onData: onData,
		selfID: selfID,
		now:    time.Now,
	}
}

// assembleIngest consumes one transport frame payload (fragment header already
// stripped is NOT the case; the full fragment including header is expected).
func (r *reassembler) ingest(data []byte) {
	if len(data) < fragmentHeaderLen {
		return
	}
	sender := binary.BigEndian.Uint32(data[0:4])
	if sender == r.selfID {
		return // SFU self-view echo
	}
	msgID := binary.BigEndian.Uint32(data[4:8])
	seq := binary.BigEndian.Uint32(data[8:12])
	total := binary.BigEndian.Uint32(data[12:16])
	payload := data[fragmentHeaderLen:]
	if total == 0 || total > maxFragmentsPerMessage || seq >= total {
		return
	}

	r.mu.Lock()
	defer r.mu.Unlock()
	r.pruneLocked(r.now())

	key := [2]uint32{sender, msgID}
	b, ok := r.builds[key]
	if !ok {
		b = &fragmentBuilder{
			total:    total,
			received: make(map[uint32][]byte, total),
			deadline: r.now().Add(reassemblyTimeout),
		}
		r.builds[key] = b
	}
	if b.total != total {
		// Conflicting fragment count for the same key; drop the whole message.
		delete(r.builds, key)
		return
	}
	if _, dup := b.received[seq]; !dup {
		b.received[seq] = append([]byte(nil), payload...)
	}
	if uint32(len(b.received)) < b.total {
		return
	}

	// All fragments present: concatenate in sequence order.
	seqs := make([]int, 0, len(b.received))
	for s := range b.received {
		seqs = append(seqs, int(s))
	}
	sort.Ints(seqs)
	size := 0
	for _, s := range seqs {
		size += len(b.received[uint32(s)])
	}
	if size > MaxMessageSize {
		delete(r.builds, key)
		return
	}
	out := make([]byte, 0, size)
	for _, s := range seqs {
		out = append(out, b.received[uint32(s)]...)
	}
	delete(r.builds, key)

	if r.onData != nil {
		r.onData(out)
	}
}

func (r *reassembler) pruneLocked(now time.Time) {
	for k, b := range r.builds {
		if now.After(b.deadline) {
			delete(r.builds, k)
		}
	}
}

// encodeFragments splits payload into fragment frames and returns them.
// Each returned frame includes the fragment header and a payload chunk.
func encodeFragments(senderID, messageID uint32, payload []byte) ([][]byte, error) {
	if len(payload) > MaxMessageSize {
		return nil, ErrMessageTooLarge
	}
	if len(payload) == 0 {
		payload = []byte{}
	}
	total := (len(payload) + maxFragmentPayload - 1) / maxFragmentPayload
	if total == 0 {
		total = 1
	}
	frames := make([][]byte, 0, total)
	for seq := 0; seq < total; seq++ {
		start := seq * maxFragmentPayload
		end := start + maxFragmentPayload
		if end > len(payload) {
			end = len(payload)
		}
		chunk := payload[start:end]
		frame := make([]byte, fragmentHeaderLen+len(chunk))
		binary.BigEndian.PutUint32(frame[0:4], senderID)
		binary.BigEndian.PutUint32(frame[4:8], messageID)
		binary.BigEndian.PutUint32(frame[8:12], uint32(seq))
		binary.BigEndian.PutUint32(frame[12:16], uint32(total))
		copy(frame[fragmentHeaderLen:], chunk)
		frames = append(frames, frame)
	}
	return frames, nil
}
