package main

import (
 "bytes"
 "context"
 "crypto/sha256"
 "encoding/binary"
 "encoding/hex"
 "encoding/json"
 "errors"
 "fmt"
 "hash"
 "io"
 "net"
 "os"
 "path/filepath"
 "sync"
 "time"

 "github.com/Joker20380/family_connect/carrier/labquic"
 "github.com/Joker20380/family_connect/carrier/tcpforward"
 "github.com/Joker20380/family_connect/carrier/telemost"
 "github.com/quic-go/quic-go"
)

var labShort bool
type receiptConn struct {net.Conn;hash hash.Hash;written int}
func (connection *receiptConn) Write(data []byte)(int,error){count,err:=connection.Conn.Write(data);connection.hash.Write(data[:count]);connection.written+=count;return count,err}
type hostStream struct {io.ReadWriteCloser;closeWrite func() error;stats func() any;confirm func([]byte)error}
func (stream *hostStream) CloseWrite() error{return stream.closeWrite()}
func (stream *hostStream) Stats() any{return stream.stats()}
func (stream *hostStream) Confirm(body []byte)error {if stream.confirm!=nil{return stream.confirm(body)};return nil}
func muxHostCompare(ctx context.Context,mux *tcpforward.Mux,port int,snapshot func()map[string]any,emit func(map[string]any)error)error {
 return labHostCompare(ctx,func(ctx context.Context)(*hostStream,error){stream,err:=mux.OpenTCP(ctx,tcpforward.OpenRequest{Host:"127.0.0.1",Port:port});if err!=nil{return nil,err};return &hostStream{ReadWriteCloser:stream,closeWrite:stream.CloseWrite,stats:func()any{return stream.Stats()}},nil},func()any{return mux.PerformanceSnapshot()},snapshot,emit)
}

type nativeStream struct { *quic.Stream; confirmed bool }
func (stream *nativeStream) Close() error {if !stream.confirmed{stream.CancelRead(7);stream.CancelWrite(7)};return nil}
func (stream *nativeStream) confirm(body []byte)error {
 digest:=sha256.Sum256(body);receipt:=binary.BigEndian.AppendUint32([]byte("QRCP"),uint32(len(body)));receipt=append(receipt,digest[:]...)
 if _,err:=io.Copy(stream.Stream,bytes.NewReader(receipt));err!=nil{return err};if err:=stream.Stream.Close();err!=nil{return err};stream.confirmed=true;return nil
}

