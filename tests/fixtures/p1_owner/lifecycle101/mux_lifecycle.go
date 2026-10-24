package tcpforward

import (
    "context"
    "encoding/binary"
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
    LocalAbort bool `json:"local_abort"`
    PeerTerminal bool `json:"peer_terminal"`
    PeerClose bool `json:"peer_close"`
    Enqueued [9]int64 `json:"enqueued"`
    SendStarted [9]int64 `json:"send_started"`
    SendDone [9]int64 `json:"send_done"`
    ReceiveAt [9]int64 `json:"receive_at"`
}

type MuxLifeIncident struct {
    Event MuxLifeEvent `json:"event"`
    Known bool `json:"known"`
    Stream MuxLifeStream `json:"stream"`
    FailureAt int64 `json:"failure_at"`
    Cancelled bool `json:"cancelled"`
    Class string `json:"class,omitempty"`
    Detail string `json:"detail,omitempty"`
    Bytes int `json:"bytes"`
    Credit int `json:"credit"`
}

type MuxLifecycle struct {
    Events []MuxLifeEvent `json:"events"`
    Dropped uint64 `json:"dropped"`
    FirstUnknown *MuxLifeIncident `json:"first_unknown,omitempty"`
    FailureAt int64 `json:"failure_at"`
    FailureReason string `json:"failure_reason"`
    CloseAt int64 `json:"close_at"`
    Incidents []MuxLifeIncident `json:"incidents"`
    IncidentDropped uint64 `json:"incident_dropped"`
    Expected uint64 `json:"expected_crossings"`
    Violations uint64 `json:"actual_violations"`
    Unclassified uint64 `json:"unclassified"`
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
    incidents [32]MuxLifeIncident
    incidentCount uint64
    expected uint64
    violations uint64
    unclassified uint64
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
        if kind < 9 {
            switch stage {
            case "enqueue": stream.life.Enqueued[kind]=event.At
            case "send_start": stream.life.SendStarted[kind]=event.At
            case "send_done": stream.life.SendDone[kind]=event.At
            case "receive": stream.life.ReceiveAt[kind]=event.At
            }
        }
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
    if stage=="unknown" && buffer.first==nil {
        incident:=&MuxLifeIncident{Event:event,FailureAt:buffer.failureAt,Cancelled:mux.ctx.Err()!=nil}
        for _,retired:=range buffer.removed {
            if retired.ID==id && retired.Created!=0 {incident.Known=true;incident.Stream=retired;break}
        }
        buffer.first=incident
    }
    if stream==nil && (stage=="send_start" || stage=="send_done") && kind<9 {
        for index:=range buffer.removed {
            retired:=&buffer.removed[index]
            if retired.ID==id {
                if stage=="send_start" {retired.SendStarted[kind]=event.At} else {retired.SendDone[kind]=event.At}
                break
            }
        }
    }
}

func (mux *Mux) lifeFrameLocked(frame muxFrame, liveViolation bool) {
    if !mux.config.Lifecycle { return }
    buffer:=&mux.life
    now:=time.Now().UnixMilli()
    incident:=MuxLifeIncident{Event:MuxLifeEvent{buffer.count,now,frame.id,frame.kind,"unknown","missing"},FailureAt:buffer.failureAt,Cancelled:mux.ctx.Err()!=nil,Bytes:len(frame.payload)}
    if frame.kind==muxWindowUpdate && len(frame.payload)==4 {incident.Credit=int(binary.BigEndian.Uint32(frame.payload))}
    var retired *MuxLifeStream
    if stream:=mux.streams[frame.id];stream!=nil {
        retired=&stream.life
        if liveViolation {incident.Event.Stage="violation"}
    } else {
        for index:=range buffer.removed {
            candidate:=&buffer.removed[index]
            if candidate.ID==frame.id && candidate.Created!=0 && now-candidate.Removed<=60000 {retired=candidate;break}
        }
    }
    if retired!=nil {incident.Known=true;incident.Stream=*retired}
    incident.Class,incident.Detail="unclassified","no_retained_history"
    if liveViolation {
        incident.Class,incident.Detail="violation","live_state"
    } else if incident.Cancelled || incident.FailureAt!=0 {
        incident.Detail="after_session_failure"
    } else if retired!=nil {
        incident.Class,incident.Detail=mux.lifeClassifyLocked(frame,retired)
    }
    switch incident.Class {
    case "expected":buffer.expected++
    case "violation":buffer.violations++
    default:buffer.unclassified++
    }
    if buffer.incidentCount<32 {buffer.incidents[buffer.incidentCount]=incident}
    buffer.incidentCount++
    if buffer.first==nil && !liveViolation {copy:=incident;buffer.first=&copy}
}

