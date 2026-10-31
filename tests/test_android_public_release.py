import base64
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from scripts.client_ci_scope import platforms


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('android_audio', ROOT / 'clients/android/audio/build.py')
audio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audio)


def test_android_changes_do_not_start_desktop_suites():
    assert platforms(['clients/android/app/build.gradle', 'pilot/android-restricted/build.py']) == {
        'android': True, 'windows': False, 'linux': False}
    assert all(platforms(['carrier/wholedevice/session.go']).values())
    assert not any(platforms(['docs/STATUS.md']).values())


def test_public_release_keeps_provisioning_disabled_and_requires_native_provenance():
    gradle = (ROOT / 'clients/android/app/build.gradle').read_text()
    assert 'versionCode 108' in gradle and "versionName '0.1.18-beta108'" in gradle
    assert "withBuildType('friends')) { builder -> builder.minSdk = 31 }" in gradle
    assert "buildConfigField 'boolean', 'PROVISIONING_TEST_SEAM', 'false'" in gradle
    assert 'src/provisioningResearch' not in gradle
    assert 'verifyFriendsRestrictedInputs' in gradle
    assert '--check-generated' in gradle


def test_public_invitation_offers_qualified_android108_and_audio_source():
    landing = (ROOT / 'deploy/friends/invite/index.html').read_text()
    android = next(line for line in landing.splitlines() if line.lstrip().startswith('android:{'))
    assert 'Beta108 · Android 12+ · ARM64 · MESH' in android
    assert '/downloads/FamilyConnect-Test-0.1.18-beta108.apk' in android
    assert '/downloads/FamilyConnect-Android-0.1.18-beta108-audio-source.tar.gz' in android
    assert 'beta60' not in android


def test_public_android108_catalog_is_signed_and_remains_optional():
    envelope = json.loads((ROOT / 'updates/android-friends-v2.json').read_bytes())
    payload = base64.b64decode(envelope['payload'], validate=True)
    anchor = base64.b64decode((ROOT / 'clients/desktop/update.pub').read_text().strip(), validate=True)
    Ed25519PublicKey.from_public_bytes(anchor).verify(
        base64.b64decode(envelope['signature'], validate=True), b'family-connect/android-update/v1\0' + payload)
    catalog = json.loads(payload)
    assert catalog['sequence'] == 3
    assert catalog['version_code'] == 108 and catalog['version'] == '0.1.18-beta108'
    assert catalog['minimum_supported_version'] == 1 and catalog['mandatory_after'] == 0
    assert catalog['size'] == 56212840
    assert catalog['sha256'] == '144b158fe4c07dd19a67683887558cf88a0202b937d135a9924698ffc11b4fdf'
    assert catalog['url'] == 'https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta108.apk'
    assert 0 < catalog['expires_at'] - catalog['issued_at'] <= 90 * 86400


def test_server_load_ui_uses_one_fresh_country_bound_presentation():
    source = (ROOT / 'clients/android/app/src/main/java/com/familyconnect/app/FriendsActivity.java').read_text()
    assert 'ServerLoadPresentation.from(serverLoads.get(loadTarget()),loadTarget(),' in source
    assert 'ServerLoadPresentation.from(serverLoads.get(code),code,' in source
    assert 'loadBar.setContentDescription(text)' in source
    assert 'load.setText(presentation.value)' in source
    assert '200 Мбит/с' not in source
    model = (ROOT / 'clients/android/app/src/main/java/com/familyconnect/app/ServerLoadPresentation.java').read_text()
    assert '!sample.country.equals(country)||!sample.fresh(now)' in model
    assert 'cpuOnly?sample.cpu:sample.percent' in model
    assert 'channel utilization unknown' in model


