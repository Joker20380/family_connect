from lab import *


def main():
    write(SOURCE/'telemost/lab_fragment.go',(FIX/'fragment.go').read_text())
    replace(SOURCE/'telemost/performance.go','case "id", "localCandidateId"','case "srtpCipher", "dtlsCipher", "id", "localCandidateId"')
    replace(SOURCE/'cmd/telemost-binary/capacity.go','FragmentMode     string','FragmentMode     string\n OriginalCarrier bool')
    replace(SOURCE/'cmd/telemost-binary/capacity.go','interactionComplete(ctx, path, mux, data.(*familysession.Session), server, emit)','interactionComplete(ctx, path, mux, data.(*familysession.Session), session, server, emit)')
    completion=SOURCE/'cmd/telemost-binary/lab_interaction_completion.go'
    replace(completion,'"github.com/Joker20380/family_connect/carrier/tcpforward"','"github.com/Joker20380/family_connect/carrier/tcpforward"\n "github.com/Joker20380/family_connect/carrier/telemost"')
    replace(completion,'session *familysession.Session, server bool','session *familysession.Session, carrier *telemost.Session, server bool')
    replace(completion,'"event": "p_drained",','"event": "p_drained", "carrier_fragments":carrier.LabFragmentStats(), "carrier_queue":carrier.Stats().SendQueueDepth,')
    replace(SOURCE/'cmd/telemost-binary/capacity_media.go','return telemost.ConfigureLabMedia','if err:=telemost.ConfigureLabCeiling(config.OriginalCarrier);err!=nil{return err}\n return telemost.ConfigureLabMedia')
    operator=WORK/'run_phase.py'
    replace(operator,"parser.add_argument('--fragment'","parser.add_argument('--original-carrier',action='store_true')\n    parser.add_argument('--fragment'")
    replace(operator,'config=dict(FragmentMode=args.fragment,','config=dict(OriginalCarrier=args.original_carrier,FragmentMode=args.fragment,')
    text=operator.read_text().replace("assert args.phase.isalnum() and len(args.phase)<25", "assert args.phase in ['CL','CS','R0','RL','RS','RSF','PL1','PS1','PSF1','PSF2','PS2','PL2']\n    assert not args.original_carrier or args.phase=='R0'")
    write(operator,text)
    module_root=TOOLS/'gopath/pkg/mod/github.com/klauspost'
    notices=[]
    for module in ['reedsolomon@v1.12.4','cpuid/v2@v2.2.8']:
        path=module_root/module/'LICENSE'
        notices.append(module+'\n'+path.read_text())
    write(SOURCE/'licenses/lab-fec-dependencies.txt','\n\n'.join(notices))
    with (WORK/'module-verify.log').open('x') as log:
        subprocess.run([TOOLS/'go/bin/go','mod','tidy'],cwd=SOURCE,env=environment(),stdout=log,stderr=subprocess.STDOUT,check=True)
        subprocess.run([TOOLS/'go/bin/go','mod','verify'],cwd=SOURCE,env=environment(),stdout=log,stderr=subprocess.STDOUT,check=True)
    build()


def build():
    operator=WORK/'run_phase.py'
    changed=[path for path in SOURCE.rglob('*.go') if not (PARENT/'source'/path.relative_to(SOURCE)).exists() or digest(path)!=digest(PARENT/'source'/path.relative_to(SOURCE))]
    subprocess.run([TOOLS/'go/bin/gofmt','-w',*changed],check=True)
    with (WORK/'admission.log').open('x') as log:
        subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-tags=fc_perf_diagnostic','-v','-run','TestFragment|TestPackingDrainRejectsTerminal|TestPackingHarness|TestMux128|TestMuxALPNProfiles|TestBatchCarriedTerminal|TestLocalCompletion|TestACKReleases','-count=1','-timeout=150s','./telemost','./familysession','./tcpforward','./cmd/telemost-binary','./reliablestream'],cwd=SOURCE,env=environment(),stdout=log,stderr=subprocess.STDOUT,check=True)
    with (WORK/'build.log').open('x') as log:
        subprocess.run([TOOLS/'go/bin/go','build','-p=1','-trimpath','-buildvcs=false','-tags=fc_perf_diagnostic','-o',WORK/'telemost-capacity','./cmd/telemost-binary'],cwd=SOURCE,env=environment(),stdout=log,stderr=subprocess.STDOUT,check=True)
    write(WORK/'lab-only.patch',delta(PARENT/'source',SOURCE))
    save(WORK/'build.json',dict(binary_sha256=digest(WORK/'telemost-capacity'),source_inventory=inventory(SOURCE),patch_sha256=digest(WORK/'lab-only.patch'),operator_sha256=digest(operator),worker_sha256=digest(WORK/'worker.py'),parent_build_sha256=digest(PARENT/'build.json'),common='RS32/32 Mux128 packingOFF Q0 A/phase0 pause2ms duration33ms; common conservative wire ceiling1048576 B/s except explicit R0 bridge',fragment='FCF2 v1 64B header 1024B source; SF shortened systematic RS up to8+2, >1024B only',bounds=dict(pending=16,held=1310720,parts=80,ttl_s=10,recent=4096)))
    print('BUILT',digest(WORK/'telemost-capacity'))


if __name__=='__main__':
    if '--build-only' in sys.argv: build()
    else: main()
