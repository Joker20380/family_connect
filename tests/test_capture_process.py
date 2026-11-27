import fcntl
import multiprocessing
import os
import signal
import socket
import time

import pytest

from control import capture_fleet as fleet
from control.capture_process import hard_deadline
from tests.test_capture_fleet import Barrier, request, setup


def worker(member, channel, other_channel, mode):
    other_channel.close()
    original = Barrier.__enter__ if mode == 'acquire' else Barrier.__exit__

    def hang(*args):
        if mode == 'acquire':
            original(*args)
        (member.root / 'callback-entered').touch()
        while True:
            time.sleep(1)

    if mode == 'acquire':
        Barrier.__enter__ = hang
    elif mode == 'snapshot':
        member.snapshot = hang
    elif mode == 'cleanup':
        Barrier.__exit__ = hang
    fleet.serve(member, channel.fileno(), channel.fileno())


@pytest.mark.parametrize('mode', ['acquire', 'snapshot', 'cleanup', 'process-death'])
def test_hanging_callbacks_and_death_release_kernel_lock_without_replay(tmp_path, mode):
    expected, members, barriers, counts, files = setup(tmp_path, seconds=1)
    member = members['OWNER']
    ready = {slot: value.run(request(value, 'HELD')) for slot, value in members.items() if slot != 'OWNER'}
    parent, child = socket.socketpair()
    process = multiprocessing.get_context('fork').Process(target=worker, args=(member, child, parent, mode))
    process.start()
    child.close()
    try:
        fleet.send(parent.fileno(), request(member, 'HELD'), time.monotonic() + .5)
        if mode != 'acquire':
            ready['OWNER'] = fleet.receive(parent.fileno(), time.monotonic() + .5)
            if mode == 'snapshot':
                fleet.send(parent.fileno(), request(member, 'CAPTURED', ready=ready), time.monotonic() + .5)
            elif mode == 'cleanup':
                fleet.send(parent.fileno(), request(member, 'HELD', changed=True), time.monotonic() + .5)
            else:
                os.kill(process.pid, signal.SIGKILL)
        process.join(3)
        assert process.exitcode == -signal.SIGKILL
        assert not (member.root / 'sealed.json').exists() and not (member.root / 'released.json').exists()
        if mode != 'process-death':
            assert (member.root / 'callback-entered').exists()
        if mode == 'cleanup':
            assert fleet.document((member.root / 'failed.json').read_bytes())['error_type'] == 'FLEET_REPLAY_CHANGED'
        with open(barriers['OWNER'].location, 'rb') as reader:
            fcntl.flock(reader, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(FileExistsError):
            fleet.Participant(expected, 'OWNER', member.signer, member.root, barriers['OWNER'], lambda: files['OWNER'])
        assert counts['OWNER'] == 0
    finally:
        if process.is_alive():
            process.kill()
            process.join(3)
        parent.close()
        for slot, value in members.items():
            if slot != 'OWNER':
                value.abort('TEST_FINISHED')


def deadline_cancelled():
    with hard_deadline(.05):
        pass
    time.sleep(.1)


def test_completed_deadline_is_disarmed():
    process = multiprocessing.get_context('fork').Process(target=deadline_cancelled)
    process.start()
    process.join(2)
    assert process.exitcode == 0


@pytest.mark.parametrize('seconds', [0, -1, 122, float('inf'), float('nan'), True])
def test_invalid_deadline_refuses(seconds):
    with pytest.raises(ValueError, match='FLEET_PROCESS_DEADLINE'):
        with hard_deadline(seconds):
            pytest.fail('invalid deadline admitted')
