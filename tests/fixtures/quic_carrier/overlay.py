from lab import *

for name in ['packet.go','transport.go','framed.go']:
    write(SOURCE/'labquic'/name,(FIX/name).read_text())
write(SOURCE/'cmd/telemost-binary/lab_quic.go',(FIX/'runtime.go').read_text())
write(SOURCE/'tcpforward/lab_quic.go','''package tcpforward
import("context";"github.com/Joker20380/family_connect/carrier/familysession")
func LabQUICMux(ctx context.Context,endpoint familysession.PacketEndpoint,server bool)*Mux{return newMuxWindow(ctx,endpoint,server,MuxConfig{Policy:Policy{TestOnlyLoopbackPort:18764}},131072)}
''')
capacity=SOURCE/'cmd/telemost-binary/capacity.go'
replace(capacity,'type capacityConfig struct {','type capacityConfig struct {\n Normalized bool\n Short bool')
replace(capacity,'config.Mode != "C" && config.Mode != "R" && config.Mode != "T" && config.Mode != "P" {','config.Mode != "C" && config.Mode != "R" && config.Mode != "T" && config.Mode != "P" && config.Mode != "QN" && config.Mode != "QS" {')
replace(capacity,'if config.Mode == "P" {\n\t\tvar stopTransfer','labShort=config.Short\n if config.Mode=="QN" || config.Mode=="QS" {return quicRun(ctx,session,path,credentialsPath,config,server,emit)}\n if config.Mode == "P" {\n\t\tvar stopTransfer')
host=SOURCE/'cmd/telemost-binary/host_compare.go'
replace(host,'func muxHostCompare(ctx context.Context, mux *tcpforward.Mux, port int, snapshot func() map[string]any, emit func(map[string]any) error) error {\n\tif port < 1 || port > 65535 {\n\t\treturn errors.New("fixture port invalid")\n\t}', 'func labHostCompare(ctx context.Context, open func(context.Context)(*hostStream,error), performance func()any, snapshot func()map[string]any,emit func(map[string]any)error)error {')
replace(host,'stream, err := mux.OpenTCP(requestContext, tcpforward.OpenRequest{Host: "127.0.0.1", Port: port})','stream, err := open(requestContext)')
write(host,host.read_text().replace('mux.PerformanceSnapshot()','performance()').replace('"github.com/Joker20380/family_connect/carrier/tcpforward"',''))
replace(host,'if err == nil {\n\t\t\terr = stream.Close()\n\t\t}', 'if err==nil && !bytes.Equal(received,expected){err=errors.New("byte mismatch")}\n if err==nil {err=stream.Confirm(received)}\n if err == nil {err = stream.Close()}')
replace(host,"singleErr := request(\"single\", 'D', 4<<20)","singleSize,parallelSize:=4<<20,2<<20;if labShort {singleSize=65536;parallelSize=65536}\n singleErr := request(\"single\", 'D', singleSize)")
replace(host,"request(\"parallel_\"+strconv.Itoa(index), 'D', 2<<20)","request(\"parallel_\"+strconv.Itoa(index), 'D', parallelSize)")
media=SOURCE/'cmd/telemost-binary/capacity_media.go'
replace(media,'return telemost.ConfigureLabMedia','telemost.ConfigureLabNormalized(config.Normalized)\n return telemost.ConfigureLabMedia')
fragment=SOURCE/'telemost/lab_fragment.go'
replace(fragment,'var labCeilingOriginal bool','var labCeilingOriginal bool\nvar labNormalized bool\nfunc ConfigureLabNormalized(normalized bool){labNormalized=normalized}')
replace(fragment,'MaxHeader int','MaxHeader int\n Frames uint64\n QueueNS uint64\n QueueMaxNS uint64')
replace(fragment,'"original_bridge": labCeilingOriginal,','"normalized":labNormalized,"frames":labRate.Frames,"queue_ns":labRate.QueueNS,"queue_max_ns":labRate.QueueMaxNS,"original_bridge": labCeilingOriginal,')
signaling=SOURCE/'telemost/signaling.go'
replace(signaling,'written := s.writeVP8Sample(frame.data, frame.point)','labRate.Lock();age:=uint64(time.Since(frame.queuedAt));labRate.Frames++;labRate.QueueNS+=age;labRate.QueueMaxNS=max(labRate.QueueMaxNS,age);labRate.Unlock()\n written := s.writeVP8Sample(frame.data, frame.point)')
replace(signaling,'time.Sleep(vp8SendInterval)','if !labNormalized {time.Sleep(vp8SendInterval)}')
wire=SOURCE/'telemost/lab_wire.go'
replace(wire,'labMediaRate(size+64, 0)','labMediaRate(size+68, 0)')
subprocess.run([TOOLS/'go/bin/gofmt','-w',*[str(path) for path in SOURCE.rglob('*.go')]],check=True)
