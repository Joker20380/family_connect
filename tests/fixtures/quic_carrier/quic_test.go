package labquic

import (
 "bytes"
 "context"
 "io"
 "testing"
 "time"
 "github.com/quic-go/quic-go"
)

func openTestPair(test *testing.T,fault string,delay time.Duration)(*quic.Conn,*quic.Conn,*memoryEndpoint,*memoryEndpoint,func()){
 test.Helper();credentials,err:=EphemeralCredentials();if err!=nil{test.Fatal(err)}
 left,right:=memoryPair(delay);left.fault=fault;if fault=="handshake" || fault=="reverse"{left.fault="";right.fault=fault}
 clientPacket,serverPacket:=NewPacketConn(left,false),NewPacketConn(right,true)
 ctx,cancel:=context.WithTimeout(context.Background(),20*time.Second);type result struct{connection *quic.Conn;cleanup func();err error};ready:=make(chan result,1)
 go func(){connection,cleanup,err:=Open(ctx,serverPacket,credentials[1],true,NewObserver());ready<-result{connection,cleanup,err}}()
 client,clientClose,err:=Open(ctx,clientPacket,credentials[0],false,NewObserver());if err!=nil{cancel();serverPacket.Close();test.Fatal(err)}
 server:=<-ready;if server.err!=nil{test.Fatal(server.err)}
 cleanup:=func(){client.CloseWithError(0,"test");server.connection.CloseWithError(0,"test");clientPacket.Close();serverPacket.Close();clientClose();server.cleanup();cancel()}
 return client,server.connection,left,right,cleanup
}

func TestQUICFaultsExact(test *testing.T){for _,fault:=range []string{"none","initial","handshake","burst","reverse","duplicate","reorder","slow"}{test.Run(fault,func(test *testing.T){
 client,server,left,right,cleanup:=openTestPair(test,fault,time.Millisecond);defer cleanup();ctx,cancel:=context.WithTimeout(context.Background(),15*time.Second);defer cancel()
 body:=bytes.Repeat([]byte("QUIC-boundary-integrity"),12000);done:=make(chan error,1)
 go func(){stream,err:=client.OpenStreamSync(ctx);if err==nil{_,err=io.Copy(stream,bytes.NewReader(body));if err==nil{err=stream.Close()}};done<-err}()
 stream,err:=server.AcceptStream(ctx);if err!=nil{test.Fatal(err)};stream.SetReadDeadline(time.Now().Add(14*time.Second));var actual bytes.Buffer;buffer:=make([]byte,397)
 for{count,err:=stream.Read(buffer);actual.Write(buffer[:count]);if fault=="slow"{time.Sleep(time.Millisecond)};if err==io.EOF{break};if err!=nil{test.Fatal(err)}}
 if err:=<-done;err!=nil || !bytes.Equal(actual.Bytes(),body){test.Fatal("body",err)}
 if (fault=="handshake" || fault=="initial" || fault=="burst" || fault=="reverse") && left.drops.Load()+right.drops.Load()==0{test.Fatal("fault not applied")}
 test.Logf("fault=%s bytes=%d dropped=%d/%d",fault,len(body),left.drops.Load(),right.drops.Load())
})}}

func TestQUICIndependentStreamGapAndReset(test *testing.T){
 client,server,left,_,cleanup:=openTestPair(test,"none",10*time.Millisecond);defer cleanup();ctx,cancel:=context.WithTimeout(context.Background(),5*time.Second);defer cancel();time.Sleep(100*time.Millisecond)
 first,err:=client.OpenStreamSync(ctx);if err!=nil{test.Fatal(err)};left.drop.Store(1);first.Write([]byte("stream-zero-gap"));first.Close()
 deadline:=time.Now().Add(time.Second);for left.drops.Load()==0 && time.Now().Before(deadline){time.Sleep(time.Millisecond)};if left.drops.Load()!=1{test.Fatal("no fault")}
 second,err:=client.OpenStreamSync(ctx);if err!=nil{test.Fatal(err)};second.Write([]byte("independent-ready"));second.Close()
 arrived:=make(chan quic.StreamID,2)
 go func(){for index:=0;index<2;index++{stream,err:=server.AcceptStream(ctx);if err!=nil{return};go func(){_,err:=io.ReadAll(stream);if err==nil{arrived<-stream.StreamID()}}()}}()
 select{case identifier:=<-arrived:if identifier!=second.StreamID(){test.Fatal("independent data blocked by first-stream gap",identifier)};case <-ctx.Done():test.Fatal(ctx.Err())}
 select{case identifier:=<-arrived:if identifier!=first.StreamID(){test.Fatal("gap not recovered")};case <-ctx.Done():test.Fatal(ctx.Err())}
 stalled,_:=client.OpenStreamSync(ctx);written:=make(chan error,1);go func(){_,err:=stalled.Write(make([]byte,384<<10));written<-err}();received,err:=server.AcceptStream(ctx);if err!=nil{test.Fatal(err)};time.Sleep(40*time.Millisecond)
 select{case <-written:test.Fatal("128KiB flow limit bypassed");default:}
 received.CancelRead(91);select{case err:=<-written:if err==nil{test.Fatal("reset not propagated")};case <-ctx.Done():test.Fatal(ctx.Err())}
 good,_:=client.OpenStreamSync(ctx);good.Write([]byte("still alive"));good.Close();peer,err:=server.AcceptStream(ctx);if err!=nil{test.Fatal(err)};body,err:=io.ReadAll(peer);if err!=nil || string(body)!="still alive"{test.Fatal("reset aborted connection",err)}
 test.Log("stream4 delivered before recovery of stream0; reset isolated; fixed flow cap blocks slow reader")
}

