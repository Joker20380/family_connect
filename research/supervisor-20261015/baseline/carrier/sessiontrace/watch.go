//go:build fc_owner_diagnostic

package sessiontrace

import "time"

const EvidenceWatchTTL = 30 * time.Second

type EvidenceWatch struct {
	Target      WatchTarget         `json:"target"`
	State       string              `json:"state"`
	StartedAtMS int64               `json:"started_at_ms"`
	EndedAtMS   int64               `json:"ended_at_ms,omitempty"`
	Events      map[string]Boundary `json:"events"`
}

type watchControl struct {
	value    *EvidenceWatch
	deadline time.Time
	identity Boundary
}

func (recorder *Recorder) EnableEvidenceWatch(target WatchTarget) bool {
	if recorder == nil || !evidenceWatchEnabled() {
		return false
	}
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	return recorder.enableEvidenceWatch(target, time.Now())
}

func (recorder *Recorder) enableEvidenceWatch(target WatchTarget, now time.Time) bool {
	if recorder.watch.value != nil || recorder.closing || recorder.value.CorrelationStatus != "VALID" ||
		target.Direction != "tx" || target.Attempt != 1 || target.Sequence == ^uint64(0) {
		return false
	}
	recorder.watch = watchControl{value: &EvidenceWatch{Target: target, State: "ACTIVE", StartedAtMS: now.UnixMilli(), Events: map[string]Boundary{}}, deadline: now.Add(EvidenceWatchTTL)}
	return true
}

func (recorder *Recorder) watchBoundary(point Boundary, now time.Time) {
	recorder.expireWatch(now)
	watch := recorder.watch.value
	if watch == nil || watch.State != "ACTIVE" {
		return
	}
	target := watch.Target
	data := point.Direction == target.Direction && point.DataKnown && point.DataSequence == target.Sequence
	if target.Direction == "tx" {
		data = data && point.AttemptKnown && point.Attempt == target.Attempt
	}
	if data && point.MessageKnown {
		identity := recorder.watch.identity
		if identity.MessageKnown && (identity.Sender != point.Sender || identity.Message != point.Message) {
			watch.State, watch.EndedAtMS = "AMBIGUOUS", now.UnixMilli()
			return
		}
		recorder.watch.identity = point
	}
	if point.Result != "ok" {
		return
	}
	ackDirection := "rx"
	if target.Direction == "rx" {
		ackDirection = "tx"
	}
	ack := point.Direction == ackDirection && Allowed(point.Stage, "ack_generated|ack_sent|ack_received|base_advanced") && point.ACKBase > target.Sequence
	if !data && !ack {
		return
	}
	if _, exists := watch.Events[point.Stage]; !exists {
		watch.Events[point.Stage] = point
	}
	required := []string{"reliable_send", "carrier_queued", "rtp_written", "ack_received", "base_advanced"}
	if target.Direction == "rx" {
		required = []string{"rtp_received", "vp8_reassembled", "carrier_message_completed", "reliable_data_accepted", "reliable_consumed", "ack_generated", "ack_sent"}
	}
	for _, stage := range required {
		if _, exists := watch.Events[stage]; !exists {
			return
		}
	}
	watch.State, watch.EndedAtMS = "COMPLETE", now.UnixMilli()
}

func (recorder *Recorder) expireWatch(now time.Time) {
	if recorder.watch.value != nil && recorder.watch.value.State == "ACTIVE" && !now.Before(recorder.watch.deadline) {
		recorder.watch.value.State, recorder.watch.value.EndedAtMS = "TIMEOUT", now.UnixMilli()
	}
}

func (recorder *Recorder) watchEvent(event Event) {
	recorder.expireWatch(time.Now())
	if recorder.watch.value != nil && recorder.watch.value.State == "ACTIVE" &&
		(event.Stage == "LOCAL_CLOSE" || event.Stage == "CLEANUP" || event.State == "FAILED") {
		recorder.watch.value.State, recorder.watch.value.EndedAtMS = "CLOSED", time.Now().UnixMilli()
	}
}

func cloneWatch(value *EvidenceWatch) *EvidenceWatch {
	if value == nil {
		return nil
	}
	copy := *value
	copy.Events = make(map[string]Boundary, len(value.Events))
	for stage, point := range value.Events {
		copy.Events[stage] = point
	}
	return &copy
}

func (recorder *Recorder) watchSnapshot() *EvidenceWatch {
	recorder.expireWatch(time.Now())
	return cloneWatch(recorder.watch.value)
}
