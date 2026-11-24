"""Bounded same-kernel joint drain of separately owned gates; no deployment or capture permit."""
from array import array
from contextlib import contextmanager, ExitStack
from dataclasses import dataclass
import json
import math
import os
import resource
import secrets
import select
import signal
import socket
import struct
import time

from .capture_gate import GateError, require

LIMIT = 4096
NANOSECONDS = 1_000_000_000
PIN_NAMES = {'.', 'admission.lock', 'operations.lock', 'pending'}


def identity():
    return os.getpid(), os.getuid(), os.getgid()


def clock():
    info = os.stat('/proc/self/ns/time')
    return [info.st_dev, info.st_ino]


def pins(value):
    require(type(value) is dict and set(value) == PIN_NAMES, 'GROUP_PINS')
    result = {}
    for name, pair in value.items():
        require(type(pair) in (list, tuple) and len(pair) == 2 and
                all(type(number) is int and number >= 0 for number in pair) and pair[1] > 0, 'GROUP_PIN_SHAPE')
        result[name] = list(pair)
    require(len({tuple(pair) for pair in result.values()}) == len(PIN_NAMES), 'GROUP_PIN_ALIAS')
    return result


def duration(value, maximum):
    require(type(value) in (int, float) and math.isfinite(value) and 0 < value <= maximum, 'GROUP_DEADLINE')
    result = int(value * NANOSECONDS)
    require(result > 0, 'GROUP_DEADLINE')
    return result


def configure(channel):
    require(channel.family == socket.AF_UNIX and channel.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE) ==
            socket.SOCK_SEQPACKET, 'GROUP_LOCAL_CHANNEL')
    channel.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    channel.setblocking(False)


def channel_pair():
    channels = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    for channel in channels:
        configure(channel)
    return channels


def unique(entries):
    result = {}
    for name, value in entries:
        require(name not in result, 'GROUP_DUPLICATE_FIELD')
        result[name] = value
    return result


def send(channel, value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    require(len(raw) <= LIMIT, 'GROUP_MESSAGE_BOUNDS')
    require(channel.send(raw) == len(raw), 'GROUP_MESSAGE_SEND')


def receive(channel, expected):
    raw, ancillary, flags, address = channel.recvmsg(LIMIT + 1, socket.CMSG_SPACE(12), socket.MSG_CMSG_CLOEXEC)
    for level, kind, data in ancillary:
        if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
            descriptors = array('i')
            descriptors.frombytes(data[:len(data) - len(data) % descriptors.itemsize])
            for descriptor in descriptors:
                os.close(descriptor)
    require(raw and len(raw) <= LIMIT and not flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC), 'GROUP_MESSAGE_BOUNDS')
    require(len(ancillary) == 1 and ancillary[0][:2] == (socket.SOL_SOCKET, socket.SCM_CREDENTIALS) and
            len(ancillary[0][2]) == 12 and struct.unpack('iII', ancillary[0][2]) == tuple(expected), 'GROUP_PEER_IDENTITY')
    try:
        value = json.loads(raw, object_pairs_hook=unique)
    except (ValueError, UnicodeError):
        raise GateError('GROUP_MESSAGE_JSON') from None
    require(type(value) is dict, 'GROUP_MESSAGE_SHAPE')
    return value


def wait(channels, deadline):
    remaining = (deadline - time.monotonic_ns()) / NANOSECONDS
    require(remaining > 0, 'GROUP_EXPIRED')
    ready, _, _ = select.select(channels, [], [], remaining)
    require(ready, 'GROUP_EXPIRED')
    return ready


def command(channel, expected, deadline, operation=None):
    wait([channel], deadline)
    value = receive(channel, expected)
    require(set(value) == {'command', 'operation'} and type(value['operation']) is str and
            len(value['operation']) == 32 and all(character in '0123456789abcdef' for character in value['operation']),
            'GROUP_COMMAND')
    require(operation is None or value['operation'] == operation, 'GROUP_OPERATION')
    return value


def serve(gate, channel, coordinator, expected_pins, *, drain_seconds=5, hold_seconds=2, renewal=None):
    drain = duration(drain_seconds, 5)
    hold = duration(hold_seconds, 2)
    expected_pins = pins(expected_pins)
    require(gate.directory is not None and pins(gate.pins) == expected_pins, 'GROUP_GATE_BINDING')
    require(len(set(os.getresuid())) == 1 and len(set(os.getresgid())) == 1, 'GROUP_PROCESS_IDENTITY')
    require(signal.getsignal(signal.SIGALRM) == signal.SIG_DFL and
            signal.SIGALRM not in signal.pthread_sigmask(signal.SIG_BLOCK, []) and
            signal.getitimer(signal.ITIMER_REAL) == (0, 0), 'ALARM_NOT_EXCLUSIVE')
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    configure(channel)
    deadline = time.monotonic_ns() + drain + hold
    signal.setitimer(signal.ITIMER_REAL, (drain + hold) / NANOSECONDS)
    try:
        request = command(channel, coordinator, min(deadline, time.monotonic_ns() + drain))
        require(request['command'] == 'BEGIN', 'GROUP_BEGIN')
        operation = request['operation']
        with gate.drain(drain_seconds), ExitStack() as settlement:
            if renewal is not None:
                from .capture_renewal import RenewalState
                retained = settlement.enter_context(RenewalState(renewal).hold())
            held_since = time.monotonic_ns()
            expires = min(deadline, held_since + hold)
            remaining = (expires - time.monotonic_ns()) / NANOSECONDS
            require(remaining > 0, 'GROUP_EXPIRED')
            signal.setitimer(signal.ITIMER_REAL, remaining)
            common = dict(operation=operation, pins=expected_pins, clock=clock(),
                          held_since_ns=held_since, expires_ns=expires)
            send(channel, dict(status='DRAINED', **common))
            request = command(channel, coordinator, expires, operation)
            require(request['command'] == 'FINISH', 'GROUP_FINISH')
            with gate.opened():
                if renewal is not None:
                    retained.verify()
                acknowledged = time.monotonic_ns()
                require(clock() == common['clock'] and acknowledged < expires, 'GROUP_EXPIRED')
                send(channel, dict(status='HELD', acknowledged_ns=acknowledged, **common))
            request = command(channel, coordinator, expires, operation)
            require(request['command'] == 'RELEASE', 'GROUP_RELEASE')
    finally:
        channel.close()
        signal.setitimer(signal.ITIMER_REAL, 0)


