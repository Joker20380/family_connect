package labquic

import (
 "context"
 "crypto/tls"
 "crypto/x509"
 "encoding/json"
 "errors"
 "net"
 "sync"
 "time"

 "github.com/quic-go/quic-go"
 "github.com/quic-go/quic-go/logging"
)

const ALPN="family-connect-quic-lab-v1"
type Credentials struct { Certificate string; PrivateKey string; Authority string }
func TLS(raw []byte,server bool) (*tls.Config,error) {
 var credential Credentials
 if err:=json.Unmarshal(raw,&credential);err!=nil{return nil,err}
 certificate,err:=tls.X509KeyPair([]byte(credential.Certificate),[]byte(credential.PrivateKey));if err!=nil{return nil,err}
 roots:=x509.NewCertPool();if !roots.AppendCertsFromPEM([]byte(credential.Authority)){return nil,errors.New("lab CA rejected")}
 config:=&tls.Config{MinVersion:tls.VersionTLS13,Certificates:[]tls.Certificate{certificate},RootCAs:roots,ClientCAs:roots,NextProtos:[]string{ALPN},ServerName:"quic-server.lab.invalid"}
 if server {config.ClientAuth=tls.RequireAndVerifyClientCert;config.ServerName="";config.VerifyConnection=func(state tls.ConnectionState) error {if len(state.VerifiedChains)==0{return errors.New("unverified lab client")};return state.PeerCertificates[0].VerifyHostname("quic-client.lab.invalid")}}
 return config,nil
}

