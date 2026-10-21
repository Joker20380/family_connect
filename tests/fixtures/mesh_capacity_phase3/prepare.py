"""Phase 3, pinned phase 1–2 capsule; never edits or rebuilds its parent."""
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
FIX = Path(__file__).resolve().parent
BASE = ROOT / 'state-client-build/mesh-capacity-20261020'
WORK = ROOT / 'state-client-build/mesh-capacity-phase3-20261020'
SOURCE = WORK / 'source'
TOOLS = ROOT / 'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment():
    values = {key: value for key, value in os.environ.items() if not key.startswith(('GO', 'CGO', 'FC_', 'YANDEX_'))}
    values.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOMAXPROCS='2', GOPATH=str(TOOLS/'gopath'), GOCACHE=str(ROOT/'state-client-build/host-compare-20261020/go-cache'))
    return values


def patch_file(path, text):
    previous = path.read_text() if path.exists() else None
    if previous == text:
        return
    patch = '*** Begin Patch\n'
    if previous is None:
        patch += '*** Add File: '+str(path)+'\n'+''.join('+'+line+'\n' for line in text.splitlines())
    else:
        patch += '*** Update File: '+str(path)+'\n@@\n'+''.join('-'+line+'\n' for line in previous.splitlines())+''.join('+'+line+'\n' for line in text.splitlines())
    subprocess.run(['apply_patch'], input=patch+'*** End Patch\n', text=True, check=True, stdout=subprocess.DEVNULL)


def replace(name, old, new):
    path = SOURCE/name
    text = path.read_text()
    assert text.count(old) == 1, (name, old)
    patch_file(path, text.replace(old, new))


