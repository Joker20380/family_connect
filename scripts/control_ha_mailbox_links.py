"""Process-lifetime RNS lineage fence; local opening is not a cross-host commit."""
import hashlib
import importlib
import sys
import threading
import types
import weakref

from scripts import control_ha_legacy_support as admission
from scripts.control_ha_mailbox_fence import AdmissionClosed, SupportFence


LINK_SHA256 = 'd1ffccda72963bfe910799b62e363fecdbd45bb5038c81ee857beccdcf3c2da1'
SLOT = '_fc_support_link_fence'


def guarded_init(self, destination=None, established_callback=None, closed_callback=None, owner=None,
                 peer_pub_bytes=None, peer_sig_pub_bytes=None, mode=1):
    return _fc_support_link_fence.birth(self, destination, established_callback, closed_callback,
                                      owner, peer_pub_bytes, peer_sig_pub_bytes, mode)


class SupportLinkFence(SupportFence):
    def __init__(self, relay, public, generation, process):
        super().__init__(relay, public, generation, process)
        self.link_module = importlib.import_module('RNS.Link')
        self.link_class = self.module.RNS.Link
        source = admission.read(self.link_module.__file__)
        admission.require(hashlib.sha256(source).hexdigest() == LINK_SHA256, 'LINK_SOURCE_PIN')
        self.link_functions = {}
        for name, value in vars(self.link_class).items():
            function = value.__func__ if isinstance(value, staticmethod) else value
            if isinstance(function, types.FunctionType):
                admission.code_matches(function, source, self.link_module.__file__)
                self.link_functions[name] = (value, function, function.__code__)
        constructor = self.link_class.__init__
        admission.require(constructor.__defaults__ == guarded_init.__defaults__ and
                          constructor.__closure__ is None, 'LINK_CONSTRUCTOR_SHAPE')
        self.constructor = types.FunctionType(constructor.__code__, constructor.__globals__,
                                              constructor.__name__, constructor.__defaults__)
        self.links = weakref.WeakKeyDictionary()
        self.epoch = None
        self.context = threading.local()
        self.admitted = set()
        self.opened = False
        self.sealed = False

    def check_links(self, installed):
        admission.require(self.module.RNS.Link is self.link_class and
                          self.link_module.Link is self.link_class, 'LINK_CLASS_CHANGED')
        for name, (value, function, code) in self.link_functions.items():
            expected = guarded_init.__code__ if installed and name == '__init__' else code
            admission.require(vars(self.link_class).get(name) is value and function.__code__ is expected,
                              'LINK_CODE_CHANGED')
        if installed:
            admission.require(vars(self.link_module).get(SLOT) is self, 'LINK_FENCE_CHANGED')

    def install(self):
        with self.lock:
            self.check_links(False)
            admission.require(SLOT not in vars(self.link_module), 'LINK_FENCE_ALREADY_PRESENT')
            admission.require(hashlib.sha256(admission.read(self.link_module.__file__)).hexdigest() == LINK_SHA256,
                              'LINK_SOURCE_PIN')
            super().install()
            setattr(self.link_module, SLOT, self)
            self.link_class.__init__.__code__ = guarded_init.__code__
        return self

    def birth(self, link, *arguments):
        with self.lock:
            epoch = self.epoch
        result = self.constructor(link, *arguments)
        with self.lock:
            self.links[link] = epoch
        return result

    def native_link(self, arguments):
        frame = sys._getframe(1)
        try:
            while frame is not None:
                if frame.f_code is self.link_functions['handle_request'][2]:
                    values = frame.f_locals
                    link = values.get('self')
                    if (type(link) is self.link_class and link.owner is self.relay.destination and
                            link.destination is self.relay.destination and link.initiator is False and
                            link.status == self.link_class.ACTIVE and self.epoch is not None and
                            self.links.get(link) is self.epoch and
                            getattr(link, '_Link__remote_identity', None) is arguments[4] and
                            values.get('path') == arguments[1] and values.get('request_data') is arguments[2] and
                            values.get('request_id') == arguments[3]):
                        return link
                    return None
                frame = frame.f_back
            return None
        finally:
            del frame

    def invoke(self, name, *arguments):
        token = None
        with self.lock:
            target = self.targeted(name, arguments)
            link = None
            reject = False
            if target and self.phase == 'HELD':
                if name == 'respond':
                    link = self.native_link(arguments)
                    reject = link is None
                else:
                    link = getattr(self.context, 'link', None)
                    reject = link is None or getattr(self.context, 'token', None) not in self.admitted
                if reject:
                    self.denied += 1
                elif name == 'respond':
                    token = object()
                    self.admitted.add(token)
        if reject:
            if name == 'respond':
                return ['unavailable'] if arguments[1] == self.module.PUT_PATH else self.module.LXMPeer.ERROR_NO_ACCESS
            raise AdmissionClosed('SUPPORT_LINK_GENERATION_CLOSED')
        if name != 'respond' or not target:
            return self.originals[name](*arguments)
        previous = getattr(self.context, 'link', None)
        previous_token = getattr(self.context, 'token', None)
        self.context.link = link
        self.context.token = token
        try:
            return self.originals[name](*arguments)
        finally:
            self.context.link = previous
            self.context.token = previous_token
            with self.lock:
                self.admitted.discard(token)

    def validate(self):
        super().validate()
        self.check_links(True)

    def observe(self):
        with self.lock:
            result = super().observe()
            result.update(new_link_admission='CLOSED' if self.epoch is None else 'OPEN_LOCAL_ONLY',
                          old_links_excluded=True, direct_support_writes_closed=True,
                          process_lifetime_guard_required=self.opened,
                          accepted_target_work=len(self.admitted), opening_invalidated=self.sealed,
                          in_process_drained=result['in_process_drained'] and not self.admitted)
            return result

    def open_after_local_drain(self, generation):
        with self.lock:
            admission.require(generation == self.generation, 'GENERATION_MISMATCH')
            self.validate()
            admission.require(not self.opened and not self.sealed, 'ONE_OPEN_ONLY')
            admission.require(self.old_frames() == 0, 'OLD_WORK_NOT_DRAINED')
            admission.require(hashlib.sha256(admission.read(self.link_module.__file__)).hexdigest() == LINK_SHA256,
                              'LINK_SOURCE_PIN')
            self.epoch = object()
            self.opened = True
            return self.observe()

    def reclose(self, generation):
        with self.lock:
            admission.require(generation == self.generation, 'GENERATION_MISMATCH')
            self.validate()
            self.epoch = None
            self.sealed = True
            return self.observe()

    def abort(self, generation):
        with self.lock:
            admission.require(generation == self.generation, 'GENERATION_MISMATCH')
            admission.require(not self.opened and not self.sealed, 'OPEN_LINEAGE_REQUIRES_GUARD')
            if self.phase == 'HELD':
                self.validate()
            elif self.phase in ('ABORTING', 'ABORTED'):
                self.check_links(False)
            else:
                admission.require(False, 'ABORT_STATE')
            restored = super().abort(generation)
            self.link_class.__init__.__code__ = self.constructor.__code__
            for frame in sys._current_frames().values():
                while frame is not None:
                    if frame.f_code is guarded_init.__code__:
                        return False
                    frame = frame.f_back
            if vars(self.link_module).get(SLOT) is self:
                delattr(self.link_module, SLOT)
            return restored
