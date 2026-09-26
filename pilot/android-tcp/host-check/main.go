// Host-only acceptance driver. Uses the real Android bridge Go file with a fake
// VpnService.protect callback; tests cannot prove Android socket protection/TUN.
package main
import (
 "bytes"
 "context"
 "encoding/json"
 "fmt"
 "net"
 "os"
 "os/signal"
 "strconv"
 "sync"
 "syscall"
 "github.com/xtls/xray-core/core"
 "github.com/xtls/xray-core/infra/conf/serial"
 _ "github.com/xtls/xray-core/proxy/socks"
)
var handlesMu sync.RWMutex
var tunnelHandles=map[int]bool{}
func main(){
 // Intentionally support only the loopback lab client's config, not a general runtime.
 args:=os.Args[1:];if len(args)<3||args[0]!="run"{os.Exit(2)}
 test:=args[1]=="-test";path:=args[len(args)-1]
 raw,err:=os.ReadFile(path);if err!=nil{os.Exit(2)}
 var value struct {Outbounds []struct{Settings struct{Vnext []struct{Address string;Port int}}}}
 if json.Unmarshal(raw,&value)!=nil||len(value.Outbounds)!=1||len(value.Outbounds[0].Settings.Vnext)!=1{os.Exit(2)}
 target:=value.Outbounds[0].Settings.Vnext[0];if target.Address!="127.0.0.1"{os.Exit(2)}
 pb,err:=serial.LoadJSONConfig(bytes.NewReader(raw));if err!=nil{os.Exit(3)}
 if test{return}
 instance,err:=core.New(pb);if err!=nil{os.Exit(4)}
 ctx,cancel:=context.WithCancel(context.Background())
 session:=&tcpSession{instance:instance,fd:-1,endpoint:net.JoinHostPort(target.Address,strconv.Itoa(target.Port)),ctx:ctx,cancel:cancel,conns:map[*tcpConn]bool{}}
 tcpInstances.Store(instance,session)
 if instance.Start()!=nil{session.close();os.Exit(5)}
 stop:=make(chan os.Signal,1);signal.Notify(stop,syscall.SIGTERM,syscall.SIGINT);<-stop
 if session.close()!=nil{os.Exit(6)}
 fmt.Println("Android bridge host driver stopped")
}
