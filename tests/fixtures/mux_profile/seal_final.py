"""Preserve complete source deltas without exporting identities or build secrets."""

import collections
import difflib
import json
import subprocess
from prepare import ROOT, WORK, BASE, ANDROID, FIXTURE, digest

def patch(name, before, after, candidates):
    chunks=[];files={}
    for relative in sorted(candidates):
        old,new=before/relative,after/relative
        if not new.is_file():continue
        content=new.read_text()
        previous=old.read_text() if old.is_file() else ''
        if content==previous:continue
        chunks.extend(difflib.unified_diff(previous.splitlines(True),content.splitlines(True),fromfile='a/'+relative if old.is_file() else '/dev/null',tofile='b/'+relative))
        files[relative]=digest(new)
    destination=FIXTURE/name
    assert not destination.exists()
    text=''.join(chunks)
    request='*** Begin Patch\n*** Add File: '+str(destination)+'\n'+''.join('+'+line+'\n' for line in text.splitlines())+'*** End Patch\n'
    subprocess.run(['apply_patch',request],check=True,stdout=subprocess.DEVNULL)
    return dict(path=str(destination.relative_to(ROOT)),sha256=digest(destination),changed=files)

def names(directory):
    return [str(path.relative_to(directory)) for path in directory.rglob('*') if path.is_file() and (path.suffix=='.go' or path.name in ('go.mod','go.sum','build.gradle')) and '.git' not in path.parts]

result={}
result['functional']=patch('complete-functional.patch',BASE/'gateway-source/carrier',WORK/'carrier',names(WORK/'carrier'))
result['gateway']=patch('complete-gateway.patch',BASE/'gateway-source/carrier',WORK/'gateway-source/carrier',names(WORK/'gateway-source/carrier'))
inventory=json.loads((WORK/'build/source-inventory.json').read_text())
result['android']=patch('complete-android.patch',ANDROID/'android-source',WORK/'android-source',[name for name in inventory if name.endswith(('.go','.gradle')) or name.endswith(('/go.mod','/go.sum'))])
result['artifacts']={name:digest(WORK/name) for name in ('gateway-negotiated','negotiated-build.json','build/source-inventory.json','delivery/FamilyConnect-0.1.18-beta95-mux-profile.apk','delivery/signing-receipt.json')}
result['tests']={}
for path in WORK.glob('*.jsonl'):
    counts=collections.Counter()
    for line in path.read_text().splitlines():
        if not line.startswith('{'):continue
        row=json.loads(line)
        if row.get('Test') and row.get('Action') in ('pass','fail','skip'):counts[row['Action']]+=1
    if counts:result['tests'][path.name]=dict(counts)
result['compatibility']=json.loads((WORK/'compatibility/results-retry.json').read_text())
result['compatibility_binaries']={name:digest(WORK/'compatibility'/name) for name in ('old-client.test','old-server.test','new.test')}
with (WORK/'final-source-seals.json').open('x') as output:json.dump(result,output,indent=2)
print(json.dumps({key:value.get('sha256') for key,value in result.items() if isinstance(value,dict) and 'sha256' in value}))
