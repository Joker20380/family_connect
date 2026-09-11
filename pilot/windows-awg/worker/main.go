// Windows AWG child for the Family Connect broker. No public UAPI listener.
package main

import (
 "bytes"
 "encoding/json"
 "errors"
 "io"
 "net"
 "os"
 "regexp"

 "github.com/amnezia-vpn/amneziawg-go/conn"
 "github.com/amnezia-vpn/amneziawg-go/device"
 "github.com/amnezia-vpn/amneziawg-go/tun"
)

type request struct { Adapter string `json:"adapter"`; Uplink string `json:"uplink"`; Config string `json:"config"` }
type bound struct { conn.Bind; index uint32 }
func (b *bound) Open(port uint16) ([]conn.ReceiveFunc,uint16,error) {
 f,p,e:=b.Bind.Open(port);if e!=nil{return nil,0,e}
 v,ok:=b.Bind.(conn.BindSocketToInterface)
 if !ok {b.Bind.Close();return nil,0,errors.New("binding unsupported")}
 // Open binds sockets before device send/receive goroutines can use them.
 if e=v.BindSocketToInterface4(b.index,false);e==nil {e=v.BindSocketToInterface6(b.index,true)}
 if e!=nil {b.Bind.Close();return nil,0,e};return f,p,nil
}
func run() error {
 // EOF is the release gate: the broker assigns its kill-on-close job first.
 raw,e:=io.ReadAll(io.LimitReader(os.Stdin,16385));if e!=nil{return e}
 if len(raw)>16384{return errors.New("size")}
 var p request;d:=json.NewDecoder(bytes.NewReader(raw));d.DisallowUnknownFields()
 if e=d.Decode(&p);e!=nil{return e}
 var extra any;if d.Decode(&extra)!=io.EOF{return errors.New("trailing input")}
 if !regexp.MustCompile(`^fcawg[0-9a-f]{8}$`).MatchString(p.Adapter)||len(p.Config)==0||len(p.Config)>8192{return errors.New("config")}
 if _,e=net.InterfaceByName(p.Adapter);e==nil{return errors.New("adapter exists")}
 uplink,e:=net.InterfaceByName(p.Uplink);if e!=nil||uplink.Index<=0{return errors.New("uplink")}
 t,e:=tun.CreateTUN(p.Adapter,1280);if e!=nil{return e}
 dev:=device.NewDevice(t,&bound{conn.NewDefaultBind(),uint32(uplink.Index)},device.NewLogger(device.LogLevelSilent,""))
 defer dev.Close()
 if e=dev.IpcSet(p.Config);e!=nil{return e}
 if e=dev.Up();e!=nil{return e}
 os.Stdout.WriteString("ready\n")
 <-dev.Wait();return nil
}
func main(){if run()!=nil{os.Stderr.WriteString("AWG worker failed\n");os.Exit(1)}}
