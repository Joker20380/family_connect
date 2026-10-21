package labquic

import (
 "context"
 "errors"
 "io"
 "net"
 "os"
 "sync"
 "time"

 "github.com/Joker20380/family_connect/carrier/localwrite"
)

const DatagramSize = 1200

type Endpoint interface {
 SendContext(context.Context, []byte) error
 Recv(context.Context) ([]byte, error)
}

type deadline struct { mutex sync.Mutex; when time.Time; changed chan struct{} }
func (limit *deadline) set(when time.Time) { limit.mutex.Lock();defer limit.mutex.Unlock();limit.when=when;close(limit.changed);limit.changed=make(chan struct{}) }
func (limit *deadline) context(parent context.Context) (context.Context,func()) {
 ctx,cancel:=context.WithCancelCause(parent);done:=make(chan struct{})
 go func(){defer close(done);for {
  limit.mutex.Lock();when,changed:=limit.when,limit.changed;limit.mutex.Unlock()
  var timer *time.Timer;var expired <-chan time.Time
  if !when.IsZero(){timer=time.NewTimer(time.Until(when));expired=timer.C}
  select {case <-ctx.Done():if timer!=nil{timer.Stop()};return
  case <-expired:cancel(os.ErrDeadlineExceeded);return
  case <-changed:if timer!=nil{timer.Stop()}}
 }}()
 return ctx,func(){cancel(context.Canceled);<-done}
}

type PacketStats struct {
 Sent,Received,Invalid,ShortBuffer,WriteErrors uint64
 SentBytes,ReceivedBytes,WriteNS,WriteMaxNS uint64
 Sizes map[int]uint64
 Closed bool
}

type PacketConn struct {
 endpoint Endpoint
 ctx context.Context
 cancel context.CancelCauseFunc
 local,peer *net.UDPAddr
 read,write deadline
 gate chan struct{}
 mutex sync.Mutex
 stats PacketStats
}

func NewPacketConn(endpoint Endpoint,server bool) *PacketConn {
 ctx,cancel:=context.WithCancelCause(context.Background())
 local,peer:=net.ParseIP("198.18.0.1"),net.ParseIP("198.18.0.2")
 if server {local,peer=peer,local}
 return &PacketConn{endpoint:endpoint,ctx:ctx,cancel:cancel,local:&net.UDPAddr{IP:local,Port:4443},peer:&net.UDPAddr{IP:peer,Port:4443},read:deadline{changed:make(chan struct{})},write:deadline{changed:make(chan struct{})},gate:make(chan struct{},1),stats:PacketStats{Sizes:make(map[int]uint64)}}
}
func (connection *PacketConn) Peer() net.Addr{return connection.peer}
func (connection *PacketConn) LocalAddr() net.Addr{return connection.local}
func (connection *PacketConn) SetDeadline(when time.Time) error {connection.read.set(when);connection.write.set(when);return nil}
func (connection *PacketConn) SetReadDeadline(when time.Time) error {connection.read.set(when);return nil}
func (connection *PacketConn) SetWriteDeadline(when time.Time) error {connection.write.set(when);return nil}
func (connection *PacketConn) Close() error {connection.cancel(net.ErrClosed);connection.mutex.Lock();connection.stats.Closed=true;connection.mutex.Unlock();return nil}
func (connection *PacketConn) Stats() PacketStats {connection.mutex.Lock();defer connection.mutex.Unlock();result:=connection.stats;result.Sizes=make(map[int]uint64);for size,count:=range connection.stats.Sizes{result.Sizes[size]=count};return result}
func (connection *PacketConn) ReadFrom(buffer []byte) (int,net.Addr,error) {
 ctx,stop:=connection.read.context(connection.ctx);defer stop()
 for {
  payload,err:=connection.endpoint.Recv(ctx)
  if ctx.Err()!=nil{return 0,nil,context.Cause(ctx)}
  if err!=nil{return 0,nil,err}
  connection.mutex.Lock()
  if len(payload)>DatagramSize || len(payload)==0 {connection.stats.Invalid++;connection.mutex.Unlock();continue}
  if len(payload)>len(buffer){connection.stats.ShortBuffer++;connection.mutex.Unlock();return 0,nil,io.ErrShortBuffer}
  connection.stats.Received++;connection.stats.ReceivedBytes+=uint64(len(payload));connection.mutex.Unlock()
  return copy(buffer,payload),connection.peer,nil
 }
}
func (connection *PacketConn) WriteTo(payload []byte,address net.Addr) (int,error) {
 if address==nil || address.Network()!=connection.peer.Network() || address.String()!=connection.peer.String(){return 0,errors.New("lab datagram peer rejected")}
 if len(payload)==0 || len(payload)>DatagramSize{return 0,errors.New("lab datagram size rejected")}
 bounded,cancel:=context.WithTimeout(connection.ctx,5*time.Second);defer cancel()
 ctx,stop:=connection.write.context(bounded);defer stop()
 select{case connection.gate<-struct{}{}:defer func(){<-connection.gate}();case <-ctx.Done():return 0,context.Cause(ctx)}
 if ctx.Err()!=nil{return 0,context.Cause(ctx)}
 started:=time.Now();owned:=append([]byte(nil),payload...)
 writeContext,write:=localwrite.Observe(ctx,nil)
 err:=connection.endpoint.SendContext(writeContext,owned)
 if err==nil{err=write.Wait()}
 if ctx.Err()!=nil{err=context.Cause(ctx)}
 elapsed:=uint64(time.Since(started));connection.mutex.Lock();defer connection.mutex.Unlock()
 connection.stats.WriteNS+=elapsed;connection.stats.WriteMaxNS=max(connection.stats.WriteMaxNS,elapsed)
 if err!=nil{connection.stats.WriteErrors++;return 0,err}
 connection.stats.Sent++;connection.stats.SentBytes+=uint64(len(payload));connection.stats.Sizes[len(payload)]++
 return len(payload),nil
}