func (mux *Mux) lifeClassifyLocked(frame muxFrame, retired *MuxLifeStream) (string,string) {
    if _,err:=decodeMuxWindow(frame.encode(),mux.window);err!=nil {return "violation","malformed"}
    if retired.PeerTerminal {return "violation","after_peer_terminal"}
    if frame.kind==resetFrame && ((retired.LocalAbort && retired.Reason=="reset") || (retired.Reason=="eof" && retired.LocalFIN && retired.RemoteFIN && retired.Used==0)) {
        retired.PeerTerminal=true
        return "expected","crossed_reset"
    }
    if !retired.LocalAbort || retired.Reason!="reset" {return "violation","not_local_abort"}
    if retired.PeerClose {return "violation","after_peer_terminal"}
    if frame.kind==openOK && retired.Opened==0 && !mux.server {
        retired.Opened=time.Now().UnixMilli()
        return "expected","cancelled_open"
    }
    if frame.kind==openError && retired.Opened==0 && !mux.server {
        var failure OpenError
        if decodeJSON(frame.payload,&failure)==nil && (validError(failure.Code)||failure.Code=="stream_limit") {
            retired.PeerTerminal=true
            return "expected","cancelled_open"
        }
    }
    if retired.Opened==0 {return "violation","not_opened"}
    switch frame.kind {
    case dataFrame:
        if retired.RemoteFIN {return "violation","data_after_fin"}
        if len(frame.payload)>retired.ReceiveCredit {return "violation","credit_overflow"}
        retired.ReceiveCredit-=len(frame.payload)
        return "expected","inflight_data_on_abort"
    case muxWindowUpdate:
        credit:=int(binary.BigEndian.Uint32(frame.payload))
        if credit>mux.window-retired.SendCredit {return "violation","credit_overflow"}
        retired.SendCredit+=credit
        return "expected","inflight_credit_on_abort"
    case finFrame:
        if retired.RemoteFIN {return "violation","duplicate_fin"}
        retired.RemoteFIN=true
        return "expected","inflight_fin_on_abort"
    case closeFrame:
        if !retired.LocalFIN || !retired.RemoteFIN {return "violation","close_before_fin"}
        retired.PeerClose=true
        return "expected","crossed_close"
    }
    return "violation","terminal_state"
}

func (mux *Mux) lifeSnapshotLocked() *MuxLifecycle {
    if !mux.config.Lifecycle { return nil }
    buffer:= &mux.life
    snapshot:= &MuxLifecycle{FailureAt:buffer.failureAt, FailureReason:buffer.failureReason, CloseAt:buffer.closeAt,Expected:buffer.expected,Violations:buffer.violations,Unclassified:buffer.unclassified}
    for index:=uint64(0);index<min(buffer.incidentCount,32);index++ {snapshot.Incidents=append(snapshot.Incidents,buffer.incidents[index])}
    if buffer.incidentCount>32 {snapshot.IncidentDropped=buffer.incidentCount-32}
    start:=uint64(0)
    if buffer.count>32 { start=buffer.count-32; snapshot.Dropped=start }
    for index:=start;index<buffer.count;index++ { snapshot.Events=append(snapshot.Events,buffer.events[index%32]) }
    if buffer.first!=nil { incident:=*buffer.first; snapshot.FirstUnknown=&incident }
    return snapshot
}
