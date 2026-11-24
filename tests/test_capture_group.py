from contextlib import contextmanager
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import threading
import time

import pytest

from control.capture_gate import Busy, GateError, initialize
from control import capture_group as group

ROOT = Path(__file__).resolve().parents[1]
GUARD = '''import json,socket,sys
sys.path.insert(0,sys.argv[1])
from control.capture_gate import Gate,GateError
from control.capture_group import serve
try:
    serve(Gate(sys.argv[2]),socket.socket(fileno=int(sys.argv[3])),json.loads(sys.argv[4]),
          json.loads(sys.argv[5]),**json.loads(sys.argv[6]))
except (OSError,ValueError):
    sys.exit(1)
'''


@contextmanager
def guards(gates, **options):
    children, participants = [], []
    try:
        for gate in gates:
            parent, child = group.channel_pair()
            process = subprocess.Popen([sys.executable, '-I', '-B', '-c', GUARD, str(ROOT), str(gate.directory),
                str(child.fileno()), json.dumps(group.identity()), json.dumps(gate.pins), json.dumps(options)],
                pass_fds=(child.fileno(),), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            child.close()
            children.append(process)
            participants.append(group.Participant(parent, (process.pid, os.getuid(), os.getgid()), gate.pins))
        yield participants, children
    finally:
        for participant in participants:
            participant.channel.close()
        for child in children:
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=2)
            assert child.stderr.read() == b''
            child.stderr.close()


@pytest.fixture
def gates(tmp_path):
    return [initialize(tmp_path / name) for name in ('console', 'publisher')]


def test_joint_interval_has_both_locks_and_final_acks(gates):
    with guards(gates) as (participants, children):
        with group.joint(participants) as window:
            assert window.receipt is None
            for gate in gates:
                with pytest.raises(Busy):
                    with gate.operation():
                        pytest.fail('writer admitted')
        receipt = window.receipt
        assert receipt['status'] == 'LOCAL_INTERVAL_CONFIRMED'
        assert receipt['capture_permitted'] is False and receipt['all_writers_qualified'] is False
        assert len(receipt['participants']) == 2
        for item in receipt['participants']:
            assert item['held_since_ns'] <= receipt['started_ns'] <= receipt['finished_ns'] <= item['acknowledged_ns']
        assert all(child.wait(timeout=2) == 0 for child in children)
    for gate in gates:
        with gate.operation():
            pass


def test_drains_previously_admitted_writer(gates):
    admitted, finish = threading.Event(), threading.Event()

    def writer():
        with gates[1].operation():
            admitted.set()
            finish.wait(3)

    thread = threading.Thread(target=writer)
    thread.start()
    assert admitted.wait(1)
    release = threading.Timer(.2, finish.set)
    release.start()
    try:
        with guards(gates) as (participants, children):
            with group.joint(participants) as window:
                assert finish.is_set()
            assert window.receipt is not None
    finally:
        finish.set()
        release.join(1)
        thread.join(2)


def test_ambiguous_marker_refuses_without_removing_it(gates):
    with gates[1].operation() as operation:
        operation.uncertain()
    original = list((gates[1].directory / 'pending').iterdir())
    with guards(gates) as (participants, children):
        with pytest.raises(OSError):
            with group.joint(participants):
                pytest.fail('uncertain participant accepted')
    assert list((gates[1].directory / 'pending').iterdir()) == original
    with gates[0].operation():
        pass


@pytest.mark.parametrize('failure', ['body', 'guard-kill', 'channel-loss', 'expiry', 'replace-lock'])
def test_no_receipt_after_incomplete_interval(gates, failure):
    with guards(gates, hold_seconds=.25 if failure == 'expiry' else 2) as (participants, children):
        window = None
        with pytest.raises((OSError, RuntimeError, ValueError)):
            with group.joint(participants, minimum_remaining_seconds=.01) as window:
                if failure == 'body':
                    raise RuntimeError('capture failed')
                if failure == 'guard-kill':
                    children[0].kill()
                    children[0].wait(timeout=2)
                if failure == 'channel-loss':
                    participants[0].channel.close()
                if failure == 'expiry':
                    time.sleep(.3)
                if failure == 'replace-lock':
                    target = gates[0].directory / 'operations.lock'
                    target.rename(target.with_suffix('.old'))
                    target.touch(mode=0o600)
        assert window is not None and window.receipt is None


@pytest.mark.parametrize('field', ['pid', 'uid', 'gid', 'pins'])
def test_bound_guard_identity_required(gates, field):
    with guards(gates) as (participants, children):
        participant = participants[0]
        if field == 'pins':
            participant.pins = dict(participant.pins, pending=(1, 12345))
        else:
            values = list(participant.identity)
            values[{'pid': 0, 'uid': 1, 'gid': 2}[field]] += 100000
            participant.identity = tuple(values)
        with pytest.raises(OSError):
            with group.joint(participants):
                pytest.fail('wrong binding accepted')


@pytest.mark.parametrize('kind', ['participant', 'gate', 'too-few', 'too-many'])
def test_duplicate_or_invalid_participant_set(gates, kind):
    with guards(gates) as (participants, children):
        if kind == 'participant':
            participants[1].identity = participants[0].identity
        elif kind == 'gate':
            participants[1].pins = participants[0].pins
        elif kind == 'too-few':
            participants = participants[:1]
        else:
            participants = participants * 5
        with pytest.raises(GateError):
            with group.joint(participants):
                pytest.fail('bad participant set')


