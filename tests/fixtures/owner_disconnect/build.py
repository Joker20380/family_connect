"""Offline beta102 app-only build; exact101 native libraries remain byte-identical."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
import zipfile
from prepare import ROOT,BASE,WORK,SOURCE,digest,inventory

TOOLS=ROOT/'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
OUT=WORK/'build'

def main():
    os.umask(0o077);OUT.mkdir(exist_ok=True)
    assert not (OUT/'receipt.json').exists()
    files=inventory(SOURCE)
    git_environment=dict(os.environ,GIT_DIR=str(ROOT/'state-client-build/mux-profile-20261020/android-source/.git'),GIT_WORK_TREE=str(SOURCE))
    changed=subprocess.check_output(['git','diff','--name-only'],cwd=SOURCE,env=git_environment,text=True).splitlines()
    changed+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=SOURCE,env=git_environment,text=True).splitlines()
    delta={name:digest(SOURCE/name) for name in sorted(changed)}
    source_hash=__import__('hashlib').sha256(json.dumps(delta,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (OUT/'source-inventory.json').write_text(json.dumps(delta,indent=2)+'\n')
    (OUT/'complete-source-inventory.json').write_text(json.dumps(files,indent=2)+'\n')
    native=OUT/'native';shutil.copytree(BASE/'build/native',native,dirs_exist_ok=True)
    assets=OUT/'research-assets';shutil.copytree(BASE/'build/research-assets',assets,dirs_exist_ok=True)
    asset=assets/'provisioning-seam-build.json';value=json.loads(asset.read_text())
    value.update(source_delta_sha256=source_hash,public_release=False,native_rebuilt=False)
    asset.write_text(json.dumps(value,indent=2)+'\n')
    init=OUT/'android.init.gradle';init.write_text((BASE/'build/android.init.gradle').read_text().replace(str(BASE/'build'),str(OUT)))
    environment=dict(git_environment,JAVA_HOME=str(TOOLS/'jdk'),ANDROID_HOME=str(TOOLS/'android'),ANDROID_SDK_ROOT=str(TOOLS/'android'),GRADLE_USER_HOME=str(TOOLS/'gradle-home'))
    environment['PATH']=str(TOOLS/'jdk/bin')+os.pathsep+environment['PATH']
    command=[TOOLS/'gradle-8.11.1/bin/gradle','--offline','--no-daemon','--max-workers=1','-I',init,'--project-cache-dir',OUT/'cache','-PfcTargetAbi=arm64-v8a','-PfcFriendsCi=false','-PfcProvisioningSeamSource='+source_hash,'-PfcProvisioningSeamAssets='+str(assets),'-PfcFriendsRestrictedDirectory='+str(native),'-PfcBuildPython='+str(ROOT/'state-client-build/field65-export16/telemost-lease-continuity-1/build/tools/python/bin/python3.10'),'-PfcRadioNative='+str(ROOT/'state-client-build/field65-export16/exit-krasnodar-candidate-1/audio-native'),':app:assemblePrivateBeta',':app:testPrivateBetaUnitTest']
    suites=[path.stem.removeprefix('TEST-') for path in sorted((BASE/'build/android/app/test-results/testPrivateBetaUnitTest').glob('TEST-*.xml'))]
    suites.append('com.familyconnect.app.RestrictedHealthPolicyTest')
    for suite in suites:command+=['--tests',suite]
    log=OUT/('gradle-'+str(time.time_ns())+'.log')
    with log.open('xb') as output:
        result=subprocess.run(list(map(str,command)),cwd=SOURCE/'clients/android',env=environment,stdout=output,stderr=subprocess.STDOUT,timeout=1200)
    print('GRADLE_EXIT',result.returncode,'LOG',log,flush=True)
    if result.returncode:raise SystemExit(result.returncode)
    results=[ET.parse(path).getroot().attrib for path in (OUT/'android/app/test-results/testPrivateBetaUnitTest').glob('TEST-*.xml')]
    assert len(results)==len(suites) and all(value['failures']==value['errors']==value['skipped']=='0' for value in results)
    apk=OUT/'android/app/outputs/apk/privateBeta/app-privateBeta-unsigned.apk'
    with zipfile.ZipFile(BASE/'delivery/FamilyConnect-0.1.18-beta101-lifecycle.apk') as old,zipfile.ZipFile(apk) as new:
        libraries={name for name in old.namelist() if name.startswith('lib/')}
        assert len(libraries)==12 and libraries=={name for name in new.namelist() if name.startswith('lib/')}
        assert all(old.read(name)==new.read(name) for name in libraries)
    assert inventory(SOURCE)==files
    receipt=dict(result='PASS_LOCAL_BUILD_JVM',version_code=102,version='0.1.18-beta102-recovery',apk_sha256=digest(apk),native_sha256=digest(native/'jniLibs/arm64-v8a/libfc_restricted.so'),source_inventory=source_hash,tests=sum(int(value['tests']) for value in results),suites=results,native_rebuilt=False,signing=False,installed=False,distributed=False,ci='NOT_RUN',primary_rs_cause='UNRESOLVED',field_ready=False)
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({key:receipt[key] for key in ('result','tests','apk_sha256','native_sha256')}))

if __name__=='__main__':main()
