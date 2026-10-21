"""Exact beta95 native reuse; isolated Java/Python delta and private beta96 tests/build."""
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
import zipfile
from prepare import ROOT, WORK, BASE, digest


def main():
    source = WORK / 'android-source'
    output = WORK / 'build'
    output.mkdir(exist_ok=True)
    baseline = json.loads((WORK / 'baseline-inventory.json').read_text())
    changed = {str(path.relative_to(source)): digest(path) for path in source.rglob('*') if path.is_file() and not any(part in ('build','__pycache__','.gradle') for part in path.relative_to(source).parts)
               and baseline.get(str(path.relative_to(source))) != digest(path)}
    assert changed and all(name.startswith('clients/android/') for name in changed)
    inventory = output / 'source-inventory.json'
    git_environment=dict(os.environ,GIT_DIR=str(BASE/'android-source/.git'),GIT_WORK_TREE=str(source))
    names=subprocess.check_output(['git','diff','--name-only'],cwd=source,env=git_environment,text=True,stderr=subprocess.DEVNULL).splitlines()
    names+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=source,env=git_environment,text=True,stderr=subprocess.DEVNULL).splitlines()
    full_inventory={name:digest(source/name) for name in sorted(set(names))}
    inventory.write_text(json.dumps(full_inventory, indent=2, sort_keys=True))
    source_hash=hashlib.sha256(json.dumps(full_inventory,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    patch = ''
    for name in sorted(changed):
        previous = BASE / 'android-source' / name
        patch += ''.join(difflib.unified_diff(previous.read_text().splitlines(True) if previous.exists() else [],
            (source / name).read_text().splitlines(True),fromfile='a/'+name if previous.exists() else '/dev/null',tofile='b/'+name))
    destination = ROOT / 'tests/fixtures/mobile_bootstrap/beta95-to-beta96.patch'
    operation = ('Update File: '+str(destination)+'\n@@\n'+''.join('-'+line+'\n' for line in destination.read_text().splitlines())) if destination.exists() else 'Add File: '+str(destination)+'\n'
    subprocess.run(['apply_patch'],input='*** Begin Patch\n*** '+operation+''.join('+'+line+'\n' for line in patch.splitlines())+'*** End Patch\n',text=True,check=True,stdout=subprocess.DEVNULL)
    for folder in ('native','research-assets'):
        shutil.copytree(BASE / 'build' / folder, output / folder, dirs_exist_ok=True)
    assert digest(output/'native/jniLibs/arm64-v8a/libfc_restricted.so') == '66a9d18d04ff71100df0144228db05decb970aea71b6d277ec321b1c6c240c63'
    asset = output/'research-assets/provisioning-seam-build.json'
    value = json.loads(asset.read_text())
    value.update(native_rebuilt=False, source_delta_sha256=source_hash, java_source_delta_sha256=source_hash, public_release=False)
    asset.write_text(json.dumps(value,indent=2))
    init = output/'android.init.gradle'
    init.write_text((BASE/'build/android.init.gradle').read_text().replace(str(BASE/'build'),str(output)))
    tools=ROOT/'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
    environment=dict(git_environment,JAVA_HOME=str(tools/'jdk'),ANDROID_HOME=str(tools/'android'),ANDROID_SDK_ROOT=str(tools/'android'),GRADLE_USER_HOME=str(tools/'gradle-home'))
    environment['PATH']=str(tools/'jdk/bin')+os.pathsep+environment['PATH']
    suites=('MobileBootstrapTest','FriendsReadinessProtocolTest','ReadinessProductTest','RestrictedCacheTest','RestrictedBootstrapTest',
        'ReadinessBootstrapRouteTest','DiagnosticRingTest','RestrictedRecoveryTest','NightRecoveryTest','AuthenticatedBootstrapRecoveryTest',
        'ConnectivityOrchestratorTest','ConnectionTerminalTest','ProductionProvisioningGateTest','BootstrapCorrelationTest','CutoverRecoveryTest',
        'TransportPresentationTest','RestrictedStartupTest','StartupFidelityTest','Ui60PresentationTest','AdmissionDiagnosticsTest',
        'ControlOperationsTest','ControlStartupTest','ControlTransactionTest')
    command=[str(tools/'gradle-8.11.1/bin/gradle'),'--offline','--no-daemon','--max-workers=1','-I',str(init),'--project-cache-dir',str(output/'cache'),
        '-PfcTargetAbi=arm64-v8a','-PfcFriendsCi=false','-PfcProvisioningSeamSource='+source_hash,'-PfcProvisioningSeamAssets='+str(output/'research-assets'),
        '-PfcFriendsRestrictedDirectory='+str(output/'native'),'-PfcBuildPython='+str(ROOT/'state-client-build/field65-export16/telemost-lease-continuity-1/build/tools/python/bin/python3.10'),
        '-PfcRadioNative='+str(ROOT/'state-client-build/field65-export16/exit-krasnodar-candidate-1/audio-native'),':app:assemblePrivateBeta',':app:testPrivateBetaUnitTest']
    for suite in suites:command+=['--tests','com.familyconnect.app.'+suite]
    log=output/('gradle-'+str(time.time_ns())+'.log')
    with log.open('wb') as handle:
        result=subprocess.run(command,cwd=source/'clients/android',env=environment,stdout=handle,stderr=subprocess.STDOUT,timeout=1000)
    print('GRADLE',result.returncode,'LOG',log,flush=True)
    assert result.returncode==0
    reports=[ET.parse(path).getroot().attrib for path in (output/'android/app/test-results/testPrivateBetaUnitTest').glob('TEST-*.xml')]
    assert len(reports)==len(suites) and all(report['failures']==report['errors']==report['skipped']=='0' for report in reports)
    assert all(digest(source/name)==expected for name,expected in full_inventory.items())
    apk=output/'android/app/outputs/apk/privateBeta/app-privateBeta-unsigned.apk'
    with zipfile.ZipFile(BASE/'delivery/FamilyConnect-0.1.18-beta95-mux-profile.apk') as previous,zipfile.ZipFile(apk) as candidate:
        names={name for name in previous.namelist() if name.startswith('lib/')}
        assert names=={name for name in candidate.namelist() if name.startswith('lib/')}
        assert len(names)==12 and all(previous.read(name)==candidate.read(name) for name in names)
    receipt=dict(result='PASS_LOCAL_BUILD_JVM',version_code=96,version='0.1.18-beta96-bootstrap',apk_sha256=digest(apk),
        native_sha256=digest(output/'native/jniLibs/arm64-v8a/libfc_restricted.so'),source_inventory=digest(inventory),tests=sum(int(report['tests']) for report in reports),
        suites=reports,patch_sha256=digest(destination),all_twelve_native_libraries_unchanged=True,installed=False,distributed=False,field_pass='NOT_RUN')
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps({key:receipt[key] for key in ('result','tests','apk_sha256','native_sha256')}))


if __name__=='__main__':main()
