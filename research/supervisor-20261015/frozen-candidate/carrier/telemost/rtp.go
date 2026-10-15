package telemost

import (
	"github.com/Joker20380/family_connect/carrier/sessiontrace"
	"github.com/pion/rtp"
	"github.com/pion/rtp/codecs"
	"time"
)

// reorderWindow bounds how many out-of-order RTP packets are held before a gap
// is treated as lost and skipped.
const reorderWindow = 256

// maxAssembledFrameSize bounds one reassembled VP8 frame. It sits above the
// largest legitimate carrier frame so a peer cannot grow the buffer without
// bound by streaming fragments that never set the marker bit.
const maxAssembledFrameSize = 4 * maxFragmentPayload

// seqLess reports whether RTP sequence a precedes b with wrap-around aware
// serial arithmetic (RFC 1982).
func seqLess(a, b uint16) bool {
	return (a-b)&0x8000 != 0
}

// reorderBuffer restores RTP sequence order before VP8 frame assembly.
type reorderBuffer struct {
	mediaTrack uint32
	trace      *sessiontrace.Recorder
	pkts       map[uint16]*rtp.Packet
	free       []*rtp.Packet
	nextSeq    uint16
	started    bool
	gapSince   time.Time
}

func newReorderBuffer() *reorderBuffer {
	return &reorderBuffer{pkts: make(map[uint16]*rtp.Packet, reorderWindow)}
}

func (b *reorderBuffer) push(pkt *rtp.Packet, deliver func(*rtp.Packet)) {
	if len(pkt.Payload) > 2048 {
		b.drop(pkt, "malformed")
		return
	}
	if !b.started {
		b.started = true
		b.nextSeq = pkt.SequenceNumber
	}
	if seqLess(pkt.SequenceNumber, b.nextSeq) {
		b.drop(pkt, "old_rtp")
		return
	}
	previousNext := b.nextSeq
	if uint16(pkt.SequenceNumber-b.nextSeq) >= reorderWindow {
		for sequence, queued := range b.pkts {
			b.drop(queued, "window")
			b.recycle(queued)
			delete(b.pkts, sequence)
		}
		b.nextSeq = pkt.SequenceNumber
	}
	if old := b.pkts[pkt.SequenceNumber]; old != nil {
		b.drop(old, "duplicate")
		b.recycle(old)
	}
	b.pkts[pkt.SequenceNumber] = b.clone(pkt)
	if len(b.pkts) >= reorderWindow || (!b.gapSince.IsZero() && time.Since(b.gapSince) > 100*time.Millisecond) {
		b.skipToOldest()
	}
	b.drain(deliver)
	if len(b.pkts) == 0 {
		b.gapSince = time.Time{}
	} else if b.gapSince.IsZero() || b.nextSeq != previousNext {
		b.gapSince = time.Now()
	}
}

func (b *reorderBuffer) drop(packet *rtp.Packet, result string) {
	b.trace.Boundary(sessiontrace.Boundary{Direction: "rx", Stage: "rtp_received", Result: result, FrameKnown: true, MediaTrack: b.mediaTrack, Timestamp: packet.Timestamp, FirstRTP: packet.SequenceNumber, LastRTP: packet.SequenceNumber, Packets: 1})
}

func (b *reorderBuffer) drain(deliver func(*rtp.Packet)) {
	for {
		pkt, ok := b.pkts[b.nextSeq]
		if !ok {
			return
		}
		delete(b.pkts, b.nextSeq)
		b.nextSeq++
		deliver(pkt)
		b.recycle(pkt)
	}
}

func (b *reorderBuffer) clone(pkt *rtp.Packet) *rtp.Packet {
	var clone *rtp.Packet
	if last := len(b.free) - 1; last >= 0 {
		clone = b.free[last]
		b.free = b.free[:last]
	} else {
		clone = &rtp.Packet{}
	}
	clone.Header = pkt.Header
	if cap(clone.Payload) < len(pkt.Payload) {
		clone.Payload = make([]byte, len(pkt.Payload))
	} else {
		clone.Payload = clone.Payload[:len(pkt.Payload)]
	}
	copy(clone.Payload, pkt.Payload)
	return clone
}

func (b *reorderBuffer) recycle(pkt *rtp.Packet) {
	pkt.Header = rtp.Header{}
	if cap(pkt.Payload) > 2*1024 {
		pkt.Payload = nil
	} else {
		pkt.Payload = pkt.Payload[:0]
	}
	b.free = append(b.free, pkt)
}

func (b *reorderBuffer) skipToOldest() {
	first := true
	var oldest uint16
	for seq := range b.pkts {
		if first || seqLess(seq, oldest) {
			oldest = seq
			first = false
		}
	}
	b.nextSeq = oldest
}

// vp8FrameState reassembles a VP8 frame from its RTP packets. It returns the
// assembled frame payload when complete, or nil otherwise.
type vp8FrameState struct {
	mediaTrack  uint32
	trace       *sessiontrace.Recorder
	vp8Pkt      codecs.VP8Packet
	frameBuf    []byte
	lastSeq     uint16
	haveLastSeq bool
	frameValid  bool
	timestamp   uint32
}

func (st *vp8FrameState) process(pkt *rtp.Packet) []byte {
	if st.frameValid && (st.haveLastSeq && pkt.SequenceNumber != st.lastSeq+1 || st.timestamp != pkt.Timestamp) {
		st.trace.Boundary(sessiontrace.Boundary{Direction: "rx", Stage: "vp8_reassembled", Result: "frame_discard", FrameKnown: true, MediaTrack: st.mediaTrack, Timestamp: st.timestamp, LastRTP: st.lastSeq})
	}
	if st.haveLastSeq && pkt.SequenceNumber != st.lastSeq+1 {
		st.frameValid = false
		st.frameBuf = st.frameBuf[:0]
	}
	st.lastSeq = pkt.SequenceNumber
	st.haveLastSeq = true

	payload, err := st.vp8Pkt.Unmarshal(pkt.Payload)
	if err != nil {
		st.frameValid = false
		st.frameBuf = st.frameBuf[:0]
		return nil
	}
	if st.timestamp != pkt.Timestamp {
		st.frameValid = false
		st.frameBuf = st.frameBuf[:0]
	}
	st.timestamp = pkt.Timestamp
	if st.vp8Pkt.S == 1 && st.vp8Pkt.PID == 0 {
		st.frameBuf = st.frameBuf[:0]
		st.frameValid = true
	}
	if !st.frameValid {
		return nil
	}
	if len(st.frameBuf)+len(payload) > maxAssembledFrameSize {
		st.frameValid = false
		st.frameBuf = st.frameBuf[:0]
		return nil
	}
	st.frameBuf = append(st.frameBuf, payload...)
	if !pkt.Marker {
		return nil
	}
	frame := st.frameBuf
	st.frameBuf = st.frameBuf[:0]
	st.frameValid = false
	if len(frame) >= len(vp8Interframe) {
		return frame
	}
	return nil
}
