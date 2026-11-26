"""Manifest-required startup fencing; local qualification tickets are not OWNER exit proof."""
import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import re
import secrets
import signal
import stat
import sys
import threading
import types

from scripts import control_ha_legacy_support as admission
from scripts.control_ha_mailbox_fence import RELAY_SHA256
from scripts.control_ha_mailbox_links import SupportLinkFence


SERVER_SHA256 = '01c4d94b9bce9b7137c4f9cc25eba3046bd57ac41f81ff683ad317a6b323077c'
TRANSPORT_SHA256 = '97224d31475741e2d943779ce497853140344f5c9898afcaa9b87ddc937b2340'
DESTINATION_SHA256 = '7db80f04e8bac330d1c8a8e57f33c49b7df99798f54c74aae3e2d8e5b3bffbde'
CREATION = threading.RLock()
ACTIVE = None


def control_wakeup(signum, frame):
    pass


def arm_control_wakeup(directory):
    directory = Path(directory)
    admission.require(directory.is_absolute() and directory.is_dir() and not directory.is_symlink() and
                      directory.stat().st_uid == os.geteuid() and not directory.stat().st_mode & 0o077,
                      'CONTROL_WAKEUP_DIRECTORY')
    admission.require(threading.current_thread() is threading.main_thread() and
                      signal.getsignal(signal.SIGUSR1) in (signal.SIG_DFL, control_wakeup), 'CONTROL_WAKEUP_HANDLER')
    signal.signal(signal.SIGUSR1, control_wakeup)
    process = admission.binding(os.getpid())
    path = directory / (str(process['pid']) + '-' + process['start'] + '.json')
    value = dict(schema=1, process=process, signal=int(signal.SIGUSR1))
    if path.exists():
        admission.require(json.loads(owned(path, os.geteuid())) == value, 'CONTROL_WAKEUP_CHANGED')
    else:
        admission.write(path, value)


def fixture_scope(manifest, unit):
    manifest = Path(manifest).absolute()
    return (re.fullmatch('fc-ha-mailbox-handoff-fixture-[0-9a-f]{32}\\.service', unit) is not None and
            manifest.parent == Path('/opt/apps/family_connect/state-ha02') / unit.removesuffix('.service') and
            re.fullmatch('manifest(?:-[0-9a-f]{64})?\\.json', manifest.name) is not None)


def unique(pairs):
    result = {}
    for key, value in pairs:
        admission.require(key not in result, 'DUPLICATE_FIELD')
        result[key] = value
    return result


