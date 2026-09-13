"""Select unchanged ARM64 payload from an accepted universal CI APK.

Output is unsigned and must be zipaligned, signed with the persistent beta key,
and independently verified before handoff. Input signature is checked externally.
"""
from pathlib import Path
import argparse,hashlib,json,zipfile
p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
assert not a.output.exists()
with zipfile.ZipFile(a.input) as src:
    manifest=json.loads(src.read('assets/awg-build.json'))
    assert set(manifest['abis'])=={'arm64-v8a','armeabi-v7a','x86','x86_64'}
    for abi,digest in manifest['abis'].items():assert hashlib.sha256(src.read('lib/'+abi+'/libfc-awg.so')).hexdigest()==digest
    manifest['abis']={'arm64-v8a':manifest['abis']['arm64-v8a']}
    manifest['packaging_source_apk_sha256']=hashlib.file_digest(a.input.open('rb'),'sha256').hexdigest()
    with zipfile.ZipFile(a.output,'x') as dst:
        for info in src.infolist():
            name=info.filename
            if name.startswith('lib/') and not name.startswith('lib/arm64-v8a/'):continue
            if name.startswith('META-INF/') and (name.upper().endswith(('.RSA','.DSA','.EC','.SF')) or name=='META-INF/MANIFEST.MF'):continue
            data=src.read(name)
            if name=='assets/awg-build.json':data=(json.dumps(manifest,indent=2)+'\n').encode()
            dst.writestr(info,data)
with zipfile.ZipFile(a.input) as src,zipfile.ZipFile(a.output) as dst:
    for name in dst.namelist():
        if name!='assets/awg-build.json':assert dst.read(name)==src.read(name)
print(json.dumps({'unsigned_bytes':a.output.stat().st_size,'abi':'arm64-v8a','retained_payload_identical':True}))
