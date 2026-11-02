import base64
import hashlib
import io
import json

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts.verify_public_invitation import policy, verify_catalog, verify_page, verify_stream


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
