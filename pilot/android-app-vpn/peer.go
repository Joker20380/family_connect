package main

import (
    "crypto/tls"
    "encoding/binary"
    "encoding/json"
    "fmt"
    "io"
    "net"
    "net/http"
    "net/netip"
    "os"
    "time"

    "github.com/amnezia-vpn/amneziawg-go/v3/conn"
    "github.com/amnezia-vpn/amneziawg-go/v3/device"
    "github.com/amnezia-vpn/amneziawg-go/v3/tun/netstack"
)

func run() error {
    var input struct { Config string; Certificate string; Key string }
    decoder:=json.NewDecoder(io.LimitReader(os.Stdin,32768));decoder.DisallowUnknownFields()
    if err:=decoder.Decode(&input);err!=nil{return err}
    certificate,err:=tls.LoadX509KeyPair(input.Certificate,input.Key);if err!=nil{return err}
    addresses:=[]netip.Addr{netip.MustParseAddr("10.0.2.2"),netip.MustParseAddr("198.19.1.1"),netip.MustParseAddr("fd79:fc::1"),netip.MustParseAddr("1.1.1.1")}
    tunnel,stack,err:=netstack.CreateNetTUN(addresses,nil,1280);if err!=nil{return err}
    engine:=device.NewDevice(tunnel,conn.NewDefaultBind(),device.NewLogger(device.LogLevelSilent,""));defer engine.Close()
    if err=engine.IpcSet(input.Config);err!=nil{return err};if err=engine.Up();err!=nil{return err}
    for _,address:=range addresses[:3]{
        listener,err:=stack.ListenTCPAddrPort(netip.AddrPortFrom(address,51904));if err!=nil{return err}
        server:=&http.Server{ReadHeaderTimeout:5*time.Second,Handler:http.HandlerFunc(func(response http.ResponseWriter,request *http.Request){fmt.Fprintf(response,"VPN_AWG%s",request.URL.Path)})}
        go server.Serve(tls.NewListener(listener,&tls.Config{MinVersion:tls.VersionTLS12,Certificates:[]tls.Certificate{certificate}}))
    }
    dns,err:=stack.ListenUDP(&net.UDPAddr{IP:net.ParseIP("1.1.1.1"),Port:53});if err!=nil{return err}
    go func(){
        buffer:=make([]byte,4096)
        for{
            size,client,err:=dns.ReadFrom(buffer);if err!=nil{return}
            question:=append([]byte(nil),buffer[:size]...);if size<17{continue}
            end:=12;for end<len(question)&&question[end]!=0{end+=int(question[end])+1};end++
            if end+4>len(question){continue};kind:=binary.BigEndian.Uint16(question[end:end+2]);end+=4
            value:=[]byte{198,19,1,1};if kind==28{value=net.ParseIP("fd79:fc::1").To16()}else if kind!=1{continue}
            answer:=append([]byte(nil),question[:end]...);answer[2]=0x81;answer[3]=0x80;answer[6]=0;answer[7]=1
            answer=append(answer,0xc0,0x0c,byte(kind>>8),byte(kind),0,1,0,0,0,0,0,byte(len(value)));answer=append(answer,value...)
            dns.WriteTo(answer,client)
        }
    }()
    fmt.Println("ready");<-engine.Wait();return nil
}
func main(){if run()!=nil{fmt.Fprintln(os.Stderr,"APP_VPN_PEER_FAILED");os.Exit(1)}}
