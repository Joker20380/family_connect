package tcpforward

import (
    "bytes"
    "context"
    "fmt"
    "testing"
    "time"
)

func TestLifecycle101RealWorkersBothProfiles(test *testing.T) {
    for _,window:=range []int{65536,131072} {
        test.Run(fmt.Sprint(window),func(test *testing.T){
            port:=muxFixture(test,muxEcho)
            ctx,cancel:=context.WithTimeout(context.Background(),15*time.Second)
            left,right:=pipePair()
            client:=newMuxWindow(ctx,left,false,MuxConfig{MaxStreams:16,Lifecycle:true},window)
            server:=newMuxWindow(ctx,right,true,MuxConfig{MaxStreams:16,Lifecycle:true,Policy:Policy{TestOnlyLoopbackPort:port}},window)
            defer func(){cancel();client.Close();server.Close()}()
            for index:=0;index<16;index++ {
                neighbor:=muxOpen(test,ctx,client,port)
                request,abort:=context.WithCancel(ctx)
                target:=muxOpen(test,request,client,port)
                if _,err:=target.Write(bytes.Repeat([]byte("queued"),2048));err!=nil {test.Fatal(err)}
                abort()
                if err:=exactMux(neighbor,bytes.Repeat([]byte("drained"),1000));err!=nil {test.Fatal(err)}
                target.Close()
            }
            cancel()
            began:=time.Now();client.Close();server.Close()
            if time.Since(began)>time.Second {test.Fatal("unbounded workers")}
            for _,mux:=range []*Mux{client,server} {
                stats:=mux.Stats()
                if stats.ActiveSockets!=0 || stats.ActiveStreams!=0 || stats.RetainedBytes!=0 {test.Fatal("resources leaked",stats)}
                if stats.Lifecycle.Violations!=0 {test.Fatal("valid cancellation misclassified",stats.Lifecycle.Incidents)}
            }
        })
    }
}

func TestLifecycle101RecordedCreditThenResetAfterPeerFIN(test *testing.T) {
    for _,window:=range []int{65536,131072} {
        test.Run(fmt.Sprint(window),func(test *testing.T){
            mux:=lifecycleMux(test,window)
            stream:=mux.makeStreamLocked(3)
            stream.opened=true
            mux.lifeLocked("opened",3,openOK,"peer")
            mux.dispatchLocked(muxFrame{dataFrame,3,[]byte("drained")})
            mux.dispatchLocked(muxFrame{finFrame,3,nil})
            output:=make([]byte,7)
            count,err:=stream.Read(output)
            if err!=nil || count!=7 || string(output)!="drained" {test.Fatal("accepted tail",count,err)}
            stream.sendCredit=window-24
            stream.resetLocked(ErrReset)
            stream.send=nil
            mux.lifeLocked("send_done",3,resetFrame,"local")
            mux.removeLocked(3)
            mux.dispatchLocked(lifecycleCredit(3,24))
            mux.dispatchLocked(muxFrame{resetFrame,3,nil})
            snapshot:=mux.lifeSnapshotLocked()
            if snapshot.Expected!=2 || snapshot.Violations!=0 || snapshot.Unclassified!=0 || mux.stats.ProtocolErrors!=2 {test.Fatal("recorded crossing",snapshot)}
            if snapshot.Incidents[0].Detail!="inflight_credit_on_abort" || snapshot.Incidents[1].Detail!="crossed_reset" {test.Fatal("wrong sequence",snapshot.Incidents)}
            if !snapshot.Incidents[0].Stream.RemoteFIN || snapshot.Incidents[0].Stream.LocalFIN || snapshot.Incidents[0].Stream.SendCredit!=window-24 || snapshot.Incidents[1].Stream.SendCredit!=window {test.Fatal("credit history",snapshot.Incidents)}
            if mux.streams[3]!=nil || stream.receive!=nil || stream.send!=nil || stream.used!=0 || stream.sendCredit!=window-24 {test.Fatal("retired state changed")}
            mux.dispatchLocked(lifecycleCredit(3,1))
            if mux.lifeSnapshotLocked().Violations!=1 || mux.stats.ProtocolErrors!=3 {test.Fatal("ordered post-RESET frame hidden")}
        })
    }
}

func TestLifecycle101RecordedCloseCrossingAfterLocalAbort(test *testing.T) {
    for _,window:=range []int{65536,131072} {
        test.Run(fmt.Sprint(window),func(test *testing.T){
            mux:=lifecycleMux(test,window)
            mux.server=true
            stream:=mux.makeStreamLocked(67)
            stream.opened=true
            mux.lifeLocked("opened",67,openOK,"peer")
            mux.dispatchLocked(muxFrame{dataFrame,67,[]byte("tail")})
            mux.dispatchLocked(muxFrame{finFrame,67,nil})
            if err:=stream.CloseWrite();err!=nil {test.Fatal(err)}
            output:=make([]byte,4)
            count,err:=stream.Read(output)
            if err!=nil || count!=4 || string(output)!="tail" {test.Fatal("tail",count,err)}
            stream.resetLocked(ErrReset)
            stream.send=nil
            mux.lifeLocked("send_done",67,resetFrame,"local")
            mux.removeLocked(67)
            mux.dispatchLocked(muxFrame{closeFrame,67,nil})
            snapshot:=mux.lifeSnapshotLocked()
            if snapshot.Expected!=1 || snapshot.Violations!=0 || snapshot.Unclassified!=0 || mux.stats.ProtocolErrors!=1 || snapshot.Incidents[0].Detail!="crossed_close" {test.Fatal("CLOSE crossing",snapshot)}
            if mux.streams[67]!=nil || stream.receive!=nil || stream.send!=nil || stream.used!=0 {test.Fatal("retired resources")}
            neighbor:=mux.makeStreamLocked(69)
            neighbor.opened=true
            mux.dispatchLocked(muxFrame{dataFrame,69,[]byte("safe")})
            count,err=neighbor.Read(output)
            if err!=nil || count!=4 || string(output)!="safe" {test.Fatal("neighbor",count,err)}
            mux.dispatchLocked(muxFrame{closeFrame,67,nil})
            if mux.lifeSnapshotLocked().Violations!=1 || mux.stats.ProtocolErrors!=2 {test.Fatal("duplicate CLOSE hidden")}
        })
    }
}
