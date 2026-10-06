package sessiontrace

import (
	"context"
	"time"
)

const BoundaryLimit = 64

const BoundaryStages = "reliable_send|carrier_queued|carrier_written|rtp_written|rtp_received|vp8_reassembled|carrier_message_completed|reliable_data_accepted|ack_generated|ack_sent|ack_received"
const BoundaryResults = "ok|write_error|no_rtp|incomplete|duplicate|stale|recent|capacity|conflict|expired|crc|malformed|protocol|old_rtp|window|frame_discard"

type Boundary struct {
	Index        uint64 `json:"index"`
	AtMS         int64  `json:"at_ms"`
	Direction    string `json:"direction"`
	Stage        string `json:"stage"`
	Result       string `json:"result"`
	DataKnown    bool   `json:"data_known,omitempty"`
	DataSequence uint64 `json:"data_sequence,omitempty"`
	AttemptKnown bool   `json:"attempt_known,omitempty"`
	Attempt      uint32 `json:"attempt,omitempty"`
	MessageKnown bool   `json:"message_known,omitempty"`
	Sender       uint32 `json:"sender,omitempty"`
	Message      uint32 `json:"message,omitempty"`
	Fragment     uint32 `json:"fragment,omitempty"`
	Total        uint32 `json:"total,omitempty"`
	FrameKnown   bool   `json:"frame_known,omitempty"`
	Timestamp    uint32 `json:"timestamp,omitempty"`
	MediaTrack   uint32 `json:"media_track,omitempty"`
	FirstRTP     uint16 `json:"first_rtp,omitempty"`
	LastRTP      uint16 `json:"last_rtp,omitempty"`
	Packets      uint32 `json:"packets,omitempty"`
	ACKBase      uint64 `json:"ack_base,omitempty"`
	ACKMask      uint32 `json:"ack_mask,omitempty"`
}

type Boundaries struct {
	Events  []Boundary `json:"events"`
	Dropped uint64     `json:"dropped"`
}

func (recorder *Recorder) Boundary(point Boundary) {
	if recorder == nil {
		return
	}
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	if recorder.value.CorrelationStatus != "VALID" || !Allowed(point.Stage, BoundaryStages) || !Allowed(point.Result, BoundaryResults) || !Allowed(point.Direction, "tx|rx") {
		return
	}
	recorder.boundaryNext++
	point.Index, point.AtMS = recorder.boundaryNext, time.Now().UnixMilli()
	recorder.boundaries[(point.Index-1)%BoundaryLimit] = point
}

func (recorder *Recorder) boundarySnapshot() *Boundaries {
	if recorder.boundaryNext == 0 {
		return nil
	}
	value := &Boundaries{Dropped: recorder.boundaryNext - min(recorder.boundaryNext, BoundaryLimit)}
	for index := value.Dropped; index < recorder.boundaryNext; index++ {
		value.Events = append(value.Events, recorder.boundaries[index%BoundaryLimit])
	}
	return value
}

func (recorder *Recorder) MessageAttempt(point Boundary) Boundary {
	if recorder == nil || !point.MessageKnown {
		return point
	}
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	for offset := uint64(0); offset < min(recorder.boundaryNext, BoundaryLimit); offset++ {
		candidate := recorder.boundaries[(recorder.boundaryNext-1-offset)%BoundaryLimit]
		if candidate.Direction == "tx" && candidate.MessageKnown && candidate.Sender == point.Sender && candidate.Message == point.Message && candidate.AttemptKnown {
			point.DataKnown, point.DataSequence = candidate.DataKnown, candidate.DataSequence
			point.AttemptKnown, point.Attempt = true, candidate.Attempt
			break
		}
	}
	return point
}

type attemptKey struct{}

func WithAttempt(ctx context.Context, sequence uint64, attempt uint32) context.Context {
	return context.WithValue(ctx, attemptKey{}, Boundary{DataKnown: true, DataSequence: sequence, AttemptKnown: true, Attempt: attempt})
}

func AttemptFrom(ctx context.Context) Boundary {
	point, _ := ctx.Value(attemptKey{}).(Boundary)
	return point
}
