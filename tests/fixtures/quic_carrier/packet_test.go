package labquic

import (
 "bytes"
 "context"
 "errors"
 "io"
 "net"
 "os"
 "sync"
 "sync/atomic"
 "testing"
 "time"
 "github.com/Joker20380/family_connect/carrier/localwrite"
)

type memoryEndpoint struct {incoming chan []byte;peer *memoryEndpoint;count atomic.Int64;drop atomic.Int64;drops atomic.Int64;delay time.Duration;fault string;held []byte;mutex sync.Mutex;done chan struct{}}
func hasHandshake(body []byte)bool {
 for len(body)>=7 && body[0]&0x80!=0 {
  kind:=(body[0]>>4)&3;if kind==2{return true};if kind==3{return false}
  position:=6+int(body[5]);if position>=len(body){return false};position+=1+int(body[position]);if position>=len(body){return false}
  integer:=func()(uint64,bool){if position>=len(body){return 0,false};count:=1<<uint(body[position]>>6);if position+count>len(body){return 0,false};value:=uint64(body[position]&63);for index:=1;index<count;index++{value=value<<8|uint64(body[position+index])};position+=count;return value,true}
  if kind==0{length,ok:=integer();if !ok || length>uint64(len(body)-position){return false};position+=int(length)}
  length,ok:=integer();if !ok || length>uint64(len(body)-position){return false};body=body[position+int(length):]
 };return false
}
func memoryPair(delay time.Duration)(*memoryEndpoint,*memoryEndpoint){left:=&memoryEndpoint{incoming:make(chan []byte,32),done:make(chan struct{}),delay:delay};right:=&memoryEndpoint{incoming:make(chan []byte,32),done:make(chan struct{}),delay:delay};left.peer=right;right.peer=left;return left,right}
func (endpoint *memoryEndpoint) SendContext(ctx context.Context,body []byte)error {
 endpoint.mutex.Lock();defer endpoint.mutex.Unlock();write,err:=localwrite.Register(ctx,1);if err!=nil{return err};if !write.Begin(){return ctx.Err()}
 if endpoint.delay>0{select{case <-time.After(endpoint.delay):case <-ctx.Done():return ctx.Err()}}
 number:=endpoint.count.Add(1);drop:=endpoint.drop.CompareAndSwap(1,0)
 if endpoint.fault=="initial" && number==1{drop=true}
 if endpoint.fault=="handshake" && hasHandshake(body) && endpoint.drops.Load()==0{drop=true}
 if endpoint.fault=="burst" && number>=12 && number<=17{drop=true}
 if endpoint.fault=="reverse" && number>=9 && number<=18{drop=true}
 if drop {endpoint.drops.Add(1);write.Complete(nil);return nil}
 send:=func(data []byte)error{select{case endpoint.peer.incoming<-append([]byte(nil),data...):return nil;case <-ctx.Done():return ctx.Err();case <-endpoint.done:return net.ErrClosed}}
 if endpoint.fault=="reorder" && number==15{endpoint.held=append([]byte(nil),body...)}else{
  if err=send(body);err==nil && endpoint.held!=nil{err=send(endpoint.held);endpoint.held=nil}
  if err==nil && endpoint.fault=="duplicate" && number%11==0{err=send(body)}
 }
 write.Complete(err);return err
}
func (endpoint *memoryEndpoint) Recv(ctx context.Context)([]byte,error){select{case body:=<-endpoint.incoming:return body,nil;case <-ctx.Done():return nil,ctx.Err();case <-endpoint.done:return nil,net.ErrClosed}}

func TestPacketContract(test *testing.T){
 left,right:=memoryPair(0);sender,receiver:=NewPacketConn(left,false),NewPacketConn(right,true);defer sender.Close();defer receiver.Close()
 for _,size:=range []int{1,1199,1200}{body:=bytes.Repeat([]byte{byte(size)},size);expected:=append([]byte(nil),body...);count,err:=sender.WriteTo(body,sender.Peer());clear(body);actual:=make([]byte,1200);received,peer,readErr:=receiver.ReadFrom(actual);if count!=size || err!=nil || readErr!=nil || received!=size || peer.String()!=receiver.Peer().String() || !bytes.Equal(actual[:received],expected){test.Fatal("boundary or ownership")}}
 if _,err:=sender.WriteTo(make([]byte,1201),sender.Peer());err==nil{test.Fatal("oversize")}
 if _,err:=sender.WriteTo([]byte{1},&net.UDPAddr{IP:net.ParseIP("127.0.0.1"),Port:4443});err==nil{test.Fatal("routing")}
 sender.WriteTo(make([]byte,1200),sender.Peer());if _,_,err:=receiver.ReadFrom(make([]byte,12));!errors.Is(err,io.ErrShortBuffer){test.Fatal(err)}
 receiver.SetReadDeadline(time.Now().Add(20*time.Millisecond));if _,_,err:=receiver.ReadFrom(make([]byte,1200));!errors.Is(err,os.ErrDeadlineExceeded){test.Fatal(err)}
 receiver.SetReadDeadline(time.Time{});done:=make(chan error,1);go func(){_,_,err:=receiver.ReadFrom(make([]byte,1200));done<-err}();time.Sleep(time.Millisecond);receiver.SetReadDeadline(time.Now().Add(10*time.Millisecond));if err:=<-done;!errors.Is(err,os.ErrDeadlineExceeded){test.Fatal(err)}
 receiver.SetReadDeadline(time.Time{});go func(){_,_,err:=receiver.ReadFrom(make([]byte,1200));done<-err}();receiver.Close();if err:=<-done;!errors.Is(err,net.ErrClosed){test.Fatal(err)}
 if _,err:=receiver.WriteTo([]byte{1},receiver.Peer());!errors.Is(err,net.ErrClosed){test.Fatal(err)}
}
func TestPacketBoundedBlockedClose(test *testing.T){
 left,_:=memoryPair(0);sender:=NewPacketConn(left,false);for index:=0;index<32;index++{if _,err:=sender.WriteTo([]byte{1},sender.Peer());err!=nil{test.Fatal(err)}}
 sender.SetWriteDeadline(time.Now().Add(15*time.Millisecond));if _,err:=sender.WriteTo([]byte{1},sender.Peer());!errors.Is(err,os.ErrDeadlineExceeded){test.Fatal(err)}
 sender.SetWriteDeadline(time.Time{});var wait sync.WaitGroup
 for index:=0;index<4;index++{wait.Add(1);go func(){defer wait.Done();_,err:=sender.WriteTo([]byte{1},sender.Peer());if err==nil{test.Error("close succeeded")}}()}
 time.Sleep(time.Millisecond);sender.Close();wait.Wait();if len(left.peer.incoming)!=32{test.Fatal("unbounded queue")}
}
