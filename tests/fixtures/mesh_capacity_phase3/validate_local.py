"""Run only with physical transfers stopped; final observation-only regression."""
import json
import subprocess
from prepare import WORK, FIX, TOOLS, environment, patch_file, digest

target=WORK/'local-tls-source'
patch_file(target/'telemost/lab_extra_test.go',(FIX/'extra_test.go').read_text())
patch_file(target/'telemost/lab_off_test.go',(FIX/'off32_test.go').read_text())
attempt=len(list(WORK.glob('final-local-*.log')))+1
with (WORK/f'final-local-{attempt}.log').open('x') as log:
    subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-tags=fc_perf_diagnostic','-v','-run','TestLab|TestConcurrentCloseAndReady|TestCanonicalMatrixAndCancellation|TestReliableTLSFaultMatrix|TestMux','-count=1','-timeout=150s','./telemost','./familysession','./tcpforward'],cwd=target,env=environment(),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=330)
patch_file(WORK/'local-observation-inventory.json',json.dumps({str(path.relative_to(target)):digest(path) for path in target.rglob('*') if path.is_file()},indent=2))
