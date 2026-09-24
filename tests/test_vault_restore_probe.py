import io
import json
import tarfile

import pytest
from scripts.vault_restore_probe import restore
from scripts.server_secret_snapshot import snapshot
from tests.test_server_secret_snapshot import infrastructure


def test_restored_tls_links_and_private_files(infrastructure,tmp_path):
    out=tmp_path/'restored';out.mkdir(mode=0o700)
    report=restore(snapshot(infrastructure,'ru',infrastructure=True),out)
    assert report['files']==3
    link=out/'opt/apps/family_connect/state-product-https/certificates/live/example/privkey.pem'
    assert link.is_symlink() and link.read_bytes()==b'synthetic TLS'
    assert (out/'etc/ssh/ssh_host_ed25519_key').stat().st_mode & 0o777==0o600
    with pytest.raises(FileExistsError):restore(snapshot(infrastructure,'ru',infrastructure=True),out)


def test_refuses_staging_symlink(infrastructure,tmp_path):
    out=tmp_path/'restored';out.mkdir()
    (out/'etc').symlink_to(infrastructure/'etc')
    with pytest.raises(ValueError,match='staging'):
        restore(snapshot(infrastructure,'ru',infrastructure=True),out)
