from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / 'tests/fixtures/android_notification_release/beta106-to107.patch'


def additions():
    return '\n'.join(line[1:] for line in PATCH.read_text().splitlines()
                     if line.startswith('+') and not line.startswith('+++'))


def test_release_delta_is_bounded_and_preserves_mesh_and_platform_support():
    changed = re.findall(r'^\+\+\+ b/(.+)$', PATCH.read_text(), re.MULTILINE)
    assert changed == [
        'clients/android/app/build.gradle',
        'clients/android/app/src/main/java/com/familyconnect/app/ConnectionService.java',
        'clients/android/app/src/main/java/com/familyconnect/app/ChatAudio.java',
    ]
    assert 'versionCodeOverride = 107' in additions()
    assert "versionNameOverride = '0.1.18-beta107'" in additions()
    assert 'minSdk' not in additions()
    assert 'PROVISIONING_TEST_SEAM' not in additions()


def test_release_notification_fix_matches_canonical_source_and_keeps_disconnect():
    notification = next(line[1:].strip() for line in PATCH.read_text().splitlines()
                        if line.startswith('+') and '.setOnlyAlertOnce(true)' in line)
    service = (ROOT / 'clients/android/app/src/main/java/com/familyconnect/app/ConnectionService.java').read_text()
    assert notification in service
    assert '.setOngoing(true)' in notification
    assert 'R.string.disconnect' in notification


def test_permission_failure_is_propagated_without_suppressing_lint():
    assert 'try{input=new AudioRecord(' in additions()
    assert 'catch(SecurityException denied){throw new IOException("pcm_capture_permission_denied",denied);}' in additions()
    assert 'SuppressLint' not in additions()
    assert 'abortOnError' not in additions()
    assert 'catch(Exception' not in additions()
