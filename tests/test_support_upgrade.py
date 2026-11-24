import hashlib
import zipfile

import pytest

from scripts import package_support_upgrade as upgrade


def test_overlay_preserves_every_non_support_byte_and_refuses_changed_runtime(tmp_path, monkeypatch):
    base = tmp_path / 'base.pyz'
    with zipfile.ZipFile(base, 'w') as archive:
        archive.writestr('friends_http.py', b'old = True\n')
        archive.writestr('control/friends/transport_reconcile.py', b'paid_vpn_fix = True\n')
        archive.writestr('control/friends/paid_beta.py', b'immutable_accepted_release = 123\n')
    monkeypatch.setattr(upgrade, 'BASE_SHA256', hashlib.sha256(base.read_bytes()).hexdigest())
    monkeypatch.setattr(upgrade, 'REPLACE', {'friends_http.py':
        (hashlib.sha256(b'old = True\n').hexdigest(), 'deploy/friends/access-api.py')})
    output = tmp_path / 'candidate.pyz'
    receipt = upgrade.build(base, output)
    assert receipt['preserved'] == 2
    with zipfile.ZipFile(base) as before, zipfile.ZipFile(output) as after:
        for name in ('control/friends/transport_reconcile.py', 'control/friends/paid_beta.py'):
            assert before.read(name) == after.read(name)
        assert after.read('friends_http.py') == (upgrade.ROOT / 'deploy/friends/access-api.py').read_bytes()
    with pytest.raises(FileExistsError):
        upgrade.build(base, output)
    base.write_bytes(base.read_bytes() + b'changed')
    with pytest.raises(ValueError, match='Runtime changed'):
        upgrade.build(base, tmp_path / 'unsafe.pyz')
