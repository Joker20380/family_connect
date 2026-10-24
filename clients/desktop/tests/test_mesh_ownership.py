import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import threading
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'linux'))
from mesh_ownership import Ownership, OwnershipError
import mesh_service

pytestmark = pytest.mark.skipif(os.geteuid() != 0, reason='actual root-owned cross-process admission required')


@pytest.fixture
def directory():
    with tempfile.TemporaryDirectory(prefix='fc-l02-admission-', dir='/run') as root:
        yield Path(root) / 'owner'


@pytest.fixture
def native(monkeypatch):
    binary = os.environ.get('FC_TEST_MESH_WORKER')
    if not binary:
        pytest.skip('current native worker required')
    monkeypatch.setattr(mesh_service, 'WORKER', binary)
    return binary


def line(process):
    assert select.select([process.stdout], [], [], 10)[0], 'peer did not complete admission/cleanup'
    value = process.stdout.readline().decode().strip()
    assert value, process.stderr.read().decode()
    return value


PEER = '''
import sys, threading, time
from pathlib import Path
from mesh_ownership import Ownership
import mesh_service
mesh_service.WORKER = sys.argv[2]
gate = Ownership('vpn', Path(sys.argv[1]))
gate.acquire(threading.Event(), time.monotonic() + 15)
worker = mesh_service.NativeWorker(gate)
assert worker.call('status')['state'] == 'DISCONNECTED'
print(worker.process.pid, flush=True)
assert sys.stdin.readline().strip() == 'release'
worker.close()
gate.finish()
print('cleaned', flush=True)
'''


def test_real_workers_admission_handoff_requires_exit_and_cleanup(directory, native):
    baseline = set(os.listdir('/sys/class/net'))
    descriptors = set(os.listdir('/proc/self/fd'))
    threads = set(threading.enumerate())
    chat = Ownership('chat', directory)
    chat.acquire(threading.Event(), time.monotonic() + 2)
    worker = mesh_service.NativeWorker(chat)
    old_pid = worker.process.pid
    environment = dict(os.environ, PYTHONPATH=str(Path(mesh_service.__file__).parent) + os.pathsep + os.getcwd())
    peer = subprocess.Popen([sys.executable, '-c', PEER, str(directory), native], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment)
    try:
        deadline = time.monotonic() + 5
        while not chat.preempted():
            assert time.monotonic() < deadline
            time.sleep(.01)
        assert not select.select([peer.stdout], [], [], .05)[0]
        worker.close()
        assert worker.process.returncode == 0 and not Path('/proc', str(old_pid)).exists()
        assert not select.select([peer.stdout], [], [], .05)[0]
        chat.finish()
        vpn_pid = int(line(peer))
        assert vpn_pid != old_pid and Path('/proc', str(vpn_pid)).exists()
        with pytest.raises(OwnershipError, match='VPN_RESERVED'):
            Ownership('chat', directory).acquire(threading.Event(), time.monotonic() + 2)
        peer.stdin.write(b'release\n')
        peer.stdin.flush()
        assert line(peer) == 'cleaned'
        assert peer.wait(5) == 0 and not Path('/proc', str(vpn_pid)).exists()
        resumed = Ownership('chat', directory)
        resumed.acquire(threading.Event(), time.monotonic() + 2)
        next_worker = mesh_service.NativeWorker(resumed)
        try:
            assert next_worker.call('status')['state'] == 'DISCONNECTED'
        finally:
            next_worker.close()
            resumed.finish()
        assert set(os.listdir('/sys/class/net')) == baseline
        assert not (directory / 'transport.lock').read_bytes()
    finally:
        if peer.poll() is None:
            peer.stdin.write(b'release\n')
            peer.stdin.flush()
            try:
                peer.wait(20)
            except subprocess.TimeoutExpired:
                peer.kill()
                peer.wait(5)
        for channel in (peer.stdin, peer.stdout, peer.stderr):
            channel.close()
        if worker.process.poll() is None:
            worker.close()
        chat.close()
    assert set(os.listdir('/proc/self/fd')) == descriptors
    assert set(threading.enumerate()) == threads


def test_inherited_lock_and_unconfirmed_cleanup_never_admit_replacement(directory, native):
    gate = Ownership('chat', directory)
    gate.acquire(threading.Event(), time.monotonic() + 2)
    worker = mesh_service.NativeWorker(gate)
    gate.close()
    try:
        with pytest.raises(OwnershipError, match='OWNER_BUSY'):
            Ownership('chat', directory).acquire(threading.Event(), time.monotonic() + 1)
    finally:
        worker.close()
    for role in ('chat', 'vpn'):
        with pytest.raises(OwnershipError, match='CLEANUP_UNCONFIRMED'):
            Ownership(role, directory).acquire(threading.Event(), time.monotonic() + 1)


def test_cancelled_reservation_does_not_clear_previous_generation(directory):
    gate = Ownership('chat', directory)
    gate.acquire(threading.Event(), time.monotonic() + 1)
    cancelled = threading.Event()
    cancelled.set()
    try:
        with pytest.raises(OwnershipError, match='ADMISSION_CANCELLED'):
            Ownership('vpn', directory).acquire(cancelled, time.monotonic() + 1)
        assert (directory / 'transport.lock').read_bytes() == b'chat'
        assert not gate.preempted()
    finally:
        gate.finish()


def test_umask_and_unsafe_ownership_paths(directory):
    mask = os.umask(0o077)
    try:
        gate = Ownership('chat', directory)
        gate.acquire(threading.Event(), time.monotonic() + 1)
        assert directory.stat().st_mode & 0o777 == 0o711
        assert (directory / 'transport.lock').stat().st_mode & 0o777 == 0o600
        gate.finish()
    finally:
        os.umask(mask)
    directory.chmod(0o777)
    with pytest.raises(OwnershipError, match='UNSAFE_OWNERSHIP'):
        Ownership('chat', directory).acquire(threading.Event(), time.monotonic() + 1)


@pytest.mark.parametrize('kind', ['symlink', 'hardlink', 'mode'])
def test_lock_injection_is_rejected(directory, kind):
    directory.mkdir(mode=0o700)
    target = directory / 'vpn.lock'
    other = directory / 'other'
    other.write_bytes(b'')
    other.chmod(0o600)
    if kind == 'symlink':
        target.symlink_to(other)
    elif kind == 'hardlink':
        os.link(other, target)
    else:
        target.write_bytes(b'')
        target.chmod(0o644)
    with pytest.raises((OwnershipError, OSError)):
        Ownership('vpn', directory).acquire(threading.Event(), time.monotonic() + 1)
