import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

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
    assert 'versionCode 107' in gradle and "versionName '0.1.18-beta107'" in gradle
    assert "withBuildType('friends')) { builder -> builder.minSdk = 31 }" in gradle
    assert "buildConfigField 'boolean', 'PROVISIONING_TEST_SEAM', 'false'" in gradle
    assert 'src/provisioningResearch' not in gradle
    assert 'verifyFriendsRestrictedInputs' in gradle
    assert '--check-generated' in gradle


def test_accepted_android_ui_and_mesh_are_not_replaced_with_old_main():
    reference = json.loads((ROOT / 'clients/shared/android106-reference.json').read_text())
    changes = {'clients/android/app/src/main/java/com/familyconnect/app/ConnectionService.java',
               'clients/android/app/src/main/java/com/familyconnect/app/ChatAudio.java'}
    for name, expected in reference['android_ui_and_handlers'].items():
        if name not in changes:
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name


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
