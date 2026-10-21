"""Generate hash-pinned overlays and verify fresh-copy application, never main."""

import difflib
import json
import os
from pathlib import Path
import shutil
import subprocess

from prepare import ROOT, WORK, digest


def seal(name,before,after):
    target=ROOT/'tests/fixtures/queue_retry'
    old={str(path.relative_to(before)):path for path in before.rglob('*') if path.is_file()}
    new={str(path.relative_to(after)):path for path in after.rglob('*') if path.is_file()}
    changes={};patch=[]
    for relative in sorted(old.keys()|new.keys()):
        left=old.get(relative);right=new.get(relative)
        if left and right and digest(left)==digest(right):continue
        changes[relative]=dict(input_sha256=digest(left) if left else None,output_sha256=digest(right) if right else None)
        patch.extend(difflib.unified_diff(left.read_text().splitlines(True) if left else [],right.read_text().splitlines(True) if right else [],
            fromfile='a/'+relative if left else '/dev/null',tofile='b/'+relative if right else '/dev/null'))
    path=target/(name+'.patch')
    with path.open('x') as handle:handle.write(''.join(patch))
    fresh=WORK/('reproduce-'+name)
    shutil.copytree(before,fresh)
    subprocess.run(['git','apply','--check',str(path)],cwd=fresh,check=True)
    subprocess.run(['git','apply',str(path)],cwd=fresh,check=True)
    actual={str(path.relative_to(fresh)):digest(path) for path in fresh.rglob('*') if path.is_file()}
    assert actual=={name:digest(path) for name,path in new.items()}
    return dict(patch_sha256=digest(path),changes=changes,fresh_application='PASS')


def main():
    os.umask(0o077)
    patches={}
    for name,before,after in [('observation','baseline-source','observation-source'),('completion','baseline-source','candidate-source'),('completion-observed','observation-source','candidate-observed-source')]:
        patches[name]=seal(name,WORK/before/'carrier',WORK/after/'carrier')
    result=dict(base_gateway_sha256='b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba',
                base_source_inventory='4722b7353ba93209657f66b45c47874915362f1fbe732845ec61745abdb673e6',patches=patches)
    with (ROOT/'tests/fixtures/queue_retry/source-pins.json').open('x') as handle:json.dump(result,handle,indent=2)
    print('THREE_FRESH_OVERLAYS_REPRODUCED')


if __name__=='__main__':main()
