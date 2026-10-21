package main

import (
 "bytes"
 "context"
 "crypto/sha256"
 "encoding/binary"
 "io"
 "sync"
 "testing"
 "time"
 "github.com/Joker20380/family_connect/carrier/labquic"
 "github.com/Joker20380/family_connect/carrier/tcpforward"
 "github.com/quic-go/quic-go"
)
type quicMemory struct{incoming,outgoing chan []byte}
func (endpoint *quicMemory) SendContext(ctx context.Context,body []byte)error{select{case endpoint.outgoing<-append([]byte(nil),body...):return nil;case <-ctx.Done():return ctx.Err()}}
func (endpoint *quicMemory) Recv(ctx context.Context)([]byte,error){select{case body:=<-endpoint.incoming:return body,nil;case <-ctx.Done():return nil,ctx.Err()}}
func TestQUICApplicationContracts(test *testing.T){for _,mode:=range []string{"QN","QS"}{test.Run(mode,func(test *testing.T){
 labShort=true;defer func(){labShort=false}();ctx,cancel:=context.WithTimeout(context.Background(),20*time.Second);defer cancel()
 first,second:=make(chan []byte,32),make(chan []byte,32);left,right:=labquic.NewPacketConn(&quicMemory{first,second},false),labquic.NewPacketConn(&quicMemory{second,first},true)
 credentials,_:=labquic.EphemeralCredentials();type result struct{connection *quic.Conn;close func();err error};ready:=make(chan result,1)
 go func(){connection,cleanup,err:=labquic.Open(ctx,right,credentials[1],true,labquic.NewObserver());ready<-result{connection,cleanup,err}}()
 client,closeClient,err:=labquic.Open(ctx,left,credentials[0],false,labquic.NewObserver());if err!=nil{test.Fatal(err)};server:=<-ready;if server.err!=nil{test.Fatal(server.err)}
 defer func(){client.CloseWithError(0,"test");server.connection.CloseWithError(0,"test");left.Close();right.Close();closeClient();server.close()}()
 var mutex sync.Mutex;count:=0;emit:=func(row map[string]any)error{if row["event"]=="host_request"{mutex.Lock();count++;mutex.Unlock();if row["passed"]!=true{test.Error(row["name"],row["error"])}};return nil}
 var receipts sync.WaitGroup
 if mode=="QN" {
  receipts.Add(17);payload:=hostPayload()
  go func(){for index:=0;index<17;index++{stream,err:=server.connection.AcceptStream(ctx);if err!=nil{test.Error(err);return};go func(){defer receipts.Done();wrapped:=&receiptConn{Conn:&labquic.StreamConn{Stream:stream,Local:right.LocalAddr(),Remote:right.Peer()},hash:sha256.New()};if err:=hostFixtureRequest(wrapped,payload);err!=nil{test.Error(err);return};stream.Close();var receipt [40]byte;if _,err:=io.ReadFull(stream,receipt[:]);err!=nil{test.Error(err);return};if string(receipt[:4])!="QRCP" || int(binary.BigEndian.Uint32(receipt[4:8]))!=wrapped.written || !bytes.Equal(receipt[8:],wrapped.hash.Sum(nil)){test.Error("receipt corruption")}}()}}()
  err=labHostCompare(ctx,func(ctx context.Context)(*hostStream,error){stream,err:=client.OpenStreamSync(ctx);if err!=nil{return nil,err};native:=&nativeStream{Stream:stream};return &hostStream{ReadWriteCloser:native,closeWrite:func()error{return nil},stats:func()any{return map[string]any{"ID":int64(stream.StreamID())}},confirm:native.confirm},nil},func()any{return nil},func()map[string]any{return nil},emit)
  if err!=nil{test.Fatal(err)};receipts.Wait()
 } else {
  stop,err:=hostFixture(ctx,18764,emit);if err!=nil{test.Fatal(err)};defer stop()
  stream,err:=client.OpenStreamSync(ctx);if err!=nil{test.Fatal(err)};clientFrame:=labquic.NewFramed(ctx,stream);defer clientFrame.Close();clientMux:=tcpforward.LabQUICMux(ctx,clientFrame,false);defer clientMux.Close()
  completed:=make(chan error,1);go func(){completed<-muxHostCompare(ctx,clientMux,18764,func()map[string]any{return nil},emit)}()
  peer,err:=server.connection.AcceptStream(ctx);if err!=nil{test.Fatal(err)};serverFrame:=labquic.NewFramed(ctx,peer);defer serverFrame.Close();serverMux:=tcpforward.LabQUICMux(ctx,serverFrame,true);defer serverMux.Close()
  if err=<-completed;err!=nil{test.Fatal(err)}
  deadline:=time.Now().Add(time.Second);for serverMux.Stats().ActiveStreams!=0 && time.Now().Before(deadline){time.Sleep(time.Millisecond)}
  for _,mux:=range []*tcpforward.Mux{clientMux,serverMux}{if mux.Stats().ActiveStreams!=0 || mux.Stats().ProtocolErrors!=0 || mux.Stats().Window!=131072{test.Fatal("QS flow/terminal")}}
 }
 if count!=17{test.Fatal("application count",count)};test.Log("17 exact operations and completion receipts, one QUIC connection",mode)
})}}
