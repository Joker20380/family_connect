package labquic

import (
 "bytes"
 "context"
 "encoding/binary"
 "errors"
 "io"
 "sync"
 "time"
 "github.com/quic-go/quic-go"
)

type Framed struct {stream *quic.Stream;mutex sync.Mutex;ctx context.Context;cancel context.CancelFunc;received chan []byte;done chan struct{};err error;errMutex sync.Mutex}
func NewFramed(parent context.Context,stream *quic.Stream) *Framed {
 ctx,cancel:=context.WithCancel(parent);endpoint:=&Framed{stream:stream,ctx:ctx,cancel:cancel,received:make(chan []byte,1),done:make(chan struct{})}
 go func(){defer close(endpoint.done);for{
  var header [4]byte;_,err:=io.ReadFull(stream,header[:]);var payload []byte
  if err==nil{length:=binary.BigEndian.Uint32(header[:]);if length==0 || length>65536{err=errors.New("QS frame size")}else{payload=make([]byte,length);_,err=io.ReadFull(stream,payload)}}
  if err!=nil{endpoint.errMutex.Lock();endpoint.err=err;endpoint.errMutex.Unlock();return}
  select{case endpoint.received<-payload:case <-ctx.Done():return}
 }}();return endpoint
}
func (endpoint *Framed) SendContext(ctx context.Context,payload []byte) error {return endpoint.SendBatchContext(ctx,[][]byte{payload})}
func (endpoint *Framed) SendBatchContext(ctx context.Context,batch [][]byte) error {
 endpoint.mutex.Lock();defer endpoint.mutex.Unlock();var total int
 for _,payload:=range batch{if len(payload)==0 || len(payload)>65536{return errors.New("QS send size")};total+=4+len(payload)}
 if total>131072{return errors.New("QS batch limit")};buffer:=make([]byte,0,total)
 for _,payload:=range batch{buffer=binary.BigEndian.AppendUint32(buffer,uint32(len(payload)));buffer=append(buffer,payload...)}
 deadline,ok:=ctx.Deadline();if !ok{deadline=time.Now().Add(10*time.Second)};endpoint.stream.SetWriteDeadline(deadline)
 stop:=context.AfterFunc(ctx,func(){endpoint.stream.CancelWrite(1)});defer stop();_,err:=io.Copy(endpoint.stream,bytes.NewReader(buffer));return err
}
func (endpoint *Framed) Recv(ctx context.Context)([]byte,error){select{case payload:=<-endpoint.received:return payload,nil;case <-endpoint.done:endpoint.errMutex.Lock();defer endpoint.errMutex.Unlock();if endpoint.err==nil{return nil,context.Canceled};return nil,endpoint.err;case <-ctx.Done():return nil,ctx.Err();case <-endpoint.ctx.Done():return nil,endpoint.ctx.Err()}}
func (endpoint *Framed) Close() error{endpoint.cancel();endpoint.stream.CancelRead(1);endpoint.stream.CancelWrite(1);<-endpoint.done;return nil}
