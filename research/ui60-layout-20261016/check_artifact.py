import hashlib
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import zipfile

root=Path(__file__).resolve().parent
accepted=root.parent/'bootstrap-pre-hello-correlation-1/gradle-native-export-final'
out=root/'build'
apk='android/app/outputs/apk/researchProvisioning/app-researchProvisioning-unsigned.apk'
tools=root.parent/'field65-export16/diag-source-freeze-1/resume-tools'
def digest(data): return hashlib.sha256(data).hexdigest()
with zipfile.ZipFile(accepted/apk) as old,zipfile.ZipFile(out/apk) as new:
    before={name:digest(old.read(name)) for name in old.namelist() if name.startswith('lib/')}
    after={name:digest(new.read(name)) for name in new.namelist() if name.startswith('lib/')}
    assert before==after
    assert old.read('assets/restricted-build.json')==new.read('assets/restricted-build.json')
    assert all(b'UiFixtureInstrumentation' not in new.read(name) and b'FixtureHostActivity' not in new.read(name) for name in new.namelist() if name.endswith('.dex'))
environment=dict(os.environ);environment['PATH']=str(tools/'jdk/bin')+os.pathsep+environment['PATH']
unsigned=subprocess.run([str(tools/'android/build-tools/35.0.0/apksigner'),'verify',str(out/apk)],env=environment,capture_output=True,text=True)
assert unsigned.returncode==1 and 'DOES NOT VERIFY' in unsigned.stdout+unsigned.stderr
subprocess.run([str(tools/'android/build-tools/35.0.0/zipalign'),'-c','4',str(out/apk)],check=True)
command=[str(tools/'android/build-tools/35.0.0/aapt2'),'dump','badging']
old_badging=subprocess.check_output(command+[str(accepted/apk)],text=True)
new_badging=subprocess.check_output(command+[str(out/apk)],text=True)
selected=lambda text:[line for line in text.splitlines() if line.startswith(('sdkVersion:','targetSdkVersion:','uses-permission:','native-code:','uses-feature:','uses-implied-feature:'))]
assert selected(old_badging)==selected(new_badging)
tests=[]
for path in sorted((out/'android/app/test-results/testResearchProvisioningUnitTest').glob('TEST-*.xml')):
    suite=ET.parse(path).getroot();assert suite.attrib['failures']==suite.attrib['errors']=='0'
    tests.append({key:suite.attrib[key] for key in ['name','tests','failures','errors','skipped']})
assert sum(int(item['tests']) for item in tests)==15
receipt=dict(all_embedded_native_payloads_identical=True,native_entries=after,restricted_manifest_byte_identical=True,permissions_sdk_abi_features_unchanged=True,manifest_scope=selected(new_badging),tests=tests,unsigned_apk_sha256=digest((out/apk).read_bytes()),product_signing='NOT_PERFORMED',unsigned_verified=True,zip_alignment=True,renderer_absent_from_product=True)
(root/'artifact-check.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({key:value for key,value in receipt.items() if key not in ['native_entries','manifest_scope']}))
