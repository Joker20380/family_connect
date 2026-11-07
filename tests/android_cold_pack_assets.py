import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'state-client-build/cold-native-diagnostic-20261106/continuation'
TOOLS=Path('/mnt/data/PycharmProjects/family_connect/state-client-build/field65-export16/diag-source-freeze-1/resume-tools')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def signature(name):
    return name.upper().startswith('META-INF/') and name.upper().endswith(('.SF','.RSA','.DSA','.EC','/MANIFEST.MF'))

def signer_command(buildtools,work,final,aligned):
    return [str(buildtools/'apksigner'),'sign','--ks',str(work/'test-signing.p12'),'--ks-key-alias','cold-runtime','--ks-pass','file:'+str(work/'test-signing.pass'),'--min-sdk-version','27','--v1-signing-enabled','true','--v2-signing-enabled','true','--v3-signing-enabled','false','--out',str(final),str(aligned)]

def main(work,base_apks=None):
    WORK=Path(work).resolve()
    base_apks=Path(base_apks).resolve() if base_apks else BASE/'offline-artifacts'
    os.umask(0o077)
    fixture=WORK/'local-auth/fixture'
    out=WORK/'apk-final'
    out.mkdir(mode=0o700)
    pairs=[('app-friends.apk',{'assets/control-anchor.pub':fixture/'anchor.pub','assets/provisioning/nl-amsterdam-1.json':fixture/'locator.json'}),('app-friends-androidTest.apk',{'assets/identity96.private':fixture/'identity96.private','assets/egress.sha256':WORK/'egress.sha256'})]
    environment=os.environ|{'JAVA_HOME':str(TOOLS/'jdk'),'PATH':str(TOOLS/'jdk/bin')+':'+os.environ['PATH']}
    buildtools=TOOLS/'android/build-tools/35.0.0'
    record={'source':'6eb61a9faa659b6b07ac16bf9f4bac46a41cd2a7','abi':'x86_64','native_sha256':'17119f000407ec1d7ccdf8d33acabe423f3cf20e32b6f8af839d209aa3360c59','method':'assets-only zip rewrite, zipalign16K, fresh isolated test signer; unchanged manifest/dex/native','apks':{}}
    record['native_source']=record['source']
    if (base_apks/'managed-source.txt').exists():record['source']=(base_apks/'managed-source.txt').read_text().strip()
    assert len(record['source'])==40 and all(value in '0123456789abcdef' for value in record['source'])
    for name,replacements in pairs:
        original=base_apks/name
        unsigned=out/(name+'.unsigned')
        aligned=out/(name+'.aligned')
        final=out/name
        with zipfile.ZipFile(original) as before,zipfile.ZipFile(unsigned,'w') as target:
            assert set(replacements).issubset(before.namelist())
            for entry in before.infolist():
                if not signature(entry.filename):
                    target.writestr(entry,replacements[entry.filename].read_bytes() if entry.filename in replacements else before.read(entry.filename))
        subprocess.run([str(buildtools/'zipalign'),'-P','16','-f','4',str(unsigned),str(aligned)],check=True,capture_output=True,timeout=20)
        subprocess.run(signer_command(buildtools,WORK,final,aligned),check=True,capture_output=True,env=environment,timeout=20)
        verified=subprocess.run([str(buildtools/'apksigner'),'verify','--verbose','--print-certs','--min-sdk-version','27',str(final)],check=True,capture_output=True,env=environment,timeout=15)
        (out/(name+'.verify.txt')).write_bytes(verified.stdout)
        subprocess.run([str(buildtools/'zipalign'),'-c','-P','16','4',str(final)],check=True,capture_output=True,timeout=15)
        with zipfile.ZipFile(original) as before,zipfile.ZipFile(final) as after:
            for name_in_archive in before.namelist():
                if not signature(name_in_archive):
                    assert after.read(name_in_archive)==(replacements[name_in_archive].read_bytes() if name_in_archive in replacements else before.read(name_in_archive))
            if name=='app-friends.apk':
                assert hashlib.sha256(after.read('lib/x86_64/libfc_restricted.so')).hexdigest()==record['native_sha256']
                assert json.loads(after.read('assets/restricted-build.json'))['source_revision']==record['native_source']
        record['apks'][name]={'sha256':digest(final),'base_sha256':digest(original),'changed_entries':list(replacements)}
    (out/'receipt.json').write_text(json.dumps(record,indent=2)+'\n')
    print('FRESH_ASSETS_ONLY_APKS_VERIFIED',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Explicit private packaging directory required')
    parser.add_argument('work');parser.add_argument('--base-apks')
    arguments=parser.parse_args();main(arguments.work,arguments.base_apks)
