"""Seal the exact functional delta before adding reused bounded observability."""

import difflib
import json
import subprocess

from prepare import WORK, ROOT, FIXTURE, BASE, digest


def main():
    source=WORK/'carrier';baseline=BASE/'gateway-source/carrier'
    patch='';files={}
    for path in sorted(source.rglob('*.go')):
        name=str(path.relative_to(source));old=baseline/name
        if old.exists() and old.read_bytes()==path.read_bytes():continue
        files[name]=digest(path)
        patch+=''.join(difflib.unified_diff(old.read_text().splitlines(True) if old.exists() else [],path.read_text().splitlines(True),fromfile='a/'+name if old.exists() else '/dev/null',tofile='b/'+name))
    target=FIXTURE/'negotiated-profile.patch'
    subprocess.run(['apply_patch','*** Begin Patch\n*** Add File: '+str(target)+'\n'+''.join('+'+line+'\n' for line in patch.splitlines())+'*** End Patch\n'],check=True)
    subprocess.run(['patch','-p1','--fuzz=0','-i',target],cwd=WORK/'android-source/carrier',check=True)
    (WORK/'functional-source.json').write_text(json.dumps(dict(patch_sha256=digest(target),files=files),indent=2))
    print('FUNCTIONAL_DELTA_SEALED',digest(target))


if __name__=='__main__':main()
