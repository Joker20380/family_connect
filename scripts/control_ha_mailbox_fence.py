"""Pinned in-process support admission/drain primitive, not an activation permit."""
import hashlib
import math
import os
import re
import sys
import threading
import time
import types

from scripts import control_ha_legacy_support as admission


RELAY_SHA256 = '2108e024353158b271ccce9289c3755a4b64f5f9d130d1e55ec79dac6bdff4ac'
SLOT = '_fc_support_mailbox_fence'


class AdmissionClosed(OSError):
    pass


def guarded_put(self, sender, blob):
    return _fc_support_mailbox_fence.invoke('put', self, sender, blob)


def guarded_get(self, recipient, data):
    return _fc_support_mailbox_fence.invoke('get', self, recipient, data)


def guarded_respond(self, path, data, request_id, remote_identity, requested_at):
    return _fc_support_mailbox_fence.invoke('respond', self, path, data, request_id,
                                            remote_identity, requested_at)


class SupportFence:
    def __init__(self, relay, public, generation, process):
        from messenger import relay as module
        from messenger.codec import identity, address

        admission.require(sys.version_info[:2] == (3, 14) and sys._is_gil_enabled(), 'CPYTHON_314_GIL_REQUIRED')
        admission.require(type(public) is bytes and len(public) == 64, 'SUPPORT_PUBLIC')
        admission.require(type(generation) is str and re.fullmatch('[0-9a-f]{64}', generation), 'GENERATION')
        admission.require(process == admission.binding(os.getpid()), 'PROCESS_BINDING')
        admission.require(type(relay) is module.ClosedRelay and type(relay.spool) is module.Spool, 'RELAY_SHAPE')
        admission.require(not {'respond'} & vars(relay).keys() and
                          not {'put', 'get'} & vars(relay.spool).keys(), 'INSTANCE_OVERRIDE')
        source = admission.read(module.__file__)
        admission.require(hashlib.sha256(source).hexdigest() == RELAY_SHA256, 'RELAY_SOURCE_PIN')
        for owner in (module.Spool, module.ClosedRelay):
            for value in vars(owner).values():
                if isinstance(value, staticmethod):
                    value = value.__func__
                if isinstance(value, types.FunctionType):
                    admission.code_matches(value, source, module.__file__)
        self.module, self.relay, self.spool = module, relay, relay.spool
        self.sender, self.recipient = identity(public).hash, address(public)
        self.generation, self.process = generation, dict(process)
        self.lock = threading.RLock()
        self.phase, self.denied = 'NEW', 0
        self.functions = dict(put=module.Spool.put, get=module.Spool.get, respond=module.ClosedRelay.respond)
        self.guards = dict(put=guarded_put, get=guarded_get, respond=guarded_respond)
        self.originals = {name: types.FunctionType(function.__code__, function.__globals__, function.__name__,
                                                  function.__defaults__, function.__closure__)
                          for name, function in self.functions.items()}

    def install(self):
        with self.lock:
            admission.require(self.phase == 'NEW', 'ONE_USE')
            admission.require(self.process == admission.binding(os.getpid()), 'PROCESS_BINDING')
            admission.require(hashlib.sha256(admission.read(self.module.__file__)).hexdigest() == RELAY_SHA256,
                              'RELAY_SOURCE_PIN')
            self.check_functions(self.originals)
            self.check_instances()
            admission.require(vars(self.module).setdefault(SLOT, self) is self, 'FENCE_ALREADY_PRESENT')
            self.phase = 'HELD'
            for name, function in self.functions.items():
                function.__code__ = self.guards[name].__code__
        return self

    def targeted(self, name, arguments):
        owner = arguments[0]
        if name == 'respond':
            remote = arguments[4]
            return owner is self.relay and remote is not None and remote.hash == self.sender
        return (owner is self.spool and arguments[1] ==
                (self.sender if name == 'put' else self.recipient))

    def invoke(self, name, *arguments):
        with self.lock:
            reject = self.phase == 'HELD' and self.targeted(name, arguments)
            if reject:
                self.denied += 1
        if reject:
            if name == 'respond':
                return ['unavailable'] if arguments[1] == self.module.PUT_PATH else self.module.LXMPeer.ERROR_NO_ACCESS
            raise AdmissionClosed('SUPPORT_ADMISSION_CLOSED')
        return self.originals[name](*arguments)

    def check_functions(self, expected):
        admission.require(self.module.Spool.put is self.functions['put'] and
                          self.module.Spool.get is self.functions['get'] and
                          self.module.ClosedRelay.respond is self.functions['respond'] and
                          all(function.__code__ is expected[name].__code__
                              for name, function in self.functions.items()), 'FENCE_CHANGED')

    def check_instances(self):
        admission.require(self.relay.spool is self.spool and
                          not {'respond'} & vars(self.relay).keys() and
                          not {'put', 'get'} & vars(self.spool).keys(), 'INSTANCE_OVERRIDE')
        admission.require(self.spool.db is not None and self.spool.owner is not None, 'SPOOL_CLOSED')
        expected = {self.module.RNS.Identity.truncated_hash(path.encode()): path
                    for path in (self.module.PUT_PATH, self.module.LXMPeer.MESSAGE_GET_PATH)}
        handlers = self.relay.destination.request_handlers
        admission.require(set(handlers) == set(expected), 'REQUEST_HANDLERS')
        for key, path in expected.items():
            handler = handlers[key]
            admission.require(type(handler) is list and len(handler) == 5 and handler[0] == path and
                              getattr(handler[1], '__self__', None) is self.relay and
                              getattr(handler[1], '__func__', None) is self.functions['respond'] and
                              handler[2:] == [self.module.RNS.Destination.ALLOW_ALL, None, False],
                              'REQUEST_HANDLERS')

    def validate(self):
        admission.require(self.phase == 'HELD' and vars(self.module).get(SLOT) is self, 'FENCE_NOT_HELD')
        admission.require(self.process == admission.binding(os.getpid()), 'PROCESS_BINDING')
        self.check_functions(self.guards)
        self.check_instances()

    def old_frames(self):
        count = 0
        codes = {function.__code__: name for name, function in self.originals.items()}
        for frame in sys._current_frames().values():
            while frame is not None:
                name = codes.get(frame.f_code)
                if name is not None:
                    values = frame.f_locals
                    arguments = [values.get('self')]
                    if name == 'respond':
                        arguments.extend([None, None, None, values.get('remote_identity')])
                    else:
                        arguments.append(values.get('sender' if name == 'put' else 'recipient'))
                    count += self.targeted(name, arguments)
                frame = frame.f_back
        return count

    def observe(self):
        with self.lock:
            self.validate()
            count = self.old_frames()
            return dict(generation=self.generation, phase='HELD', process=dict(self.process),
                        old_target_frames=count, in_process_drained=count == 0, denied=self.denied,
                        cross_host_bound=False, restart_protected=False, external_settlement_proven=False,
                        activation_ready=False, capture_permitted=False)

    def drain(self, seconds):
        admission.require(type(seconds) in (int, float) and math.isfinite(seconds) and 0 <= seconds <= 60,
                          'DRAIN_INTERVAL')
        deadline = time.monotonic() + seconds
        while True:
            observed = self.observe()
            if observed['in_process_drained'] or time.monotonic() >= deadline:
                return observed
            time.sleep(.01)

    def abort(self, generation):
        with self.lock:
            admission.require(generation == self.generation, 'GENERATION_MISMATCH')
            if self.phase == 'HELD':
                self.validate()
                self.phase = 'ABORTING'
                for name, function in self.functions.items():
                    function.__code__ = self.originals[name].__code__
            admission.require(self.phase in ('ABORTING', 'ABORTED'), 'ABORT_STATE')
            self.check_functions(self.originals)
            self.check_instances()
            guard_codes = {function.__code__ for function in self.guards.values()}
            for frame in sys._current_frames().values():
                while frame is not None:
                    if frame.f_code in guard_codes:
                        return False
                    frame = frame.f_back
            if self.phase == 'ABORTING':
                admission.require(vars(self.module).get(SLOT) is self, 'FENCE_CHANGED')
                delattr(self.module, SLOT)
                self.phase = 'ABORTED'
            return True
