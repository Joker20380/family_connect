package labquic

import (
 "context"
 "errors"
 "net"
 "runtime"
 "testing"
 "time"
)

func TestLabDeadlineExtensionAndClosedLifetimes(test *testing.T){
 before:=runtime.NumGoroutine()
 left,right:=memoryPair(0);sender,receiver:=NewPacketConn(left,false),NewPacketConn(right,true)
 receiver.SetReadDeadline(time.Now().Add(50*time.Millisecond));done:=make(chan error,1)
 go func(){_,_,err:=receiver.ReadFrom(make([]byte,1200));done<-err}()
 time.Sleep(10*time.Millisecond);receiver.SetReadDeadline(time.Now().Add(time.Second));time.Sleep(65*time.Millisecond)
 sender.WriteTo([]byte{1},sender.Peer());if err:=<-done;err!=nil{test.Fatal("old deadline fired after extension",err)}
 sender.Close();receiver.Close();right.incoming<-[]byte{2}
 if _,_,err:=receiver.ReadFrom(make([]byte,1200));!errors.Is(err,net.ErrClosed){test.Fatal("stale delivery after close",err)}
 for index:=0;index<5;index++{client,_,_,_,cleanup:=openTestPair(test,"none",time.Millisecond);stream,err:=client.OpenStreamSync(context.Background());if err!=nil{test.Fatal(err)};stream.Write([]byte{1});cleanup()}
 deadline:=time.Now().Add(2*time.Second)
 for runtime.NumGoroutine()>before+2 && time.Now().Before(deadline){runtime.GC();time.Sleep(20*time.Millisecond)}
 after:=runtime.NumGoroutine();if after>before+2{test.Fatal("goroutine lifetime growth",before,after)}
 test.Logf("five complete transport lifetimes; goroutines before=%d after=%d; no new live traffic",before,after)
}
