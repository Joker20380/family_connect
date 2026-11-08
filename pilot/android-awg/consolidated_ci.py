"""Offline in-place storage-format fixtures, never owner installs or historical APK acceptance."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

from friends_ci import ready_emulator

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = 'com.familyconnect.app.friends'


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise SystemExit('Disposable hosted emulator only')
    serial = ready_emulator()
    adb = ['adb', '-s', serial]
    build = ROOT/'clients/android'
    gradle = ['gradle', '--no-daemon', '-PfcTestBuildType=friends', '-PfcFriendsCi=true', '-PfcTargetAbi=x86_64']
    output = ROOT/'android-ci-ui'
    output.mkdir(exist_ok=True)
    results = []
    def run(command, **kwargs):
        return subprocess.run(command, check=True, timeout=600, **kwargs)
    def build_version(version, init):
        init.write_text("allprojects { afterEvaluate { project -> if (project.path == ':app') { "
                        "android.sourceSets.androidTest.java.srcDir('"+str(ROOT/'tests/android-consolidated/java')+"'); "
                        "android.defaultConfig.versionCode = "+str(version)+"; "
                        "android.defaultConfig.versionName = '0.1.18-beta"+str(version)+"' } } }\n")
        run(gradle+['--init-script', str(init), ':app:assembleFriends', ':app:assembleFriendsAndroidTest'], cwd=build)
        apk, = (build/'app/build/outputs/apk/friends').glob('*.apk')
        tests, = (build/'app/build/outputs/apk/androidTest/friends').glob('*.apk')
        run(adb+['install', '-r', str(apk)])
        run(adb+['install', '-r', str(tests)])
    def instrument(method, version):
        result = run(adb+['shell', 'am', 'instrument', '-w', '-e', 'fc_disposable', 'true',
                    '-e', 'sourceVersion', str(version), '-e', 'class',
                    'com.familyconnect.app.ConsolidatedStorageRuntimeTest#'+method,
                    PACKAGE+'.test/androidx.test.runner.AndroidJUnitRunner'], capture_output=True, text=True)
        print(result.stdout, flush=True)
        if method == 'verifyUpgradeAndSubscriptionScreen':
            subprocess.run(adb+['pull', '/sdcard/Android/data/'+PACKAGE+'/files/ui-acceptance/consolidated-subscription-'+str(version)+'.png', str(output)], timeout=30, check=False)
        if 'OK (1 test)' not in result.stdout:
            raise RuntimeError('Storage fixture instrumentation failed')
    try:
        run(adb+['shell', 'svc', 'wifi', 'disable'])
        run(adb+['shell', 'svc', 'data', 'disable'])
        with tempfile.TemporaryDirectory(prefix='fc-upgrade-ci-') as temporary:
            init = Path(temporary)/'version-fixture.gradle'
            for version in (119, 120):
                build_version(version, init)
                instrument('prepareHistoricalFormat', version)
                run(adb+['shell', 'am', 'force-stop', PACKAGE])
                build_version(121, init)
                instrument('verifyUpgradeAndSubscriptionScreen', version)
                if not (output/('consolidated-subscription-'+str(version)+'.png')).is_file():
                    raise RuntimeError('Actual subscription visual evidence missing')
                results.append(dict(from_version=version, to_version=121, status='PASS',
                    scope='in-place format fixture; exact historical vault source, not historical signed APK'))
                for package in (PACKAGE+'.test', PACKAGE):
                    run(adb+['uninstall', package])
        (output/'consolidated-storage.json').write_text(json.dumps(results, indent=2)+'\n')
    finally:
        run(adb+['shell', 'svc', 'wifi', 'enable'])
        run(adb+['shell', 'svc', 'data', 'enable'])
        for package in (PACKAGE+'.test', PACKAGE):
            subprocess.run(adb+['uninstall', package], timeout=60, check=False)


if __name__ == '__main__':
    main()
