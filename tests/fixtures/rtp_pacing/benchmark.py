"""Bounded local overhead comparison; not a network throughput claim."""
import subprocess
import sys
from prepare import WORK, TOOLS, environment

label=sys.argv[1] if len(sys.argv)>1 else 'initial'
assert label.isalnum()
with (WORK/('overhead-'+label+'.log')).open('x') as output:
    subprocess.run([str(TOOLS/'go/bin/go'),'test','-run','^$','-bench','BenchmarkPacingObservation','-benchtime=500ms','-count=3','./packetpace'],
        cwd=WORK/'candidate',env=environment(),stdout=output,stderr=subprocess.STDOUT,check=True,timeout=120)
print('OVERHEAD_CAPTURED')
