"""Build and test only the bounded counter overlay, preserving b9 bootstrap."""

import json
import os
import subprocess
import sys

from prepare import WORK, BASE, TOOLS, FIXTURE, digest, environment


def main():
    os.umask(0o077)
    source=WORK/'observation-source/carrier'
    for name in ('main.go','seed_recovery.go','seed_recovery_test.go'):
        assert digest(source/'cmd/bootstrap-broker'/name)==digest(BASE/'gateway-source/carrier/cmd/bootstrap-broker'/name)
    if sys.argv[1] in ('test','delta'):
        import shutil
        shutil.copyfile(FIXTURE/'credit_counters_test.go',source/'tcpforward/credit_counters_test.go')
        shutil.copyfile(FIXTURE/'compact_export_test.go',source/'roombroker/compact_export_test.go')
        index=len(list(WORK.glob('checks-*.jsonl')))+1
        env=environment(); env['FC_EXPECT_SEED_OBSERVABILITY']='1'
        with (WORK/f'checks-{index}.jsonl').open('xb') as output:
            packages=['./tcpforward','./reliablestream','./familysession','./sessiontrace','./sessiondiag','./telemost','./roombroker','./cmd/bootstrap-broker']
            if sys.argv[1]=='delta':packages=['-run','^TestCredit|^TestPerformance','./tcpforward','./roombroker']
            result=subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-tags=fc_perf_diagnostic','-json','-count=1','-timeout=180s',*packages],
                                  cwd=source,env=env,stdout=output,stderr=subprocess.STDOUT,timeout=600)
        print('CHECK_EXIT',result.returncode);raise SystemExit(result.returncode)
    assert sys.argv[1]=='build'
    binary=WORK/'gateway-observation';assert not binary.exists()
    with (WORK/'build.log').open('xb') as output:
        subprocess.run([TOOLS/'go/bin/go','build','-p=1','-trimpath','-buildvcs=false','-tags=fc_perf_diagnostic','-o',binary,'./cmd/bootstrap-broker'],
                       cwd=source,env=environment(),stdout=output,stderr=subprocess.STDOUT,check=True,timeout=300)
    files={str(path.relative_to(source)):digest(path) for path in source.rglob('*') if path.is_file()}
    (WORK/'observation-build.json').write_text(json.dumps(dict(sha256=digest(binary),files=files,bootstrap1011_preserved=True,full_packet_export=False),indent=2))
    print('COUNTER_BINARY',digest(binary))


if __name__=='__main__':main()
