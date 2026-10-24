package tcpforward

import (
    "context"
    "errors"
    "io"
    "time"
)

type MuxLifeEvent struct {
    Index uint64 `json:"index"`
    At int64 `json:"at"`
    ID uint32 `json:"id"`
    Kind byte `json:"kind"`
    Stage string `json:"stage"`
    Reason string `json:"reason"`
}

type MuxLifeStream struct {
    ID uint32 `json:"id"`
    Created int64 `json:"created"`
    Opened int64 `json:"opened"`
    Finished int64 `json:"finished"`
    Removed int64 `json:"removed"`
    Reason string `json:"reason"`
    Sent uint64 `json:"sent"`
    Received uint64 `json:"received"`
    Used int `json:"used"`
    SendCredit int `json:"send_credit"`
    ReceiveCredit int `json:"receive_credit"`
    LocalFIN bool `json:"local_fin"`
    RemoteFIN bool `json:"remote_fin"`
}

type MuxLifeIncident struct {
    Event MuxLifeEvent `json:"event"`
    Known bool `json:"known"`
    Stream MuxLifeStream `json:"stream"`
    FailureAt int64 `json:"failure_at"`
    Cancelled bool `json:"cancelled"`
}

type MuxLifecycle struct {
    Events []MuxLifeEvent `json:"events"`
    Dropped uint64 `json:"dropped"`
    FirstUnknown *MuxLifeIncident `json:"first_unknown,omitempty"`
    FailureAt int64 `json:"failure_at"`
    FailureReason string `json:"failure_reason"`
    CloseAt int64 `json:"close_at"`
}

type muxLifeBuffer struct {
    events [32]MuxLifeEvent
    count uint64
    removed [64]MuxLifeStream
    removedCount uint64
    first *MuxLifeIncident
    failureAt int64
    failureReason string
    closeAt int64
}

func lifeReason(err error) string {
    switch {
    case err == nil: return "none"
    case errors.Is(err, io.EOF): return "eof"
    case errors.Is(err, ErrReset): return "reset"
    case errors.Is(err, ErrProtocol): return "protocol"
    case errors.Is(err, context.Canceled): return "cancelled"
    case errors.Is(err, context.DeadlineExceeded): return "deadline"
    case errors.Is(err, io.ErrClosedPipe): return "closed_pipe"
    default: return "other"
    }
}

func (mux *Mux) lifeLocked(stage string, id uint32, kind byte, reason string) {
    if !mux.config.Lifecycle { return }
    buffer := &mux.life
    buffer.count++
    event := MuxLifeEvent{buffer.count, time.Now().UnixMilli(), id, kind, stage, reason}
    buffer.events[(buffer.count-1)%32] = event
    stream := mux.streams[id]
    if stream != nil {
        if stage == "create" { stream.life.ID = id; stream.life.Created = event.At }
        if stage == "opened" { stream.life.Opened = event.At }
        if stage == "finish" {
            stream.life.Finished = event.At; stream.life.Reason = reason
            stream.life.Sent, stream.life.Received, stream.life.Used = stream.sent, stream.received, stream.used
            stream.life.SendCredit, stream.life.ReceiveCredit = stream.sendCredit, stream.receiveCredit
            stream.life.LocalFIN, stream.life.RemoteFIN = stream.localFIN, stream.remoteFIN
        }
        if stage == "remove" {
            stream.life.Removed = event.At
            buffer.removed[buffer.removedCount%64] = stream.life
            buffer.removedCount++
        }
    }
    if stage == "failure" && buffer.failureAt == 0 { buffer.failureAt = event.At; buffer.failureReason = reason }
    if stage == "close" && buffer.closeAt == 0 { buffer.closeAt = event.At }
    if stage == "unknown" && buffer.first == nil {
        incident := &MuxLifeIncident{Event:event, FailureAt:buffer.failureAt, Cancelled:mux.ctx.Err()!=nil}
        for _, retired := range buffer.removed {
            if retired.ID == id && retired.Created != 0 { incident.Known=true; incident.Stream=retired; break }
        }
        buffer.first=incident
    }
}

func (mux *Mux) lifeSnapshotLocked() *MuxLifecycle {
    if !mux.config.Lifecycle { return nil }
    buffer:= &mux.life
    snapshot:= &MuxLifecycle{FailureAt:buffer.failureAt, FailureReason:buffer.failureReason, CloseAt:buffer.closeAt}
    start:=uint64(0)
    if buffer.count>32 { start=buffer.count-32; snapshot.Dropped=start }
    for index:=start;index<buffer.count;index++ { snapshot.Events=append(snapshot.Events,buffer.events[index%32]) }
    if buffer.first!=nil { incident:=*buffer.first; snapshot.FirstUnknown=&incident }
    return snapshot
}
