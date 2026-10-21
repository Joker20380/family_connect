import runpy
from lab import *

assert not (WORK/'source-v1').exists()
shutil.copytree(SOURCE,WORK/'source-v1')
for old,new in [('build.json','build-v1.json'),('lab-only.patch','lab-only-v1.patch'),('telemost-capacity','telemost-capacity-v1'),('run_phase.py','run_phase.v2.py')]:
    shutil.copy2(WORK/old,WORK/new)
for name in ['operator_prepare.py','finish_prepare.py']:
    runpy.run_path(str(FIX/name))
with (WORK/'admission-v2.log').open('x') as log:
    subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-tags=fc_perf_diagnostic','-v','-run','TestLabStartGate|TestPacket|TestQUIC|TestPackingDrainRejectsTerminal|TestMux128|TestMuxALPNProfiles|TestBatchCarriedTerminal|TestLocalCompletion|TestACKReleases','-count=1','-timeout=150s','./labquic','./telemost','./familysession','./tcpforward','./cmd/telemost-binary','./reliablestream'],cwd=SOURCE,env=environment(),stdout=log,stderr=subprocess.STDOUT,check=True)
with (WORK/'build-v2.log').open('x') as log:
    subprocess.run([TOOLS/'go/bin/go','build','-p=1','-trimpath','-buildvcs=false','-tags=fc_perf_diagnostic','-o',WORK/'telemost-capacity','./cmd/telemost-binary'],cwd=SOURCE,env=environment(),stdout=log,stderr=subprocess.STDOUT,check=True)
write(WORK/'startup-gate-only.patch',delta(WORK/'source-v1',SOURCE))
write(WORK/'lab-only.patch',delta(PARENT/'source',SOURCE))
manifest=json.loads((WORK/'build-v1.json').read_text())
manifest.update(binary_sha256=digest(WORK/'telemost-capacity'),source_inventory=inventory(SOURCE),patch_sha256=digest(WORK/'lab-only.patch'),operator_sha256=digest(WORK/'run_phase.py'),worker_sha256=digest(WORK/'worker.py'),proof_sha256=digest(WORK/'proof.py'),revision='v2 common both-media-connected start gate; no transport parameter changes',v1_manifest_sha256=digest(WORK/'build-v1.json'),startup_delta_sha256=digest(WORK/'startup-gate-only.patch'))
write(WORK/'build.json',json.dumps(manifest,indent=2)+'\n')
save(WORK/'startup-gate-repair.json',dict(reason='A1R server RS startup expired before client media connected: client setup 21.153s versus existing 20s RS timeout',scope='all modes; max45s controller gate before protocol startup and180s phase timer; timers and transport parameters unchanged',parent_binary=json.loads((WORK/'build-v1.json').read_text())['binary_sha256'],binary=manifest['binary_sha256'],source_delta=manifest['startup_delta_sha256'],failed_attempts_retained=['A1','A1R']))
print('FROZEN_V2',manifest['binary_sha256'])
