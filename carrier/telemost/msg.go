package telemost

import (
	"encoding/binary"
	"errors"
	"hash/crc32"
	"sync"
	"time"
)

const (
	fragmentHeaderLen      = 24
	MaxMessageSize         = 64 * 1024
	maxFragmentPayload     = 8 * 1024
	maxFragmentsPerMessage = MaxMessageSize / maxFragmentPayload
	reassemblyTimeout      = 10 * time.Second
	maxPendingMessages     = 16
	maxRecentMessages      = 4096
)

var (
	ErrMessageTooLarge = errors.New("telemost: message too large")
	ErrClosed          = errors.New("telemost: carrier closed")
)

type fragmentBuilder struct {
	total    uint32
	length   uint32
	checksum uint32
	received map[uint32][]byte
	deadline time.Time
}

type reassembler struct {
	mu     sync.Mutex
	builds map[[2]uint32]*fragmentBuilder
	recent map[[2]uint32]time.Time
	onData func([]byte)
	selfID uint32
	now    func() time.Time
}

func newReassembler(selfID uint32, onData func([]byte)) *reassembler {
	return &reassembler{builds: make(map[[2]uint32]*fragmentBuilder), recent: make(map[[2]uint32]time.Time), onData: onData, selfID: selfID, now: time.Now}
}

func (r *reassembler) ingest(data []byte) {
	if len(data) < fragmentHeaderLen || len(data) > fragmentHeaderLen+maxFragmentPayload {
		return
	}
	sender := binary.BigEndian.Uint32(data[0:4])
	messageID := binary.BigEndian.Uint32(data[4:8])
	sequence := binary.BigEndian.Uint32(data[8:12])
	total := binary.BigEndian.Uint32(data[12:16])
	length := binary.BigEndian.Uint32(data[16:20])
	checksum := binary.BigEndian.Uint32(data[20:24])
	if sender == r.selfID || length > MaxMessageSize || total == 0 || total > maxFragmentsPerMessage || sequence >= total {
		return
	}
	expectedTotal := max(uint32(1), (length+maxFragmentPayload-1)/maxFragmentPayload)
	expectedLength := min(uint32(maxFragmentPayload), length-sequence*maxFragmentPayload)
	if total != expectedTotal || uint32(len(data)-fragmentHeaderLen) != expectedLength {
		return
	}
	key := [2]uint32{sender, messageID}
	r.mu.Lock()
	r.pruneLocked(r.now())
	if _, seen := r.recent[key]; seen {
		r.mu.Unlock()
		return
	}
	builder := r.builds[key]
	if builder == nil {
		if len(r.builds) >= maxPendingMessages || len(r.recent)+len(r.builds) >= maxRecentMessages {
			r.mu.Unlock()
			return
		}
		builder = &fragmentBuilder{total: total, length: length, checksum: checksum, received: make(map[uint32][]byte), deadline: r.now().Add(reassemblyTimeout)}
		r.builds[key] = builder
	}
	_, duplicate := builder.received[sequence]
	if duplicate || builder.total != total || builder.length != length || builder.checksum != checksum {
		delete(r.builds, key)
		r.recent[key] = builder.deadline
		r.mu.Unlock()
		return
	}
	builder.received[sequence] = append([]byte(nil), data[fragmentHeaderLen:]...)
	if uint32(len(builder.received)) != total {
		r.mu.Unlock()
		return
	}
	output := make([]byte, 0, length)
	for index := uint32(0); index < total; index++ {
		output = append(output, builder.received[index]...)
	}
	delete(r.builds, key)
	r.recent[key] = r.now().Add(reassemblyTimeout)
	r.mu.Unlock()
	if r.onData != nil && crc32.ChecksumIEEE(output) == checksum {
		r.onData(output)
	}
}

func (r *reassembler) pruneLocked(now time.Time) {
	for key, deadline := range r.recent {
		if !now.Before(deadline) {
			delete(r.recent, key)
		}
	}
	for key, builder := range r.builds {
		if !now.Before(builder.deadline) {
			delete(r.builds, key)
			r.recent[key] = now.Add(reassemblyTimeout)
		}
	}
}

func (r *reassembler) prune() {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.pruneLocked(r.now())
}

func encodeFragments(senderID, messageID uint32, payload []byte) ([][]byte, error) {
	if len(payload) > MaxMessageSize {
		return nil, ErrMessageTooLarge
	}
	total := max(1, (len(payload)+maxFragmentPayload-1)/maxFragmentPayload)
	frames := make([][]byte, 0, total)
	for sequence := 0; sequence < total; sequence++ {
		start := sequence * maxFragmentPayload
		end := min(start+maxFragmentPayload, len(payload))
		frame := make([]byte, fragmentHeaderLen+end-start)
		binary.BigEndian.PutUint32(frame[0:4], senderID)
		binary.BigEndian.PutUint32(frame[4:8], messageID)
		binary.BigEndian.PutUint32(frame[8:12], uint32(sequence))
		binary.BigEndian.PutUint32(frame[12:16], uint32(total))
		binary.BigEndian.PutUint32(frame[16:20], uint32(len(payload)))
		binary.BigEndian.PutUint32(frame[20:24], crc32.ChecksumIEEE(payload))
		copy(frame[fragmentHeaderLen:], payload[start:end])
		frames = append(frames, frame)
	}
	return frames, nil
}
