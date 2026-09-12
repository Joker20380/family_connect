package main
// #include <stdint.h>
// int fcProtect(uintptr_t owner, int fd);
// void fcRelease(uintptr_t owner);
import "C"
import (
 "bytes"
 "context"
 "encoding/base64"
 "encoding/json"
 "errors"
 "io"
 "net"
 "net/netip"
 "os"
 "regexp"
 "strconv"
 "sync"
 "sync/atomic"
 "syscall"
 "time"
 xnet "github.com/xtls/xray-core/common/net"
 "github.com/xtls/xray-core/core"
 "github.com/xtls/xray-core/infra/conf/serial"
 "github.com/xtls/xray-core/transport/internet"
 "golang.org/x/sys/unix"
 _ "github.com/xtls/xray-core/app/dispatcher"
 _ "github.com/xtls/xray-core/app/proxyman/inbound"
 _ "github.com/xtls/xray-core/app/proxyman/outbound"
 _ "github.com/xtls/xray-core/app/policy"
 _ "github.com/xtls/xray-core/app/router"
 _ "github.com/xtls/xray-core/app/log"
 _ "github.com/xtls/xray-core/app/dns"
 _ "github.com/xtls/xray-core/app/stats"
 _ "github.com/xtls/xray-core/proxy/tun"
 _ "github.com/xtls/xray-core/proxy/vless/outbound"
 _ "github.com/xtls/xray-core/transport/internet/tcp"
 _ "github.com/xtls/xray-core/transport/internet/reality"
 _ "github.com/xtls/xray-core/transport/internet/tls"
 _ "github.com/xtls/xray-core/transport/internet/udp"
 _ "github.com/xtls/xray-core/transport/internet/tagged/taggedimpl"
)
var tcpRunning atomic.Bool
var tcpMu sync.Mutex
var tcpCurrent *tcpSession
var tcpSequence int64
var tcpInstances sync.Map // immutable instance -> session binding; old dials never use a new session
var denied=errors.New("TCP operation refused")
type tcpSession struct {
 id int64
 instance *core.Instance
 owner C.uintptr_t
 fd int
 endpoint string
 ctx context.Context
 cancel context.CancelFunc
 mu sync.Mutex
 closing bool
 dials sync.WaitGroup
 conns map[*tcpConn]bool
}
type tcpConn struct {net.Conn;s *tcpSession}
func(c *tcpConn)Close()error{err:=c.Conn.Close();c.s.mu.Lock();delete(c.s.conns,c);c.s.mu.Unlock();return err}
type protectedDialer struct{}
func(protectedDialer)DestIpAddress()xnet.IP{return nil}
func(protectedDialer)Dial(ctx context.Context,_ xnet.Address,dest xnet.Destination,_ *internet.SocketConfig)(xnet.Conn,error){
 value,ok:=tcpInstances.Load(core.FromContext(ctx));if !ok{return nil,denied};s:=value.(*tcpSession)
 if dest.Network!=xnet.Network_TCP||dest.NetAddr()!=s.endpoint{return nil,denied}
 s.mu.Lock();if s.closing{s.mu.Unlock();return nil,denied};s.dials.Add(1);s.mu.Unlock();defer s.dials.Done()
 dialCtx,cancel:=context.WithCancel(ctx);defer cancel();unhook:=context.AfterFunc(s.ctx,cancel);defer unhook()
 d:=net.Dialer{Timeout:16*time.Second,KeepAlive:30*time.Second,Control:func(_, _ string,raw syscall.RawConn)error{
  protectErr:=denied
  if err:=raw.Control(func(fd uintptr){if C.fcProtect(s.owner,C.int(fd))!=0{protectErr=nil}});err!=nil{return err}
  return protectErr
 }}
 conn,err:=d.DialContext(dialCtx,"tcp",s.endpoint);if err!=nil{return nil,denied}
 s.mu.Lock();defer s.mu.Unlock();if s.closing{conn.Close();return nil,denied}
 tracked:=&tcpConn{Conn:conn,s:s};s.conns[tracked]=true;return tracked,nil
}
func init(){internet.UseAlternativeSystemDialer(protectedDialer{})}
func tcpConfig(raw string)([]byte,string,error){
 if len(raw)>4096{return nil,"",denied}
 dec:=json.NewDecoder(bytes.NewBufferString(raw));t,e:=dec.Token();if e!=nil||t!=json.Delim('{'){return nil,"",denied}
 p:=map[string]json.RawMessage{}
 for dec.More(){t,e=dec.Token();if e!=nil{return nil,"",denied};key,ok:=t.(string);if !ok||p[key]!=nil{return nil,"",denied};var value json.RawMessage;if dec.Decode(&value)!=nil{return nil,"",denied};p[key]=value}
 if _,e=dec.Token();e!=nil{return nil,"",denied};if _,e=dec.Token();e!=io.EOF{return nil,"",denied}
 if len(p)!=7{return nil,"",denied};values:=map[string]string{}
 for _,key:=range []string{"type","server","id","public_key","server_name","short_id"}{var v string;if json.Unmarshal(p[key],&v)!=nil{return nil,"",denied};values[key]=v}
 var port int;if json.Unmarshal(p["port"],&port)!=nil||port<1||port>65535||values["type"]!="vless-reality-v1"{return nil,"",denied}
 ip,e:=netip.ParseAddr(values["server"]);if e!=nil||!ip.Is4()||ip.String()!=values["server"]||ip.IsLoopback()||ip.As4()[0]==0||ip.As4()[0]>=224{return nil,"",denied}
 if !regexp.MustCompile(`^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$`).MatchString(values["id"])||values["id"]=="00000000-0000-0000-0000-000000000000"{return nil,"",denied}
 key,e:=base64.RawURLEncoding.DecodeString(values["public_key"]);if e!=nil||len(key)!=32||bytes.Equal(key,make([]byte,32))||base64.RawURLEncoding.EncodeToString(key)!=values["public_key"]{return nil,"",denied}
 if len(values["server_name"])>253||!regexp.MustCompile(`^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$`).MatchString(values["server_name"])||!regexp.MustCompile(`^(?:[0-9a-f]{2}){1,8}$`).MatchString(values["short_id"]){return nil,"",denied}
 config:=map[string]any{"log":map[string]any{"loglevel":"none"},"inbounds":[]any{map[string]any{"tag":"tun","protocol":"tun","settings":map[string]any{"name":"fctcp","MTU":1280}}},"outbounds":[]any{map[string]any{"tag":"vpn","protocol":"vless","settings":map[string]any{"vnext":[]any{map[string]any{"address":values["server"],"port":port,"users":[]any{map[string]any{"id":values["id"],"encryption":"none","flow":"xtls-rprx-vision"}}}}},"streamSettings":map[string]any{"network":"raw","security":"reality","realitySettings":map[string]any{"fingerprint":"chrome","serverName":values["server_name"],"password":values["public_key"],"shortId":values["short_id"]}}}}}
 b,e:=json.Marshal(config);return b,net.JoinHostPort(values["server"],strconv.Itoa(port)),e
}
func(s *tcpSession)close()error{
 s.mu.Lock();s.closing=true;s.cancel();list:=make([]*tcpConn,0,len(s.conns));for c:=range s.conns{list=append(list,c)};s.mu.Unlock()
 for _,c:=range list{c.Close()};s.dials.Wait()
 var err error
 if s.instance!=nil{tcpInstances.Delete(s.instance);err=s.instance.Close()}
 if s.fd>=0{unix.Close(s.fd);s.fd=-1}
 if s.owner!=0{C.fcRelease(s.owner);s.owner=0}
 return err
}
//export fcTcpStart
func fcTcpStart(tunFd int32,raw string,owner C.uintptr_t)int64{
 tcpMu.Lock();defer tcpMu.Unlock();handlesMu.Lock();defer handlesMu.Unlock()
 if tcpCurrent!=nil||len(tunnelHandles)>0{C.fcRelease(owner);return -1}
 config,endpoint,err:=tcpConfig(raw);if err!=nil||tunFd<3{C.fcRelease(owner);return -2}
 fd,err:=unix.Dup(int(tunFd));if err!=nil{C.fcRelease(owner);return -3};unix.CloseOnExec(fd)
 ctx,cancel:=context.WithCancel(context.Background());tcpSequence++;s:=&tcpSession{id:tcpSequence,owner:owner,fd:fd,endpoint:endpoint,ctx:ctx,cancel:cancel,conns:map[*tcpConn]bool{}}
 success:=false;tcpRunning.Store(true);defer func(){if !success{s.close();tcpRunning.Store(false)}}()
 if os.Setenv("xray.tun.fd",strconv.Itoa(fd))!=nil{return -4};defer os.Unsetenv("xray.tun.fd")
 pb,err:=serial.LoadJSONConfig(bytes.NewReader(config));if err!=nil{return -5}
 s.instance,err=core.New(pb);if err!=nil{return -6};tcpInstances.Store(s.instance,s)
 if s.instance.Start()!=nil{return -7};tcpCurrent=s;success=true;return s.id
}
//export fcTcpStop
func fcTcpStop(id int64)int32{
 tcpMu.Lock();defer tcpMu.Unlock();if tcpCurrent==nil{return 1};if tcpCurrent.id!=id{return 0}
 if tcpCurrent.close()!=nil{return 0};tcpCurrent=nil;tcpRunning.Store(false);return 1
}
//export fcTcpConnections
func fcTcpConnections(id int64)int32{
 tcpMu.Lock();defer tcpMu.Unlock();if tcpCurrent==nil{return 0};if id!=0&&id!=tcpCurrent.id{return -1}
 tcpCurrent.mu.Lock();defer tcpCurrent.mu.Unlock();return int32(len(tcpCurrent.conns))
}