@pytest.mark.parametrize('value', [0, -1, 6, 1e-20, float('nan'), float('inf'), True, '1'])
def test_invalid_duration(value):
    with pytest.raises(GateError):
        group.duration(value, 5)


def test_stream_socket_refused():
    parent, child = socket.socketpair()
    try:
        with pytest.raises(GateError, match='GROUP_LOCAL_CHANNEL'):
            group.configure(parent)
    finally:
        parent.close()
        child.close()


@pytest.mark.parametrize('raw', [b'[]', b'{', b'{"a":1,"a":2}', b'x' * (group.LIMIT + 2), b'\xff'])
def test_packet_shape_refuses(raw):
    parent, child = group.channel_pair()
    try:
        child.send(raw)
        with pytest.raises(GateError):
            group.receive(parent, group.identity())
    finally:
        parent.close()
        child.close()


def test_unexpected_received_file_descriptors_are_closed(tmp_path):
    parent, child = group.channel_pair()
    parent.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 0)
    with (tmp_path / 'descriptor').open('w') as source:
        before = len(list(Path('/proc/self/fd').iterdir()))
        try:
            from array import array
            child.sendmsg([b'{}'], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array('i', [source.fileno()]))])
            with pytest.raises(GateError):
                group.receive(parent, group.identity())
            assert len(list(Path('/proc/self/fd').iterdir())) == before
        finally:
            parent.close()
            child.close()


@pytest.mark.parametrize('mutation', ['nonce', 'clock', 'expired', 'future', 'phase', 'extra'])
def test_false_ready_receipts_refuse(gates, mutation):
    parent, child = group.channel_pair()
    participant = group.Participant(parent, group.identity(), group.pins(gates[0].pins))
    operation = 'a' * 32
    now = time.monotonic_ns()
    value = dict(status='DRAINED', operation=operation, pins=participant.pins, clock=group.clock(),
                 held_since_ns=now, expires_ns=now + group.NANOSECONDS)
    if mutation == 'nonce':
        value['operation'] = 'b' * 32
    elif mutation == 'clock':
        value['clock'] = [0, 1]
    elif mutation == 'expired':
        value['expires_ns'] = now - 1
    elif mutation == 'future':
        value['held_since_ns'] = now + group.NANOSECONDS
    elif mutation == 'phase':
        value['status'] = 'HELD'
    else:
        value['unexpected'] = True
    try:
        group.send(child, value)
        with pytest.raises(GateError):
            group.collect([participant], operation, 'DRAINED', now + group.NANOSECONDS, group.clock())
    finally:
        parent.close()
        child.close()


def test_different_time_drains_do_not_enter_body(gates):
    admitted, release = threading.Event(), threading.Event()

    def writer():
        with gates[1].operation():
            admitted.set()
            release.wait(3)

    thread = threading.Thread(target=writer)
    thread.start()
    assert admitted.wait(1)
    try:
        with guards(gates, hold_seconds=.15) as (participants, children):
            with pytest.raises(OSError):
                with group.joint(participants, minimum_remaining_seconds=.01):
                    pytest.fail('no common interval')
            release.set()
    finally:
        release.set()
        thread.join(2)


def test_insufficient_remaining_overlap_refuses(gates):
    with guards(gates) as (participants, children):
        with pytest.raises(GateError, match='GROUP_OVERLAP_TOO_SHORT'):
            with group.joint(participants, minimum_remaining_seconds=2):
                pytest.fail('insufficient interval accepted')


def test_failure_does_not_release_another_boundary(gates):
    with gates[0].drain(.1):
        with guards(gates) as (participants, children):
            with pytest.raises(OSError):
                with group.joint(participants):
                    pytest.fail('occupied gate accepted')
        with pytest.raises(Busy):
            with gates[0].operation():
                pytest.fail('unrelated lock released')


@pytest.mark.parametrize('field', ['operation', 'acknowledged_ns', 'expires_ns', 'held_since_ns', 'pins'])
def test_final_ack_must_match_initial_hold(gates, monkeypatch, field):
    receive = group.receive

    def changed(channel, expected):
        value = receive(channel, expected)
        if value['status'] == 'HELD':
            if field == 'operation':
                value[field] = 'b' * 32
            elif field == 'acknowledged_ns':
                value[field] = 0
            elif field == 'pins':
                value[field]['pending'][1] += 1
            else:
                value[field] -= 1
        return value

    monkeypatch.setattr(group, 'receive', changed)
    with guards(gates) as (participants, children):
        with pytest.raises(GateError):
            with group.joint(participants) as window:
                pass
        assert window.receipt is None


def test_time_namespace_change_refuses_completion(gates, monkeypatch):
    with guards(gates) as (participants, children):
        with pytest.raises(GateError, match='GROUP_EXPIRED'):
            with group.joint(participants) as window:
                monkeypatch.setattr(group, 'clock', lambda: [0, 1])
        assert window.receipt is None


def test_wrong_initial_command_does_not_acquire_gate(gates):
    with guards(gates[:1]) as (participants, children):
        group.send(participants[0].channel, dict(command='FINISH', operation='a' * 32))
        assert children[0].wait(timeout=2) == 1
    with gates[0].operation():
        pass
