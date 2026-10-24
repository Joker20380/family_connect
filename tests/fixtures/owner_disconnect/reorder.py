"""Exact103 ->104 bounded reorder correction; isolated native rebuild, no server mutation."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import time
import types

ROOT=Path(__file__).resolve().parents[3]
FIXTURE=Path(__file__).resolve().parent
BASE=ROOT/'state-client-build/owner-deadline103-20261022'
WORK=ROOT/'state-client-build/owner-reorder104-20261022'
SOURCE=WORK/'android-source'
TOOLS=ROOT/'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
sys.path.insert(0,str(FIXTURE))
from deadline import inventory,digest,patch as edit


def prepare():
    WORK.mkdir(mode=0o700)
    before=inventory(BASE/'android-source')
    for name in before:
        target=SOURCE/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(BASE/'android-source'/name,target)
    assert inventory(SOURCE)==before
    shutil.copyfile(FIXTURE/'late_frame_test.go',SOURCE/'carrier/telemost/owner_late_frame_test.go')
    build=SOURCE/'clients/android/app/build.gradle'
    text=build.read_text()
    assert 'versionCodeOverride = 103' in text and 'beta103-recovery' in text
    edit(build,"            variant.outputs.all { versionCodeOverride = 103; versionNameOverride = '0.1.18-beta103-recovery' }",
        "            variant.outputs.all { versionCodeOverride = 104; versionNameOverride = '0.1.18-beta104-recovery' }")
    (WORK/'parent-inventory.json').write_text(json.dumps(before,indent=2)+'\n')


def go_environment():
    environment={key:value for key,value in os.environ.items() if not key.startswith(('FC_','YANDEX_','GO','CGO_','CC'))}
    environment.update(GOMAXPROCS='2',GOTOOLCHAIN='local',GOWORK='off',GOPROXY='off',GOSUMDB='off',
        GOCACHE=str(WORK/'go-cache'),GOPATH=str(TOOLS/'gopath'))
    return environment


def tests(label, baseline=False):
    assert label in ('before','after','after-expiry-fixture')
    command=[str(TOOLS/'go/bin/go'),'test','-count=1','-race']
    command+=['./telemost','-run','TestOwnerCompleteLateFrames'] if baseline else ['./telemost','./reliablestream','./tcpforward','./wholedevice','./familysession','./sessiondiag','./sessiontrace']
    log=WORK/(label+'-go.log')
    with log.open('xb') as output:
        result=subprocess.run(command,cwd=SOURCE/'carrier',env=go_environment(),stdout=output,stderr=subprocess.STDOUT,timeout=600)
    print(label,result.returncode,flush=True)
    assert bool(result.returncode)==baseline
    if baseline:
        assert 'all three packets arrived but complete carrier message was lost' in log.read_text()


def patch():
    source=SOURCE/'carrier/telemost/rtp.go'
    text=source.read_text()
    assert text.count('time.Since(b.gapSince) > 100*time.Millisecond')==1
    edit(source,'const reorderWindow = 256','const reorderWindow = 256\nconst reorderGapTimeout = 750 * time.Millisecond')
    edit(source,'\tif len(b.pkts) >= reorderWindow || (!b.gapSince.IsZero() && time.Since(b.gapSince) > 100*time.Millisecond) {',
        '\tif len(b.pkts) >= reorderWindow || (!b.gapSince.IsZero() && time.Since(b.gapSince) > reorderGapTimeout) {')
    edit(SOURCE/'carrier/telemost/head_loss_test.go','\t\tpoint.peer.reorder.gapSince = time.Now().Add(-101 * time.Millisecond)',
        '\t\tpoint.peer.reorder.gapSince = time.Now().Add(-reorderGapTimeout - time.Millisecond)')
    subprocess.run([str(TOOLS/'go/bin/gofmt'),'-w',str(SOURCE/'carrier/telemost/owner_late_frame_test.go')],check=True)
    current=inventory(SOURCE)
    before=json.loads((WORK/'parent-inventory.json').read_text())
    delta={name:dict(before=before.get(name),after=value) for name,value in current.items() if before.get(name)!=value}
    assert set(delta)=={'clients/android/app/build.gradle','carrier/telemost/rtp.go','carrier/telemost/owner_late_frame_test.go','carrier/telemost/head_loss_test.go'}
    (WORK/'source-delta.json').write_text(json.dumps(delta,indent=2)+'\n')


def build():
    out=WORK/'build';out.mkdir()
    before=json.loads((WORK/'parent-inventory.json').read_text())
    current=inventory(SOURCE)
    delta={name:dict(before=before.get(name),after=value) for name,value in current.items() if before.get(name)!=value}
    assert set(delta)=={'clients/android/app/build.gradle','carrier/telemost/rtp.go','carrier/telemost/owner_late_frame_test.go','carrier/telemost/head_loss_test.go'}
    (WORK/'source-delta-final.json').write_text(json.dumps(delta,indent=2)+'\n')
    environment=go_environment()
    environment.update(GOOS='android',GOARCH='arm64',CGO_ENABLED='1',
        CC=str(TOOLS/'android/ndk/28.2.13676358/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android26-clang'),
        CGO_LDFLAGS='-Wl,-z,max-page-size=16384')
    module=out/'native.mod'
    shutil.copyfile(SOURCE/'pilot/android-restricted/go.mod',module)
    shutil.copyfile(SOURCE/'pilot/android-restricted/go.sum',out/'native.sum')
    go=TOOLS/'go/bin/go'
    subprocess.run([go,'mod','edit','-modfile='+str(module),'-replace=github.com/Joker20380/family_connect/carrier='+str(SOURCE/'carrier'),
        '-replace=github.com/xtls/xray-core='+str(ROOT/'state-client-build/transport-write-batching-1/xray')],cwd=SOURCE/'pilot/android-restricted',env=environment,check=True)
    native=out/'native';shutil.copytree(BASE/'build/native',native)
    binary=native/'jniLibs/arm64-v8a/libfc_restricted.so'
    with (out/'native-build.log').open('xb') as output:
        subprocess.run([go,'build','-p=1','-buildvcs=false','-modfile='+str(module),'-trimpath','-ldflags=-checklinkname=0','-buildmode=c-shared','-o',binary,'./native'],
            cwd=SOURCE/'pilot/android-restricted',env=environment,stdout=output,stderr=subprocess.STDOUT,timeout=600,check=True)
    manifest=native/'assets/restricted-build.json'
    value=json.loads(manifest.read_text());value.update(binary_sha256=digest(binary),source_delta_sha256=digest(WORK/'source-delta-final.json'),actual_runner_sha256=digest(Path(__file__)),actual_build_receipt='owner-reorder104-20261022/build/receipt.json')
    manifest.write_text(json.dumps(value,indent=2)+'\n')
    source=(FIXTURE/'build.py').read_text()
    source=source.replace("native=OUT/'native';shutil.copytree(BASE/'build/native',native,dirs_exist_ok=True)","native=OUT/'native'")
    source=source.replace("native=OUT/'native'", "native=OUT/'native'\n    native_manifest=native/'assets/restricted-build.json'\n    native_value=json.loads(native_manifest.read_text());native_value['source_delta_sha256']=source_hash\n    native_manifest.write_text(json.dumps(native_value,indent=2)+'\\n')")
    source=source.replace('native_rebuilt=False','native_rebuilt=True')
    source=source.replace("suites.append('com.familyconnect.app.RestrictedHealthPolicyTest')",'')
    source=source.replace("BASE/'delivery/FamilyConnect-0.1.18-beta101-lifecycle.apk'","BASE/'delivery/FamilyConnect-0.1.18-beta103-recovery.apk'")
    source=source.replace('assert all(old.read(name)==new.read(name) for name in libraries)',"assert [name for name in sorted(libraries) if old.read(name)!=new.read(name)] == ['lib/arm64-v8a/libfc_restricted.so']")
    source=source.replace('version_code=102','version_code=104').replace('beta102-recovery','beta104-recovery')
    source=source.replace("primary_rs_cause='UNRESOLVED'","primary_rs_cause='COMPLETE_LATE_RTP_DROPPED_BY_100MS_REORDER_BOUND_OWNER_ACCEPTANCE_PENDING'")
    module=types.ModuleType('prepare')
    for key,value in dict(ROOT=ROOT,BASE=BASE,WORK=WORK,SOURCE=SOURCE,digest=digest,inventory=inventory).items():setattr(module,key,value)
    sys.modules['prepare']=module
    exec(compile(source,str(FIXTURE/'build.py'),'exec'),dict(__name__='__main__',__file__=str(FIXTURE/'build.py')))


def deliver(action):
    if action=='sign':
        source=runpy.run_path(str(ROOT/'tests/fixtures/support_automation/sign.py'))['source_code']()
        changes={
            'support-automation-20261021':'owner-reorder104-20261022',
            'state-client-build/speed-candidate-20261021/delivery/FamilyConnect-0.1.18-beta97-speed.apk':
                'state-client-build/owner-deadline103-20261022/delivery/FamilyConnect-0.1.18-beta103-recovery.apk',
            'd7c02ef5e947733702490c2bf5b6afc0d17dbcb5f19b44eca478d621dfcf928f':
                '0d274fe5e0250301242d0307ae69c345bb27e935d79248d859afde817693fb04',
            'metadata(baseline, 97, True), metadata(unsigned, 98, False)':'metadata(baseline, 103, True), metadata(unsigned, 104, False)',
            'metadata(signed, 98, True)':'metadata(signed, 104, True)',
            'FamilyConnect-0.1.18-beta98-support.apk':'FamilyConnect-0.1.18-beta104-recovery.apk',
            'SIGNED_PRIVATE_SUPPORT_NOT_SPEED_FIX':'SIGNED_REORDER_CANDIDATE_OWNER_ACCEPTANCE_PENDING',
        }
        for old,new in changes.items():
            assert old in source,old
            source=source.replace(old,new)
    else:
        assert action=='install' and sys.argv[2:]==['--allow-owner-vpn-interruption']
        source=(ROOT/'tests/fixtures/support_automation/install.py').read_text()
        source=source.replace('support-automation-20261021','owner-reorder104-20261022')
        source=source.replace("before['code']==97","before['code']==103").replace("after['code']==98","after['code']==104")
        source=source.replace('1fa75ee968ae75ad6446000e1907c35ae39a3993625220c51c76bf607f71ee82','97d0bf793f8c4bb9975f32579f19369df0e7201786609ab9f46decdea3fec263')
        source=source.replace('FamilyConnect-0.1.18-beta98-support.apk','FamilyConnect-0.1.18-beta104-recovery.apk').replace('INSTALLED98_SETTINGS_OPEN','INSTALLED104_SETTINGS_OPEN')
        source=source.replace("online_default='OFF'","online_consent='PRESERVED'")
        source=source.replace('ROOT=Path(__file__).resolve().parents[3]','ROOT=Path('+repr(str(ROOT))+')')
        sys.argv=[__file__,'--allow-owner-vpn-interruption']
    exec(compile(source,__file__,'exec'),dict(__name__='__main__',__file__=__file__))


if __name__=='__main__':
    os.umask(0o077)
    action=sys.argv[1]
    if action=='prepare':prepare()
    elif action=='before':tests('before',True)
    elif action=='patch':patch()
    elif action=='after':tests('after')
    elif action=='after-expiry-fixture':tests(action)
    elif action=='build':build()
    elif action in ('sign','install'):deliver(action)
    else:raise ValueError('Use prepare/before/patch/after/build/sign/install')