func TestQUICAuthRejectAndClose(test *testing.T){
 first,_:=EphemeralCredentials();second,_:=EphemeralCredentials()
 for _,bad:=range []string{"ca","role","alpn"}{test.Run(bad,func(test *testing.T){
 left,right:=memoryPair(0);clientPacket,serverPacket:=NewPacketConn(left,false),NewPacketConn(right,true);ctx,cancel:=context.WithTimeout(context.Background(),700*time.Millisecond);defer cancel();defer clientPacket.Close();defer serverPacket.Close()
 serverTLS,_:=TLS(first[1],true);clientTLS,_:=TLS(first[0],false);if bad=="ca"{clientTLS,_=TLS(second[0],false)};if bad=="role"{clientTLS,_=TLS(first[1],false)};if bad=="alpn"{clientTLS.NextProtos=[]string{"wrong"}}
 serverTransport:=&quic.Transport{Conn:serverPacket};listener,err:=serverTransport.Listen(serverTLS,Config(NewObserver()));if err!=nil{test.Fatal(err)};defer func(){serverPacket.Close();listener.Close();serverTransport.Close()}()
 accepted:=make(chan error,1);go func(){connection,err:=listener.Accept(ctx);if err==nil{connection.CloseWithError(1,"unexpected")};accepted<-err}()
 clientTransport:=&quic.Transport{Conn:clientPacket};connection,err:=clientTransport.Dial(ctx,clientPacket.Peer(),clientTLS,Config(NewObserver()));if err==nil{connection.CloseWithError(0,"test")};clientPacket.Close();clientTransport.Close()
 if serverErr:=<-accepted;serverErr==nil{test.Fatal("bad peer accepted")}
 })}
 client,_,_,_,cleanup:=openTestPair(test,"none",time.Millisecond);stream,_:=client.OpenStreamSync(context.Background());done:=make(chan error,1);go func(){_,err:=stream.Write(make([]byte,1<<20));done<-err}();time.Sleep(30*time.Millisecond);client.CloseWithError(9,"cancel incomplete");select{case err:=<-done:if err==nil{test.Fatal("incomplete close success")};case <-time.After(time.Second):test.Fatal("close leaked")};cleanup()
}

func TestQUICStreamCountLimit(test *testing.T){
 client,_,_,_,cleanup:=openTestPair(test,"none",time.Millisecond);defer cleanup()
 for index:=0;index<24;index++{stream,err:=client.OpenStream();if err!=nil{test.Fatal(index,err)};if _,err:=stream.Write([]byte{1});err!=nil{test.Fatal(err)}}
 if _,err:=client.OpenStream();err==nil{test.Fatal("stream count limit absent")}
}

func TestQUICSharedStreamGap(test *testing.T){
 client,server,left,_,cleanup:=openTestPair(test,"none",10*time.Millisecond);defer cleanup();ctx,cancel:=context.WithTimeout(context.Background(),5*time.Second);defer cancel();time.Sleep(100*time.Millisecond)
 stream,_:=client.OpenStreamSync(ctx);left.drop.Store(1);stream.Write(bytes.Repeat([]byte{1},32));deadline:=time.Now().Add(time.Second)
 for left.drops.Load()==0 && time.Now().Before(deadline){time.Sleep(time.Millisecond)};if left.drops.Load()!=1{test.Fatal("fault not applied")}
 stream.Write(bytes.Repeat([]byte{2},32));stream.Close();peer,err:=server.AcceptStream(ctx);if err!=nil{test.Fatal(err)}
 peer.SetReadDeadline(time.Now().Add(10*time.Millisecond));buffer:=make([]byte,64);count,err:=peer.Read(buffer);if err==nil || count!=0{test.Fatal("shared ordered stream bypassed missing prefix",count,err)}
 peer.SetReadDeadline(time.Now().Add(3*time.Second));body,err:=io.ReadAll(peer);expected:=append(bytes.Repeat([]byte{1},32),bytes.Repeat([]byte{2},32)...);if err!=nil || !bytes.Equal(body,expected){test.Fatal("shared stream recovery",err)}
 test.Log("same-stream later bytes blocked behind missing prefix; contrasted with native independent-stream test")
}