def test_load_screenshots_export_only_from_disposable_emulator():
    helper = (ROOT / 'pilot/android-awg/friends_ci.py').read_text()
    assert 'os.environ.get("GITHUB_ACTIONS") != "true"' in helper
    assert 'if not serial.startswith("emulator-"):' in helper
    assert 'for name in ("dashboard-cpu-load.png", "server-row-cpu-load.png"):' in helper
    assert '["adb", "-s", serial, "pull"' in helper
    assert '"-Pandroid.injected.androidTest.leaveApksInstalledAfterRun=true"' in helper
    assert helper.index('"pull"') < helper.index('finally:') < helper.index('"uninstall"')
    workflow = (ROOT / '.github/workflows/clients.yml').read_text()
    assert 'name: FamilyConnect-Android-ui' in workflow
    assert 'path: android-ci-ui/*.png' in workflow


def test_emulator_runner_failures_remain_fatal_and_are_retained(tmp_path):
    workflow = (ROOT / '.github/workflows/clients.yml').read_text()
    for runner, log in [('run.py', 'android-emulator-runner.log'),
                        ('friends_ci.py', 'android-friends-runtime.log')]:
        assert f"bash -o pipefail -c 'python3 -u pilot/android-awg/{runner} 2>&1 | tee {log}'" in workflow
        assert f'            {log}\n' in workflow
    module_spec = importlib.util.spec_from_file_location('android_ci_report', ROOT / 'pilot/android-awg/report_ci.py')
    reporter = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(reporter)
    (tmp_path / 'android-emulator-runner.log').write_text('subprocess.TimeoutExpired: bounded synthetic log capture\n')
    (tmp_path / 'android-friends-runtime.log').write_text('subprocess.CalledProcessError: synthetic UI runner\n')
    assert len(reporter.report(tmp_path)['hints']) == 2


@pytest.mark.parametrize('states', [
    ['emulator-5554\toffline', 'emulator-5554\tdevice'],
    ['', 'emulator-5554\tdevice'],
])
def test_ui_runner_waits_for_disposable_emulator_before_starting_tests(monkeypatch, states):
    import subprocess
    module_spec = importlib.util.spec_from_file_location('friends_ci', ROOT / 'pilot/android-awg/friends_ci.py')
    helper = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(helper)
    remaining = iter(states)
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        output = 'List of devices attached\n' + next(remaining) + '\n' if command == ['adb', 'devices'] else '1\n'
        return subprocess.CompletedProcess(command, 0, output, '')
    monkeypatch.setattr(helper.subprocess, 'run', run)
    monkeypatch.setattr(helper.time, 'sleep', lambda seconds: None)
    assert helper.ready_emulator() == 'emulator-5554'
    assert calls[-1] == ['adb', '-s', 'emulator-5554', 'shell', 'getprop', 'sys.boot_completed']
    assert len(calls) == 3


@pytest.mark.parametrize('devices', ['physical-device\tdevice', 'emulator-5554\tdevice\nemulator-5556\tdevice'])
def test_ui_runner_refuses_physical_or_ambiguous_target(monkeypatch, devices):
    import subprocess
    module_spec = importlib.util.spec_from_file_location('friends_ci', ROOT / 'pilot/android-awg/friends_ci.py')
    helper = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(helper)
    monkeypatch.setattr(helper.subprocess, 'run', lambda command, **kwargs:
                        subprocess.CompletedProcess(command, 0, 'List of devices attached\n' + devices, ''))
    with pytest.raises(SystemExit, match='only one disposable emulator'):
        helper.ready_emulator()


def test_ui_runner_offline_wait_is_bounded(monkeypatch):
    import subprocess
    module_spec = importlib.util.spec_from_file_location('friends_ci', ROOT / 'pilot/android-awg/friends_ci.py')
    helper = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(helper)
    ticks = iter([0, 0, 91])
    monkeypatch.setattr(helper.time, 'monotonic', lambda: next(ticks))
    monkeypatch.setattr(helper.time, 'sleep', lambda seconds: None)
    monkeypatch.setattr(helper.subprocess, 'run', lambda command, **kwargs:
                        subprocess.CompletedProcess(command, 0, 'List of devices attached\nemulator-5554\toffline\n', ''))
    with pytest.raises(SystemExit, match='within 90 seconds'):
        helper.ready_emulator()