def prepare():
    original = json.loads((BASE/'build.json').read_text())
    assert digest(BASE/'telemost-capacity') == original['binary_sha256']
    assert all(digest(BASE/'source'/name) == value for name, value in original['source_inventory'].items())
    WORK.mkdir(mode=0o700)
    shutil.copytree(BASE/'source', SOURCE)
    for name in ['lab_media.go', 'lab_media_test.go']:
        patch_file(SOURCE/'telemost'/name, (FIX/name).read_text())
    replace('cmd/telemost-binary/main.go', 'flag.Parse()', '''flag.Parse()
if *capacityFile != "" { if err := capacityMediaConfigure(*capacityFile); err != nil { return err } }''')
    replace('cmd/telemost-binary/main.go', 'stopMetrics()\n\t\tvar usage', 'stopMetrics()\ntelemost.LabMediaFlush(emit)\n\t\tvar usage')
    replace('cmd/telemost-binary/capacity.go', 'type capacityConfig struct {', 'type capacityConfig struct {\nMediaPolicy string\nKeepalivePhaseMS int')
    patch_file(SOURCE/'cmd/telemost-binary/capacity_media.go', '''package main
import("encoding/json";"os";"github.com/Joker20380/family_connect/carrier/telemost")
func capacityMediaConfigure(path string) error { raw,err:=os.ReadFile(path);if err!=nil{return err};var config capacityConfig;if err=json.Unmarshal(raw,&config);err!=nil{return err};return telemost.ConfigureLabMedia(config.MediaPolicy, config.KeepalivePhaseMS) }
''')
    replace('telemost/signaling.go', 'keepalive := time.NewTicker(vp8KeepaliveInterval)\n\t\tdefer keepalive.Stop()', '''keepalive := time.NewTicker(vp8KeepaliveInterval)
shifted:=labMediaPhase()!=0
if shifted {keepalive.Reset(vp8KeepaliveInterval+labMediaPhase())}
defer keepalive.Stop()''')
    replace('telemost/signaling.go', 'case <-keepalive.C:\n\t\t\t\ts.writeVP8Sample(vp8Keepalive)', 'case <-keepalive.C:\nif shifted {keepalive.Reset(vp8KeepaliveInterval);shifted=false}\n\t\t\t\ts.writeVP8Sample(vp8Keepalive)')
    replace('telemost/signaling.go', 's.track.WriteSample(media.Sample{Data: data, Duration: vp8FrameDuration})', 's.labWriteSample(media.Sample{Data: data, Duration: vp8FrameDuration})')
    replace('telemost/session.go', 'type Session struct {', 'type Session struct {\nlabSampleTime time.Time')
    replace('telemost/signaling.go', 'observer.packet(&pkt.Header, pkt.Payload, "ok")', 'labMediaPacket("rx", &pkt.Header, pkt.Payload, "ok")\nobserver.packet(&pkt.Header, pkt.Payload, "ok")')
    replace('telemost/signaling.go', 'correlated.packet(&ordered.Header, ordered.Payload, "ok")', 'labMediaPacket("ordered", &ordered.Header, ordered.Payload, "ok")\ncorrelated.packet(&ordered.Header, ordered.Payload, "ok")')
    replace('telemost/signaling.go', 's.mediaStats.FramesReceived++', 's.mediaStats.FramesReceived++') if False else None
    replace('telemost/signaling.go', 'if frag, ok := decodeVP8Frame(frame); ok {', 'labMediaFrame("assembled", frame, ordered.Timestamp, ordered.SequenceNumber)\nif frag, ok := decodeVP8Frame(frame); ok {')
    replace('telemost/rtp.go', 'b.trace.Boundary(sessiontrace.Boundary{Direction: "rx"', 'labMediaPacket("drop_"+result, &packet.Header, packet.Payload, result)\nb.trace.Boundary(sessiontrace.Boundary{Direction: "rx"')
    replace('telemost/lab_wire.go', 'return writer.Write(header, payload, attributes)', '''count,err:=writer.Write(header, payload, attributes)
result:="ok";if err!=nil{result="write_error"};labMediaPacket("tx",header,payload,result)
return count,err''')
    replace('telemost/lab_wire.go', 'return writer.Write(packets, attributes)', 'count,err:=writer.Write(packets, attributes);labMediaRTCP("rtcp_tx",packets);return count,err')
    patch_file(SOURCE/'telemost/lab_rtcp.go', '''package telemost
import("github.com/pion/interceptor";"github.com/pion/rtcp")
func (*labWireInterceptor) BindRTCPReader(reader interceptor.RTCPReader) interceptor.RTCPReader { return interceptor.RTCPReaderFunc(func(buffer []byte, attributes interceptor.Attributes)(int,interceptor.Attributes,error){ count,attrs,err:=reader.Read(buffer,attributes);if err==nil {packets,parseErr:=rtcp.Unmarshal(buffer[:count]);if parseErr==nil{labMediaRTCP("rtcp_rx",packets)}};return count,attrs,err }) }
''')
    replace('tcpforward/mux.go', 'ProtocolErrors     uint64', 'ProtocolErrors     uint64\nLabProtocolReasons [6]uint64\nLabProtocolKind uint8\nLabProtocolID uint32')
    category = 0
    for name in ['tcpforward/mux.go', 'tcpforward/mux_dns.go']:
        path = SOURCE/name
        text = path.read_text()
        pieces = text.split('mux.stats.ProtocolErrors++')
        result = pieces[0]
        for part in pieces[1:]:
            result += 'mux.stats.ProtocolErrors++; mux.stats.LabProtocolReasons['+str(category)+']++; mux.stats.LabProtocolKind=uint8(frame.kind); mux.stats.LabProtocolID=frame.id'+part
            category += 1
        patch_file(path, result)
    assert category == 6
    replace('cmd/telemost-binary/capacity.go', 'raw, err := os.ReadFile(path)', 'ctx,cancelPhase:=context.WithCancel(ctx);defer cancelPhase()\nraw, err := os.ReadFile(path)')
    replace('cmd/telemost-binary/capacity.go', 'defer mux.Close()\n\t\tif server', '''muxContext,stopMux:=context.WithCancel(ctx)
var muxSamples sync.WaitGroup;muxSamples.Add(1)
_ = emit(map[string]any{"event":"mux_lab_start","mux":mux.Stats()})
go func(){defer muxSamples.Done();ticker:=time.NewTicker(100*time.Millisecond);defer ticker.Stop();for{select{case <-muxContext.Done():return;case <-ticker.C:stats:=mux.Stats();_ = emit(map[string]any{"event":"mux_lab_sample","mux":stats});if stats.ProtocolErrors!=0{cancelPhase();return}}}}()
defer func(){stopMux();muxSamples.Wait();mux.Close();_ = emit(map[string]any{"event":"mux_lab_final","mux":mux.Stats()})}()
if server''')
    original_runner = (ROOT/'tests/fixtures/mesh_capacity/run.py').read_text()
    original_runner = original_runner.replace("parser.add_argument('--reverse',action='store_true')", "parser.add_argument('--reverse',action='store_true')\n    parser.add_argument('--media',choices=['A','B'],default='A')\n    parser.add_argument('--phase-ms',type=int,default=0)")
    original_runner = original_runner.replace('Reverse=args.reverse)', 'Reverse=args.reverse,MediaPolicy=args.media,KeepalivePhaseMS=args.phase_ms)')
    original_runner = original_runner.replace('args=parser.parse_args()', "args=parser.parse_args()\n    assert not (WORK/'verification.json').exists(),'PHASE3_CLOSED_NO_FURTHER_LOAD'")
    original_runner = original_runner.replace('capacity-20261020-', 'capacity3-20261020-')
    original_runner = original_runner.replace("if args.mode=='P':check_product_protocol(rows(directory/'peer.jsonl'))", "if args.mode=='P':check_product_protocol(rows(directory/'peer.jsonl'))")
    original_runner = original_runner.replace("counters=[row[boundary]['ProtocolErrors']", "counters=[row[boundary]['ProtocolErrors']")
    original_runner = original_runner.replace("assert counters and not any(counters),'P_PROTOCOL_COUNTER_NONZERO_STOP'", "counters += [row['mux']['ProtocolErrors'] for row in events if row.get('event','').startswith('mux_lab_')]\n    assert counters and not any(counters),'P_PROTOCOL_COUNTER_NONZERO_STOP'\n    assert any(row.get('event')=='mux_lab_final' for row in events),'P_FINAL_READBACK_MISSING'")
    original_runner = original_runner.replace("current=production_state()", "if args.mode=='P':\n                local_events=rows(directory/'peer.jsonl')\n                assert not any(row.get('mux',{}).get('ProtocolErrors',0) for row in local_events),'P_CLIENT_PROTOCOL_ERROR'\n            current=production_state()")
    original_runner = original_runner.replace("cleanup=\"\"\"import json,os,shutil", "if args.mode=='P':\n                try:check_product_protocol(rows(directory/'server-peer.jsonl'))\n                except AssertionError as error:failure=failure or str(error)\n            cleanup=\"\"\"import json,os,shutil")
    patch_file(FIX/'run.py', original_runner)
    patch_file(FIX/'worker.py', (ROOT/'tests/fixtures/mesh_capacity/worker.py').read_text())
    patch_file(WORK/'matrix.json', json.dumps(dict(source_limit=128*1024**2, outgoing_limit=256*1024**2, plan=['C A0 / A+1000ms / B0 / B0 / A0, 20s at 1Mbit carrier input; stop overload escalation', 'R32 A B B A, 4MiB each, unchanged reliability', 'P32 A B B A only if C/R improvement, 8MiB download each', 'reserve remaining for affected repairs, no unbounded continuation'], production_before=dict(ActiveState='active', InvocationID='27e2c972a69f4527a454cbfd95e5bf50', MainPID='47501', binary='734b6ca6eb42be0367b703b657be87c624f3500ae408bbd771309ffaeb86128e', profile='abda003f81f75b9bb249c62972e7e2660e0910dfb00c2bdac91621f32ebd5805'), parent_unchanged=True), indent=2))


