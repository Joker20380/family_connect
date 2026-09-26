package main
import (
 "encoding/json"
 "strings"
 "testing"
 "bytes"
 "github.com/xtls/xray-core/infra/conf/serial"
)
const good=`{"type":"vless-xhttp-tls-v1","server":"192.0.2.1","port":443,"id":"00000000-0000-4000-8000-000000000001","server_name":"edge.example.com","path":"/fc_test_only_path_1234/","mode":"packet-up"}`
func TestXhttpProfile(t *testing.T){
 raw,endpoint,err:=tcpConfig(good);if err!=nil||endpoint!="192.0.2.1:443"{t.Fatal("profile rejected")}
 if _,err=serial.LoadJSONConfig(bytes.NewReader(raw));err!=nil{t.Fatal(err)}
 var c map[string]any;if json.Unmarshal(raw,&c)!=nil{t.Fatal("JSON")}
 outbound:=c["outbounds"].([]any)[0].(map[string]any)
 stream:=outbound["streamSettings"].(map[string]any)
 if stream["network"]!="xhttp"||stream["security"]!="tls"{t.Fatal("transport")}
 tls:=stream["tlsSettings"].(map[string]any);if tls["allowInsecure"]!=nil||tls["serverName"]!="edge.example.com"{t.Fatal("TLS")}
 user:=outbound["settings"].(map[string]any)["vnext"].([]any)[0].(map[string]any)["users"].([]any)[0].(map[string]any)
 if user["flow"]!=nil{t.Fatal("Vision flow must not be used with XHTTP")}
}
func TestXhttpRejectsUnsafeOptions(t *testing.T){
 for _,bad:=range []string{
  strings.Replace(good,"packet-up","auto",1),strings.Replace(good,"fc_test_only_path_1234","..",1),
  strings.Replace(good,"192.0.2.1","127.0.0.1",1),strings.Replace(good,`"port":443`,`"port":true`,1),
  strings.Replace(good,"{",`{"allowInsecure":true,`,1),strings.Replace(good,"{",`{"mode":"packet-up",`,1),
 }{if _,_,err:=tcpConfig(bad);err==nil{t.Fatal("unsafe profile accepted")}}
}
