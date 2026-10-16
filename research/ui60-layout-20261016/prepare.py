import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import io

root=Path(__file__).resolve().parent
state=root.parent
review=state/'owner-cumulative-client-acceptance-1-resume/review-publication'
retained=state/'bootstrap-pre-hello-correlation-1/reconstructed-final'
build=state/'bootstrap-pre-hello-correlation-1/gradle-native-export-final'
inventory=json.loads((review/'research/bootstrap-pre-hello-20261016/results/cumulative-source.json').read_bytes())
expected='b36c4a21ee6cf04acb192a0e6d140fa565b3e5ae75f6fc8d028d029c3152781d'
assert inventory['source_delta_sha256']==expected
for name,checksum in inventory['files'].items():
    assert hashlib.sha256((retained/name).read_bytes()).hexdigest()==checksum,name
assert hashlib.sha256((build/'native/jniLibs/arm64-v8a/libfc_restricted.so').read_bytes()).hexdigest()=='be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2'
source=root/'source'
subprocess.run(['git','clone','--no-checkout','--shared',str(build/'source'),str(source)],check=True)
subprocess.run(['git','-C',str(source),'checkout','--detach',inventory['base']],check=True)
shutil.copytree(retained,source,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.git'))
reference=subprocess.check_output(['git','-C',str(review),'rev-parse','5c740f2d^{commit}'],text=True).strip()
paths=['clients/android/app/src/main','clients/android/app/build.gradle']
archive=subprocess.check_output(['git','-C',str(review),'archive',reference,*paths])
with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
    bundle.extractall(root/'beta60',filter='data')
(root/'inputs.json').write_text(json.dumps(dict(base=inventory['base'],client_inventory=expected,beta60_reference=reference,
    native_sha256='be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2',source=str(source)),indent=2)+'\n')
print('EXACT_RETAINED_SOURCE_AND_NATIVE_VERIFIED; ISOLATED_DERIVATIVE_READY; BETA60_REFERENCE',reference)
