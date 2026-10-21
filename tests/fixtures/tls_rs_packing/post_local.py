"""Post-network validation copy: never edits the frozen live binary/source."""
import json
import shutil
import subprocess
from prepare import SOURCE,WORK,FIX,TOOLS,environment,patch_file,digest

target=WORK/'post-local-source'
if not target.exists():shutil.copytree(SOURCE,target)
for path in (FIX/'validation').glob('*.go'):
    patch_file(target/'familysession'/('lab_'+path.name),path.read_text())
duplicate=target/'familysession/lab_drain_test.go'
if duplicate.exists():
    patch_file(duplicate,'package familysession\n')
attempt=len(list(WORK.glob('post-local-*.log')))+1
with (WORK/f'post-local-{attempt}.log').open('x') as output:
    subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-tags=fc_perf_diagnostic','-v','-run','TestPackingPreWriteRetryControl|TestPackingCalibration|TestPackingDrainRejectsTerminal|TestPackingMemoryAccounting','-count=1','-timeout=90s','./familysession'],cwd=target,env=environment(),stdout=output,stderr=subprocess.STDOUT,check=True,timeout=120)
patch_file(WORK/'post-local-inventory.json',json.dumps({str(path.relative_to(target)):digest(path) for path in target.rglob('*') if path.is_file()},indent=2))
