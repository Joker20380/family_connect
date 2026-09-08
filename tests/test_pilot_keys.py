import base64
import stat

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from scripts.create_pilot_clients import generate


def test_separate_device_keys_and_private_permissions(tmp_path, capsys):
    server = base64.b64encode(X25519PrivateKey.generate().public_key().public_bytes_raw()).decode()
    generate(tmp_path, server, '185.251.89.19:51820')
    assert (tmp_path / 'android.pub').read_text() != (tmp_path / 'linux.pub').read_text()
    for name in ('android', 'linux'):
        profile = tmp_path / f'fc-ru-{name}.conf'
        assert len(profile.stem) <= 15
        assert stat.S_IMODE(profile.stat().st_mode) == 0o600
        assert 'AllowedIPs = 0.0.0.0/0, ::/0' in profile.read_text()
        assert (tmp_path / f'{name}.key').read_text().strip() not in capsys.readouterr().out


def test_rerun_keeps_existing_private_keys(tmp_path):
    generate(tmp_path, '', '185.251.89.19:51820')
    before = (tmp_path / 'linux.key').read_bytes()
    generate(tmp_path, '', '185.251.89.19:51820')
    assert (tmp_path / 'linux.key').read_bytes() == before
