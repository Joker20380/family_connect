import multiprocessing
import os
from pathlib import Path
import signal
import socket
import stat
import sys
import tempfile
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'linux'))
import chat_direct_host
from provisioning import chat_bridge_protocol as wire


pytestmark = pytest.mark.skipif(os.geteuid() != 0, reason='isolated root/UID gate')


def run_service(directory, mask):
    chat_direct_host.Path = lambda _: directory
    sys.argv = ['chat_direct_host', '65534']
    os.umask(mask)
    chat_direct_host.main()


def probe_as(uid, endpoint, result):
    os.setgroups([])
    os.setgid(uid)
    os.setuid(uid)
    try:
        with socket.socket(socket.AF_UNIX) as channel:
            channel.settimeout(2)
            channel.connect(str(endpoint))
            wire.write(channel, dict(schema=1, id=1, action='probe', device='a' * 32, budget_ms=1000))
            result.send(wire.read(channel, time.monotonic() + 2).get('ok', False))
    except OSError:
        result.send(False)
    finally:
        result.close()


@pytest.mark.parametrize('unsafe', [None, 'writable', 'symlink', 'owner', 'ancestor', 'lock'])
def test_unit_umask_fresh_runtime_and_real_uid(unsafe):
    unit = Path(__file__).resolve().parents[2] / 'linux/family-connect-chat-direct@.service'
    mask = int(next(line.split('=')[1] for line in unit.read_text().splitlines() if line.startswith('UMask=')), 8)
    assert mask == 0o077
    context = multiprocessing.get_context('fork')
    with tempfile.TemporaryDirectory(prefix='fc-direct-runtime-', dir='/run') as temporary:
        parent = Path(temporary)
        parent.chmod(0o711)
        directory = parent / 'runtime'
        if unsafe == 'symlink':
            directory.symlink_to(parent, target_is_directory=True)
        elif unsafe in ('writable', 'owner'):
            directory.mkdir(mode=0o711)
            if unsafe == 'writable':
                directory.chmod(0o777)
            else:
                os.chown(directory, 65534, 65534)
        elif unsafe == 'ancestor':
            parent.chmod(0o777)
        elif unsafe == 'lock':
            directory.mkdir(mode=0o711)
            (directory / '65534.lock').touch(mode=0o644)
        process = context.Process(target=run_service, args=(directory, mask))
        process.start()
        try:
            endpoint = directory / '65534.chat.sock'
            deadline = time.monotonic() + 5
            while process.is_alive() and not endpoint.exists() and time.monotonic() < deadline:
                time.sleep(.02)
            if unsafe:
                process.join(1)
                assert not process.is_alive() and process.exitcode != 0
                assert not endpoint.exists()
                return
            assert endpoint.exists()
            for uid, expected in ((65534, True), (65533, False)):
                reader, writer = context.Pipe(duplex=False)
                client = context.Process(target=probe_as, args=(uid, endpoint, writer))
                client.start()
                writer.close()
                try:
                    assert reader.poll(4) and reader.recv() is expected, ('UID access', uid)
                finally:
                    client.join(4)
                    reader.close()
                assert client.exitcode == 0
            info = directory.lstat()
            assert info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o711
            assert endpoint.stat().st_uid == 65534 and stat.S_IMODE(endpoint.stat().st_mode) == 0o600
            lock = directory / '65534.lock'
            assert lock.stat().st_uid == 0 and stat.S_IMODE(lock.stat().st_mode) == 0o600
        finally:
            if process.is_alive():
                os.kill(process.pid, signal.SIGTERM)
                process.join(5)
            if process.is_alive():
                process.kill()
                process.join(5)
