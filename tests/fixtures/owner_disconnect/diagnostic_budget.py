"""Immutable105 ->106 app-only aggregate diagnostic bound correction."""
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import types

from deadline import digest, inventory, patch

ROOT=Path(__file__).resolve().parents[3]
FIXTURE=Path(__file__).resolve().parent
BASE=ROOT/'state-client-build/owner-pressure105-20261022'
WORK=ROOT/'state-client-build/owner-diagnostic106-20261022'
SOURCE=WORK/'android-source'
JAVA=Path('clients/android/app/src/main/java/com/familyconnect/app')
TEST=Path('clients/android/app/src/test/java/com/familyconnect/app')
PARENT_HASH='91ba2d6e4cb6d3c789e4921df96b79ea196d42bc602bc72ea727fa1489aef2a3'


def prepare():
    WORK.mkdir(mode=0o700,exist_ok=True)
    assert not SOURCE.exists()
    apk=BASE/'delivery/FamilyConnect-0.1.18-beta105-recovery.apk'
    assert digest(apk)==PARENT_HASH
    shutil.copytree(BASE/'android-source',SOURCE,ignore=shutil.ignore_patterns('.git','__pycache__','.gradle','build'))
    before=inventory(SOURCE)
    for name,relative in [('DiagnosticRecordBudget.java',JAVA),('DiagnosticRecordBudgetTest.java',TEST)]:
        text=(FIXTURE/name).read_text()
        subprocess.run(['apply_patch'],input='*** Begin Patch\n*** Add File: '+str(SOURCE/relative/name)+'\n'+''.join('+'+line+'\n' for line in text.splitlines())+'*** End Patch\n',text=True,check=True)
    patch(SOURCE/JAVA/'DiagnosticRing.java',
        '        JsonArray recent=new JsonArray();for(JsonObject event:events)recent.add(event.deepCopy());result.add("events",recent);return result;',
        '        JsonArray recent=new JsonArray();for(JsonObject event:events)recent.add(event.deepCopy());result.add("events",recent);return DiagnosticRecordBudget.apply(result);')
    patch(SOURCE/'clients/android/app/build.gradle',
        "            variant.outputs.all { versionCodeOverride = 105; versionNameOverride = '0.1.18-beta105-recovery' }",
        "            variant.outputs.all { versionCodeOverride = 106; versionNameOverride = '0.1.18-beta106-recovery' }")
    after=inventory(SOURCE)
    (WORK/'source-delta.json').write_text(json.dumps(dict(parent_apk_sha256=digest(apk),before=before,
        changed={name:dict(before=before.get(name),after=value) for name,value in after.items() if before.get(name)!=value}),indent=2)+'\n')
    print('PREPARED106',len(after))


def build():
    module=types.ModuleType('prepare')
    for name in ('ROOT','BASE','WORK','SOURCE','digest','inventory'):setattr(module,name,globals()[name])
    sys.modules['prepare']=module
    source=(FIXTURE/'build.py').read_text()
    changes={
        "suites.append('com.familyconnect.app.RestrictedHealthPolicyTest')":"suites.append('com.familyconnect.app.DiagnosticRecordBudgetTest')",
        'FamilyConnect-0.1.18-beta101-lifecycle.apk':'FamilyConnect-0.1.18-beta105-recovery.apk',
        'version_code=102':'version_code=106',
        "version='0.1.18-beta102-recovery'":"version='0.1.18-beta106-recovery'",
    }
    for old,new in changes.items():assert old in source,old;source=source.replace(old,new)
    (WORK/'build-runner.py').write_text(source)
    exec(compile(source,str(WORK/'build-runner.py'),'exec'),dict(__name__='__main__',__file__=str(FIXTURE/'build.py')))