@dataclass
class Participant:
    channel: socket.socket
    identity: tuple
    pins: dict


@dataclass
class Window:
    operation: str
    started_ns: int
    deadline_ns: int
    receipt: dict | None = None


def collect(participants, operation, status, deadline, expected_clock, prior=None):
    pending = {participant.channel: participant for participant in participants}
    result = {}
    while pending:
        for channel in wait(list(pending), deadline):
            participant = pending.pop(channel)
            value = receive(channel, participant.identity)
            required = {'status', 'operation', 'pins', 'clock', 'held_since_ns', 'expires_ns'}
            if status == 'HELD':
                required.add('acknowledged_ns')
            require(set(value) == required and value['status'] == status and value['operation'] == operation,
                    'GROUP_REPLY')
            require(value['clock'] == expected_clock and pins(value['pins']) == participant.pins, 'GROUP_BINDING')
            require(type(value['held_since_ns']) is int and type(value['expires_ns']) is int and
                    0 < value['held_since_ns'] <= time.monotonic_ns() < value['expires_ns'] and
                    0 < value['expires_ns'] - value['held_since_ns'] <= 2 * NANOSECONDS, 'GROUP_INTERVAL')
            if prior is not None:
                before = prior[participant.identity]
                require(all(value[name] == before[name] for name in ('held_since_ns', 'expires_ns', 'clock', 'pins')) and
                        type(value['acknowledged_ns']) is int and
                        value['held_since_ns'] <= value['acknowledged_ns'] <= time.monotonic_ns(), 'GROUP_ACK')
            result[participant.identity] = value
            deadline = min(deadline, value['expires_ns'])
    return result


@contextmanager
def joint(participants, *, drain_seconds=5, minimum_remaining_seconds=.1):
    drain = duration(drain_seconds, 5)
    minimum = duration(minimum_remaining_seconds, 2)
    require(type(participants) in (list, tuple) and 2 <= len(participants) <= 8, 'GROUP_PARTICIPANTS')
    participants = [Participant(item.channel, tuple(item.identity), pins(item.pins)) for item in participants]
    require(all(len(item.identity) == 3 and all(type(number) is int and number >= 0 for number in item.identity)
                and item.identity[0] > 0 for item in participants), 'GROUP_IDENTITIES')
    require(len({item.identity[0] for item in participants}) == len(participants) and
            len({item.channel.fileno() for item in participants}) == len(participants), 'GROUP_DUPLICATE_PARTICIPANT')
    gate_inodes = [tuple(pair) for item in participants for pair in item.pins.values()]
    require(len(set(gate_inodes)) == len(gate_inodes), 'GROUP_GATE_ALIAS')
    operation = secrets.token_hex(16)
    try:
        for participant in participants:
            configure(participant.channel)
            send(participant.channel, dict(command='BEGIN', operation=operation))
        expected_clock = clock()
        ready = collect(participants, operation, 'DRAINED', time.monotonic_ns() + drain, expected_clock)
        deadline = min(value['expires_ns'] for value in ready.values())
        started = time.monotonic_ns()
        require(deadline - started >= minimum, 'GROUP_OVERLAP_TOO_SHORT')
        window = Window(operation, started, deadline)
        yield window
        finished = time.monotonic_ns()
        require(clock() == expected_clock and started <= finished < deadline, 'GROUP_EXPIRED')
        for participant in participants:
            send(participant.channel, dict(command='FINISH', operation=operation))
        receipts = collect(participants, operation, 'HELD', deadline, expected_clock, ready)
        require(all(value['acknowledged_ns'] >= finished for value in receipts.values()), 'GROUP_FINISH_NOT_HELD')
        window.receipt = dict(status='LOCAL_INTERVAL_CONFIRMED', operation=operation, clock=expected_clock,
                              started_ns=started, finished_ns=finished, expires_ns=deadline,
                              participants=[dict(identity=list(item.identity), **receipts[item.identity]) for item in participants],
                              capture_permitted=False, all_writers_qualified=False)
    finally:
        for participant in participants:
            try:
                send(participant.channel, dict(command='RELEASE', operation=operation))
            except OSError:
                pass
            participant.channel.close()
