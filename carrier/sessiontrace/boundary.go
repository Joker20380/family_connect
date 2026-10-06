package sessiontrace

import (
	"context"
	"time"
)

const BoundaryLimit = 64

const BoundaryResults = "ok|write_error|no_rtp|incomplete|duplicate|stale|recent|capacity|conflict|expired|crc|malformed|protocol|old_rtp|window|frame_discard"

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
	recorder.correlationBoundary(point, time.Now())
	recorder.boundaries[(point.Index-1)%BoundaryLimit] = point
	recorder.watchBoundary(point, time.Now())
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
	if selected, matched := recorder.watchAttempt(point); matched {
		return selected
	}
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