func quicRun(ctx context.Context,carrier *telemost.Session,path,credentialsPath string,config capacityConfig,server bool,emit func(map[string]any)error)error {
 ctx,cancel:=context.WithTimeout(ctx,180*time.Second);defer cancel()
 packet:=labquic.NewPacketConn(carrier,server);observer:=labquic.NewObserver();credentials,err:=os.ReadFile(credentialsPath);if err!=nil{return err}
 setup:=time.Now();connection,cleanup,err:=labquic.Open(ctx,packet,credentials,server,observer);clear(credentials);if err!=nil{return err};defer cleanup();defer connection.CloseWithError(0,"lab complete")
 _=emit(map[string]any{"event":"quic_ready","server":server,"setup_seconds":time.Since(setup).Seconds(),"alpn":connection.ConnectionState().TLS.NegotiatedProtocol,"peer_verified":len(connection.ConnectionState().TLS.VerifiedChains)>0,"config":config,"quic_config":map[string]any{"version":"v0.54.1","datagram":1200,"stream_window":131072,"connection_window":524288,"max_streams":24,"cc":"quic-go default Reno (NewCubicSender useReno=true)","pmtud":false,"zero_rtt":false,"native_datagrams":false}})
 snapshot:=func()map[string]any{result:=carrier.PerformanceSnapshot();result["quic"]=observer.Snapshot();result["adapter"]=packet.Stats();result["lab_rate"]=telemost.LabRateStats();result["lab_fragments"]=carrier.LabFragmentStats();return result}
 sampleContext,stopSamples:=context.WithCancel(ctx);var workers sync.WaitGroup;workers.Add(1)
 go func(){defer workers.Done();ticker:=time.NewTicker(time.Second);defer ticker.Stop();for{select{case <-sampleContext.Done():return;case <-ticker.C:_=emit(map[string]any{"event":"capacity_sample","transport":snapshot()})}}}()
 defer func(){stopSamples();workers.Wait();_=emit(map[string]any{"event":"capacity_final","transport":snapshot()})}()
 _=emit(map[string]any{"event":"capacity_config","config":config,"server":server,"reliability_config":nil})
 var receiptsMutex sync.Mutex;receipts:=map[string]any{};var nativeWorkers sync.WaitGroup
 var mux *tcpforward.Mux
 if config.Mode=="QS" {
  var stream *quic.Stream
  if server{stream,err=connection.AcceptStream(ctx)}else{stream,err=connection.OpenStreamSync(ctx)}
  if err!=nil{return err};framed:=labquic.NewFramed(ctx,stream);defer framed.Close();mux=tcpforward.LabQUICMux(ctx,framed,server);defer mux.Close()
  if !server{err=muxHostCompare(ctx,mux,18764,snapshot,emit)}
 } else if server {
  acceptContext,stopAccept:=context.WithCancel(ctx);defer func(){stopAccept();nativeWorkers.Wait()}()
  nativeWorkers.Add(1);go func(){defer nativeWorkers.Done();payload:=hostPayload();for index:=0;index<24;index++ {
   stream,acceptErr:=connection.AcceptStream(acceptContext);if acceptErr!=nil{return};nativeWorkers.Add(1)
   go func(){defer nativeWorkers.Done();stop:=context.AfterFunc(acceptContext,func(){stream.CancelRead(8);stream.CancelWrite(8)});defer stop();wrapped:=&receiptConn{Conn:&labquic.StreamConn{Stream:stream,Local:packet.LocalAddr(),Remote:packet.Peer()},hash:sha256.New()};handleErr:=hostFixtureRequest(wrapped,payload)
    if handleErr==nil{handleErr=stream.Close()}
    var receipt [40]byte;if handleErr==nil{_,handleErr=io.ReadFull(stream,receipt[:])}
    var tail [1]byte;if handleErr==nil{_,tailErr:=stream.Read(tail[:]);if tailErr!=io.EOF{handleErr=errors.New("QUIC receipt FIN")}}
    if handleErr==nil && string(receipt[:4])!="QRCP"{handleErr=errors.New("QUIC receipt magic")}
    if handleErr==nil && (int(binary.BigEndian.Uint32(receipt[4:8]))!=wrapped.written || !bytes.Equal(receipt[8:],wrapped.hash.Sum(nil))){handleErr=errors.New("QUIC receipt mismatch")}
    row:=map[string]any{"id":int64(stream.StreamID()),"bytes":binary.BigEndian.Uint32(receipt[4:8]),"sha256":hex.EncodeToString(receipt[8:]),"passed":handleErr==nil,"error":fmt.Sprint(handleErr)}
    receiptsMutex.Lock();receipts[fmt.Sprint(stream.StreamID())]=row;receiptsMutex.Unlock();_=emit(map[string]any{"event":"quic_receiver_receipt","receipt":row})
    if handleErr!=nil{stream.CancelRead(8);stream.CancelWrite(8)}
   }()
  }}()
 } else {
  err=labHostCompare(ctx,func(request context.Context)(*hostStream,error){stream,openErr:=connection.OpenStreamSync(request);if openErr!=nil{return nil,openErr};deadline,_:=request.Deadline();stream.SetDeadline(deadline);native:=&nativeStream{Stream:stream};return &hostStream{ReadWriteCloser:native,closeWrite:func()error{return nil},stats:func()any{return map[string]any{"ID":int64(stream.StreamID())}},confirm:native.confirm},nil},func()any{return observer.Snapshot()},snapshot,emit)
 }
 if err!=nil{return err}
 if !server{_=emit(map[string]any{"event":"p_workload_done"})}
 wait:=func(name string)error {ticker:=time.NewTicker(25*time.Millisecond);defer ticker.Stop();for{if _,err:=os.Stat(filepath.Join(filepath.Dir(path),name));err==nil{return nil};select{case <-ctx.Done():return ctx.Err();case <-connection.Context().Done():cause:=context.Cause(connection.Context());var application *quic.ApplicationError;if name=="finish.input" && errors.As(cause,&application) && application.ErrorCode==0{return nil};return cause;case <-ticker.C:}}}
 if err=wait("drain.input");err!=nil{return err}
 if config.Mode=="QN" && server {deadline:=time.Now().Add(10*time.Second);for{receiptsMutex.Lock();count:=len(receipts);receiptsMutex.Unlock();if count==17{break};if time.Now().After(deadline){return errors.New("missing receiver receipts")};time.Sleep(20*time.Millisecond)}}
 if mux!=nil {deadline:=time.Now().Add(10*time.Second);for mux.Stats().ActiveStreams!=0 && time.Now().Before(deadline){time.Sleep(20*time.Millisecond)};if mux.Stats().ActiveStreams!=0 || mux.Stats().ProtocolErrors!=0{return errors.New("QS terminal or streams")}}
 receiptsMutex.Lock();copyReceipts:=make(map[string]any);for key,value:=range receipts{copyReceipts[key]=value};receiptsMutex.Unlock()
 proof:=map[string]any{"event":"p_drained","server":server,"error":"<nil>","quic":observer.Snapshot(),"adapter":packet.Stats(),"receipts":copyReceipts,"carrier_queue":carrier.Stats().SendQueueDepth};if mux!=nil{proof["mux"]=mux.Stats();proof["flow"]=mux.LabObservation()};_=emit(proof)
 if err=wait("finish.input");err!=nil{return err};_=emit(map[string]any{"event":"quic_finished","server":server,"transport":snapshot()});return nil
}

func quicConfig(path string)(capacityConfig,error){var config capacityConfig;raw,err:=os.ReadFile(path);if err==nil{err=json.Unmarshal(raw,&config)};return config,err}
