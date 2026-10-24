"""Immutable102 ->103 deadline/cache derivative, same offline build and signing workflow."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import types

ROOT=Path(__file__).resolve().parents[3]
FIXTURE=Path(__file__).resolve().parent
BASE=ROOT/'state-client-build/owner-disconnections-20261022'
WORK=ROOT/'state-client-build/owner-deadline103-20261022'
SOURCE=WORK/'android-source'
JAVA=Path('clients/android/app/src/main/java/com/familyconnect/app')
TEST=Path('clients/android/app/src/test/java/com/familyconnect/app')


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {str(path.relative_to(root)):digest(path) for path in root.rglob('*') if path.is_file()
        and not any(part in ('.git','.gradle','__pycache__') for part in path.relative_to(root).parts)
        and not str(path.relative_to(root)).startswith(('clients/android/build/','clients/android/app/build/'))}


def patch(path,old,new):
    assert path.read_text().count(old)==1,(path,old)
    command='*** Begin Patch\n*** Update File: '+str(path)+'\n@@\n'
    command+=''.join('-'+line+'\n' for line in old.splitlines())
    command+=''.join('+'+line+'\n' for line in new.splitlines())+'*** End Patch\n'
    subprocess.run(['apply_patch'],input=command,text=True,check=True)


def prepare():
    WORK.mkdir(mode=0o700,exist_ok=True)
    assert not SOURCE.exists()
    apk=BASE/'delivery/FamilyConnect-0.1.18-beta102-recovery.apk'
    assert digest(apk)=='bd7eab4920c7358c1343c0a4a6f425df7483301044e051fad3ee365b6a948427'
    shutil.copytree(BASE/'android-source',SOURCE,ignore=shutil.ignore_patterns('.git','__pycache__','.gradle','build'))
    before=inventory(SOURCE)
    for name,relative in [('ReadinessStop.java',JAVA),('ReadinessStopTest.java',TEST)]:
        text=(FIXTURE/name).read_text()
        subprocess.run(['apply_patch'],input='*** Begin Patch\n*** Add File: '+str(SOURCE/relative/name)+'\n'+''.join('+'+line+'\n' for line in text.splitlines())+'*** End Patch\n',text=True,check=True)
    path=SOURCE/JAVA/'ControlRnsAndroid.java'
    patch(path,'        public boolean cancelled(){return stop.get()||android.os.SystemClock.elapsedRealtime()>=deadline;}',
        '        public String stopReason(){return ReadinessStop.reason(stop.get(),android.os.SystemClock.elapsedRealtime(),deadline);}\n        public boolean cancelled(){return stop.get()||android.os.SystemClock.elapsedRealtime()>=deadline;}')
    patch(path,'        if(cancelled())throw new IOException("RNS cancelled");',
        '        if(readiness)ReadinessStop.check(cancelled.get(),android.os.SystemClock.elapsedRealtime(),deadline);\n        else if(cancelled())throw new IOException("RNS cancelled");')
    patch(path,'    byte[] requestReadiness(String path,byte[] raw)throws Exception {\n        if(channel==null||cancelled())throw new IOException("RNS unavailable");',
        '    byte[] requestReadiness(String path,byte[] raw)throws Exception {\n        ReadinessStop.check(cancelled.get(),android.os.SystemClock.elapsedRealtime(),deadline);\n        if(channel==null)throw new IOException("RNS unavailable");')
    path=SOURCE/'clients/android/app/src/main/python/fc_rns_transport.py'
    patch(path,"                if callbacks.cancelled():\n                    raise OSError('RNS cancelled')","                self._check_cancelled()")
    patch(path,"            if self.callbacks.cancelled():\n                raise OSError('RNS cancelled')","            self._check_cancelled()")
    patch(path,'        if self.callbacks.cancelled():\n            raise OSError("RNS cancelled")','        self._check_cancelled()')
    patch(path,'    def _wait(self, predicate, deadline):','''    def _check_cancelled(self):
        classify = getattr(self.callbacks, 'stopReason', None)
        if classify is None:
            if self.callbacks.cancelled():
                raise OSError('RNS cancelled')
            return
        reason = str(classify())
        if reason == 'CANCELLED':
            raise OSError('RNS cancelled')
        if reason == 'TIMEOUT':
            raise TransportUnavailable('RNS shared deadline')
        if reason != 'NONE':
            raise ValueError('Invalid RNS stop reason')

    def _wait(self, predicate, deadline):''')
    patch(SOURCE/'clients/android/app/build.gradle',"            variant.outputs.all { versionCodeOverride = 102; versionNameOverride = '0.1.18-beta102-recovery' }",
        "            variant.outputs.all { versionCodeOverride = 103; versionNameOverride = '0.1.18-beta103-recovery' }")
    after=inventory(SOURCE)
    (WORK/'source-delta.json').write_text(json.dumps(dict(parent_apk_sha256=digest(apk),before=before,
        changed={name:dict(before=before.get(name),after=value) for name,value in after.items() if before.get(name)!=value}),indent=2)+'\n')
    print('PREPARED103',len(after))


def build():
    module=types.ModuleType('prepare')
    for name in ('ROOT','BASE','WORK','SOURCE','digest','inventory'):setattr(module,name,globals()[name])
    sys.modules['prepare']=module
    source=(FIXTURE/'build.py').read_text()
    source=source.replace("suites.append('com.familyconnect.app.RestrictedHealthPolicyTest')","suites.append('com.familyconnect.app.ReadinessStopTest')")
    source=source.replace('FamilyConnect-0.1.18-beta101-lifecycle.apk','FamilyConnect-0.1.18-beta102-recovery.apk')
    source=source.replace('version_code=102','version_code=103').replace("version='0.1.18-beta102-recovery'","version='0.1.18-beta103-recovery'")
    exec(compile(source,str(FIXTURE/'build.py'),'exec'),dict(__name__='__main__',__file__=str(FIXTURE/'build.py')))


def deliver(action):
    module=types.ModuleType('prepare')
    for name in ('ROOT','BASE','WORK'):setattr(module,name,globals()[name])
    sys.modules['prepare']=module
    source=(FIXTURE/'deliver.py').read_text()
    source=source.replace("'owner-disconnections-20261022'","'owner-deadline103-20261022'")
    source=source.replace('state-client-build/p1-lifecycle-101-20261021/delivery/FamilyConnect-0.1.18-beta101-lifecycle.apk',
        'state-client-build/owner-disconnections-20261022/delivery/FamilyConnect-0.1.18-beta102-recovery.apk')
    source=source.replace('3c023e39d95e29fe0561dc462e28f1e643b9e14558cf49700d58df528b2963d9','bd7eab4920c7358c1343c0a4a6f425df7483301044e051fad3ee365b6a948427')
    source=source.replace("'metadata(baseline, 101, True), metadata(unsigned, 102, False)'","'metadata(baseline, 102, True), metadata(unsigned, 103, False)'")
    source=source.replace("'metadata(signed, 102, True)'","'metadata(signed, 103, True)'")
    source=source.replace("'FamilyConnect-0.1.18-beta102-recovery.apk'","'FamilyConnect-0.1.18-beta103-recovery.apk'")
    source=source.replace('"before[\'code\']==101"','"before[\'code\']==102"').replace('"after[\'code\']==102"','"after[\'code\']==103"')
    source=source.replace('INSTALLED102_SETTINGS_OPEN','INSTALLED103_SETTINGS_OPEN')
    exec(compile(source,str(FIXTURE/'deliver.py'),'exec'),dict(__name__='__main__',__file__=str(FIXTURE/'deliver.py')))


if __name__=='__main__':
    os.umask(0o077)
    action=sys.argv[1]
    if action=='prepare':prepare()
    elif action=='build':build()
    elif action in ('sign','install'):deliver(action)
    else:raise ValueError('Use prepare/build/sign/install')