type Metrics struct {
 SentPackets,SentPacketBytes,ReceivedPackets,LostPackets,AckedPackets,DroppedPackets uint64
 StreamBytesSent,StreamBytesRepeated,StreamBlocked,ConnectionBlocked uint64
 PTOUpdates,PTOMax uint64
 CWND,PeakCWND,BytesInFlight,PeakInFlight uint64
 SmoothedRTTNS,RTTVariationNS,LatestRTTNS uint64
 Closed string
 StreamAccountingIncomplete bool
}
type Observer struct {mutex sync.Mutex;metrics Metrics;high map[uint64]uint64}
func NewObserver() *Observer {return &Observer{high:map[uint64]uint64{}}}
func (observer *Observer) Snapshot() Metrics {observer.mutex.Lock();defer observer.mutex.Unlock();return observer.metrics}
func (observer *Observer) sent(size logging.ByteCount,frames []logging.Frame) {
 observer.mutex.Lock();defer observer.mutex.Unlock();observer.metrics.SentPackets++;observer.metrics.SentPacketBytes+=uint64(size)
 for _,frame:=range frames{switch item:=frame.(type){
 case *logging.StreamFrame:
  start,end,key:=uint64(item.Offset),uint64(item.Offset+item.Length),uint64(item.StreamID)
  high,exists:=observer.high[key];if !exists && len(observer.high)>=64{observer.metrics.StreamAccountingIncomplete=true;continue}
  if start>high {observer.metrics.StreamAccountingIncomplete=true}
  observer.metrics.StreamBytesSent+=end-start
  if start<high {observer.metrics.StreamBytesRepeated+=min(end,high)-start}
  observer.high[key]=max(high,end)
 case *logging.StreamDataBlockedFrame:observer.metrics.StreamBlocked++
 case *logging.DataBlockedFrame:observer.metrics.ConnectionBlocked++
 }}
}
func (observer *Observer) Tracer(context.Context,logging.Perspective,quic.ConnectionID) *logging.ConnectionTracer {
 return &logging.ConnectionTracer{
 SentLongHeaderPacket:func(_ *logging.ExtendedHeader,size logging.ByteCount,_ logging.ECN,_ *logging.AckFrame,frames []logging.Frame){observer.sent(size,frames)},
 SentShortHeaderPacket:func(_ *logging.ShortHeader,size logging.ByteCount,_ logging.ECN,_ *logging.AckFrame,frames []logging.Frame){observer.sent(size,frames)},
 ReceivedLongHeaderPacket:func(_ *logging.ExtendedHeader,_ logging.ByteCount,_ logging.ECN,_ []logging.Frame){observer.mutex.Lock();observer.metrics.ReceivedPackets++;observer.mutex.Unlock()},
 ReceivedShortHeaderPacket:func(_ *logging.ShortHeader,_ logging.ByteCount,_ logging.ECN,_ []logging.Frame){observer.mutex.Lock();observer.metrics.ReceivedPackets++;observer.mutex.Unlock()},
 LostPacket:func(logging.EncryptionLevel,logging.PacketNumber,logging.PacketLossReason){observer.mutex.Lock();observer.metrics.LostPackets++;observer.mutex.Unlock()},
 AcknowledgedPacket:func(logging.EncryptionLevel,logging.PacketNumber){observer.mutex.Lock();observer.metrics.AckedPackets++;observer.mutex.Unlock()},
 DroppedPacket:func(logging.PacketType,logging.PacketNumber,logging.ByteCount,logging.PacketDropReason){observer.mutex.Lock();observer.metrics.DroppedPackets++;observer.mutex.Unlock()},
 UpdatedPTOCount:func(value uint32){observer.mutex.Lock();observer.metrics.PTOUpdates++;observer.metrics.PTOMax=max(observer.metrics.PTOMax,uint64(value));observer.mutex.Unlock()},
 UpdatedMetrics:func(rtt *logging.RTTStats,cwnd,inflight logging.ByteCount,_ int){observer.mutex.Lock();defer observer.mutex.Unlock();observer.metrics.CWND=uint64(cwnd);observer.metrics.PeakCWND=max(observer.metrics.PeakCWND,uint64(cwnd));observer.metrics.BytesInFlight=uint64(inflight);observer.metrics.PeakInFlight=max(observer.metrics.PeakInFlight,uint64(inflight));observer.metrics.SmoothedRTTNS=uint64(rtt.SmoothedRTT());observer.metrics.RTTVariationNS=uint64(rtt.MeanDeviation());observer.metrics.LatestRTTNS=uint64(rtt.LatestRTT())},
 ClosedConnection:func(err error){observer.mutex.Lock();if err!=nil{observer.metrics.Closed=err.Error()};observer.mutex.Unlock()},
 }
}
func Config(observer *Observer) *quic.Config {
 return &quic.Config{Versions:[]quic.Version{quic.Version1},HandshakeIdleTimeout:15*time.Second,MaxIdleTimeout:25*time.Second,InitialStreamReceiveWindow:128<<10,MaxStreamReceiveWindow:128<<10,InitialConnectionReceiveWindow:512<<10,MaxConnectionReceiveWindow:512<<10,MaxIncomingStreams:24,MaxIncomingUniStreams:-1,InitialPacketSize:DatagramSize,DisablePathMTUDiscovery:true,Allow0RTT:false,EnableDatagrams:false,Tracer:observer.Tracer}
}
func Open(ctx context.Context,packet *PacketConn,credentials []byte,server bool,observer *Observer) (*quic.Conn,func(),error) {
 config,err:=TLS(credentials,server);if err!=nil{return nil,nil,err}
 transport:=&quic.Transport{Conn:packet,ConnectionIDLength:8}
 cleanup:=func(){transport.Close();packet.Close()}
 if server {listener,err:=transport.Listen(config,Config(observer));if err!=nil{cleanup();return nil,nil,err};connection,err:=listener.Accept(ctx);if err!=nil{listener.Close();cleanup();return nil,nil,err};return connection,func(){listener.Close();cleanup()},nil}
 connection,err:=transport.Dial(ctx,packet.Peer(),config,Config(observer));if err!=nil{cleanup();return nil,nil,err};return connection,cleanup,nil
}

type StreamConn struct { *quic.Stream; Local,Remote net.Addr }
func (stream *StreamConn) LocalAddr() net.Addr{return stream.Local}
func (stream *StreamConn) RemoteAddr() net.Addr{return stream.Remote}
