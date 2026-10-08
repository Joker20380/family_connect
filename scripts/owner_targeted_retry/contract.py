import hashlib
import json
from pathlib import Path
import re


SIGNER = '67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_pair(acceptance_path):
    acceptance = json.loads(acceptance_path.read_text())
    assert acceptance['result'] == 'PASS'
    pair = Path(acceptance['pair_directory'])
    path = pair / 'pair-manifest.json'
    assert digest(path) == acceptance['manifest_sha256']
    manifest = json.loads(path.read_text())
    assert manifest['result'] == 'PASS' and manifest['sealed'] is True
    assert manifest['source_revision'] == acceptance['source_revision']
    assert re.fullmatch('[0-9a-f]{40}', manifest['source_revision'])
    assert manifest['source_tag'] == 'diag-owner-beta70-ci1'
    assert manifest['version'] == '0.1.18-beta70' and manifest['version_code'] == 70
    assert manifest['package_id'] == 'com.familyconnect.app.friends'
    assert manifest['debuggable'] is False
    assert manifest['android_architecture'] == 'arm64-v8a'
    assert manifest['gateway_architecture'] == 'linux/amd64'
    assert manifest['signer_sha256'] == SIGNER
    assert manifest['expected_signer_sha256'] == SIGNER
    assert manifest['publication_jobs'] == 'skipped'
    assert manifest['callback_chain_acceptance'] == 'PASS'
    for name, expected in manifest['files'].items():
        assert Path(name).name == name
        assert digest(pair / name) == expected, 'Artifact changed: ' + name
    assert manifest['files']['FamilyConnect-OwnerDiagnostic-0.1.18-beta70.apk'] == manifest['signed_apk_sha256']
    assert all(name in manifest['files'] for name in ('bootstrap-broker', 'libfc_restricted.so', 'libfc-awg.so'))
    return manifest


def expected(manifest):
    return dict(package='com.familyconnect.app.friends', version_name='0.1.18-beta70',
                version_code='70', abi='arm64-v8a', debuggable=False,
                apk_sha256=manifest['signed_apk_sha256'], signer=SIGNER,
                gateway_sha256=manifest['files']['bootstrap-broker'],
                revision=manifest['source_revision'], serial='31ce63ba', uid='10283')


def validate(observation, manifest):
    for key, value in expected(manifest).items():
        assert observation[key] == value, 'Identity mismatch: ' + key