def owned(path, owner_uid):
    path = Path(path).absolute()
    for parent in path.parents:
        info = parent.lstat()
        admission.require(stat.S_ISDIR(info.st_mode) and info.st_uid in (0, owner_uid) and
                          (not info.st_mode & 0o022 or info.st_uid == 0 and info.st_mode & stat.S_ISVTX),
                          'UNSAFE_CONTROL_PARENT')
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as source:
        before = os.fstat(source.fileno())
        admission.require(stat.S_ISREG(before.st_mode) and before.st_uid == owner_uid and
                          before.st_nlink == 1 and not before.st_mode & 0o022, 'UNSAFE_CONTROL_FILE')
        raw = source.read(16385)
        after = os.fstat(source.fileno())
    admission.require(len(raw) <= 16384 and
                      (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                      (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'CONTROL_READ_CHANGED')
    return raw


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def pinned_class(owner, expected):
    filename = inspect.getfile(owner)
    source = admission.read(filename)
    admission.require(hashlib.sha256(source).hexdigest() == expected, 'STARTUP_SOURCE_PIN')
    for value in vars(owner).values():
        function = value.__func__ if isinstance(value, staticmethod) else value
        if isinstance(function, types.FunctionType):
            admission.code_matches(function, source, filename)


class PersistentLinkFence(SupportLinkFence):
    def abort(self, generation):
        raise ValueError('MANIFEST_REQUIRES_FENCE')


class Startup:
    def __init__(self, manifest, *, owner_uid=0, fixture=False, control_ready=None):
        self.path = Path(manifest).absolute()
        self.owner_uid = owner_uid
        self.control_ready = control_ready
        self.fixture = owner_uid != 0
        if fixture:
            unit = self.path.parent.name + '.service'
            admission.require(owner_uid == 0 and fixture_scope(self.path, unit) and
                              any(line.rsplit('/', 1)[-1] == unit for line in
                                  Path('/proc/self/cgroup').read_text().splitlines()), 'ROOT_FIXTURE_SCOPE')
            self.fixture = True
        raw = owned(self.path, owner_uid)
        self.manifest = json.loads(raw, object_pairs_hook=unique)
        admission.require(type(self.manifest) is dict and set(self.manifest) ==
                          {'schema', 'generation', 'support_public', 'owner_binding_sha256', 'replacement_plan_sha256'},
                          'MANIFEST_SHAPE')
        admission.require(type(self.manifest['schema']) is int and self.manifest['schema'] == 1, 'MANIFEST_SCHEMA')
        for name in ('generation', 'owner_binding_sha256', 'replacement_plan_sha256'):
            admission.require(type(self.manifest[name]) is str and re.fullmatch('[0-9a-f]{64}', self.manifest[name]),
                              'MANIFEST_DIGEST')
        public = self.manifest['support_public']
        admission.require(type(public) is str and re.fullmatch('[0-9a-f]{128}', public), 'MANIFEST_PUBLIC')
        self.digest = hashlib.sha256(raw).hexdigest()
        self.process = admission.binding(os.getpid())
        self.challenge = secrets.token_hex(32)
        self.fence = None
        self.published = False
        self.used = False
        self.consumed = None
        self.seal = self.path.with_suffix('.reclosed.json')
        self.adopted = False

    def unchanged(self):
        admission.require(hashlib.sha256(owned(self.path, self.owner_uid)).hexdigest() == self.digest,
                          'MANIFEST_CHANGED')
        admission.require(admission.binding(os.getpid()) == self.process, 'STARTUP_PROCESS_CHANGED')

    def ticket(self):
        self.unchanged()
        return dict(schema=1, generation=self.manifest['generation'], manifest_sha256=self.digest,
                    support_public_sha256=hashlib.sha256(bytes.fromhex(self.manifest['support_public'])).hexdigest(),
                    process=dict(self.process), challenge=self.challenge,
                    owner_binding_sha256=self.manifest['owner_binding_sha256'],
                    replacement_plan_sha256=self.manifest['replacement_plan_sha256'])

    def create(self, relay_identity, spool, *, allowed_public, membership=None):
        import RNS
        from messenger import relay as native

        with CREATION:
            admission.require(not self.used, 'ONE_STARTUP_ONLY')
            self.used = True
            self.unchanged()
            for owner, expected in ((native.ClosedRelay, RELAY_SHA256), (native.Spool, RELAY_SHA256),
                                    (RNS.Destination, DESTINATION_SHA256)):
                pinned_class(owner, expected)
            filename = inspect.getfile(RNS.Transport)
            source = admission.read(filename)
            admission.require(hashlib.sha256(source).hexdigest() == TRANSPORT_SHA256, 'TRANSPORT_SOURCE_PIN')
            registration = RNS.Transport.register_destination
            admission.code_matches(registration, source, filename)
            descriptor = vars(RNS.Transport)['register_destination']
            admission.require(isinstance(descriptor, staticmethod), 'REGISTRATION_SHAPE')
            expected_hash = RNS.Destination.hash(relay_identity, 'lxmf', 'propagation')
            admission.require(not any(destination.hash == expected_hash for destination in RNS.Transport.destinations)
                              and expected_hash not in RNS.Transport.destinations_map, 'DESTINATION_ALREADY_PUBLIC')
            captured = []
            creator = threading.get_ident()

            def defer(destination):
                if destination.hash != expected_hash or destination.direction != RNS.Destination.IN:
                    return registration(destination)
                admission.require(threading.get_ident() == creator and not captured and
                                  destination.identity is relay_identity, 'UNEXPECTED_REGISTRATION')
                captured.append(destination)

            replacement = staticmethod(defer)
            RNS.Transport.register_destination = replacement
            try:
                relay = native.ClosedRelay(relay_identity, spool, allowed_public=allowed_public, membership=membership)
                admission.require(captured == [relay.destination] and
                                  all(destination is not relay.destination for destination in RNS.Transport.destinations)
                                  and expected_hash not in RNS.Transport.destinations_map, 'PREMATURE_PUBLICATION')
                self.fence = PersistentLinkFence(relay, bytes.fromhex(self.manifest['support_public']),
                                                 self.manifest['generation'], self.process).install()
                if self.seal.exists() or self.seal.is_symlink():
                    self.check_seal()
                    self.fence.reclose(self.manifest['generation'])
                self.unchanged()
                admission.require(self.fence.observe()['new_link_admission'] == 'CLOSED', 'STARTUP_NOT_CLOSED')
            finally:
                admission.require(vars(RNS.Transport)['register_destination'] is replacement, 'REGISTRATION_CHANGED')
                RNS.Transport.register_destination = descriptor
            registration(relay.destination)
            self.published = True
            if self.control_ready is not None:
                arm_control_wakeup(self.control_ready)
            return relay

    def observe(self):
        ticket = self.ticket()
        admission.require(self.published and self.fence is not None, 'STARTUP_NOT_PUBLISHED')
        return dict(ticket=ticket, ticket_sha256=hashlib.sha256(encoded(ticket)).hexdigest(),
                    root_owned_manifest=self.owner_uid == 0, closed_before_publication=not self.adopted,
                    restart_defaults_closed=not self.adopted, live_adoption=self.adopted, fence=self.fence.observe(),
                    owner_exit_verified=False, installed_unit_verified=False, activation_ready=False,
                    capture_permitted=False, consumed=self.consumed)

    def adopt(self, relay):
        import RNS
        from messenger import relay as native
        with CREATION:
            admission.require(not self.used, 'ONE_STARTUP_ONLY')
            self.unchanged()
            for owner, expected in ((native.ClosedRelay, RELAY_SHA256), (native.Spool, RELAY_SHA256),
                                    (RNS.Destination, DESTINATION_SHA256)):
                pinned_class(owner, expected)
            admission.require(type(relay) is native.ClosedRelay and
                              RNS.Transport.destinations_map.get(relay.destination.hash) is relay.destination and
                              relay.destination in RNS.Transport.destinations, 'ADOPTION_DESTINATION')
            self.used = True
            self.adopted = True
            self.fence = PersistentLinkFence(relay, bytes.fromhex(self.manifest['support_public']),
                                             self.manifest['generation'], self.process).install()
            if self.seal.exists() or self.seal.is_symlink():
                self.check_seal()
                self.fence.reclose(self.manifest['generation'])
            self.published = True
            if self.control_ready is not None:
                arm_control_wakeup(self.control_ready)
            return self.observe()

    def check_seal(self):
        seal = json.loads(owned(self.seal, self.owner_uid), object_pairs_hook=unique)
        admission.require(seal == dict(schema=1, generation=self.manifest['generation'],
                                      manifest_sha256=self.digest, opening_invalidated=True), 'RECLOSURE_SEAL')

    def consume(self, request):
        admission.require(self.fence is not None and self.published, 'STARTUP_NOT_PUBLISHED')
        raw = owned(request, self.owner_uid)
        value = json.loads(raw, object_pairs_hook=unique)
        admission.require(type(value) is dict and set(value) == {'action', 'ticket', 'witness', 'reservation'} and
                          value['action'] == 'OWNER_HANDOFF', 'HANDOFF_REQUEST')
        with self.fence.lock:
            admission.require(encoded(value['ticket']) == encoded(self.ticket()), 'STALE_OR_UNBOUND_TICKET')
            admission.require(not self.seal.exists() and not self.seal.is_symlink() and not self.fence.sealed,
                              'OPENING_INVALIDATED')
            request_sha = hashlib.sha256(encoded(value)).hexdigest()
            if self.consumed is not None:
                admission.require(self.consumed['request_sha256'] == request_sha, 'WITNESS_ALREADY_CONSUMED')
                return self.observe()
            ticket, witness, reservation = value['ticket'], value['witness'], value['reservation']
            sha = lambda item: hashlib.sha256(encoded(item)).hexdigest()
            admission.require(type(witness) is dict and type(witness.get('schema')) is int and witness.get('schema') == 1 and
                              witness.get('result') == 'OWNER_REPLACEMENT_SAMPLED' and
                              witness.get('owner_exit_verified') is True and
                              witness.get('independent_controller') is True and
                              witness.get('legacy_uncertainty_preserved') is True and
                              witness.get('rollback_requires_mailbox_reclosure') is True and
                              witness.get('opening_permitted') is False and witness.get('capture_permitted') is False,
                              'OWNER_EXIT_WITNESS')
            admission.require(witness.get('fixture') is self.fixture and
                              witness.get('controller_uid') == self.owner_uid, 'WITNESS_AUTHORITY')
            admission.require(witness.get('ticket_sha256') == sha(ticket) and
                              witness.get('plan_sha256') == ticket['replacement_plan_sha256'] and
                              sha(witness.get('old_binding')) == ticket['owner_binding_sha256'], 'WITNESS_BINDING')
            admission.require(type(reservation) is dict and set(reservation) == {
                'schema', 'ticket_sha256', 'plan_sha256', 'accepted_sha256', 'opening_permitted', 'capture_permitted'}
                and type(reservation.get('schema')) is int and reservation.get('schema') == 1 and
                reservation.get('ticket_sha256') == sha(ticket) and
                reservation.get('plan_sha256') == ticket['replacement_plan_sha256'] and
                reservation.get('accepted_sha256') == witness.get('accepted_sha256') and
                reservation.get('opening_permitted') is False and reservation.get('capture_permitted') is False and
                sha(reservation) == witness.get('reservation_sha256'), 'RESERVATION_BINDING')
            admission.require(witness.get('archive_sha256') ==
                              '621009b8df9baffb81e0d9069cfa52b3781e7dd7bf4e435dd89740e38cae5739',
                              'CANDIDATE_ARCHIVE')
            self.fence.open_after_local_drain(self.manifest['generation'])
            self.consumed = dict(request_sha256=request_sha, witness_sha256=sha(witness),
                                 reservation_sha256=sha(reservation), ticket_sha256=sha(ticket))
            return self.observe()

    def reclose(self, request):
        value = json.loads(owned(request, self.owner_uid), object_pairs_hook=unique)
        admission.require(value == dict(action='RECLOSE', ticket=self.ticket()), 'STALE_OR_UNBOUND_TICKET')
        self.check_seal()
        admission.require(self.fence is not None and self.published, 'STARTUP_NOT_PUBLISHED')
        self.fence.reclose(self.manifest['generation'])
        return self.observe()

    def open_for_qualification(self, request):
        admission.require(self.fence is not None and self.published, 'STARTUP_NOT_PUBLISHED')
        with self.fence.lock:
            value = json.loads(owned(request, self.owner_uid), object_pairs_hook=unique)
            admission.require(encoded(value) == encoded(dict(action='LOCAL_QUALIFICATION_ONLY', ticket=self.ticket())),
                              'STALE_OR_UNBOUND_TICKET')
            self.fence.open_after_local_drain(self.manifest['generation'])
            return self.observe()


def main():
    global ACTIVE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--control-ready', type=Path)
    parser.add_argument('server_arguments', nargs=argparse.REMAINDER)
    arguments = parser.parse_args()
    startup = Startup(arguments.manifest, control_ready=arguments.control_ready)
    from messenger import server
    source = admission.read(server.__file__)
    admission.require(hashlib.sha256(source).hexdigest() == SERVER_SHA256, 'SERVER_SOURCE_PIN')
    admission.code_matches(server.main, source, server.__file__)
    native = server.ClosedRelay
    ACTIVE = startup
    server.ClosedRelay = startup.create
    previous = sys.argv
    options = arguments.server_arguments
    sys.argv = [server.__file__, *(options[1:] if options[:1] == ['--'] else options)]
    try:
        server.main()
    finally:
        sys.argv = previous
        server.ClosedRelay = native


if __name__ == '__main__':
    main()
