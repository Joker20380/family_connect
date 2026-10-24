"""Freeze source-only deltas and private evidence hashes; no upload or release."""
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

from observe import ROOT,WORK
from scripts.owner_android_support import save


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def patch(parent,source,names,target):
    text='';changed=[]
    for name in sorted(names):
        path=source/name;before=parent/name
        if before.exists() and digest(before)==digest(path):continue
        assert path.suffix in ('.go','.java','.gradle','.h','.c','.cpp')
        previous=before.read_text().splitlines(True) if before.exists() else []
        text+=''.join(difflib.unified_diff(previous,path.read_text().splitlines(True),fromfile='a/'+str(name),tofile='b/'+str(name)))
        changed.append(str(name))
    assert not target.exists()
    subprocess.run(['apply_patch','*** Begin Patch\n*** Add File: '+str(target)+'\n'+''.join('+'+line+'\n' for line in text.splitlines())+'*** End Patch\n'],check=True)
    return dict(changed=changed,patch_sha256=digest(target))


def main():
    inventory=json.loads((WORK/'build/source-inventory.json').read_text())
    source=WORK/'android-source'
    assert all(digest(source/name)==expected for name,expected in inventory.items()),'Built source inventory changed'
    android=patch(ROOT/'state-client-build/support-cadence99-20261021/android-source',source,inventory,
                  Path(__file__).with_name('android99-to100.patch'))
    gateway_source=WORK/'gateway-source'
    gateway=patch(ROOT/'state-client-build/speed-candidate-20261021/gateway-source',gateway_source,
                  [path.relative_to(gateway_source) for path in gateway_source.rglob('*.go')],Path(__file__).with_name('gateway-ae527-to-f631.patch'))
    receipts={str(path.relative_to(WORK)):digest(path) for path in sorted(WORK.rglob('*')) if path.is_file() and path.suffix in ('.json','.jsonl','.log') and not any(part in ('android-source','gateway-source','go-cache','prepare-attempt1','prepare-attempt2','gateway-prepare-attempt1') for part in path.relative_to(WORK).parts)}
    save(WORK/'manifest.json',dict(schema=1,android=android,gateway=gateway,
         source_inventory_sha256=digest(WORK/'build/source-inventory.json'),receipts=receipts,
         raw_private_evidence_not_for_git=True,distribution=False,commit_or_push=False))
    print('SEALED_SOURCE_AND_PRIVATE_RECEIPTS',len(receipts))


if __name__=='__main__':main()
