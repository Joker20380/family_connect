package sessiontrace

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"strings"
	"sync"
	"time"
)

const Limit = 192

type Event struct {
	SessionTag  string `json:"session_tag"`
	Sequence    uint64 `json:"sequence"`
	TimestampMS int64  `json:"timestamp_ms"`
	Stage       string `json:"stage"`
	State       string `json:"state"`
	Reason      string `json:"reason"`
	Target      string `json:"target,omitempty"`
	CloseCode   int    `json:"close_code,omitempty"`
	CloseReason string `json:"close_reason,omitempty"`
	TX          uint64 `json:"tx"`
	RX          uint64 `json:"rx"`
}

type Snapshot struct {
	SessionTag        string  `json:"session_tag"`
	CorrelationStatus string  `json:"correlation_status"`
	Events            []Event `json:"trace"`
	FirstFailure      *Event  `json:"first_failure,omitempty"`
	Dropped           uint64  `json:"trace_dropped"`
	ExportDropped     uint64  `json:"export_dropped"`
}

type Recorder struct {
	mu       sync.Mutex
	value    Snapshot
	sequence uint64
	closing  bool
	sink     func(Event) bool
}

func Tag(identifier string) (string, string) {
	if identifier == "" {
		return "", "MISSING"
	}
	if len(identifier) != 64 {
		return "", "INVALID"
	}
	raw, err := hex.DecodeString(identifier)
	if err != nil || len(raw) != 32 {
		return "", "INVALID"
	}
	digest := sha256.Sum256(append([]byte("family-connect/session-diagnostic/v2\x00"), raw...))
	return hex.EncodeToString(digest[:]), "VALID"
}

func New(identifier string, sink func(Event) bool) *Recorder {
	tag, status := Tag(identifier)
	return &Recorder{value: Snapshot{SessionTag: tag, CorrelationStatus: status, Events: []Event{}}, sink: sink}
}

func Allowed(value, choices string) bool {
	return strings.Contains("|"+choices+"|", "|"+value+"|") && !strings.Contains(value, "|")
}

const Stages = "AUTHORIZED|ROOM_CREATION|DESCRIPTOR|GATEWAY_JOIN|SIGNALING|WEBSOCKET|ICE|PEER_CONNECTION|CARRIER|CARRIER_ACTIVITY|FAMILY_TLS|GATEWAY_SESSION|HEARTBEAT|LIVENESS|LOCAL_CLOSE|REMOTE_CLOSE|RECOVERY|CLEANUP"
const States = "STARTED|ESTABLISHED|ISSUED|TX|RX|FAILED|CLOSED|COMPLETED|ATTEMPTED|NOT_ATTEMPTED|new|checking|connecting|connected|completed|disconnected|failed|closed"
const Reasons = "NONE|SIGNAL_WS_CLOSE|ICE_DISCONNECTED|ICE_FAILED|PEER_CONNECTION_FAILED|CARRIER_EOF|CARRIER_ERROR|FAMILY_TLS_EOF|FAMILY_TLS_ERROR|GATEWAY_CLOSE|HEARTBEAT_TIMEOUT|REMOTE_CLOSE|RECOVERY_CLEANUP_FAILED|RECOVERY_DESCRIPTOR_FAILED|RECOVERY_JOIN_FAILED|RECOVERY_CARRIER_FAILED|UNKNOWN_INTERNAL"

func (recorder *Recorder) Record(event Event) {
	if recorder == nil {
		return
	}
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	if recorder.value.CorrelationStatus != "VALID" || !Allowed(event.Stage, Stages) || !Allowed(event.State, States) || !Allowed(event.Reason, Reasons) || !Allowed(event.Target, "|SUBSCRIBER|PUBLISHER") {
		recorder.value.Dropped++
		return
	}
	if event.CloseCode < 1000 || event.CloseCode > 4999 {
		event.CloseCode = 0
	}
	if !Allowed(event.CloseReason, "|ping|timeout|duplicate|expired|inactivity|shutdown|restart|invalid|ack|idle|session|READ_ERROR|READ_TIMEOUT|INVALID_MESSAGE|WRITE_ERROR") {
		event.CloseReason = ""
	}
	recorder.sequence++
	event.Sequence, event.TimestampMS, event.SessionTag = recorder.sequence, time.Now().UnixMilli(), recorder.value.SessionTag
	if event.Stage == "LOCAL_CLOSE" {
		recorder.closing = true
	}
	if event.Reason != "NONE" && !recorder.closing && recorder.value.FirstFailure == nil {
		first := event
		recorder.value.FirstFailure = &first
	}
	if len(recorder.value.Events) == Limit {
		copy(recorder.value.Events, recorder.value.Events[1:])
		recorder.value.Events = recorder.value.Events[:Limit-1]
		recorder.value.Dropped++
	}
	recorder.value.Events = append(recorder.value.Events, event)
	if recorder.sink != nil && !recorder.sink(event) {
		recorder.value.ExportDropped++
	}
}

func (recorder *Recorder) Add(stage, state, reason string) {
	recorder.Record(Event{Stage: stage, State: state, Reason: reason})
}

func (recorder *Recorder) Snapshot() Snapshot {
	if recorder == nil {
		return Snapshot{CorrelationStatus: "MISSING", Events: []Event{}}
	}
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	value := recorder.value
	value.Events = append([]Event{}, value.Events...)
	if value.FirstFailure != nil {
		first := *value.FirstFailure
		value.FirstFailure = &first
	}
	return value
}

type contextKey struct{}
type slotKey struct{}
type slot struct {
	sync.Mutex
	recorder *Recorder
}

func With(ctx context.Context, recorder *Recorder) context.Context {
	return context.WithValue(ctx, contextKey{}, recorder)
}
func Watch(ctx context.Context) context.Context { return context.WithValue(ctx, slotKey{}, &slot{}) }
func Publish(ctx context.Context, recorder *Recorder) {
	if holder, ok := ctx.Value(slotKey{}).(*slot); ok {
		holder.Lock()
		holder.recorder = recorder
		holder.Unlock()
	}
}
func From(ctx context.Context) *Recorder {
	if recorder, ok := ctx.Value(contextKey{}).(*Recorder); ok {
		return recorder
	}
	if holder, ok := ctx.Value(slotKey{}).(*slot); ok {
		holder.Lock()
		defer holder.Unlock()
		return holder.recorder
	}
	return nil
}
