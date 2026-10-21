"""Offline pinned tests/build with retained unique logs; no live operations."""
import json
import subprocess
import sys
from prepare import ROOT, WORK, TOOLS, environment

variant,label,*packages=sys.argv[1:]
assert variant in ('baseline','candidate') and label.replace('-','').isalnum()
source=WORK/variant
fixtures=WORK/'tests'
if not fixtures.exists(): fixtures.symlink_to(ROOT/'tests',target_is_directory=True)
env=environment()
env.update(FC_EXPECT_SEED_OBSERVABILITY='1',FC_QUEUE_COMPLETION_EXPECTED='1' if variant=='candidate' and not label.startswith('legacy') else '0')
if label.startswith('paced-'): env['FC_PACKET_PACER']='1'
log=WORK/(variant+'-'+label+'.log')
with log.open('x') as output:
    result=subprocess.run([str(TOOLS/'go/bin/go'),'test','-race','-tags=fc_perf_diagnostic','-json','-count=1','-timeout','120s',*packages],cwd=source,env=env,stdout=output,stderr=subprocess.STDOUT,timeout=600)
print(json.dumps(dict(exit=result.returncode,log=str(log))))
raise SystemExit(result.returncode)
