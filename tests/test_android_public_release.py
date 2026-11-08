import base64
import hashlib
import importlib.util
import json
import re
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
    assert platforms(['tests/test_android_public_release.py']) == {
        'android': True, 'windows': False, 'linux': False}
    assert all(platforms(['carrier/wholedevice/session.go']).values())
    assert not any(platforms(['docs/STATUS.md']).values())


def test_android122_candidate_keeps_test_seam_disabled_and_requires_native_provenance():
    gradle = (ROOT / 'clients/android/app/build.gradle').read_text()
    assert 'versionCode 122' in gradle and "versionName '0.1.18-beta122'" in gradle
    assert "withBuildType('friends')) { builder -> builder.minSdk = 27 }" in gradle
    assert "buildConfigField 'boolean', 'PROVISIONING_TEST_SEAM', 'false'" in gradle
    assert 'src/provisioningResearch' not in gradle
    assert 'verifyFriendsRestrictedInputs' in gradle
    assert '--check-generated' in gradle
    assert 'file(restrictedDirectory).absolutePath' in gradle
    assert '--native-source-commit' in gradle


def test_android120_field_entry_matches_canonical_nl1_not_retired_gateway():
    from control_plane.apps.console.collector import SOURCES
    manifest = json.loads((ROOT / 'deploy/friends/restricted/cold-provision-deployment.json').read_text())
    binding = manifest['binding']
    assert manifest['node'] == binding['logical_gateway'] == 'nl-amsterdam-1'
    assert manifest['entry_host'] == SOURCES[manifest['node']]['host'] == '185.10.158.212'
    assert manifest['entry_host'] != binding['retired_host_not_an_alias'] == '186.246.45.246'
    assert SOURCES['gateway-nl']['host'] is None
    assert manifest['entry_host'] != SOURCES['nl-amsterdam-2']['host']
    receipt = json.loads((ROOT / binding['evidence']).read_text())
    assert receipt['catalogs'][0]['sha256'] == binding['routing_catalog_sha256']
    assert receipt['catalogs'][2]['sha256'] == binding['routing_forward_rollback_sha256']
    assert receipt['fresh_live_verification'] == 'NOT_RUN'
    assert 'never copy a key' in binding['identity_rule']


def test_signaling_read_classes_match_without_changing_legacy_recovery():
    native = (ROOT / 'carrier/sessiontrace/trace.go').read_text()
    android = ROOT / 'clients/android/app/src/main/java/com/familyconnect/app'
    java = (android / 'RestrictedTrace.java').read_text()
    native_classes = re.search(r'SignalingReadErrorClasses = "([^"]+)"', native).group(1)
    java_classes = re.search(r'SIGNALING_READ_ERROR_CLASSES="([^"]+)"', java).group(1)
    assert native_classes == java_classes
    assert len(set(native_classes.split('|'))) == 12
    assert 'ReadErrorClass' in native and 'read_error_class,omitempty' in native
    assert 'signaling_read_error' in (android / 'DiagnosticRing.java').read_text()
    assert hashlib.sha256((android / 'RestrictedRecovery.java').read_bytes()).hexdigest() == (
        '5fc3a518a74c1e05de1d99216ee9196e400fad3338994b8150caaa207cb75a00')


def test_public_invitation_offers_qualified_android113_and_audio_source():
    landing = (ROOT / 'deploy/friends/invite/index.html').read_text()
    android = next(line for line in landing.splitlines() if line.lstrip().startswith('android:{'))
    assert 'Beta113 · Android 8.1+ · ARM64 · MESH' in android
    assert '/downloads/FamilyConnect-Test-0.1.18-beta113.apk' in android
    assert '/downloads/FamilyConnect-Android-0.1.18-beta113-audio-source.tar.gz' in android
    assert 'beta60' not in android


def test_public_android113_catalog_is_signed_sdk_bound_and_remains_optional():
    envelope = json.loads((ROOT / 'updates/android-friends-v2.json').read_bytes())
    payload = base64.b64decode(envelope['payload'], validate=True)
    anchor = base64.b64decode((ROOT / 'clients/desktop/update.pub').read_text().strip(), validate=True)
    Ed25519PublicKey.from_public_bytes(anchor).verify(
        base64.b64decode(envelope['signature'], validate=True), b'family-connect/android-update/v1\0' + payload)
    catalog = json.loads(payload)
    assert catalog['sequence'] == 7 and catalog['min_sdk'] == 27
    assert catalog['version_code'] == 113 and catalog['version'] == '0.1.18-beta113'
    assert catalog['minimum_supported_version'] == 1 and catalog['mandatory_after'] == 0
    assert catalog['size'] == 50273696
    assert catalog['sha256'] == '6078d0610272c5eb1b8008d330f9e646163b90b89df180b4bd56fd8ae4edc094'
    assert catalog['url'] == 'https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta113.apk'
    assert 0 < catalog['expires_at'] - catalog['issued_at'] <= 90 * 86400


