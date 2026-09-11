// Synthetic CI peer: UDP echo in a memory TUN, no host routes or external service.
package main
import (
 "bytes"
 "encoding/binary"
 "encoding/json"
 "errors"
 "io"
 "os"
 "sync"
 "strings"
 "time"
 "strconv"
 "sync/atomic"
 "golang.org/x/sys/windows"
 "github.com/amnezia-vpn/amneziawg-go/conn"
 "github.com/amnezia-vpn/amneziawg-go/device"
 "github.com/amnezia-vpn/amneziawg-go/tun"
)
// RIO reports ICMP port-unreachable as a receive error after the test kills a client.
// Keep the synthetic gateway listening; all other errors retain native handling.
type peerBind struct{conn.Bind; resets atomic.Uint64}
func(b *peerBind)Open(port uint16)([]conn.ReceiveFunc,uint16,error){
 fs,p,e:=b.Bind.Open(port);if e!=nil{return nil,0,e}
 for i,f:=range fs{fs[i]=func(bufs [][]byte,sizes []int,eps []conn.Endpoint)(int,error){
  for{n,e:=f(bufs,sizes,eps);if errors.Is(e,windows.WSAECONNRESET){b.resets.Add(1);continue};return n,e}
 }}
 return fs,p,nil
}
type memory struct { packets chan []byte; events chan tun.Event; done chan struct{}; once sync.Once }
func (m *memory) File()*os.File{return nil}
func (m *memory) Name()(string,error){return "fixture",nil}
func (m *memory) MTU()(int,error){return 1280,nil}
func (m *memory) BatchSize()int{return 1}
func (m *memory) Events()<-chan tun.Event{return m.events}
func (m *memory) Close()error{m.once.Do(func(){close(m.done)});return nil}
func (m *memory) Read(b [][]byte,sizes []int,offset int)(int,error){select{case p:=<-m.packets:sizes[0]=copy(b[0][offset:],p);return 1,nil;case <-m.done:return 0,os.ErrClosed}}
func sum(p []byte)uint16{var s uint32;for len(p)>1{s+=uint32(binary.BigEndian.Uint16(p));p=p[2:]} ;if len(p)>0{s+=uint32(p[0])<<8};for s>>16!=0{s=(s&65535)+(s>>16)};return ^uint16(s)}
func echo(in []byte)[]byte{
 p:=append([]byte(nil),in...);var n int;var pseudo []byte
 if len(p)>=28&&p[0]>>4==4&&p[9]==17 {
  n=int(p[0]&15)*4;if n<20||len(p)<n+8{return nil}
  src:=append([]byte(nil),p[12:16]...);copy(p[12:16],p[16:20]);copy(p[16:20],src)
  p[10]=0;p[11]=0;binary.BigEndian.PutUint16(p[10:12],sum(p[:n]))
  pseudo=append(pseudo,p[12:20]...);pseudo=append(pseudo,0,17,byte((len(p)-n)>>8),byte(len(p)-n))
 }else if len(p)>=48&&p[0]>>4==6&&p[6]==17 {
  n=40;src:=append([]byte(nil),p[8:24]...);copy(p[8:24],p[24:40]);copy(p[24:40],src)
  pseudo=append(pseudo,p[8:40]...);pseudo=append(pseudo,0,0,byte((len(p)-n)>>8),byte(len(p)-n),0,0,0,17)
 }else{return nil}
 if int(binary.BigEndian.Uint16(p[n+4:n+6]))!=len(p)-n{return nil}
 port:=binary.BigEndian.Uint16(p[n:n+2]);copy(p[n:n+2],p[n+2:n+4]);binary.BigEndian.PutUint16(p[n+2:n+4],port)
 p[n+6]=0;p[n+7]=0;c:=sum(append(pseudo,p[n:]...));if c==0{c=65535};binary.BigEndian.PutUint16(p[n+6:n+8],c);return p
}
func(m *memory)Write(b [][]byte,offset int)(int,error){for _,p:=range b{if r:=echo(p[offset:]);r!=nil{select{case m.packets<-r:case <-m.done:return 0,os.ErrClosed}}};return len(b),nil}
func run()error{
 if os.Getenv("GITHUB_ACTIONS")!="true"{return errors.New("CI required")}
 raw,e:=io.ReadAll(io.LimitReader(os.Stdin,16385));if e!=nil||len(raw)>16384{return errors.New("size")}
 var cfg struct{Config string `json:"config"`};d:=json.NewDecoder(bytes.NewReader(raw));d.DisallowUnknownFields();if e=d.Decode(&cfg);e!=nil{return e}
 m:=&memory{packets:make(chan []byte,64),events:make(chan tun.Event,1),done:make(chan struct{})};m.events<-tun.EventUp
 var countsMu sync.Mutex;counts:=map[string]int{}
 logf:=func(format string,args ...any){
  for _,label:=range []string{"Received handshake initiation","Received handshake response","Received invalid initiation","Received invalid response","invalid mac1","disallowed source","Failed to receive","Failed to send"}{
   if strings.Contains(format,label){countsMu.Lock();counts[label]++;countsMu.Unlock()}
  }
 }
 bind:=&peerBind{Bind:conn.NewDefaultBind()}
 dev:=device.NewDevice(m,bind,&device.Logger{Verbosef:logf,Errorf:logf});defer dev.Close()
 if e=dev.IpcSet(cfg.Config);e!=nil{return e};if e=dev.Up();e!=nil{return e};os.Stdout.WriteString("ready\n")
 ticker:=time.NewTicker(time.Second);defer ticker.Stop()
 for {select {case <-dev.Wait():return nil;case <-ticker.C:
  // CI-only aggregate counters, never key/config material.
  raw,e:=dev.IpcGet();if e!=nil{continue};stats:=map[string]string{"connection_reset_ignored":strconv.FormatUint(bind.resets.Load(),10)}
  for _,line:=range strings.Split(raw,"\n"){k,v,ok:=strings.Cut(line,"=");if ok&&(k=="last_handshake_time_sec"||k=="rx_bytes"||k=="tx_bytes"){stats[k]=v}}
  countsMu.Lock();for k,v:=range counts{stats[k]=strconv.Itoa(v)};countsMu.Unlock();json.NewEncoder(os.Stdout).Encode(stats)
 }}
}
func main(){if run()!=nil{os.Stderr.WriteString("AWG fixture failed\n");os.Exit(1)}}
