from pathlib import Path
import importlib.util
import json
import subprocess
from types import SimpleNamespace

import pytest
from scripts import sign_update

ROOT = Path(__file__).resolve().parents[1]


def test_android_signed_metadata_checks_artifact_and_signer(tmp_path, monkeypatch):
    args = SimpleNamespace(version='0.1.18-beta59', sequence=1, minimum_supported_code=1,
                           mandatory_after=0, artifacts=tmp_path, apksigner='apksigner', aapt='aapt')
    (tmp_path/'FamilyConnect-Test-0.1.18-beta59.apk').write_bytes(b'a'*2048)
    def output(command, **kwargs):
        if command[0] == 'apksigner':
            return f'Signer #1 certificate SHA-256 digest: {sign_update.ANDROID_SIGNER}\n'
        return "package: name='com.familyconnect.app.friends' versionCode='59' versionName='0.1.18-beta59'"
    monkeypatch.setattr(subprocess, 'check_output', output)
    data = sign_update.android_payload(args, 1000)
    assert data['minimum_supported_version'] == 1 and data['mandatory_after'] == 0
    assert data['version_code'] == 59 and data['size'] == 2048
    args.minimum_supported_code = 60
    with pytest.raises(ValueError):
        sign_update.android_payload(args, 1000)
    args.minimum_supported_code = 1
    monkeypatch.setattr(subprocess, 'check_output', lambda *args, **kwargs: 'foreign signer')
    with pytest.raises(ValueError, match='APK signer'):
        sign_update.android_payload(args, 1000)


def test_publisher_rejects_unsigned_catalog():
    spec = importlib.util.spec_from_file_location('field_publisher', ROOT/'deploy/friends/install-android-update.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises((KeyError, ValueError)):
        module.verify_signed(json.dumps({'schema': 1}).encode(), {})


def test_public_manifest_and_export_have_no_private_controls():
    import xml.etree.ElementTree as ET
    manifest = ET.parse(ROOT/'clients/android/app/src/main/AndroidManifest.xml')
    android = '{http://schemas.android.com/apk/res/android}'
    components = manifest.findall('.//activity') + manifest.findall('.//service') + manifest.findall('.//receiver')
    assert not any('Diagnostic' in item.attrib[android+'name'] or 'Acceptance' in item.attrib[android+'name'] for item in components)
    provider = next(item for item in manifest.findall('.//provider') if item.attrib[android+'name'] == '.DiagnosticsProvider')
    assert provider.attrib[android+'exported'] == 'false'
    ring = (ROOT/'clients/android/app/src/main/java/com/familyconnect/app/DiagnosticRing.java').read_text()
    assert 'events.size()==128' in ring and 'UUID.randomUUID()' in ring
    assert 'ControlIdentity' not in ring and 'Throwable' not in ring
    assert not any(name in ring for name in ('room_url', 'oauth_token', 'private_key', 'query_name'))


def test_update_anchor_reuses_desktop_root():
    source = (ROOT/'clients/android/app/src/main/java/com/familyconnect/app/AndroidUpdateManifest.java').read_text()
    assert (ROOT/'clients/desktop/update.pub').read_text().strip() in source
