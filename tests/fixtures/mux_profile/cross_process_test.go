package tcpforward

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"os"
	"path/filepath"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

type profilePacketConnection struct {
	net.Conn
	send sync.Mutex
}

func (endpoint *profilePacketConnection) SendContext(ctx context.Context, payload []byte) error {
	endpoint.send.Lock();defer endpoint.send.Unlock()
	encoded:=make([]byte,4+len(payload));binary.BigEndian.PutUint32(encoded,uint32(len(payload)));copy(encoded[4:],payload)
	_,err:=endpoint.Write(encoded);return err
}

func (endpoint *profilePacketConnection) Recv(ctx context.Context) ([]byte,error) {
	var header [4]byte
	if _,err:=io.ReadFull(endpoint,header[:]);err!=nil {return nil,err}
	size:=binary.BigEndian.Uint32(header[:]);if size==0||size>65536 {return nil,fmt.Errorf("invalid packet")}
	payload:=make([]byte,size);_,err:=io.ReadFull(endpoint,payload);return payload,err
}

func TestProfileCrossProcess(test *testing.T) {
	directory:=os.Getenv("MUX_PROFILE_FIXTURE");if directory=="" {test.Skip("explicit old/new fixture only")}
	role:=os.Getenv("MUX_PROFILE_ROLE")
	if role=="credentials" {
		client,server:=testCredentials(test)
		if err:=os.WriteFile(filepath.Join(directory,"client.json"),client,0600);err!=nil {test.Fatal(err)}
		if err:=os.WriteFile(filepath.Join(directory,"server.json"),server,0600);err!=nil {test.Fatal(err)}
		return
	}
	ctx,cancel:=context.WithTimeout(context.Background(),20*time.Second);defer cancel()
	server:=role=="server";var connection net.Conn;var err error;var port int
	if server {
		port=muxFixture(test,muxEcho)
		listener,failure:=net.Listen("tcp4","127.0.0.1:0");if failure!=nil {test.Fatal(failure)};defer listener.Close()
		info,_:=json.Marshal(map[string]any{"address":listener.Addr().String(),"port":port});if err:=os.WriteFile(filepath.Join(directory,"ready.json"),info,0600);err!=nil {test.Fatal(err)}
		context.AfterFunc(ctx,func(){listener.Close()});connection,err=listener.Accept()
	} else {
		infoRaw,failure:=os.ReadFile(filepath.Join(directory,"ready.json"));if failure!=nil {test.Fatal(failure)}
		var info struct{Address string;Port int};if json.Unmarshal(infoRaw,&info)!=nil {test.Fatal("bad fixture address")};port=info.Port
		connection,err=net.DialTimeout("tcp4",info.Address,3*time.Second)
	}
	if err!=nil {test.Fatal(err)};defer connection.Close();connection.SetDeadline(time.Now().Add(18*time.Second))
	raw,err:=os.ReadFile(filepath.Join(directory,role+".json"));if err!=nil {test.Fatal(err)}
	secured,err:=familysession.OpenMux(ctx,&profilePacketConnection{Conn:connection},raw,server,os.Getenv("MUX_PROFILE_ENABLE")=="1")
	if err!=nil {test.Fatal(err)};defer secured.Close()
	want:=os.Getenv("MUX_PROFILE_EXPECT");if secured.ConnectionState().NegotiatedProtocol!=want {test.Fatal("unexpected selected ALPN")}
	config:=MuxConfig{MaxStreams:4};if server {config.Policy=Policy{TestOnlyLoopbackPort:port}}
	mux,err:=NewMux(ctx,secured,server,config);if err!=nil {test.Fatal(err)}
	defer func(){mux.Close();if mux.Stats().RetainedBytes!=0 {test.Error("retained after close")}}()
	if server {mux.Wait()} else {
		streams:=make([]*MuxStream,4);for index:=range streams {streams[index]=muxOpen(test,ctx,mux,port)}
		completed:=make(chan error,4)
		for _,stream:=range streams {go func(){
			payload:=bytes.Repeat([]byte{81},384<<10);written:=make(chan error,1)
			go func(){_,err:=stream.Write(payload);if err==nil {err=stream.CloseWrite()};written<-err}()
			body:=make([]byte,len(payload));_,err:=io.ReadFull(stream,body)
			if failure:=<-written;err==nil {err=failure};if err==nil&&!bytes.Equal(body,payload) {err=fmt.Errorf("byte mismatch")}
			stream.Close();completed<-err
		}()}
		for range streams {if err:=<-completed;err!=nil {test.Fatal(err)}}
	}
	encoded,_:=json.Marshal(map[string]any{"role":role,"alpn":secured.ConnectionState().NegotiatedProtocol,"stats":mux.Stats(),"byte_exact":true})
	test.Log("PROFILE_RECEIPT "+string(encoded))
}
