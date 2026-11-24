"""Disposable root-container probes; unchanged receivers with simulated engine commands."""
import base64
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import zipfile

sys.path.insert(0, '/stand/source')
from control.capture_gate import GateError, initialize


def main():
    assert os.geteuid() == 0 and Path('/.dockerenv').is_file()
    assert os.environ.get('FC_CAPTURE_RECEIVER_NATIVE_STAND') == '1'
    root = Path('/opt/apps/family_connect')
    assert root.is_dir() and not list(root.iterdir())
    private = Path(tempfile.mkdtemp(prefix='native-receivers-'))
    gate = initialize(private / 'gate')
    sources = Path('/stand/source')
    awg, tcp, mailbox = root / 'friends-awg', root / 'friends-tcp', root / 'mailbox-pilot'
    for directory in (awg, tcp, mailbox, private / 'bin'):
        directory.mkdir(mode=0o700)
    (awg / 'settings.json').write_text(json.dumps(dict(network='10.83.0.0/24')))
    (tcp / 'server.json').write_text(json.dumps(dict(inbounds=[dict(tag='friends', port=443,
                                                                 settings=dict(clients=[]))])))
    (awg / 'awg').write_text('#!/bin/sh\nexit 0\n')
    (awg / 'awg').chmod(0o700)
    (tcp / 'xray').write_text('#!/usr/local/bin/python\nfrom pathlib import Path\nprint(Path(__file__).with_name("server.json").read_text())\n')
    (tcp / 'xray').chmod(0o700)
    (private / 'bin/systemctl').write_text('#!/bin/sh\nexit 0\n')
    (private / 'bin/systemctl').chmod(0o700)
    (mailbox / 'settings.json').write_text(json.dumps(dict(public_key='ab' * 64)))
    (mailbox / 'bootstrap.json').write_text(json.dumps(dict(server='192.0.2.1', port=4243, public_key='ab' * 64)))
    library = private / 'membership.pyz'
    with zipfile.ZipFile(library, 'w') as bundle:
        bundle.writestr('messenger/', b'')
        bundle.writestr('messenger/__init__.py', b'')
        bundle.writestr('messenger/membership.py', (sources / 'messenger/membership.py').read_bytes())
    library.chmod(0o600)

    def prepare(kind, source, libraries):
        entry = private / (kind + '.py')
        entry.write_bytes((sources / source).read_bytes())
        entry.chmod(0o600)
        binding = private / (kind + '.json')
        binding.write_text(json.dumps(dict(schema=1, kind=kind, capture_gate=str(gate.directory),
            entry_path=str(entry), entry_sha256=hashlib.sha256(entry.read_bytes()).hexdigest(), libraries=libraries)))
        binding.chmod(0o600)
        return [sys.executable, '-I', '-B', '/stand/receiver.pyz', '--binding', str(binding),
                '--binding-sha256', hashlib.sha256(binding.read_bytes()).hexdigest()]

    awg_command = prepare('awg-register', 'deploy/friends/awg-gateway.py', [])
    mailbox_command = prepare('mailbox-membership', 'pilot/messenger/accept_membership.py',
        [dict(path=str(library), sha256=hashlib.sha256(library.read_bytes()).hexdigest())])

    def invoke(command, remote, value):
        env = dict(os.environ, SSH_ORIGINAL_COMMAND=remote, PATH=str(private / 'bin') + ':' + os.environ['PATH'])
        return subprocess.run(command, input=json.dumps(value).encode(), env=env, capture_output=True, timeout=10)

    request = dict(public_key=base64.b64encode(b'a' * 32).decode(), tcp_id='00000000-0000-4000-8000-000000000001', device='a' * 32)
    snapshot = dict(sequence=1, expires_at=int(time.time()) + 100, public_keys=[])
    with gate.drain(.2):
        for command, remote, value in ((awg_command, 'register', request), (mailbox_command, 'chat-sync', snapshot)):
            result = invoke(command, remote, value)
            assert result.returncode == 75 and not result.stdout
    assert not (awg / 'peers.db').exists() and not (mailbox / 'members.json').exists()
    for _ in range(2):
        result = invoke(awg_command, 'register', request)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)['address'] == '10.83.0.2/32'
        with sqlite3.connect(awg / 'peers.db') as database:
            assert database.execute('SELECT COUNT(*) FROM peers').fetchone()[0] == 1
    result = invoke(mailbox_command, 'chat-sync', snapshot)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['sequence'] == 1
    assert json.loads((mailbox / 'members.json').read_bytes()) == snapshot
    assert not list((gate.directory / 'pending').iterdir())
    assert invoke(mailbox_command, 'chat-sync', snapshot).returncode == 1
    retained = set((gate.directory / 'pending').iterdir())
    assert len(retained) == 1
    assert invoke(mailbox_command, 'chat-sync', dict(snapshot, sequence=2)).returncode == 0
    assert set((gate.directory / 'pending').iterdir()) == retained
    (tcp / 'xray').write_text('#!/bin/sh\nexit 1\n')
    failed = dict(request, public_key=base64.b64encode(b'b' * 32).decode(),
                  tcp_id='00000000-0000-4000-8000-000000000002', device='b' * 32)
    assert invoke(awg_command, 'register', failed).returncode == 1
    with sqlite3.connect(awg / 'peers.db') as database:
        assert database.execute('SELECT COUNT(*) FROM peers').fetchone()[0] == 1
    assert len(json.loads((tcp / 'server.json').read_bytes())['inbounds'][0]['settings']['clients']) == 2
    assert len(list((gate.directory / 'pending').iterdir())) == 2
    try:
        with gate.drain(.2):
            raise AssertionError('partially written receiver state admitted capture')
    except GateError as error:
        assert str(error) == 'UNSETTLED_OPERATION'
    print(json.dumps(dict(result='ISOLATED_NATIVE_RECEIVER_PASS', native_sources_unchanged=True,
                         engines_simulated=True, production_touched=False, capture_permitted=False)))


if __name__ == '__main__':
    main()
