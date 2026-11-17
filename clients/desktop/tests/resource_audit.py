"""Test-scoped socket/thread ownership, with bounded, payload-free diagnostics."""
from collections import deque
from contextlib import contextmanager
import json
import os
import socket
import stat
import sys
import threading
import weakref

import pytest


def descriptor_snapshot():
    result = {}
    for name in os.listdir('/proc/self/fd'):
        descriptor = int(name)
        try:
            metadata = os.fstat(descriptor)
            target = os.readlink(f'/proc/self/fd/{descriptor}')
        except OSError:
            continue
        kind = stat.S_IFMT(metadata.st_mode)
        purpose = target if target.startswith(('socket:[', 'pipe:[')) else stat.filemode(metadata.st_mode)[0]
        result[descriptor] = (metadata.st_dev, metadata.st_ino, kind, purpose)
    return result


class ResourceAudit:
    def __init__(self):
        self.lock = threading.RLock()
        self.threads = {threading.current_thread()}
        self.records = []
        self.events = deque(maxlen=256)
        self.protected = []
        self.violations = []
        self.patch = pytest.MonkeyPatch()

    def event(self, action, **values):
        with self.lock:
            self.events.append(dict(action=action, thread=threading.current_thread().name, **values))

    def checkpoint(self, boundary):
        self.event('boundary', boundary=boundary, descriptors=descriptor_snapshot())

    def __enter__(self):
        original_init = socket.socket.__init__
        original_close = socket.socket.close
        original_detach = socket.socket.detach
        original_start = threading.Thread.start

        def start(thread, *args, **kwargs):
            with self.lock:
                if threading.current_thread() in self.threads:
                    self.threads.add(thread)
            return original_start(thread, *args, **kwargs)

        def initialize(channel, *args, **kwargs):
            original_init(channel, *args, **kwargs)
            with self.lock:
                if threading.current_thread() not in self.threads:
                    return
                assert len(self.records) < 1024, 'socket audit capacity exceeded'
                descriptor = channel.fileno()
                identity = descriptor_snapshot()[descriptor]
                number = len(self.records)
                caller = sys._getframe(1)
                owner = f'{caller.f_globals.get("__name__")}.{caller.f_code.co_name}'
                reference = weakref.ref(channel, lambda _: self.event('finalized', resource=number))
                self.records.append((reference, identity, descriptor))
                self.event('acquired', resource=number, descriptor=descriptor, identity=identity, owner=owner)

        def closed(channel, operation, original, *args, **kwargs):
            with self.lock:
                descriptor = channel.fileno()
                for guarded, label in self.protected:
                    if guarded is channel and descriptor >= 0:
                        self.violations.append(f'premature {operation}: {label}')
                owned = [number for number, (reference, _, _) in enumerate(self.records) if reference() is channel]
                self.event(operation, descriptor=descriptor, resources=owned)
            return original(channel, *args, **kwargs)

        self.patch.setattr(threading.Thread, 'start', start)
        self.patch.setattr(socket.socket, '__init__', initialize)
        self.patch.setattr(socket.socket, 'close', lambda channel, *args, **kwargs: closed(channel, 'close', original_close, *args, **kwargs))
        self.patch.setattr(socket.socket, 'detach', lambda channel, *args, **kwargs: closed(channel, 'detach', original_detach, *args, **kwargs))
        self.checkpoint('audit-entry')
        return self

    @contextmanager
    def keep_alive(self, channel, label):
        identity = descriptor_snapshot()[channel.fileno()]
        guard = (channel, label)
        self.protected.append(guard)
        try:
            yield
        finally:
            self.protected.remove(guard)
            if descriptor_snapshot().get(channel.fileno()) != identity:
                self.violations.append(f'premature release: {label}')

    def verify(self):
        snapshot = descriptor_snapshot()
        with self.lock:
            failures = list(self.violations)
            for number, (reference, identity, descriptor) in enumerate(self.records):
                channel = reference()
                remaining = [current for current, value in snapshot.items() if value == identity]
                if remaining or (channel is not None and channel.fileno() >= 0):
                    failures.append(f'owned socket {number} acquired fd={descriptor} remains at {remaining}')
            alive = sorted(thread.name for thread in self.threads if thread is not threading.current_thread() and thread.is_alive())
            if alive:
                failures.append(f'owned threads remain: {alive}')
        assert not failures, '\n'.join(failures) + '\n' + json.dumps(list(self.events), sort_keys=True)

    def __exit__(self, *exception):
        try:
            self.checkpoint('audit-exit')
            self.verify()
        finally:
            self.patch.undo()


def boundary(request, label):
    audit = getattr(request.node, '_public_resource_audit', None)
    if audit is not None:
        audit.checkpoint(label)
