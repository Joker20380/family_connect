from lab import *

notices=[]
module_root=TOOLS/'gopath/pkg/mod'
for name,license_name in [('github.com/quic-go/quic-go@v0.54.1','LICENSE'),('go.uber.org/mock@v0.5.0','LICENSE'),('golang.org/x/mod@v0.18.0','LICENSE'),('golang.org/x/sync@v0.8.0','LICENSE'),('golang.org/x/tools@v0.22.0','LICENSE')]:
    notices.append(name+'\n'+(module_root/name/license_name).read_text())
write(SOURCE/'licenses/lab-quic-dependencies.txt','\n\n'.join(notices))
subprocess.run([TOOLS/'go/bin/gofmt','-w',*[str(path) for path in SOURCE.rglob('*.go')]],check=True)
with (WORK/'admission.log').open('x') as log:
    subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-tags=fc_perf_diagnostic','-v','-run','TestPacket|TestQUIC|TestPackingDrainRejectsTerminal|TestMux128|TestMuxALPNProfiles|TestBatchCarriedTerminal|TestLocalCompletion|TestACKReleases','-count=1','-timeout=150s','./labquic','./telemost','./familysession','./tcpforward','./cmd/telemost-binary','./reliablestream'],cwd=SOURCE,env=environment(),stdout=log,stderr=subprocess.STDOUT,check=True)
with (WORK/'build.log').open('x') as log:
    for target,output in [('./cmd/telemost-binary','telemost-capacity'),('./cmd/lab-quic-issue','lab-quic-issue')]:
        subprocess.run([TOOLS/'go/bin/go','build','-p=1','-trimpath','-buildvcs=false','-tags=fc_perf_diagnostic','-o',WORK/output,target],cwd=SOURCE,env=environment(),stdout=log,stderr=subprocess.STDOUT,check=True)
write(WORK/'lab-only.patch',delta(PARENT/'source',SOURCE))
save(WORK/'build.json',dict(binary_sha256=digest(WORK/'telemost-capacity'),issuer_sha256=digest(WORK/'lab-quic-issue'),source_inventory=inventory(SOURCE),patch_sha256=digest(WORK/'lab-only.patch'),operator_sha256=digest(WORK/'run_phase.py'),worker_sha256=digest(WORK/'worker.py'),proof_sha256=digest(WORK/'proof.py'),parent_build_sha256=digest(PARENT/'build.json'),go=subprocess.check_output([TOOLS/'go/bin/go','version'],text=True).strip(),quic='v0.54.1 Go>=1.23 MIT; default Reno and pacing retained; no library patches',common='L, phase0, 33ms timestamps; original2ms/frame or normalized1048576 B/s max2ms burst credit no fixed frame sleep',baseline='RS32/32 Family TLS Mux128 packing OFF Q0',quic_limits=dict(packet=1200,stream=131072,connection=524288,incoming_streams=24,unidirectional=0,send_queue=8,adapter_writes=1,write_deadline_s=5,zero_rtt=False,pmtud=False)))
print('FROZEN',digest(WORK/'telemost-capacity'))