def sign():
    source=runpy.run_path(str(ROOT/'tests/fixtures/support_automation/sign.py'))['source_code']()
    changes={
        'support-automation-20261021':'owner-diagnostic106-20261022',
        'state-client-build/speed-candidate-20261021/delivery/FamilyConnect-0.1.18-beta97-speed.apk':'state-client-build/owner-pressure105-20261022/delivery/FamilyConnect-0.1.18-beta105-recovery.apk',
        'd7c02ef5e947733702490c2bf5b6afc0d17dbcb5f19b44eca478d621dfcf928f':PARENT_HASH,
        'metadata(baseline, 97, True), metadata(unsigned, 98, False)':'metadata(baseline, 105, True), metadata(unsigned, 106, False)',
        'metadata(signed, 98, True)':'metadata(signed, 106, True)',
        "== ['lib/arm64-v8a/libfc_restricted.so']":'== []',
        'SIGNED_PRIVATE_SUPPORT_NOT_SPEED_FIX':'SIGNED_DIAGNOSTIC_BUDGET_NOT_FIELD_READY',
        'FamilyConnect-0.1.18-beta98-support.apk':'FamilyConnect-0.1.18-beta106-recovery.apk',
    }
    for old,new in changes.items():assert old in source,old;source=source.replace(old,new)
    exec(compile(source,__file__,'exec'),dict(__name__='__main__',__file__=__file__))


def install():
    helpers=runpy.run_path(str(ROOT/'tests/fixtures/mesh_throughput_trace/upgrade.py'))
    signing=json.loads((WORK/'delivery/signing-receipt.json').read_text())
    apk=WORK/'delivery/FamilyConnect-0.1.18-beta106-recovery.apk'
    assert digest(apk)==signing['signed']['sha256']
    before=helpers['snapshot']()
    if before['code']==106:
        assert before['apk_sha256']==signing['signed']['sha256']
        print('ALREADY_INSTALLED106_NO_WRITE')
        return
    assert before['code']==105 and before['apk_sha256']==PARENT_HASH
    assert before['native_sha256']==signing['native_sha256']
    assert not before['vpn'] and not before['vpn_service'], 'Preserve active VPN; read back before update'
    intent=WORK/'install-intent.json'
    assert not intent.exists(), 'Reconcile previous install before another attempt'
    with intent.open('x') as output:
        json.dump(dict(before=before,apk_sha256=signing['signed']['sha256'],
            method='adb install -r',uninstall=False,clear_data=False,force_stop=False),output,indent=2)
        output.flush();os.fsync(output.fileno())
    try:
        result=subprocess.run(['adb','-s','31ce63ba','install','-r',str(apk)],capture_output=True,text=True,timeout=180)
    except subprocess.TimeoutExpired:
        (WORK/'install-receipt.json').write_text(json.dumps(dict(result='UNKNOWN_TIMEOUT_READBACK_REQUIRED',before=before),indent=2)+'\n')
        raise SystemExit('INSTALL_OUTCOME_UNKNOWN_DO_NOT_RETRY')
    receipt=dict(exit=result.returncode,stdout=result.stdout,stderr=result.stderr,before=before,
        identity_profile_verification='PENDING_FRESH_APP_JSON',uninstall=False,clear_data=False)
    target=WORK/'install-receipt.json'
    target.write_text(json.dumps(receipt,indent=2)+'\n')
    after=helpers['snapshot']();receipt['after']=after
    target.write_text(json.dumps(receipt,indent=2)+'\n')
    assert result.returncode==0 and result.stdout.strip().endswith('Success')
    assert after['code']==106 and after['uid']==before['uid']
    assert after['apk_sha256']==signing['signed']['sha256'] and after['native_sha256']==signing['native_sha256']
    subprocess.run(['adb','-s','31ce63ba','shell','am','start','-n',
        'com.familyconnect.app.friends/com.familyconnect.app.FriendsActivity','--ei','tab','3'],
        check=True,capture_output=True,timeout=15)
    print(json.dumps(dict(result='INSTALLED106_SETTINGS_OPEN',uid=after['uid'],apk_sha256=after['apk_sha256'],
        next='NORMAL_USB_CONSENT_THEN_FRESH_JSON',identity_profile_verification='PENDING')))


if __name__=='__main__':
    os.umask(0o077)
    action=sys.argv[1]
    if action=='prepare':prepare()
    elif action=='build':build()
    elif action=='sign':sign()
    elif action=='install':install()
    else:raise ValueError('Use prepare/build/sign/install')
