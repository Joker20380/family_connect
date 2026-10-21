import runpy
import argparse
from lab import *
import lab

parser=argparse.ArgumentParser()
parser.add_argument('--revision',default='v2',choices=['v2'])
args=parser.parse_args()
target=WORK/('replay-'+args.revision)
assert not target.exists()
target.mkdir()
shutil.copytree(PARENT/'source',target/'source')
for name in ['run_phase.py','worker.py']:shutil.copy2(PARENT/name,target/name)
original_work=WORK
lab.WORK=target;lab.SOURCE=target/'source'
for name in ['go.mod','go.sum']:write(lab.SOURCE/name,(FIX/'module'/name).read_text())
for name in ['overlay.py','operator_prepare.py','finish_prepare.py']:runpy.run_path(str(FIX/name))
write(lab.SOURCE/'licenses/lab-quic-dependencies.txt',(SOURCE/'licenses/lab-quic-dependencies.txt').read_text())
subprocess.run([TOOLS/'go/bin/gofmt','-w',*[str(path) for path in lab.SOURCE.rglob('*.go')]],check=True)
expected=json.loads((original_work/'build.json').read_text())['source_inventory'];actual=inventory(lab.SOURCE)
differences=[name for name in set(expected)|set(actual) if expected.get(name)!=actual.get(name)]
save(original_work/('replay-'+args.revision+'.json'),dict(source_exact=not differences,differences=sorted(differences),files=len(expected),scope='source reconstruction only; no test data or live traffic'))
print('replay source exact',not differences,'differences',differences)
assert not differences