def test_accepted_android_ui_and_mesh_are_not_replaced_with_old_main():
    reference = json.loads((ROOT / 'clients/shared/android106-reference.json').read_text())
    changes = {'clients/android/app/src/main/java/com/familyconnect/app/FriendsActivity.java',
               'clients/android/app/src/main/java/com/familyconnect/app/ConnectionService.java',
               'clients/android/app/src/main/java/com/familyconnect/app/ChatAudio.java'}
    for name, expected in reference['android_ui_and_handlers'].items():
        if name not in changes:
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name


def test_accepted_jni_startup_observation_helper_is_in_public_source():
    helper = ROOT / 'pilot/android-restricted/native/startup_owner.go'
    assert hashlib.sha256(helper.read_bytes()).hexdigest() == 'f9e96fdad59e255dc4808a196e146265d3ad77ead697b7ac33b2ebdbf99700f5'
    assert 'func retainStartup(' in helper.read_text()
    assert 'func startupStats(' in helper.read_text()
    assert '//go:build' not in helper.read_text()


def test_audio_linker_rejects_missing_speech_objects(tmp_path):
    with pytest.raises(ValueError, match='Incomplete'):
        audio.objects_for_link(tmp_path)


def test_audio_linker_requires_codebooks_and_excludes_other_modes(tmp_path):
    objects = tmp_path / 'src/CMakeFiles/codec2.dir'
    objects.mkdir(parents=True)
    for name in audio.SPEECH:
        (objects / (name + '.o')).touch()
    with pytest.raises(ValueError, match='codebooks'):
        audio.objects_for_link(tmp_path)
    (objects / 'codebook.c.o').touch()
    (objects / 'unrelated.c.o').touch()
    selected = audio.objects_for_link(tmp_path)
    assert len(selected) == len(audio.SPEECH) + 1
    assert not any(path.name == 'unrelated.c.o' for path in selected)


def test_workflow_exports_corresponding_source_without_building_gateway():
    workflow = (ROOT / '.github/workflows/clients.yml').read_text()
    android = workflow.split('  android:\n', 1)[1].split('  windows:\n', 1)[0]
    assert 'audio-generated/corresponding-source/' in android
    assert '--android-only' in android
    assert 'go build -trimpath -o ../restricted-release/bootstrap-broker' not in android
    assert 'go list -deps' in android
    assert 'mapfile -t packages < "$RUNNER_TEMP/android-carrier-packages"' in android
    assert '< <(go list' not in android
    assert './wholedevice ./restrictedowner ./startupdiag ./sessionprofile' in android
    assert 'go test -race "${packages[@]}"' in android
    assert 'go test -race ./...' not in android


def test_runtime_consent_harness_targets_system_button_and_checks_quiet_notification():
    harness = (ROOT / 'clients/android/app/src/androidTest/java/com/familyconnect/app/AwgRuntimeTest.java').read_text()
    assert '"com.android.vpndialogs".contentEquals(node.getPackageName())' in harness
    assert 'findAccessibilityNodeInfosByViewId("android:id/button1")' in harness
    assert 'node.isVisibleToUser()' in harness
    assert 'automation.injectInputEvent(down,true)' in harness
    assert 'System VPN confirmation not found: roots=' in harness
    assert 'FLAG_ONLY_ALERT_ONCE' in harness and 'FLAG_ONGOING_EVENT' in harness
    assert 'quietNotification();traffic(type);quietNotification();' in harness


def test_runtime_ui_checks_match_retained_async_and_scroll_contracts():
    layout = (ROOT / 'clients/android/app/src/androidTest/java/com/familyconnect/app/DashboardLayoutRuntimeTest.java').read_text()
    audio = (ROOT / 'clients/android/app/src/androidTest/java/com/familyconnect/app/VoiceBubbleRuntimeTest.java').read_text()
    assert 'Dashboard must not scroll' not in layout
    assert 'Navigation must not scroll' in layout
    assert 'Scroll viewport must fit' in layout
    assert 'Control touch height' in layout
    assert 'audio.selected("preview")&&audio.playing("preview")' in audio
    assert 'Async audio must prepare and start before pause/seek' in audio
    assert 'Paused audio seek must advance' in audio
