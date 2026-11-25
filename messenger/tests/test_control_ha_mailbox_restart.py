import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import RNS

from messenger.relay import Spool
from messenger.tests.test_control_ha_mailbox_startup import write


ROOT = Path(__file__).resolve().parents[2]


def request(root, action, **values):
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(40)
        connection.connect(str(root / 'control.sock'))
        connection.sendall(json.dumps(dict(action=action, **values)).encode() + b'\n')
        return json.loads(connection.makefile('rb').readline(16384))


def prepare(root):
    publics = []
    for name in ('support', 'peer'):
        directory = root / name
        directory.mkdir(mode=0o700)
        identity = RNS.Identity()
        identity.to_file(str(directory / 'synthetic.identity'))
        publics.append(identity.get_public_key().hex())
    return publics


def test_crash_restart_defaults_closed_rejects_old_ticket_and_preserves_native_rows(tmp_path):
    runtime = tmp_path / 'runtime'
    runtime.mkdir(mode=0o700)
    publics = prepare(runtime)
    allowed = write(tmp_path / 'allowed.json', publics)
    manifest = write(tmp_path / 'manifest.json', dict(schema=1, generation='a' * 64, support_public=publics[0],
                                                    owner_binding_sha256='b' * 64, replacement_plan_sha256='c' * 64))
    processes = []

    def start():
        process = subprocess.Popen([sys.executable, '-B', str(ROOT / 'tests/fixtures/mailbox_startup.py'),
                                    str(runtime), str(manifest), str(allowed), str(os.getuid())],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   env={**os.environ, 'PYTHONPATH': str(ROOT)})
        processes.append(process)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            assert process.poll() is None, process.communicate()[1] if process.poll() is not None else ''
            try:
                status = request(runtime, 'status')
                if status['ticket']['process']['pid'] == process.pid:
                    return process, status
            except (OSError, ValueError):
                pass
            time.sleep(.05)
        raise AssertionError('RESTART_FIXTURE_TIMEOUT')

    try:
        first, before = start()
        assert before['fence']['new_link_admission'] == 'CLOSED'
        assert request(runtime, 'support') == ['unavailable']
        old_request = write(tmp_path / 'old-open.json', dict(action='LOCAL_QUALIFICATION_ONLY', ticket=before['ticket']))
        assert request(runtime, 'open', path=str(old_request))['fence']['new_link_admission'] == 'OPEN_LOCAL_ONLY'
        assert request(runtime, 'support') == ['stored']
        first.kill()
        assert first.wait(timeout=5) == -9
        second, after = start()
        assert after['ticket'] != before['ticket'] and after['count'] == 1
        assert after['fence']['new_link_admission'] == 'CLOSED'
        assert request(runtime, 'open', path=str(old_request))['reason'] == 'STALE_OR_UNBOUND_TICKET'
        assert request(runtime, 'support') == ['unavailable']
        assert request(runtime, 'peer') == ['stored']
        fresh = write(tmp_path / 'fresh-open.json', dict(action='LOCAL_QUALIFICATION_ONLY', ticket=after['ticket']))
        assert request(runtime, 'open', path=str(fresh))['fence']['new_link_admission'] == 'OPEN_LOCAL_ONLY'
        assert request(runtime, 'support') == ['stored']
        assert request(runtime, 'stop') == dict(count=3)
        assert second.wait(timeout=5) == 0
        reopened = Spool(runtime / 'spool')
        try:
            assert reopened.stats()['count'] == 3
        finally:
            reopened.close()
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            process.stdout.close()
            process.stderr.close()
