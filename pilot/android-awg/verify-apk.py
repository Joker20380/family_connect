"""Verify the packaged native libraries against the build manifest."""
import hashlib,json,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[2]
apk=root/'clients/android/app/build/outputs/apk/debug/app-debug.apk'
with zipfile.ZipFile(apk) as z:
 manifest=json.loads(z.read('assets/awg-build.json'))
 assert manifest['transport_version']=='3.1'
 assert manifest['engine_revision']=='b5928efb6ca19f0153958460c3d141f04abc5c2e'
 assert manifest['engine_patch_sha256']==hashlib.sha256((root/'pilot/awg31/patches/0001-refresh-s4-after-tun-read.patch').read_bytes()).hexdigest()
 assert manifest['interface_patch_sha256']==hashlib.sha256((root/'pilot/android-awg/awg31-interface.patch').read_bytes()).hexdigest()
 assert set(manifest['abis'])=={'arm64-v8a','armeabi-v7a','x86','x86_64'}
 for abi,digest in manifest['abis'].items():
  assert hashlib.sha256(z.read('lib/'+abi+'/libfc-awg.so')).hexdigest()==digest
  assert 'lib/'+abi+'/libwg-go.so' not in z.namelist()
 for name in ('Android.txt','Engine.txt','Xray.txt','gVisor.txt'):assert z.read('assets/awg-licenses/'+name)
 assert not any('peer-fixture' in n or 'xray-peer' in n for n in z.namelist())
 for name in ('BouncyCastle.txt','Gson.txt'):assert z.read('assets/control-licenses/'+name)
 assert not any('control-v1/' in n or 'TEST-ONLY' in n for n in z.namelist())
 assert manifest['xray_revision']=='d2758a023cd7f4174a5a5fa4ff66e487d4342ba0'
result={'apk_sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'bytes':apk.stat().st_size,'build':manifest}
(root/'android-awg-apk.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
