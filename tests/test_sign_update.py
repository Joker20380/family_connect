import base64
import hashlib
import json
import sys

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from scripts import sign_update


@pytest.mark.parametrize('platform', ['both', 'windows'])
def test_platform_catalog(tmp_path, monkeypatch, platform):
    key = Ed25519PrivateKey.generate()
    private = tmp_path / 'test.key'
    private.write_bytes(key.private_bytes_raw())
    private.chmod(0o600)
    names = ['FamilyConnect-Setup-0.2.13-pilot-unsigned.exe']
    if platform == 'both':
        names.append('FamilyConnect-Linux-0.2.13.tar.gz')
    for name in names:
        (tmp_path / name).write_bytes(name.encode())
    output = tmp_path / 'catalog.json'
    monkeypatch.setattr(sys, 'argv', ['sign_update', '--key', str(private), '--platform', platform,
        '--version', '0.2.13', '--sequence', '9', '--artifacts', str(tmp_path), '--output', str(output)])
    sign_update.main()
    envelope = json.loads(output.read_text())
    payload = base64.b64decode(envelope['payload'])
    domain = sign_update.WINDOWS_DOMAIN if platform == 'windows' else sign_update.DOMAIN
    key.public_key().verify(base64.b64decode(envelope['signature']), domain + payload)
    data = json.loads(payload)
    assert data['sequence'] == 9 and data['version'] == '0.2.13'
    assert data['expires_at'] - data['issued_at'] == 90 * 86400
    if platform == 'windows':
        assert data['schema'] == 2 and data['platform'] == 'windows' and 'artifacts' not in data
        artifacts = [data['artifact']]
    else:
        assert data['schema'] == 1 and set(data['artifacts']) == {'linux', 'windows'}
        artifacts = list(data['artifacts'].values())
    for artifact in artifacts:
        name = artifact['url'].rsplit('/', 1)[1]
        tag = 'windows-v0.2.13' if platform == 'windows' else 'v0.2.13'
        assert artifact['url'] == f'https://github.com/Joker20380/family_connect/releases/download/{tag}/{name}'
        assert artifact['sha256'] == hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()
        assert artifact['size'] == (tmp_path / name).stat().st_size


@pytest.mark.parametrize('version,sequence', [('0.2.13', '0'), ('0.2.13', str(2**63)), ('../0.2.13', '9')])
def test_bad_metadata_rejected_before_key_access(tmp_path, monkeypatch, version, sequence):
    monkeypatch.setattr(sys, 'argv', ['sign_update', '--key', str(tmp_path / 'absent.key'),
        '--platform', 'windows', '--version', version, '--sequence', sequence])
    with pytest.raises(ValueError, match='invalid version or sequence'):
        sign_update.main()
