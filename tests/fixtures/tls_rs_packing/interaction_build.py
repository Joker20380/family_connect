"""Focused local admission and one frozen lab binary; never release signing."""
import json
import subprocess
from interaction_prepare import SOURCE, WORK, PARENT, TOOLS, environment, inventory, digest, save, write, delta


def main():
    assert not list(WORK.glob('*/reservation.json'))
    assert not (WORK/'build.json').exists()
    attempt=len(list(WORK.glob('build-check-*.log')))+1
    changed=[path for path in SOURCE.rglob('*.go') if not (PARENT/'source'/path.relative_to(SOURCE)).exists() or digest(path)!=digest(PARENT/'source'/path.relative_to(SOURCE))]
    subprocess.run([TOOLS/'go/bin/gofmt','-w',*changed],check=True)
    with (WORK/f'build-check-{attempt}.log').open('x') as output:
        subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-tags=fc_perf_diagnostic','-run','TestPackingDrain|TestPackingTail|TestPackingOldest|TestPackingACKLoss|TestPackingHarness|TestMux128|TestMuxProfile|TestBatchScheduler|TestBatchCarried|TestMuxTerminal|TestMuxMalformed|TestMuxClaim|TestMuxLease','-v','-count=1','-timeout=120s','./familysession','./tcpforward','./cmd/telemost-binary'],cwd=SOURCE,env=environment(),stdout=output,stderr=subprocess.STDOUT,check=True,timeout=150)
    with (WORK/f'build-{attempt}.log').open('x') as output:
        subprocess.run([TOOLS/'go/bin/go','build','-p=1','-trimpath','-buildvcs=false','-tags=fc_perf_diagnostic','-o',WORK/'telemost-capacity','./cmd/telemost-binary'],cwd=SOURCE,env=environment(),stdout=output,stderr=subprocess.STDOUT,check=True,timeout=180)
    write(WORK/'lab-only.patch',delta(PARENT/'source',SOURCE))
    save(WORK/'build.json',dict(binary_sha256=digest(WORK/'telemost-capacity'),source_inventory=inventory(SOURCE),parent_build_sha256=digest(PARENT/'build.json'),patch_sha256=digest(WORK/'lab-only.patch'),operator_sha256=digest(WORK/'run_phase.py'),worker_sha256=digest(WORK/'worker.py'),common='Q0 mediaA phase0 RS32/32, packing A/B2; negotiated LEGACY64/CREDIT128 only',completion='17 exact bodies + both-end drain/ciphertext/ACK barrier before finish.input; ProtocolErrors through closure'))
    print('BUILT',digest(WORK/'telemost-capacity'))


if __name__=='__main__':
    main()
