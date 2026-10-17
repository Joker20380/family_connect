import hashlib
import json
from pathlib import Path
import shutil
import subprocess

root=Path(__file__).resolve().parent
generated=root/'source/clients/android/build/reports/problems/problems-report.html'
destination=root/'build/gradle-generated/problems-report.html'
if not destination.exists():
    assert generated.is_file()
    destination.parent.mkdir(exist_ok=True)
    generated.rename(destination)
else:
    assert not generated.exists()
digest=hashlib.sha256(destination.read_bytes()).hexdigest()
assert hashlib.sha256(destination.read_bytes()).hexdigest()==digest
parent_generated=root.parent/'browser-admission-fix-1/source/clients/android/build/reports/problems/problems-report.html'
assert parent_generated.is_file()
shutil.copyfile(parent_generated,generated)
sealed=subprocess.run(['python3',str(root/'seal.py')],capture_output=True,text=True)
receipt=dict(initial_postbuild_seal='REJECTED_GENERATED_GRADLE_REPORT',generated_sha256=digest,
    preserved_as='build/gradle-generated/problems-report.html',post_relocation_exit=sealed.returncode,
    expected_extra_path='clients/android/build/reports/problems/problems-report.html',
    inherited_nonproduct_report_restored=True,
    inherited_report_sha256=hashlib.sha256(parent_generated.read_bytes()).hexdigest(),
    output=sealed.stdout,source_inventory_unchanged=False)
if sealed.returncode==0:
    source=json.loads((root/'cumulative-source.json').read_text())
    build=json.loads((root/'build/receipt.json').read_text())
    receipt['source_inventory_unchanged']=source['source_delta_sha256']==build['source_inventory']
(root/'postbuild-seal.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert sealed.returncode==0 and receipt['source_inventory_unchanged'],sealed.stderr
print(json.dumps(receipt))
