package telemost

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"github.com/pion/rtcp"
	"github.com/pion/rtp"
	"github.com/pion/rtp/codecs"
	"github.com/pion/webrtc/v4/pkg/media"
	"hash/fnv"
	"sync"
	"time"
)

type labMediaEvent struct {
	At           int64  `json:"ns"`
	Stage        string `json:"stage"`
	Kind         string `json:"kind,omitempty"`
	SSRC         uint32 `json:"ssrc,omitempty"`
	Timestamp    uint32 `json:"ts,omitempty"`
	Sequence     uint16 `json:"seq,omitempty"`
	Marker       bool   `json:"marker,omitempty"`
	Start        bool   `json:"start,omitempty"`
	Picture      uint16 `json:"picture,omitempty"`
	PictureKnown bool   `json:"picture_known,omitempty"`
	Hash         uint64 `json:"hash,omitempty"`
	Size         int    `json:"size,omitempty"`
	Sender       uint32 `json:"sender,omitempty"`
	Message      uint32 `json:"message,omitempty"`
	Fragment     uint32 `json:"fragment,omitempty"`
	Total        uint32 `json:"total,omitempty"`
	AppID        uint64 `json:"app_id,omitempty"`
	AppKind      byte   `json:"app_kind,omitempty"`
	RSSeq        uint64 `json:"rs_seq,omitempty"`
	NTP          uint64 `json:"ntp,omitempty"`
	Count        uint32 `json:"count,omitempty"`
	Lost         uint32 `json:"lost,omitempty"`
	Jitter       uint32 `json:"jitter,omitempty"`
}

var labMedia = struct {
	sync.Mutex
	start    time.Time
	enabled  bool
	policy   string
	phase    time.Duration
	events   []labMediaEvent
	overflow uint64
}{start: time.Now()}

func ConfigureLabMedia(policy string, phaseMS int) error {
	if policy != "A" && policy != "B" {
		return errors.New("lab media policy must be A or B")
	}
	if phaseMS != 0 && phaseMS != 1000 {
		return errors.New("lab keepalive phase must be 0 or 1000ms")
	}
	labMedia.Lock()
	defer labMedia.Unlock()
	labMedia.enabled = true
	labMedia.policy = policy
	labMedia.phase = time.Duration(phaseMS) * time.Millisecond
	labMedia.events = make([]labMediaEvent, 0, 100000)
	labMedia.overflow = 0
	labMedia.start = time.Now()
	return nil
}

func labMediaPhase() time.Duration { return labMedia.phase }

func labRecord(event labMediaEvent) {
	if !labMedia.enabled {
		return
	}
	event.At = time.Since(labMedia.start).Nanoseconds()
	labMedia.Lock()
	defer labMedia.Unlock()
	if len(labMedia.events) == cap(labMedia.events) {
		labMedia.overflow++
		return
	}
	labMedia.events = append(labMedia.events, event)
}

func labIdentity(event *labMediaEvent, body []byte) {
	hash := fnv.New64a()
	hash.Write(body)
	event.Hash = hash.Sum64()
	if bytes.Equal(body, vp8Keepalive) {
		event.Kind = "keepalive"
		return
	}
	if !bytes.HasPrefix(body, vp8Interframe) || len(body) < len(vp8Interframe)+fragmentHeaderLen {
		return
	}
	fragment := body[len(vp8Interframe):]
	event.Kind = "data"
	event.Sender = binary.BigEndian.Uint32(fragment)
	event.Message = binary.BigEndian.Uint32(fragment[4:])
	event.Fragment = binary.BigEndian.Uint32(fragment[8:])
	event.Total = binary.BigEndian.Uint32(fragment[12:])
	if event.Fragment != 0 {
		return
	}
	payload := fragment[fragmentHeaderLen:]
	if len(payload) >= 32 && string(payload[:4]) == "FCAP" {
		event.AppKind = payload[4]
		event.AppID = binary.BigEndian.Uint64(payload[16:])
	}
	if len(payload) >= 64 && string(payload[:4]) == "FRS1" && payload[4] == 2 {
		event.RSSeq = binary.BigEndian.Uint64(payload[40:])
	}
}

func labMediaPacket(stage string, header *rtp.Header, payload []byte, result string) {
	if !labMedia.enabled {
		return
	}
	event := labMediaEvent{Stage: stage, SSRC: header.SSRC, Timestamp: header.Timestamp, Sequence: header.SequenceNumber, Marker: header.Marker, Size: len(payload)}
	var descriptor codecs.VP8Packet
	body, err := descriptor.Unmarshal(payload)
	if err == nil {
		event.Start = descriptor.S == 1 && descriptor.PID == 0
		event.PictureKnown = descriptor.I == 1
		event.Picture = descriptor.PictureID
		labIdentity(&event, body)
	} else {
		event.Kind = "invalid_descriptor"
	}
	if result != "ok" {
		event.Stage = stage + "_" + result
	}
	labRecord(event)
}

func labMediaFrame(stage string, body []byte, stamp uint32, sequence uint16) {
	event := labMediaEvent{Stage: stage, Timestamp: stamp, Sequence: sequence, Size: len(body)}
	labIdentity(&event, body)
	labRecord(event)
}

func labMediaRTCP(stage string, packets []rtcp.Packet) {
	for _, packet := range packets {
		event := labMediaEvent{Stage: stage, Kind: fmt.Sprintf("%T", packet), Size: packet.MarshalSize()}
		switch report := packet.(type) {
		case *rtcp.SenderReport:
			event.SSRC = report.SSRC
			event.Timestamp = report.RTPTime
			event.NTP = report.NTPTime
			event.Count = report.PacketCount
		case *rtcp.ReceiverReport:
			for _, block := range report.Reports {
				labRecord(labMediaEvent{Stage: stage, Kind: "RRblock", SSRC: block.SSRC, Count: block.LastSequenceNumber, Lost: block.TotalLost, Jitter: block.Jitter})
			}
		}
		labRecord(event)
	}
}

func LabMediaFlush(emit func(map[string]any) error) {
	labMedia.Lock()
	events := append([]labMediaEvent(nil), labMedia.events...)
	overflow := labMedia.overflow
	labMedia.Unlock()
	for _, event := range events {
		_ = emit(map[string]any{"event": "media", "entry": event})
	}
	_ = emit(map[string]any{"event": "media_trace_end", "count": len(events), "overflow": overflow, "policy": labMedia.policy, "keepalive_phase_ms": labMedia.phase.Milliseconds()})
}

func (session *Session) labWriteSample(sample media.Sample) error {
	return session.labWriteSampleAt(sample, time.Now())
}

func (session *Session) labWriteSampleAt(sample media.Sample, now time.Time) error {
	if labMedia.policy != "B" {
		return session.track.WriteSample(sample)
	}
	if !session.labSampleTime.IsZero() {
		elapsed := now.Sub(session.labSampleTime)
		if elapsed < 0 {
			return errors.New("nonmonotonic laboratory sample clock")
		}
		for elapsed > time.Hour {
			if err := session.track.WriteSample(media.Sample{Duration: time.Hour}); err != nil {
				return err
			}
			elapsed -= time.Hour
		}
		if err := session.track.WriteSample(media.Sample{Duration: elapsed}); err != nil {
			return err
		}
	}
	session.labSampleTime = now
	sample.Duration = 0
	return session.track.WriteSample(sample)
}
