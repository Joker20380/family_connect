import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from scripts import control_ha_legacy_support as admission
from scripts import control_ha_support_exit as bridge
from test_control_ha_legacy_support import installed, running, read, wait_for, ipc
from test_control_ha_support_quiesce import check_hooks


def invoke(root, installed, process, seconds=8):
    output = root / 'exit'
    launcher = bridge.prepare(process.pid, installed, output, seconds=seconds)
    sys.remote_exec(process.pid, str(launcher))
    wait_for(lambda: (output / 'entered.json').exists() or (output / 'error.json').exists())
    assert not (output / 'error.json').exists(), read(output / 'error.json')
    return output


def ready(output):
    wait_for(lambda: (output / 'ready.json').exists() or (output / 'error.json').exists())
    assert not (output / 'error.json').exists(), read(output / 'error.json')


def verify_state(root, delivered=False, ratchet=False):
    code = ('import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);'
            'from messenger.store import Store;from RNS.vendor import umsgpack;'
            'root=Path(sys.argv[2]);store=Store(root/"store",b"s"*32,create=False);'
            'assert store._get("meta")=={"format":1};'
            'assert not int(sys.argv[3]) or store._get("bridge-synthetic")=={"completed":True};'
            'store.close();'
            'records=umsgpack.unpackb((root/"runtime/storage/known_destinations").read_bytes());'
            'assert records[b"d"*16][2]==(root/"public").read_bytes();'
            'assert not int(sys.argv[4]) or umsgpack.unpackb((root/"runtime/storage/ratchets"/'
            '(b"d"*16).hex()).read_bytes())["ratchet"]==b"r"*32')
    subprocess.run([os.environ['FC_TEST_SUPPORT_PYTHON'], '-I', '-c', code,
                    str(root.parent / 'source'), str(root), str(int(delivered)), str(int(ratchet))],
                   check=True, capture_output=True, timeout=5)


@pytest.mark.parametrize('mode', ['rns-idle', 'rns-exchange', 'rns-async', 'rns-queue', 'rns-descendant'])
def test_two_phase_exit_persists_native_state_and_decrypted_store(running, installed, mode):
    root, process, _ = running(mode)
    output = invoke(root, installed, process)
    if mode != 'rns-idle':
        time.sleep(.1)
        assert not (output / 'ready.json').exists()
        (root / 'release').touch()
    ready(output)
    with ipc(root) as connection:
        connection.settimeout(.1)
        with pytest.raises(TimeoutError):
            connection.recv(1)
        bridge.authorize(output)
        assert process.wait(5) == 0
    assert read(output / 'exited.json')['stores_closed'] is True
    assert read(output / 'exited.json')['capture_permitted'] is False
    assert read(output / 'uncertainty.json')['legacy_external_outcomes_proven'] is False
    assert not (root / 'worker.sock').exists()
    assert not (output / 'restored.json').exists()
    verify_state(root, delivered=mode == 'rns-exchange', ratchet=mode in ('rns-async', 'rns-queue', 'rns-descendant'))


def test_no_controller_commit_restores_same_process_and_hooks(running, installed):
    root, process, _ = running('rns-idle')
    binding = admission.binding(process.pid)
    output = invoke(root, installed, process, seconds=2.5)
    ready(output)
    wait_for(lambda: (output / 'restored.json').exists())
    assert read(output / 'error.json')['irreversible'] is False
    assert not (output / 'committed.json').exists()
    assert admission.binding(process.pid) == binding
    check_hooks(root, process)
    with ipc(root) as connection:
        assert json.loads(connection.recv(16384))['ok'] is False


@pytest.mark.parametrize('field', ['binding', 'request_sha256', 'capture_permitted'])
def test_wrong_commit_refused_before_irreversible_boundary(running, installed, field):
    root, process, _ = running('rns-idle')
    output = invoke(root, installed, process)
    ready(output)
    receipt = read(output / 'ready.json')
    receipt[field] = 'wrong'
    admission.write(output / 'commit.json', receipt)
    wait_for(lambda: (output / 'restored.json').exists())
    assert read(output / 'error.json') == dict(reason='COMMIT_BINDING', irreversible=False, capture_permitted=False)
    check_hooks(root, process)


@pytest.mark.parametrize('mode', ['rns-final-write', 'rns-final-fsync', 'rns-final-close',
                                 'rns-final-receipt', 'rns-final-commitreceipt'])
def test_post_commit_fault_never_resumes_admission_or_exits(running, installed, mode):
    root, process, _ = running(mode)
    output = invoke(root, installed, process, seconds=3)
    ready(output)
    bridge.authorize(output)
    wait_for(lambda: (output / 'error.json').exists())
    assert read(output / 'error.json')['irreversible'] is True
    time.sleep(3.1)
    assert process.poll() is None
    assert not (output / 'exited.json').exists()
    assert not (output / 'restored.json').exists()
    with pytest.raises(ValueError, match='EXIT_REFUSED'):
        bridge.authorize(output)


def test_final_writer_can_outlive_precommit_deadline_without_controller(running, installed):
    root, process, _ = running('rns-final-blocked')
    output = invoke(root, installed, process, seconds=3)
    ready(output)
    bridge.authorize(output)
    wait_for(lambda: (root / 'final-entered').exists())
    process.terminate()
    time.sleep(3.1)
    assert process.poll() is None and not (output / 'exited.json').exists()
    assert not (output / 'restored.json').exists()
    (root / 'release').touch()
    assert process.wait(5) == 0
    verify_state(root)


def test_controller_process_dies_before_commit_and_service_restores(running, installed):
    root, process, _ = running('rns-idle')
    output = root / 'exit'
    launcher = bridge.prepare(process.pid, installed, output, seconds=2.5)
    subprocess.run([sys.executable, '-I', '-c',
                    'import sys,os;sys.remote_exec(int(sys.argv[1]),sys.argv[2]);os._exit(0)',
                    str(process.pid), str(launcher)], check=True, capture_output=True, timeout=4)
    ready(output)
    wait_for(lambda: (output / 'restored.json').exists())
    check_hooks(root, process)


def test_duplicate_remote_invocation_cannot_claim_or_commit_twice(running, installed):
    root, process, _ = running('rns-idle')
    output = invoke(root, installed, process, seconds=2.5)
    ready(output)
    claimed = (output / 'claimed-exit.json').read_bytes()
    sys.remote_exec(process.pid, str(output / 'exit-invoke.py'))
    wait_for(lambda: (output / 'restored.json').exists())
    assert (output / 'claimed-exit.json').read_bytes() == claimed
    assert not (output / 'committed.json').exists()
    check_hooks(root, process)


@pytest.mark.parametrize('filename', ['exit.py', 'probe.py', 'runtime.py', 'admission.py', 'request.json', 'exit-request.json'])
def test_all_staged_sources_and_requests_are_pinned(running, installed, filename):
    root, process, _ = running('rns-idle')
    output = root / 'exit'
    launcher = bridge.prepare(process.pid, installed, output)
    path = output / filename
    path.write_bytes(path.read_bytes() + b'\n')
    sys.remote_exec(process.pid, str(launcher))
    time.sleep(1.2)
    assert not (output / 'claimed-exit.json').exists()
    assert not (output / 'committed.json').exists()
    check_hooks(root, process)
