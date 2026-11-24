from copy import deepcopy
import fcntl
import json
import os
import signal
import subprocess
import sys
import time

import pytest
import RNS

from scripts import control_ha_file_custody as custody
from scripts import control_ha_mailbox_custody as mailbox
from scripts.control_ha_installed_inventory import Refused


@pytest.fixture
def source(tmp_path, monkeypatch):
    monkeypatch.setattr(custody, 'ROOTS', (tmp_path,))
    root = tmp_path / 'mailbox'
    root.mkdir(mode=0o700)
    for relative in mailbox.FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'fixture')
    (root / '.members.lock').touch()
    identity = RNS.Identity()
    marker = 'a' * 32
    public = identity.get_public_key().hex()
    values = {'settings.json': dict(volume_id=marker, public_key=public, allowed_public=[public]),
              'bootstrap.json': dict(server='192.0.2.1', port=4243, public_key=public,
                  destination=RNS.Destination.hash(identity, 'lxmf', 'propagation').hex()),
              'members.json': dict(sequence=8, expires_at=int(time.time()) + 100, public_keys=[public])}
    for name, value in values.items():
        (root / name).write_text(json.dumps(value))
    (root / 'node.identity').write_bytes(identity.get_private_key())
    (root / 'state/.volume-id').write_text(marker + '\n')
    monkeypatch.setattr(mailbox, 'PINS', {name: custody.digest(b'fixture') for name in mailbox.PINS})
    return root


def test_mailbox_exact_capture_encrypt_restore_and_identity(source, tmp_path):
    before = {str(path): path.read_bytes() for path in source.rglob('*') if path.is_file()}
    document, receipt = mailbox.capture(source)
    assert receipt['barrier_seconds'] < .25 and receipt['dispatcher_fence'] is False
    summary = mailbox.validate(document)
    assert summary['sequence'] == 8 and summary['dynamic_members'] == 1
    key = os.urandom(32)
    capsule, pin = custody.seal(document, key)
    restored = custody.unseal(capsule, key, pin)
    custody.restore(restored, tmp_path / 'offline')
    assert mailbox.validate(restored) == summary
    assert {str(path): path.read_bytes() for path in source.rglob('*') if path.is_file()} == before
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)


def test_member_writer_contention_never_waits(source):
    with (source / '.members.lock').open('rb') as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            mailbox.capture(source)
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)


@pytest.mark.parametrize('change', ('identity', 'volume', 'bootstrap', 'expired', 'source', 'duplicate', 'spool'))
def test_corrupt_authority_is_not_qualified(source, change):
    if change == 'identity':
        (source / 'node.identity').write_bytes(RNS.Identity().get_private_key())
    elif change == 'volume':
        (source / 'state/.volume-id').write_text('b' * 32)
    elif change == 'bootstrap':
        value = json.loads((source / 'bootstrap.json').read_bytes()); value['destination'] = '0' * 32
        (source / 'bootstrap.json').write_text(json.dumps(value))
    elif change in ('expired', 'duplicate'):
        value = json.loads((source / 'members.json').read_bytes())
        if change == 'expired': value['expires_at'] = int(time.time()) - 1
        else: value['public_keys'] *= 2
        (source / 'members.json').write_text(json.dumps(value))
    elif change == 'source':
        (source / 'accept_membership.py').write_bytes(b'changed')
    with pytest.raises((ValueError, Refused)):
        document, receipt = mailbox.capture(source)
        if change == 'spool':
            document = deepcopy(document)
            document['entries']['spool'] = document['entries']['node.identity']
        mailbox.validate(document)


def test_stalled_mailbox_capture_is_kernel_bounded(source):
    program = '''
import sys,time
from pathlib import Path
from scripts import control_ha_file_custody as custody
from scripts import control_ha_mailbox_custody as mailbox
root=Path(sys.argv[1]);custody.ROOTS=(root.parent,)
mailbox.PINS={name:custody.digest(b'fixture') for name in mailbox.PINS}
custody.capture=lambda plan:time.sleep(5)
mailbox.capture(root)
'''
    result = subprocess.run([sys.executable, '-c', program, str(source)], capture_output=True, timeout=3)
    assert result.returncode == -signal.SIGALRM and result.stdout == b''
    with (source / '.members.lock').open('rb') as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