def test_server_load_ui_uses_one_fresh_country_bound_presentation():
    source = (ROOT / 'clients/android/app/src/main/java/com/familyconnect/app/FriendsActivity.java').read_text()
    assert 'ServerLoadPresentation.from(serverLoads.get(loadTarget()),loadTarget(),' in source
    assert 'ServerLoadPresentation.from(serverLoads.get(code),code,' in source
    assert 'loadBar.setContentDescription(text)' in source
    assert 'load.setText(presentation.percent==null?"—":presentation.value)' in source
    assert '200 Мбит/с' not in source
    model = (ROOT / 'clients/android/app/src/main/java/com/familyconnect/app/ServerLoadPresentation.java').read_text()
    assert '!sample.country.equals(country)||!sample.fresh(now)' in model
    assert 'cpuOnly?sample.cpu:sample.percent' in model
    assert 'channel utilization unknown' in model


def test_load_screenshots_export_only_from_disposable_emulator():
    helper = (ROOT / 'pilot/android-awg/friends_ci.py').read_text()
    assert 'os.environ.get("GITHUB_ACTIONS") != "true"' in helper
    assert 'if not serial.startswith("emulator-"):' in helper
    assert 'for name in ("dashboard-cpu-load.png", "server-row-cpu-load.png", "dashboard-failed-controls.png", "server-netherlands-1.png", "server-netherlands-2.png", "server-list.png", "server-list-en.png", "server-list-ru.png", "server-list-en-large.png", "server-list-ru-large.png", "android-compatibility-voice.png"):' in helper
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
        'ServerLoad.java': 'eea65b43cbb53f338c516e91b0f84531ce48ecd62ed1253b5d49b9fa3962cf41',
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
    reviewed_gateway_readiness = {
        'AutomaticConnection.java': '599419b0dabed171117a271405bb50d040803ee35c8f940c396c0e638be3f9b5',
        'FriendsAccessAndroid.java': '3c243fb137cb79c3889bcb4641bd903cf2c71023cd86ee0232902eb3b90590f7',
        'FriendsRestricted.java': '3b66d4452c8d2f550d60e5e34a8cb232218616208e816a36e1f8b38e04edc670',
        'ReadinessReceiptStore.java': '09549b755e43ebfe970593f5ee64bee52566549bbc4f82be936bcd2bf8473d90',
        'RestrictedTunnelEngine.java': '0b9bcd34f9f7829a832c9b091ac6fde6a7a24480448c73ad4b99e676c1586470',
        'RestrictedVault.java': '160fff98281d78fd769c88fbcdd8ffce5e05a64e6e4c0e28e0165d45bee1f432',
    }
    reviewed_slow_link_recovery = {
        'RestrictedRecovery.java': '18c572db0f92e2cc0bbf054f64d21e008336a8d96ea9fb9f530b591fb1e3c028',
    }
    reviewed_idle_ack_recovery = {
        'DiagnosticRing.java': '20ad8811578eda5b4dc3d2a56a5316752e07cf25837dc1f144d12491024d8101',
        'RestrictedTrace.java': '4810d2c168bd9b01d1a59516a6d9f79b278e91eb016ebef413b597fc174b1e41',
        'RestrictedRecovery.java': '5fc3a518a74c1e05de1d99216ee9196e400fad3338994b8150caaa207cb75a00',
    }
    reviewed_signaling_read_diagnostics = {
        'DiagnosticRing.java': 'd6f0f8888164384c2c07627a283a00a9e2383e1488a177816b4f1352f92d0c68',
        'RestrictedTrace.java': '34a50256ffd04d98cb29274be2c5b800a18a7756c47f5da4568e3bc5a5418561',
    }
    reviewed_subscription_beta119 = {
        'ChatActivity.java': '4a1e7a28cc374aef5d72664237a2c4dff8cd8d078aff760a1e996646bfb75a0d',
        'ChatLocalAndroid.java': 'd5a01e8137b10b577b7e84e35980b64f0a2f42739bd588a74b868ac5388ecf15',
        'ChatNotifications.java': '75f7b6e2a188df6e87a084afddb6238707927c1567a93abac1b0f2ba2ed64f42',
        'ChatRuntime.java': '4568fd78a2b63ab764b1d11d38976238abf7984f9063676d8167f05bc124b32b',
        'FriendsAccessAndroid.java': '98563acb61287b7272adf3f74d3d9705b2d37c192420ce5bae63f51dcc638a24',
    }
    reviewed_inherited_renewal_beta119 = {
        'FriendsRestricted.java': '8c8228f2188f0bc09348586ce4c9bf0585ab51c4c7894f3d1cf4faacd641f70a',
        'NativeRestricted.java': 'bcf81d360910e4348133dffa13901701e2cf4461b26c1f21b5b4d872b2d2a867',
        'RestrictedTunnelEngine.java': 'b8cb9725620a1086dfafa907b3edb5126282cc9e500bd990e3a162cb71b795c3',
    }
    reviewed_cold_candidate_9bf02724 = {
        'ChatNetworkAndroid.java': '181fa6d969786cf46aac0840abb35d2e7da1b1ecf65951f7e215ca8e307ce9cf',
        'ConnectivityOrchestrator.java': '93b6d8c322ad95ef74594aab2ce30a1b2fea02d54d2ac06b4a3308fe3664224e',
        'DiagnosticRing.java': '5c9db0e90368bfd642446f735d856ae2960026ba6fc48ce41ffbd4e72c32ea61',
        'FriendsAccessAndroid.java': '8c26c43dec6210318911785231c673546dce98505e642cedb0326e0d8b5f6642',
        'FriendsRestricted.java': '985bd6739c38c28537112dead9217f0cf1471a5c51433c51cbc5b17c1415cce8',
        'NativeRestricted.java': '4b79103dd6e67039d95eae83af0bcc3df30f298f0d92221fc53f5c97bdc75939',
        'ReadinessBootstrapRoute.java': 'b1f21dfb01d7a79cef793d898b8b58c99b324c75c53d745c47b370f679bbe5ef',
        'ReadinessFetchTrace.java': 'c91f00af4852bdc9cee839cf7db4a798ac387781d8d9d36a5f730c37e8915cc8',
        'ReadinessProduct.java': '3f63c57c4b543df769a96a72599f3380ba8fb32af4c5ddede6b21b6e36ae7074',
        'RestrictedTunnelEngine.java': 'b331aa8c3678fdaf12a0552239cd3e6927c23028b95493b741d96faf23c80740',
    }
    reviewed_consolidated_beta121 = {
        'FriendsAccessAndroid.java': 'f4eb3235f067d91e66109e8d18e8a7c9986b42d6b92cd6b0d4e2661c6c54f3e7',
    }
    reviewed_app_vpn_beta122 = {
        'AutomaticConnection.java': 'f393817ca84ccc444203d4bfad9be7943fef65c7351981c2dc32ebc8b88f6a48',
        'AutomaticNormalEngine.java': '360cfbe0399ed03d5cf1b56525cb712b84a688f6efd7aa5b6cab6073a56f1484',
        'AutomaticVpnOwner.java': '7ae1cae2dc4cb863b57e996ed4526ab31a5b40c69b7c632d8f47fbb23ef17975',
        'NativeRestricted.java': 'c86f49e49dbf8b01d3b67a949665952c6c7cfd784d89bb8d85bb38a044cc4cd6',
        'NativeTcp.java': 'fc9b01ee9b735e9fbc0ec2768eba0724e07b2ebfed0fff621a1facd2a02c3657',
        'RestrictedTunnelEngine.java': '919f560ee47ec73a48b3347aff307517bc83394341a754a1b7294de56e5b13d4',
        'TcpTunnelEngine.java': '351320841926e095ab524743a413de12bce774c1937c36ff395324b102f146a6',
        'TunnelEngine.java': 'bd0414885d4ec6d228e411ccd375b34fc8f5ac21853ce11fc46a82893fc49608',
        'VpnHealth.java': '01e7b553c995958dd1e882fbc929bdfff3d7ff805bb0ac69738d579b1f6646aa',
    }
    reviewed_handlers = {**reviewed_ui109, **reviewed_gateway_selection, **reviewed_android81,
                         **reviewed_gateway_readiness, **reviewed_slow_link_recovery,
                         **reviewed_idle_ack_recovery, **reviewed_signaling_read_diagnostics,
                         **reviewed_subscription_beta119, **reviewed_inherited_renewal_beta119,
                         **reviewed_cold_candidate_9bf02724, **reviewed_consolidated_beta121,
                         **reviewed_app_vpn_beta122}
    reviewed_resources = {
        'clients/android/app/src/main/res/values-ru/strings.xml': '89b334900a7febe2e50bfe06d593673961c320704a16ead76c09d9baa22ea279',
        'clients/android/app/src/main/res/values/strings.xml': '85e40c0044eaec9ebe8fb6f77d0a026ddc6bead90fb044237abd23b305fd2c39',
        'clients/android/app/src/main/res/values-ru/exit_radio.xml': 'bb5198a35cf336c3b364bb5ecd65285a948614a4f60b3d1434cec0e7d9b7608b',
        'clients/android/app/src/main/res/values/exit_radio.xml': 'f0147662d5ca508fba482cca46906a2198b2f7f4ae72d692a61631123ad07404',
    }
    reviewed_subscription_resources_beta119 = {
        'clients/android/app/src/main/res/values-ru/strings.xml': '120dfc00876e5603eb04edc3422023f6daf113744e3f112fa79136e9587af30e',
        'clients/android/app/src/main/res/values/strings.xml': 'e5db89007bb81fe8a7a78632eb8bd29ef2d1a35ca7f85970e8cc709f289e3b23',
    }
    reviewed_app_vpn_resources_beta122 = {
        'clients/android/app/src/main/res/values-ru/strings.xml': 'b88a2342bc5e6b797187adfe3480ee91e980a53e2fb6c64e8de274f3a3a9f2cc',
        'clients/android/app/src/main/res/values/strings.xml': 'a66f9bd10f72728c471a413061cf44b5227e3617c2f890ef6aba32cfcb2946a8',
    }
    reviewed_resources = {**reviewed_resources, **reviewed_subscription_resources_beta119, **reviewed_app_vpn_resources_beta122}
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
