"""Prove the frozen patch reproduces the candidate from exact compatible sources."""
import json
import re
import shutil
import subprocess
from prepare import ROOT, WORK, BASE, TOOLS, digest, environment

destination=WORK/'reapplied'
assert not destination.exists()
shutil.copytree(BASE/'gateway-source/carrier',destination)
patch=ROOT/'tests/fixtures/rtp_pacing/packet-pacing.patch'
subprocess.run(['git','apply','--check',str(patch)],cwd=destination,check=True)
sections=re.split(r'(?m)^--- ',patch.read_text())[1:]
operations=[]
for section in sections:
    lines=section.splitlines()
    old=lines[0];new=lines[1].removeprefix('+++ b/')
    assert not new.startswith('/') and '..' not in new
    if old=='/dev/null':
        operations.append('*** Add File: '+str(destination/new))
        operations.extend(line for line in lines[2:] if not line.startswith('@@'))
    else:
        operations.append('*** Update File: '+str(destination/new))
        operations.extend('@@' if line.startswith('@@') else line for line in lines[2:])
subprocess.run(['apply_patch'],input='*** Begin Patch\n'+'\n'.join(operations)+'\n*** End Patch\n',text=True,check=True,stdout=subprocess.DEVNULL)
expected=json.loads((WORK/'source-inventory.json').read_text())
actual={str(path.relative_to(destination)):digest(path) for path in destination.rglob('*') if path.is_file()}
assert actual==expected
with (WORK/'reapplied-race.log').open('x') as output:
    subprocess.run([str(TOOLS/'go/bin/go'),'test','-race','-count=5','-timeout','60s','-run','TestPacing(Exact|Replacement|RTCPWhile|BoundedClose|NACK|Cancel)','./packetpace'],cwd=destination,env=environment(),stdout=output,stderr=subprocess.STDOUT,check=True,timeout=120)
(WORK/'reapplied-result.json').write_text(json.dumps(dict(result='PASS_EXACT_TREE_AND_REPEAT_RACE',patch_sha256=digest(patch),files=len(actual),log_sha256=digest(WORK/'reapplied-race.log')),indent=2))
print('FROZEN_PATCH_REPRODUCED_AND_REPEAT_RACE_PASS')
