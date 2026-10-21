package telemost

import (
 "bytes"
 "context"
 "io"
 "sync"
 "testing"
 "time"
 "github.com/Joker20380/family_connect/carrier/labquic"
 "github.com/pion/interceptor"
 "github.com/pion/rtp"
 "github.com/quic-go/quic-go"
)

func TestQUICCarrierBoundPion(test *testing.T){for _,normalized:=range []bool{false,true}{test.Run(map[bool]string{false:"original",true:"normalized"}[normalized],func(test *testing.T){
 ConfigureLabNormalized(normalized);labCeilingOriginal=!normalized
 defer func(){ConfigureLabNormalized(false);labCeilingOriginal=false}()
 ctx,cancel:=context.WithTimeout(context.Background(),25*time.Second);defer cancel();left,right:=headLossPair(test,ctx,0,"none");defer left.Close();defer right.Close()
 var mutex sync.Mutex;packets,maximum:=0,0
 for _,point:=range []*headLossEndpoint{left,right}{
  point.track.Unbind(lossTrackContext{});boundary,_:=(&boundaryFactory{trace:point.cfg.Trace,writes:&point.rtpWrites}).NewInterceptor("")
  writer:=boundary.BindLocalStream(&interceptor.StreamInfo{MimeType:"video/VP8"},interceptor.RTPWriterFunc(func(header *rtp.Header,payload []byte,_ interceptor.Attributes)(int,error){
   labMediaRate(header.MarshalSize()+len(payload)+64,header.MarshalSize())
   mutex.Lock();packets++;maximum=max(maximum,header.MarshalSize()+len(payload));mutex.Unlock()
   point.peer.receive([]*rtp.Packet{(&rtp.Packet{Header:*header,Payload:payload}).Clone()});return header.MarshalSize()+len(payload),nil
  }))
  if _,err:=point.track.Bind(lossTrackContext{writer:lossTrackWriter{writer}});err!=nil{test.Fatal(err)};point.startWorker(point.writerLoop)
 }
 clientPacket,serverPacket:=labquic.NewPacketConn(left.Session,false),labquic.NewPacketConn(right.Session,true);defer clientPacket.Close();defer serverPacket.Close()
 body:=bytes.Repeat([]byte{0xab},1200);started:=time.Now();received:=make(chan error,1)
 go func(){buffer:=make([]byte,1200);for index:=0;index<300;index++{count,_,err:=serverPacket.ReadFrom(buffer);if err!=nil{received<-err;return};if count!=1200 || !bytes.Equal(buffer,body){received<-io.ErrUnexpectedEOF;return}};received<-nil}()
 for index:=0;index<300;index++{if _,err:=clientPacket.WriteTo(body,clientPacket.Peer());err!=nil{test.Fatal(err)}}
 if err:=<-received;err!=nil{test.Fatal(err)};elapsed:=time.Since(started)
 mutex.Lock();packetCount,maxPacket:=packets,maximum;mutex.Unlock()
 if packetCount!=600 || maxPacket!=1200{test.Fatal("packetization",packetCount,maxPacket)}
 test.Logf("ADAPTER normalized=%t bytes=360000 datagrams=300 frames=300 RTP=600 maxRTP=%d seconds=%.6f datagrams_s=%.2f bytes_s=%.2f actual_write_max_ms=%.3f",normalized,maxPacket,elapsed.Seconds(),300/elapsed.Seconds(),360000/elapsed.Seconds(),float64(clientPacket.Stats().WriteMaxNS)/1e6)
 credentials,_:=labquic.EphemeralCredentials();type opened struct{connection *quic.Conn;cleanup func();err error};ready:=make(chan opened,1)
 go func(){connection,cleanup,err:=labquic.Open(ctx,serverPacket,credentials[1],true,labquic.NewObserver());ready<-opened{connection,cleanup,err}}()
 client,closeClient,err:=labquic.Open(ctx,clientPacket,credentials[0],false,labquic.NewObserver());if err!=nil{test.Fatal(err)};peer:=<-ready;if peer.err!=nil{test.Fatal(peer.err)}
 defer func(){client.CloseWithError(0,"test");peer.connection.CloseWithError(0,"test");clientPacket.Close();serverPacket.Close();closeClient();peer.cleanup()}()
 expected:=bytes.Repeat([]byte("QUIC-on-Pion-L"),24000);done:=make(chan error,1)
 go func(){stream,err:=client.OpenStreamSync(ctx);if err==nil{_,err=stream.Write(expected);if err==nil{err=stream.Close()}};done<-err}()
 stream,err:=peer.connection.AcceptStream(ctx);if err!=nil{test.Fatal(err)};actual,err:=io.ReadAll(stream);if err!=nil || !bytes.Equal(actual,expected){test.Fatal("QUIC/Pion integrity",err)};if err:=<-done;err!=nil{test.Fatal(err)}
 if clientPacket.Stats().WriteErrors!=0{test.Fatal("write failed")}
 test.Logf("QUIC_PION bytes=%d max_datagram=%d",len(expected),1200)
})}}
