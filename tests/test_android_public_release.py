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
    assert 'versionCode 111' in gradle and "versionName '0.1.18-beta111'" in gradle
    assert "withBuildType('friends')) { builder -> builder.minSdk = 27 }" in gradle
    assert "buildConfigField 'boolean', 'PROVISIONING_TEST_SEAM', 'false'" in gradle
    assert 'src/provisioningResearch' not in gradle
    assert 'verifyFriendsRestrictedInputs' in gradle
    assert '--check-generated' in gradle


def test_public_invitation_offers_qualified_android110_and_audio_source():
    landing = (ROOT / 'deploy/friends/invite/index.html').read_text()
    android = next(line for line in landing.splitlines() if line.lstrip().startswith('android:{'))
    assert 'Beta110 · Android 12+ · ARM64 · MESH' in android
    assert '/downloads/FamilyConnect-Test-0.1.18-beta110.apk' in android
    assert '/downloads/FamilyConnect-Android-0.1.18-beta110-audio-source.tar.gz' in android
    assert 'beta60' not in android


def test_public_android110_catalog_is_signed_and_remains_optional():
    envelope = json.loads((ROOT / 'updates/android-friends-v2.json').read_bytes())
    payload = base64.b64decode(envelope['payload'], validate=True)
    anchor = base64.b64decode((ROOT / 'clients/desktop/update.pub').read_text().strip(), validate=True)
    Ed25519PublicKey.from_public_bytes(anchor).verify(
        base64.b64decode(envelope['signature'], validate=True), b'family-connect/android-update/v1\0' + payload)
    catalog = json.loads(payload)
    assert catalog['sequence'] == 5
    assert catalog['version_code'] == 110 and catalog['version'] == '0.1.18-beta110'
    assert catalog['minimum_supported_version'] == 1 and catalog['mandatory_after'] == 0
    assert catalog['size'] == 56221032
    assert catalog['sha256'] == '159034142f0430445caf6420c7d491866f7802a7a3eb615a4d4bfb7908641861'
    assert catalog['url'] == 'https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta110.apk'
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
    assert 'for name in ("dashboard-cpu-load.png", "server-row-cpu-load.png", "dashboard-failed-controls.png", "server-amsterdam-1.png", "server-amsterdam-2.png", "android-compatibility-voice.png"):' in helper
    assert '["adb", "-s", serial, "pull"' in helper
    assert '"-Pandroid.injected.androidTest.leaveApksInstalledAfterRun=true"' in helper
    assert helper.index('"pull"') < helper.index('finally:') < helper.index('"uninstall"')
    workflow = (ROOT / '.github/workflows/clients.yml').read_text()
    assert 'name: FamilyConnect-Android-ui' in workflow
    assert 'path: android-ci-ui/**/*.png' in workflow


def test_android81_acceptance_preserves_modern_gates_and_native_lifecycle():
    workflow = (ROOT / '.github/workflows/clients.yml').read_text()
    assert 'api-level: 35' in workflow and 'api-level: 27' in workflow
    assert workflow.count('python3 -u pilot/android-awg/run.py 2>&1 | tee ') == 2
    assert workflow.count('run: python3 pilot/android-awg/report_control_ci.py') == 2
    assert 'android-runtime-matrix/api35' in workflow
    assert "bash -o pipefail -c 'python3 -u pilot/android-awg/friends_ci.py --legacy 2>&1 | tee android-legacy-friends-runtime.log'" in workflow
    helper = (ROOT / 'pilot/android-awg/friends_ci.py').read_text()
    assert 'if args.legacy and sdk != 27:' in helper
    assert 'if sdk >= 33:' in helper
    assert 'AndroidCompatibilityRuntimeTest' in helper


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
    (tmp_path / 'android-legacy-friends-runtime.log').write_text('subprocess.CalledProcessError: synthetic API27 runner\n')
    assert len(reporter.report(tmp_path)['hints']) == 3


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
    reviewed_ui109 = {
        'ConnectionTerminal.java': '6aedb6c35dd9119d9005e5e6f328ef7b7c23eb1d9e0e6f2e007a34ce0913d582',
        'ConnectionTerminalView.java': 'e2e543655f0e9191ebc037e239852df3f7407e44c02260a60d42134a3cf91804',
        'TerminalUi.java': 'a7ba76489e0605a63b38b1113445dc149b89a871db2aad3529af8b6121b6bc41',
        'Ui60Presentation.java': '47f67af0f36f4219f092bcc5f5b7fa5c17f51725a8e60fb865649cb168f4b744',
    }
    reviewed_gateway_selection = {
        'ControlFriendsCatalog.java': '04f2fad75383465fd338c2ae2bad8ca9712cbb8ff9f26385c2b45ef4a8394cf2',
        'FriendsAccessAndroid.java': '8ee37ad8f38e6413cdb8b32f6f6b76e3dcdff609bcb6a1e3a7032b6088327b35',
        'FriendsConfigurationVault.java': '4d76d775ddf03fd6892e66152f75629ee4825d618de37d613255f60cb94d5fec',
    }
    reviewed_android81 = {
        'AppUpdate.java': '45aa84d5195cd74095523af61dc28f8d5a3c132e2172dc08604066d6ad95b31e',
        'AppUpdateUi.java': '716ef54432385e932717dd34ce2c5c0d7acc644f2c5fe568c74b4de0abe71046',
        'ChatActivity.java': '34aec6a30af77ece7753ee65ac592fd97a2fb3af8d19721de3edfb14e623e488',
        'RadioSettings.java': 'dcda8f1f9e8e326642e738323f93b51e197623b08470fb977d3dc9ddec46c022',
    }
    reviewed_handlers = {**reviewed_ui109, **reviewed_gateway_selection, **reviewed_android81}
    reviewed_resources = {
        'clients/android/app/src/main/res/values-ru/strings.xml': 'd46ebfadc2f6814a9db5ca8bc0835cd500b615eda0ad4cf76a6b042bd8e7f294',
        'clients/android/app/src/main/res/values/strings.xml': '53f68508b47e50d7e7b4554b3eb93cfbb03380b6ee8056befa134996c2308135',
        'clients/android/app/src/main/res/values-ru/exit_radio.xml': 'bb5198a35cf336c3b364bb5ecd65285a948614a4f60b3d1434cec0e7d9b7608b',
        'clients/android/app/src/main/res/values/exit_radio.xml': 'f0147662d5ca508fba482cca46906a2198b2f7f4ae72d692a61631123ad07404',
    }
    changes = {'clients/android/app/src/main/java/com/familyconnect/app/FriendsActivity.java',
               'clients/android/app/src/main/java/com/familyconnect/app/ConnectionService.java',
               'clients/android/app/src/main/java/com/familyconnect/app/ChatAudio.java'}
    for name, expected in reference['android_ui_and_handlers'].items():
        if name not in changes:
            reviewed = reviewed_resources.get(name, reviewed_handlers.get(Path(name).name, expected))
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == reviewed, name


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


