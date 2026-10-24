package tcpforward

import (
    "bytes"
    "context"
    "encoding/json"
    "io"
    "testing"
)

func TestLifeCrossedResetAfterLocalRemoval(test *testing.T) {
    ctx,cancel:=context.WithCancel(context.Background());defer cancel()
    mux:=&Mux{window:131072,ctx:ctx,cancel:cancel,config:MuxConfig{Lifecycle:true},streams:make(map[uint32]*MuxStream),changed:make(chan struct{})}
    stream:=mux.makeStreamLocked(91);stream.opened=true
    mux.lifeLocked("opened",91,openOK,"peer")
    neighbor:=mux.makeStreamLocked(93);neighbor.opened=true
    stream.resetLocked(ErrReset)
    if len(stream.send)!=1 || stream.send[0].kind!=resetFrame {test.Fatal("missing local reset")}
    stream.send=nil
    mux.lifeLocked("send_done",91,resetFrame,"local")
    mux.removeLocked(91)
    mux.dispatchLocked(muxFrame{kind:resetFrame,id:91})
    incident:=mux.lifeSnapshotLocked().FirstUnknown
    if incident==nil || !incident.Known || incident.Stream.Reason!="reset" || incident.Event.Kind!=resetFrame || incident.Stream.Removed>incident.Event.At || incident.FailureAt!=0 || incident.Cancelled {test.Fatal("crossed reset provenance",incident)}
    if stream.receive!=nil || stream.send!=nil || stream.used!=0 || mux.streams[91]!=nil {test.Fatal("retained retired stream")}
    mux.dispatchLocked(muxFrame{kind:dataFrame,id:93,payload:[]byte("neighbor intact")})
    buffer:=make([]byte,15);count,err:=neighbor.Read(buffer)
    if err!=nil || !bytes.Equal(buffer[:count],[]byte("neighbor intact")) {test.Fatal("neighbor corrupted",err)}
    if mux.stats.ProtocolErrors!=1 || mux.stats.ProtocolErrorReasons.UnknownStream!=1 {test.Fatal("raw history rewritten")}
    mux.dispatchLocked(muxFrame{kind:resetFrame,id:999})
    mux.dispatchLocked(muxFrame{kind:openOK,id:93})
    if mux.stats.ProtocolErrors!=3 || neighbor.terminal!=ErrProtocol {test.Fatal("real violations hidden")}
}

func TestLifeLateControlAfterResetDoesNotChangeNeighbor(test *testing.T) {
    for _,kind:=range []byte{muxWindowUpdate,closeFrame} {
        ctx,cancel:=context.WithCancel(context.Background())
        mux:=&Mux{window:131072,ctx:ctx,cancel:cancel,config:MuxConfig{Lifecycle:true},streams:make(map[uint32]*MuxStream),changed:make(chan struct{})}
        stream:=mux.makeStreamLocked(47);stream.opened=true
        neighbor:=mux.makeStreamLocked(49);neighbor.opened=true
        stream.resetLocked(ErrReset);stream.send=nil;mux.removeLocked(47)
        frame:=muxFrame{kind:kind,id:47}
        if kind==muxWindowUpdate {frame.payload=[]byte{0,0,0,24}}
        decoded,err:=decodeMuxWindow(frame.encode(),131072)
        if err!=nil {test.Fatal(err)}
        credit:=neighbor.sendCredit
        mux.dispatchLocked(decoded)
        incident:=mux.lifeSnapshotLocked().FirstUnknown
        if incident==nil || !incident.Known || incident.Stream.Reason!="reset" || incident.Event.Kind!=kind || incident.FailureAt!=0 {test.Fatal("missing late control history")}
        if neighbor.sendCredit!=credit || neighbor.terminal!=nil || mux.stats.ProtocolErrors!=1 || mux.streams[47]!=nil {test.Fatal("changed stream state or hid raw event")}
        frame.payload=[]byte{1}
        if _,err:=decodeMuxWindow(frame.encode(),131072);err!=ErrProtocol {test.Fatal("malformed control accepted")}
        cancel()
    }
}

