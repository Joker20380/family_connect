from lab import *

for name in ['packet.go','transport.go','framed.go','credentials.go','packet_test.go','quic_test.go']:
    write(SOURCE/'labquic'/name,(FIX/name).read_text())
write(SOURCE/'telemost/lab_quic_test.go',(FIX/'pion_test.go').read_text())
write(SOURCE/'cmd/telemost-binary/lab_quic.go',(FIX/'runtime.go').read_text())
write(SOURCE/'cmd/telemost-binary/lab_quic_test.go',(FIX/'application_test.go').read_text())
for name in ['start_gate.go','start_gate_test.go']:
    write(SOURCE/'cmd/telemost-binary'/('lab_'+name),(FIX/name).read_text())
capacity=SOURCE/'cmd/telemost-binary/capacity.go'
text=capacity.read_text()
if 'StartBarrier' not in text:
    text=text.replace('type capacityConfig struct {','type capacityConfig struct {\n StartBarrier bool')
    text=text.replace('labShort = config.Short','if config.StartBarrier {if err=labStartGate(ctx,path,emit);err!=nil{return err}}\n labShort = config.Short')
    write(capacity,text)
fragment=SOURCE/'telemost/lab_fragment.go'
text=fragment.read_text();start=text.index('func labMediaRate(');end=text.index('func LabRateStats()',start)
write(fragment,text[:start]+(FIX/'cadence.go').read_text().split('\n',1)[1]+'\n\n'+text[end:])
text=fragment.read_text()
if 'func labFramePauseNS()' not in text:
    write(fragment,text.replace('int64(vp8SendInterval)','labFramePauseNS()')+'\nfunc labFramePauseNS()int64{if labNormalized{return 0};return int64(vp8SendInterval)}\n')
wire=SOURCE/'telemost/lab_wire.go'
text=wire.read_text();start=text.index('func (*labWireInterceptor) BindRTCPWriter')
write(wire,text[:start]+text[start:].replace('labWireReserve(size)', 'labWireReserve(size+4)',1))
write(SOURCE/'cmd/lab-quic-issue/main.go','''package main
import("os";"path/filepath";"github.com/Joker20380/family_connect/carrier/labquic")
func main(){if len(os.Args)!=2{panic("output directory required")};credentials,err:=labquic.EphemeralCredentials();if err!=nil{panic(err)};for index,name:=range []string{"quic-client.json","quic-server.json"}{if err=os.WriteFile(filepath.Join(os.Args[1],name),credentials[index],0600);err!=nil{panic(err)};clear(credentials[index])}}
''')
subprocess.run([TOOLS/'go/bin/gofmt','-w',*[str(path) for path in SOURCE.rglob('*.go')]],check=True)