def build():
    changed = [path for path in SOURCE.rglob('*.go') if not (BASE/'source'/path.relative_to(SOURCE)).exists() or digest(path)!=digest(BASE/'source'/path.relative_to(SOURCE))]
    subprocess.run([TOOLS/'go/bin/gofmt','-w',*changed],check=True)
    attempt = len(list(WORK.glob('local-tests-*.log')))+1
    with (WORK/f'local-tests-{attempt}.log').open('x') as log:
        subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-tags=fc_perf_diagnostic','-v','-run','TestLabMedia|TestCapacity|TestAdapter|TestFraming|TestRTP|TestHead|TestQueue','-count=1','-timeout=150s','./telemost','./cmd/telemost-binary','./tcpforward'],cwd=SOURCE,env=environment(),stdout=log,stderr=subprocess.STDOUT,timeout=300,check=True)
    with (WORK/f'build-{attempt}.log').open('x') as log:
        subprocess.run([TOOLS/'go/bin/go','build','-p=1','-trimpath','-buildvcs=false','-tags=fc_perf_diagnostic','-o',WORK/'telemost-capacity','./cmd/telemost-binary'],cwd=SOURCE,env=environment(),stdout=log,stderr=subprocess.STDOUT,timeout=180,check=True)
    inventory = {str(path.relative_to(SOURCE)):digest(path) for path in SOURCE.rglob('*') if path.is_file()}
    delta = []
    for name,value in inventory.items():
        parent = BASE/'source'/name
        if not parent.exists() or digest(parent)!=value:
            delta.extend(difflib.unified_diff(parent.read_text().splitlines(True) if parent.exists() else [], (SOURCE/name).read_text().splitlines(True), fromfile='a/'+name,tofile='b/'+name))
    patch_file(WORK/'lab-only.patch',''.join(delta))
    patch_file(WORK/'build.json',json.dumps(dict(binary_sha256=digest(WORK/'telemost-capacity'),source_inventory=inventory,base_build_sha256=digest(BASE/'build.json'),lab_patch_sha256=digest(WORK/'lab-only.patch'), media_policies=dict(A='exact33ms per sample',B='monotonic elapsed before sample, zero duration actual sample; same Pion packetizer'),trace_limit=100000),indent=2))


if __name__=='__main__':
    os.umask(0o077)
    if '--build' in sys.argv:build()
    else:prepare()