func TestLifeLateResetAfterClosedEOF(test *testing.T) {
    ctx,cancel:=context.WithCancel(context.Background());defer cancel()
    mux:=&Mux{window:131072,ctx:ctx,cancel:cancel,server:true,config:MuxConfig{Lifecycle:true},streams:make(map[uint32]*MuxStream),changed:make(chan struct{})}
    stream:=mux.makeStreamLocked(51);stream.opened=true;stream.localFIN=true;stream.remoteFIN=true
    neighbor:=mux.makeStreamLocked(53);neighbor.opened=true
    stream.finishLocked(io.EOF);mux.removeLocked(51)
    mux.dispatchLocked(muxFrame{kind:resetFrame,id:51})
    incident:=mux.lifeSnapshotLocked().FirstUnknown
    if incident==nil || !incident.Known || incident.Stream.Reason!="eof" || !incident.Stream.LocalFIN || !incident.Stream.RemoteFIN || incident.Stream.Used!=0 {test.Fatal("lost completed-stream provenance")}
    if mux.stats.ProtocolErrors!=1 || neighbor.terminal!=nil || mux.streams[51]!=nil {test.Fatal("late reset changed a live stream or hid the counter")}
}

func TestLifeUnknownAfterResetAndNeverKnown(test *testing.T) {
    ctx,cancel:=context.WithCancel(context.Background());defer cancel()
    mux:=&Mux{window:131072,ctx:ctx,cancel:cancel,config:MuxConfig{Lifecycle:true},streams:make(map[uint32]*MuxStream),changed:make(chan struct{})}
    stream:=mux.makeStreamLocked(1);stream.opened=true
    mux.lifeLocked("opened",1,openOK,"peer")
    neighbor:=mux.makeStreamLocked(3);neighbor.opened=true
    mux.dispatchLocked(muxFrame{kind:resetFrame,id:1})
    mux.dispatchLocked(muxFrame{kind:dataFrame,id:1,payload:[]byte{42}})
    snapshot:=mux.lifeSnapshotLocked()
    incident:=snapshot.FirstUnknown
    if incident==nil || !incident.Known || incident.Stream.ID!=1 || incident.Stream.Reason!="reset" || incident.Stream.Created==0 || incident.Stream.Opened==0 || incident.Stream.Removed<incident.Stream.Finished || incident.FailureAt!=0 || incident.Cancelled {test.Fatal("lost provenance",incident)}
    if mux.stats.ProtocolErrors!=1 || neighbor.terminal!=nil {test.Fatal("observation changed behavior")}
    incident.Stream.ID=99
    if mux.lifeSnapshotLocked().FirstUnknown.Stream.ID!=1 {test.Fatal("aliased incident")}
    mux.life.first=nil
    mux.dispatchLocked(muxFrame{kind:dataFrame,id:101,payload:[]byte{42}})
    if mux.lifeSnapshotLocked().FirstUnknown.Known {test.Fatal("invented stream history")}
}

func TestLifeBoundsAndFailureOrder(test *testing.T) {
    ctx,cancel:=context.WithCancel(context.Background());defer cancel()
    mux:=&Mux{ctx:ctx,cancel:cancel,config:MuxConfig{Lifecycle:true},streams:make(map[uint32]*MuxStream),changed:make(chan struct{})}
    for index:=uint32(1);index<10000;index++ {
        stream:=mux.makeStreamLocked(index);stream.finishLocked(ErrReset);mux.removeLocked(index)
    }
    mux.lifeLocked("failure",0,0,"closed_pipe")
    mux.dispatchLocked(muxFrame{kind:dataFrame,id:9999,payload:[]byte{1}})
    snapshot:=mux.lifeSnapshotLocked()
    if len(snapshot.Events)!=32 || snapshot.Dropped==0 || snapshot.FirstUnknown.FailureAt==0 || len(mux.streams)!=0 {test.Fatal("unbounded or missing failure")}
    raw,err:=json.Marshal(snapshot)
    if err!=nil || len(raw)>8192 {test.Fatal("export bound",len(raw),err)}
    snapshot.Events[0].Stage="modified"
    if mux.lifeSnapshotLocked().Events[0].Stage=="modified" {test.Fatal("aliased ring")}
    mux.config.Lifecycle=false
    if mux.lifeSnapshotLocked()!=nil {test.Fatal("disabled observer exported")}
}
