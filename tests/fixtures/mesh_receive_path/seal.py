"""Seal deltas against exact accepted sources, then reproduce on fresh copies."""

import difflib
import json
import os
import shutil
import subprocess

from preserve import ROOT, WORK, PARENT, digest


def files(root):
    return {str(path.relative_to(root)):path for path in root.rglob('*')
            if path.is_file() and not any(part in ('.git','.gradle','__pycache__') for part in path.relative_to(root).parts)}


def seal(label, before, after, selected=None):
    left,right=files(before),files(after)
    changed=[name for name in sorted(set(left)|set(right)) if
             (selected is None or name in selected) and
             (digest(left[name]) if name in left else None)!=(digest(right[name]) if name in right else None)]
    patch=ROOT/'tests/fixtures/mesh_receive_path'/(label+'.patch')
    blocks=[]
    for name in changed:
        old=left[name].read_text() if name in left else ''
        new=right[name].read_text() if name in right else ''
        blocks.extend(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),
                                          fromfile='a/'+name if old else '/dev/null',tofile='b/'+name if new else '/dev/null'))
    patch.write_text(''.join(blocks))
    result=dict(patch_sha256=digest(patch),inputs={name:digest(left[name]) if name in left else None for name in changed},
                outputs={name:digest(right[name]) if name in right else None for name in changed})
    target=WORK/'sealed-reproduction'/label
    shutil.copytree(before,target,ignore=shutil.ignore_patterns('.git','.gradle','__pycache__'))
    for dry in (True,False):
        subprocess.run(['patch','-p1','--fuzz=0',*(['--dry-run'] if dry else []),'-i',str(patch)],cwd=target,check=True,stdout=subprocess.DEVNULL)
    assert all((digest(target/name) if (target/name).exists() else None)==expected for name,expected in result['outputs'].items())
    return result


def main():
    os.umask(0o077)
    result=dict(baseline_checkpoint='dddc3347db5b02896c123488f2e5e0292ff2b7a7',
                baseline_gateway='b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba',
                android=seal('android-observation',PARENT/'android-source',WORK/'android-source'),
                gateway=seal('gateway-observation',PARENT/'gateway-source/carrier',WORK/'gateway-source/carrier'),
                local_candidate=seal('discarded-frame-candidate',WORK/'gateway-source/carrier',WORK/'candidate-local/carrier',
                                     {'telemost/rtp.go','telemost/signaling.go','telemost/msg.go'}))
    result['observation_apk']=json.loads((WORK/'delivery/signing-receipt.json').read_text())['signed']
    result['observation_gateway_sha256']=digest(WORK/'gateway-observation')
    result['candidate_status']='LOCAL_TEST_ONLY_NOT_BUILT_OR_DEPLOYED'
    (ROOT/'tests/fixtures/mesh_receive_path/source-pins.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS_THREE_EXACT_SOURCE_OVERLAY_REPRODUCTIONS')


if __name__=='__main__':main()
