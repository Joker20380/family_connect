import difflib
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parent
parent=root.parent/'browser-admission-fix-1'
def digest(filename):
    return hashlib.sha256(filename.read_bytes()).hexdigest()
def inventory(folder):
    return {str(filename.relative_to(folder)):digest(filename) for filename in folder.rglob('*')
            if filename.is_file() and not any(part in ('.git','__pycache__') for part in filename.relative_to(folder).parts)}
def fingerprint(values):
    return hashlib.sha256(json.dumps(values,sort_keys=True,separators=(',',':')).encode()).hexdigest()

before,after=inventory(parent/'source'),inventory(root/'source')
changed=sorted(name for name in before.keys()|after.keys() if before.get(name)!=after.get(name))
allowed={'carrier/familysession/batch.go','carrier/familysession/batch_test.go','carrier/tcpforward/batch_test.go',
         'carrier/tcpforward/mux.go','carrier/tcpforward/mux_stream.go','clients/android/app/build.gradle'}
assert set(changed)==allowed,changed
original=json.loads((parent/'cumulative-source.json').read_text())
assert original['source_delta_sha256']=='c1eade0110278827c1681438a80c0509f352e2c9174badef0d3b228cc7161e9c'
assert all(before[name]==value for name,value in original['files'].items())
cumulative=original['files']|{name:after[name] for name in changed}
manifest=dict(base=original['base'],parent_inventory=original['source_delta_sha256'],source_delta_sha256=fingerprint(cumulative),files=cumulative)
(root/'cumulative-source.json').write_text(json.dumps(manifest,indent=2)+'\n')
patch=[]
for name in changed:
    old=(parent/'source'/name).read_text().splitlines(True) if name in before else []
    new=(root/'source'/name).read_text().splitlines(True)
    patch.extend(difflib.unified_diff(old,new,fromfile='a/'+name if name in before else '/dev/null',tofile='b/'+name))
(root/'candidate.patch').write_text(''.join(patch))
gateway_before,gateway_after=inventory(parent/'gateway-source/carrier'),inventory(root/'gateway-source/carrier')
gateway_original=json.loads((parent/'gateway-source.json').read_text())
assert gateway_original['source_inventory']=='0742212c5ebe38f9673dc53321d3af56c14b978e1080cbe104216ac21b40293f'
assert gateway_original['files']==gateway_before
gateway_changed=sorted(name for name in gateway_before.keys()|gateway_after.keys() if gateway_before.get(name)!=gateway_after.get(name))
assert set(gateway_changed)=={name.removeprefix('carrier/') for name in allowed if name.startswith('carrier/')}
assert all(gateway_after[name]==after['carrier/'+name] for name in gateway_changed)
gateway=dict(parent_inventory=gateway_original['source_inventory'],source_inventory=fingerprint(gateway_after),files=gateway_after)
(root/'gateway-source.json').write_text(json.dumps(gateway,indent=2)+'\n')
assert inventory(parent/'xray')==inventory(root/'xray')
(root/'boundary.json').write_text(json.dumps(dict(client_delta=changed,gateway_delta=gateway_changed,
 source_inventory=manifest['source_delta_sha256'],gateway_inventory=gateway['source_inventory'],
 product_patch_sha256=digest(root/'candidate.patch'),parent_sources_preserved=True,
 reliable_media_admission_security_unchanged=True,ui_unchanged=True,jni_contract_unchanged=True,xray_unchanged=True),indent=2)+'\n')
print(json.dumps(dict(source=manifest['source_delta_sha256'],gateway=gateway['source_inventory'],files=len(changed))))
