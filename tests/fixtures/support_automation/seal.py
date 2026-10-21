"""Seal delta and receipts; no phone or network operation."""
import difflib
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tests/fixtures/speed_candidate'))
from prepare import write,digest


def main():
    work=ROOT/'state-client-build/support-automation-20261021'
    parent=ROOT/'state-client-build/speed-candidate-20261021/android-source'
    source=work/'android-source'
    inventory=json.loads((work/'build/source-inventory.json').read_text())
    assert all(digest(source/name)==expected for name,expected in inventory.items())
    changes=[];patch=''
    for path in sorted(source.rglob('*')):
        name=path.relative_to(source)
        if not path.is_file() or any(part in ('build','.gradle','.git','__pycache__') for part in name.parts):continue
        before=parent/name
        if before.exists() and before.read_bytes()==path.read_bytes():continue
        changes.append(str(name))
        patch+=''.join(difflib.unified_diff(before.read_text().splitlines(True) if before.exists() else [],path.read_text().splitlines(True),fromfile='a/'+str(name),tofile='b/'+str(name)))
    write(Path(__file__).with_name('android97-to98.patch'),patch)
    signing=json.loads((work/'delivery/signing-receipt.json').read_text())
    report=dict(schema=1,source_basis='exact installed97, HTTP e986f98e',changed_android=changes,
                android_patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),
                build=json.loads((work/'build/receipt.json').read_text()),signing=signing,
                http=json.loads((work/'http/receipt.json').read_text()))
    for file in ('install-receipt.json','http-deploy.json','http-deploy-2.json'):
        if (work/file).exists():report[file]=json.loads((work/file).read_text())
    write(work/'manifest.json',json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(changed=len(changes),patch_sha256=report['android_patch_sha256'],apk_sha256=signing['signed']['sha256'])))


if __name__=='__main__':main()