def test_runtime_consent_requires_awake_unlocked_emulator_without_bypassing_dialog():
    harness = (ROOT / 'clients/android/app/src/androidTest/java/com/familyconnect/app/AwgRuntimeTest.java').read_text()
    consent = harness.split('void revokeThroughSystemDialog()', 1)[1].split('void quietNotification()', 1)[0]
    assert consent.index('shell("input keyevent 224")') < consent.index('shell("am start -W -n ')
    assert 'shell("wm dismiss-keyguard")' in consent
    assert 'assertTrue("System VPN consent requires an interactive display",power.isInteractive())' in consent
    assert 'assertFalse("System VPN consent blocked by keyguard",keyguard.isKeyguardLocked())' in consent
    assert 'android.os.SystemClock.elapsedRealtime()+15000' in consent
    assert 'system_roots=' in consent and 'interactive=' in consent and 'locked=' in consent
    assert 'ACTIVATE_VPN allow' not in consent
    assert 'assertTrue("System VPN confirmation not found:' in consent and ',clicked);' in consent
    activity = (ROOT / 'clients/android/app/src/androidTest/java/com/familyconnect/app/RevokeVpnActivity.java').read_text()
    assert 'FLAG_KEEP_SCREEN_ON' in activity
    assert 'VpnService.prepare(this)' in activity and 'startActivityForResult(permission,1)' in activity
    runner = (ROOT / 'pilot/android-awg/run.py').read_text()
    assert "'logcat','-d','-b','main','-b','system','-b','crash','-t','2000'" in runner


def test_runtime_ui_checks_match_retained_async_and_scroll_contracts():
    layout = (ROOT / 'clients/android/app/src/androidTest/java/com/familyconnect/app/DashboardLayoutRuntimeTest.java').read_text()
    audio = (ROOT / 'clients/android/app/src/androidTest/java/com/familyconnect/app/VoiceBubbleRuntimeTest.java').read_text()
    assert 'Dashboard must not scroll' not in layout
    assert 'Navigation must not scroll' in layout
    assert 'Scroll viewport must fit' in layout
    assert 'Control touch height' in layout
    assert 'verifyFailureControls(activity,root,w,h)' in layout
    assert 'selector.isShown()' in layout and 'selector.isEnabled()' in layout
    assert '"dashboard-failed-controls.png"' in layout
    assert 'Synthetic failure requires an empty CI device' in layout
    assert 'audio.selected("preview")&&audio.playing("preview")' in audio
    assert 'Async audio must prepare and start before pause/seek' in audio
    assert 'Paused audio seek must advance' in audio


def test_language_runtime_waits_for_recreated_activity_not_old_matching_text():
    source = (ROOT / 'clients/android/app/src/androidTest/java/com/familyconnect/app/AppLanguageRuntimeTest.java').read_text()
    assert 'previous.set(activity)' in source
    assert 'activity!=previous.get()' in source
    assert '!activity.isFinishing()&&!activity.isDestroyed()' in source
    assert 'language.equals(activity.getResources().getConfiguration().getLocales().get(0).getLanguage())' in source
    assert 'SystemClock.elapsedRealtime()+15000' in source
    assert 'Old settings callback cannot undo a newer language selection' in source
    activity = (ROOT / 'clients/android/app/src/main/java/com/familyconnect/app/FriendsActivity.java').read_text()
    assert '!selectedLanguage.equals(AppLanguage.selected(FriendsActivity.this))' in activity
