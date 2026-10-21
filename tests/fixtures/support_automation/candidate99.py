"""Narrow support-upload completion timing fix; exact98 native reused unchanged."""
import argparse
import difflib
import json
import os
from pathlib import Path
import runpy
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'state-client-build/support-automation-20261021'
WORK = ROOT / 'state-client-build/support-cadence99-20261021'
JAVA = Path('clients/android/app/src/main/java/com/familyconnect/app')
sys.path.insert(0, str(ROOT / 'tests/fixtures/speed_candidate'))
from prepare import write, replace, digest


def prepare():
    source = WORK / 'android-source'
    assert not source.exists()
    inventory = json.loads((BASE / 'build/source-inventory.json').read_text())
    assert all(digest(BASE / 'android-source' / name) == value for name, value in inventory.items())
    WORK.mkdir(mode=0o700, exist_ok=True)
    shutil.copytree(BASE / 'android-source', source, ignore=shutil.ignore_patterns('.git','.gradle','build','__pycache__'))
    for name in ('SupportAutomation.java', 'SupportUploadSchedule.java'):
        write(source / JAVA / name, (ROOT / JAVA / name).read_text())
    test = Path('clients/android/app/src/test/java/com/familyconnect/app/SupportUploadScheduleTest.java')
    write(source / test, (ROOT / test).read_text())
    path = source / JAVA / 'FriendsAccessAndroid.java'
    replace(path, '    static final class Conflict extends Exception {}',
            '    static final class Conflict extends Exception {}\n    static final class SupportRateLimited extends IOException {}')
    replace(path, 'int status=connection.getResponseCode();',
            'int status=connection.getResponseCode();if(path.equals("/friends/device/diagnostics")&&status==429)throw new SupportRateLimited();')
    replace(source / 'clients/android/app/build.gradle',
            "versionCodeOverride = 98; versionNameOverride = '0.1.18-beta98-support'",
            "versionCodeOverride = 99; versionNameOverride = '0.1.18-beta99-support'")
    patch = ''
    for path in sorted(source.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        before = BASE / 'android-source' / relative
        if before.exists() and before.read_bytes() == path.read_bytes():
            continue
        assert not str(relative).startswith(('carrier/', 'pilot/'))
        patch += ''.join(difflib.unified_diff(before.read_text().splitlines(True) if before.exists() else [],
                         path.read_text().splitlines(True), fromfile='a/' + str(relative), tofile='b/' + str(relative)))
    write(Path(__file__).with_name('android98-to99.patch'), patch)
    print('PREPARED99_UPLOAD_TIMING_ONLY_NATIVE_UNCHANGED')


def build():
    source = (BASE / 'executed-android-build.py').read_text()
    source = source.replace(str(BASE), str(WORK))
    source = source.replace('version_code=98', 'version_code=99').replace('0.1.18-beta98-support', '0.1.18-beta99-support')
    source = source.replace('support-automation-20261021/build/receipt.json', 'support-cadence99-20261021/build/receipt.json')
    source = source.replace("parent = Path(" + repr(str(ROOT / 'state-client-build/speed-candidate-20261021/android-source')) + ")",
                            "parent = Path(" + repr(str(BASE / 'android-source')) + ")")
    source = source.replace('FamilyConnect-0.1.18-beta97-speed.apk', 'FamilyConnect-0.1.18-beta98-support.apk')
    source = source.replace("'SupportSnapshotTest',", "'SupportSnapshotTest', 'SupportUploadScheduleTest',")
    start = source.index("    run('native',")
    end = source.index("    receipt['native_sha256']", start)
    source = source[:start] + "    shutil.copyfile(parent.parent / 'build/native/jniLibs/arm64-v8a/libfc_restricted.so', binary)\n" + source[end:]
    source = source.replace('native_rebuilt=True', 'native_rebuilt=False')
    source = source.replace("== ['lib/arm64-v8a/libfc_restricted.so']", '== []')
    for folder in ('carrier', 'pilot'):
        for path in (BASE / 'android-source' / folder).rglob('*'):
            if path.is_file() and not any(part in ('build', '.git', '__pycache__') for part in path.parts):
                assert digest(path) == digest(WORK / 'android-source' / path.relative_to(BASE / 'android-source'))
    os.environ['GIT_DIR'] = str(ROOT / 'state-client-build/mux-profile-20261020/android-source/.git')
    os.environ['GIT_WORK_TREE'] = str(WORK / 'android-source')
    runner = WORK / 'executed-android-build.py'
    write(runner, source)
    exec(compile(source, str(runner), 'exec'), dict(__name__='__main__', __file__=str(runner)))


def sign():
    source = runpy.run_path(str(Path(__file__).with_name('sign.py')))['source_code']()
    source = source.replace('support-automation-20261021', 'support-cadence99-20261021')
    source = source.replace('state-client-build/speed-candidate-20261021/delivery/FamilyConnect-0.1.18-beta97-speed.apk',
                            'state-client-build/support-automation-20261021/delivery/FamilyConnect-0.1.18-beta98-support.apk')
    source = source.replace('d7c02ef5e947733702490c2bf5b6afc0d17dbcb5f19b44eca478d621dfcf928f',
                            'a6f534f8a4258fc51ea961b7ca4f9b0512b8a38a96655fc57e2bb5c343be56c8')
    source = source.replace('metadata(baseline, 97, True), metadata(unsigned, 98, False)',
                            'metadata(baseline, 98, True), metadata(unsigned, 99, False)')
    source = source.replace('metadata(signed, 98, True)', 'metadata(signed, 99, True)')
    source = source.replace("signed = WORK / 'delivery/FamilyConnect-0.1.18-beta98-support.apk'",
                            "signed = WORK / 'delivery/FamilyConnect-0.1.18-beta99-support.apk'")
    source = source.replace("== ['lib/arm64-v8a/libfc_restricted.so']", '== []')
    exec(compile(source, __file__, 'exec'), dict(__name__='__main__', __file__=__file__))


def install():
    source = Path(__file__).with_name('install.py').read_text()
    source = source.replace('support-automation-20261021', 'support-cadence99-20261021')
    source = source.replace("before['code']==97", "before['code']==98")
    source = source.replace('1fa75ee968ae75ad6446000e1907c35ae39a3993625220c51c76bf607f71ee82',
                            '3f700aef7952c67de69de1de7cd6878287ed51d6b97be28c464d304a4cfb6673')
    source = source.replace('FamilyConnect-0.1.18-beta98-support.apk', 'FamilyConnect-0.1.18-beta99-support.apk')
    source = source.replace("after['code']==98", "after['code']==99").replace('INSTALLED98_SETTINGS_OPEN', 'INSTALLED99_SETTINGS_OPEN')
    source = source.replace("online_default='OFF'", "online_consent='PRESERVED_IF_PREVIOUSLY_ENABLED'")
    sys.argv = [__file__, '--allow-owner-vpn-interruption']
    exec(compile(source, __file__, 'exec'), dict(__name__='__main__', __file__=__file__))


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'build', 'sign', 'install'])
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--allow-owner-vpn-interruption', action='store_true')
    args = parser.parse_args()
    assert not args.check_only or args.action == 'sign'
    assert args.allow_owner_vpn_interruption == (args.action == 'install')
    {'prepare': prepare, 'build': build, 'sign': sign, 'install': install}[args.action]()


if __name__ == '__main__':
    main()
