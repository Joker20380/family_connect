import base64
import hashlib
import io
import json

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts.verify_public_invitation import BASE, policy, verify_android_catalog, verify_catalog, verify_page, verify_stream


HTML = b'<style>body {color: black}</style><script>const version="0.2.16";</script>'


def test_page_requires_actual_response_csp_not_locally_generated_header():
    verify_page(HTML, policy(HTML), HTML)
    with pytest.raises(ValueError, match='CSP'):
        verify_page(HTML, policy(HTML.replace(b'0.2.16', b'0.2.15')), HTML)
    with pytest.raises(ValueError, match='source'):
        verify_page(HTML + b' ', policy(HTML), HTML)


@pytest.mark.parametrize('tag', ['script', 'style'])
def test_duplicate_or_missing_inline_blocks_rejected(tag):
    with pytest.raises(ValueError, match='Expected one'):
        policy(HTML + ('<' + tag + '>extra</' + tag + '>').encode())
    with pytest.raises(ValueError, match='Expected one'):
        policy(b'<html></html>')


def test_html_newline_normalization_matches_browser():
    assert policy(HTML.replace(b'black', b'black\r\n')) == policy(HTML.replace(b'black', b'black\n'))


def test_stream_requires_full_signed_bytes():
    raw = b'synthetic installer'
    expected = dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    assert verify_stream(io.BytesIO(raw), expected) == expected
    for other in (raw[:-1], b'X' + raw[1:], raw + b'X'):
        with pytest.raises(ValueError):
            verify_stream(io.BytesIO(other), expected)


def test_catalog_signature_lease_and_exact_publication():
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes_raw()
    payload = json.dumps(dict(schema=2, platform='windows', version='0.2.16', sequence=12,
                             issued_at=100, expires_at=200, artifact=dict(size=15, sha256='a' * 64,
                             url='https://github.com/Joker20380/family_connect/releases/download/windows-v0.2.16/FamilyConnect-Setup-0.2.16-pilot-unsigned.exe'))).encode()
    raw = json.dumps(dict(payload=base64.b64encode(payload).decode(), signature=base64.b64encode(
        key.sign(b'family-connect/app-update/v2\0' + payload)).decode())).encode()
    assert verify_catalog(raw, raw, public, 150)[0]['sequence'] == 12
    with pytest.raises(ValueError, match='lease'):
        verify_catalog(raw, raw, public, 200)
    with pytest.raises(ValueError, match='source'):
        verify_catalog(raw + b' ', raw, public, 150)
    from cryptography.exceptions import InvalidSignature
    with pytest.raises(InvalidSignature):
        verify_catalog(raw, raw, Ed25519PrivateKey.generate().public_key().public_bytes_raw(), 150)


def android_fixture(changes=None):
    key = Ed25519PrivateKey.generate()
    data = dict(schema=1, channel='android-field', sequence=5, package='com.familyconnect.app.friends',
                abi='arm64-v8a', version_code=110, version='0.1.18-beta110', size=2048, sha256='a' * 64,
                url=BASE + '/downloads/FamilyConnect-Test-0.1.18-beta110.apk', issued_at=100, expires_at=200,
                minimum_supported_version=1, mandatory_after=0,
                signer_fingerprint='67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a')
    data.update(changes or {})
    payload = json.dumps(data).encode()
    raw = json.dumps(dict(payload=base64.b64encode(payload).decode(), signature=base64.b64encode(
        key.sign(b'family-connect/android-update/v1\0' + payload)).decode())).encode()
    fields = ('schema', 'package', 'abi', 'version_code', 'version', 'url', 'size', 'sha256')
    legacy = json.dumps({field: data[field] for field in fields}).encode()
    return raw, legacy, key.public_key().public_bytes_raw()


def test_android_discovery_matches_signature_legacy_and_reviewed_bytes():
    raw, legacy, public = android_fixture()
    assert verify_android_catalog(raw, raw, legacy, public, 150)[0]['version_code'] == 110
    for changed in (b'{}', legacy.replace(b'110', b'109')):
        with pytest.raises(ValueError, match='Legacy'):
            verify_android_catalog(raw, raw, changed, public, 150)
    with pytest.raises(ValueError, match='source'):
        verify_android_catalog(raw + b' ', raw, legacy, public, 150)
    from cryptography.exceptions import InvalidSignature
    with pytest.raises(InvalidSignature):
        verify_android_catalog(raw, raw, legacy, Ed25519PrivateKey.generate().public_key().public_bytes_raw(), 150)


@pytest.mark.parametrize('changes', [
    {'version_code': True}, {'version': '0.1.18-beta109'}, {'schema': 2}, {'sequence': 0},
    {'package': 'com.other.app'}, {'abi': 'x86_64'}, {'channel': 'other'}, {'signer_fingerprint': 'a' * 64},
    {'expires_at': 150}, {'issued_at': 151}, {'expires_at': 100 + 91 * 86400},
    {'minimum_supported_version': 111}, {'mandatory_after': 201},
    {'min_sdk': None}, {'min_sdk': True}, {'min_sdk': '27'}, {'min_sdk': 25}, {'min_sdk': 10001},
    {'url': 'https://example.invalid/file.apk'}, {'size': 150_000_001}, {'sha256': '../file'},
])
def test_android_rejects_wrong_binding_or_lease_even_when_signed(changes):
    raw, legacy, public = android_fixture(changes)
    with pytest.raises(ValueError):
        verify_android_catalog(raw, raw, legacy, public, 150)


def test_android_signed_sdk_is_optional_for_old_catalogs_and_bound_for_new_ones():
    raw, legacy, public = android_fixture({'min_sdk': 27})
    assert verify_android_catalog(raw, raw, legacy, public, 150)[0]['min_sdk'] == 27
