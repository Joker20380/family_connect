"""Causal four-host capture receipts; physical writer adapters remain separately required."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import select
import stat
import struct
import time

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

SLOTS = ('RU', 'NL1', 'NL2', 'OWNER')
PURPOSE = 'family-connect/four-host-causal-capture/v1'
LIMIT = 1024 * 1024


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def unique(pairs):
    result = {}
    for name, value in pairs:
        require(name not in result, 'FLEET_DUPLICATE_FIELD')
        result[name] = value
    return result


def document(raw):
    require(type(raw) is bytes and 0 < len(raw) <= LIMIT, 'FLEET_DOCUMENT_BOUNDS')
    value = json.loads(raw, object_pairs_hook=unique,
                       parse_constant=lambda value: require(False, 'FLEET_NONFINITE'))
    require(encoded(value) == raw, 'FLEET_NONCANONICAL')
    return value


def hex_value(value, length=64):
    return type(value) is str and re.fullmatch('[0-9a-f]{' + str(length) + '}', value) is not None


def filename(name):
    return type(name) is str and re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9_.-]{0,95}', name) is not None and '..' not in name


def kernel():
    return digest(Path('/proc/sys/kernel/random/boot_id').read_bytes().strip())


def inventory(files):
    require(type(files) is dict and 0 < len(files) <= 256, 'FLEET_FILES')
    require(all(filename(name) and type(raw) is bytes and 0 < len(raw) <= 64 * LIMIT
                for name, raw in files.items()), 'FLEET_FILE_SHAPE')
    require(sum(map(len, files.values())) <= 128 * LIMIT, 'FLEET_FILE_BOUNDS')
    return {name: dict(bytes=len(raw), sha256=digest(raw)) for name, raw in sorted(files.items())}


def contract(value):
    require(type(value) is dict and set(value) == {'purpose', 'operation', 'challenge', 'participants'},
            'FLEET_CONTRACT')
    require(value['purpose'] == PURPOSE and hex_value(value['operation'], 32) and
            hex_value(value['challenge']), 'FLEET_OPERATION')
    members = value['participants']
    require(type(members) is dict and set(members) == set(SLOTS), 'FLEET_PARTICIPANTS')
    public_keys = set()
    for member in members.values():
        require(type(member) is dict and set(member) == {'public_key', 'source_sha256', 'coverage_sha256',
                'files', 'late_policy_sha256', 'boot', 'journal'}, 'FLEET_MEMBER')
        require(all(hex_value(member[name]) for name in ('public_key', 'source_sha256', 'coverage_sha256',
                                                        'late_policy_sha256', 'boot')), 'FLEET_PINS')
        journal = member['journal']
        require(type(journal) is str and 1 < len(journal) <= 1024 and journal.startswith('/') and
                not journal.startswith('//') and str(Path(journal)) == journal and '..' not in Path(journal).parts,
                'FLEET_JOURNAL_PATH')
        require(type(member['files']) is list and 0 < len(member['files']) <= 256 and
                all(filename(name) for name in member['files']) and
                member['files'] == sorted(set(member['files'])), 'FLEET_EXPECTED_FILES')
        public_keys.add(member['public_key'])
    require(len(public_keys) == len(SLOTS), 'FLEET_INDEPENDENT_SIGNERS')
    return digest(encoded(value))


def verify_receipt(receipt, expected, slot, phase):
    binding = contract(expected)
    require(slot in SLOTS, 'FLEET_SLOT')
    require(type(receipt) is dict and set(receipt) == {'body', 'signature'}, 'FLEET_RECEIPT')
    body = receipt['body']
    require(type(body) is dict and set(body) == {'purpose', 'contract', 'operation', 'slot', 'phase',
            'previous', 'payload'}, 'FLEET_RECEIPT_BODY')
    require(body['purpose'] == PURPOSE and body['contract'] == binding and
            body['operation'] == expected['operation'] and body['slot'] == slot and
            body['phase'] == phase and hex_value(body['previous']) and type(body['payload']) is dict,
            'FLEET_RECEIPT_BINDING')
    require(hex_value(receipt['signature'], 128), 'FLEET_SIGNATURE_SHAPE')
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(expected['participants'][slot]['public_key'])).verify(
            bytes.fromhex(receipt['signature']), encoded(body))
    except InvalidSignature:
        raise ValueError('FLEET_SIGNATURE') from None
    return body


def receipt_set(receipts, expected, phase):
    require(type(receipts) is dict and set(receipts) == set(SLOTS), 'FLEET_RECEIPT_COVERAGE')
    return {slot: verify_receipt(receipts[slot], expected, slot, phase) for slot in SLOTS}


def prepared(receipts, expected):
    bodies = receipt_set(receipts, expected, 'HELD')
    for slot, body in bodies.items():
        require(body['previous'] == contract(expected) and set(body['payload']) == {'lease', 'coverage', 'late_policy'}
                and hex_value(body['payload']['lease']) and
                body['payload']['coverage'] == expected['participants'][slot]['coverage_sha256'] and
                body['payload']['late_policy'] == expected['participants'][slot]['late_policy_sha256'],
                'FLEET_HELD_PROOF')
    return digest(encoded(receipts))


def captured(receipts, ready, expected):
    ready_hash = prepared(ready, expected)
    bodies = receipt_set(receipts, expected, 'CAPTURED')
    for slot, body in bodies.items():
        require(body['previous'] == digest(encoded(ready[slot])) and
                set(body['payload']) == {'ready_set', 'files', 'lease'} and
                body['payload']['ready_set'] == ready_hash and
                body['payload']['lease'] == ready[slot]['body']['payload']['lease'], 'FLEET_CAPTURE_CHAIN')
        files = body['payload']['files']
        require(type(files) is dict and set(files) == set(expected['participants'][slot]['files']),
                'FLEET_SNAPSHOT_COVERAGE')
        for entry in files.values():
            require(type(entry) is dict and set(entry) == {'bytes', 'sha256'} and
                    type(entry['bytes']) is int and 0 < entry['bytes'] <= 64 * LIMIT and
                    hex_value(entry['sha256']), 'FLEET_SNAPSHOT_ENTRY')
    return digest(encoded(receipts))


def verified_manifest(expected, ready, snapshots, files):
    capture_hash = captured(snapshots, ready, expected)
    require(type(files) is dict and set(files) == set(SLOTS), 'FLEET_OBJECT_COVERAGE')
    for slot in SLOTS:
        require(inventory(files[slot]) == snapshots[slot]['body']['payload']['files'], 'FLEET_EXACT_BYTES')
    return dict(purpose=PURPOSE, contract=contract(expected), ready_set=digest(encoded(ready)),
                capture_set=capture_hash, files={slot: inventory(files[slot]) for slot in SLOTS})


def sealed(receipts, ready, snapshots, manifest, expected):
    captured(snapshots, ready, expected)
    require(type(manifest) is dict and set(manifest) == {'purpose', 'contract', 'ready_set', 'capture_set', 'files'}
            and manifest['purpose'] == PURPOSE and manifest['contract'] == contract(expected) and
            manifest['ready_set'] == digest(encoded(ready)) and
            manifest['capture_set'] == digest(encoded(snapshots)) and
            manifest['files'] == {slot: snapshots[slot]['body']['payload']['files'] for slot in SLOTS},
            'FLEET_MANIFEST_BINDING')
    bodies = receipt_set(receipts, expected, 'SEALED')
    for slot, body in bodies.items():
        require(body['previous'] == digest(encoded(snapshots[slot])) and
                body['payload'] == dict(manifest=digest(encoded(manifest)),
                                        lease=ready[slot]['body']['payload']['lease']), 'FLEET_SEAL_CHAIN')
    return digest(encoded(receipts))


def verify_bundle(expected, ready, snapshots, seals, releases, files):
    manifest = verified_manifest(expected, ready, snapshots, files)
    seal_hash = sealed(seals, ready, snapshots, manifest, expected)
    bodies = receipt_set(releases, expected, 'RELEASED')
    for slot, body in bodies.items():
        require(body['previous'] == digest(encoded(seals[slot])) and
                body['payload'] == dict(seal_set=seal_hash), 'FLEET_RELEASE_CHAIN')
    return dict(result='CAUSAL_INTERVAL_AND_EXACT_SET_VERIFIED', operation=expected['operation'],
                manifest_sha256=digest(encoded(manifest)), capture_permitted=False,
                physical_writer_coverage='REQUIRES_QUALIFIED_ADAPTERS', normal_resume='NOT_ATTESTED')


def private_write(root, name, raw):
    require(filename(name) and type(raw) is bytes, 'FLEET_PRIVATE_FILE')
    descriptor = os.open(root / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


class Participant:
    def __init__(self, expected, slot, signer, root, barrier, snapshot, *, seconds=30):
        self.binding = contract(expected)
        require(slot in SLOTS and signer.public_key().public_bytes_raw().hex() ==
                expected['participants'][slot]['public_key'], 'FLEET_LOCAL_SIGNER')
        require(type(seconds) in (int, float) and 0 < seconds <= 120, 'FLEET_LEASE_BOUND')
        self.expected = document(encoded(expected))
        self.slot, self.signer = slot, signer
        self.root = Path(root)
        require(str(self.root) == expected['participants'][slot]['journal'], 'FLEET_JOURNAL_BINDING')
        require(kernel() == expected['participants'][slot]['boot'], 'FLEET_BOOT_BINDING')
        require(self.root.is_absolute() and not any(item.is_symlink() for item in (self.root, *self.root.parents)),
                'FLEET_PRIVATE_PATH')
        self.root.mkdir(mode=0o700, exist_ok=False)
        info = self.root.stat()
        require(info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700, 'FLEET_PRIVATE_PERMISSIONS')
        self.root_identity = info.st_dev, info.st_ino, info.st_uid, info.st_mode
        self.barrier, self.snapshot = barrier, snapshot
        self.deadline = time.monotonic() + seconds
        self.state, self.responses, self.requests = 'NEW', {}, {}
        self.entered = False
        self.release_attempted = False
        private_write(self.root, 'contract.json', encoded(expected))

    def check(self):
        require(self.entered and time.monotonic() < self.deadline, 'FLEET_LEASE_EXPIRED')
        info = self.root.lstat()
        require((info.st_dev, info.st_ino, info.st_uid, info.st_mode) == self.root_identity and
                digest((self.root / 'contract.json').read_bytes()) == self.binding, 'FLEET_JOURNAL_CHANGED')
        try:
            observed = self.barrier.check()
        except Exception:
            raise ValueError('FLEET_BARRIER_LOST') from None
        require(observed == self.lease, 'FLEET_BARRIER_LOST')
        require(time.monotonic() < self.deadline, 'FLEET_LEASE_EXPIRED')

    def sign(self, phase, previous, payload):
        body = dict(purpose=PURPOSE, contract=self.binding, operation=self.expected['operation'],
                    slot=self.slot, phase=phase, previous=previous, payload=payload)
        receipt = dict(body=body, signature=self.signer.sign(encoded(body)).hex())
        private_write(self.root, phase.lower() + '.json', encoded(receipt))
        return receipt

    def run(self, request):
        try:
            require(self.state != 'FAILED', 'FLEET_TERMINAL_FAILURE')
            require(type(request) is dict and set(request) == {'command', 'operation', 'payload'} and
                    request['operation'] == self.expected['operation'] and type(request['payload']) is dict,
                    'FLEET_REQUEST')
            phase = request['command']
            require(phase in ('HELD', 'CAPTURED', 'SEALED', 'RELEASED'), 'FLEET_COMMAND')
            request_hash = digest(encoded(request))
            if phase in self.responses:
                require(self.requests[phase] == request_hash, 'FLEET_REPLAY_CHANGED')
                if self.state != 'RELEASED':
                    self.check()
                return self.responses[phase]
            require(self.state != 'RELEASED', 'FLEET_COMPLETED')
            result = self.execute(phase, request['payload'])
            self.requests[phase], self.responses[phase], self.state = request_hash, result, phase
            return result
        except BaseException as error:
            reason = str(error)
            self.abort(reason if re.fullmatch('[A-Z][A-Z0-9_]{0,95}', reason) else type(error).__name__, error)
            raise

    def execute(self, phase, payload):
        if phase == 'HELD':
            require(self.state == 'NEW' and payload == {}, 'FLEET_PHASE')
            self.entered = True
            self.barrier.__enter__()
            self.lease = self.barrier.check()
            require(hex_value(self.lease), 'FLEET_LEASE_ID')
            self.check()
            member = self.expected['participants'][self.slot]
            return self.sign(phase, self.binding, dict(lease=self.lease, coverage=member['coverage_sha256'],
                                                      late_policy=member['late_policy_sha256']))
        self.check()
        if phase == 'CAPTURED':
            require(self.state == 'HELD' and set(payload) == {'ready'}, 'FLEET_PHASE')
            prepared(payload['ready'], self.expected)
            require(payload['ready'][self.slot] == self.responses['HELD'], 'FLEET_LOCAL_HELD')
            self.ready = document(encoded(payload['ready']))
            files = self.snapshot()
            entries = inventory(files)
            require(set(entries) == set(self.expected['participants'][self.slot]['files']), 'FLEET_SNAPSHOT_COVERAGE')
            directory = self.root / 'objects'
            directory.mkdir(mode=0o700)
            for name, raw in files.items():
                private_write(directory, name, raw)
            self.check()
            return self.sign(phase, digest(encoded(self.responses['HELD'])), dict(
                ready_set=digest(encoded(self.ready)), lease=self.lease, files=entries))
        if phase == 'SEALED':
            require(self.state == 'CAPTURED' and set(payload) == {'snapshots', 'manifest'}, 'FLEET_PHASE')
            captured(payload['snapshots'], self.ready, self.expected)
            require(payload['snapshots'][self.slot] == self.responses['CAPTURED'], 'FLEET_LOCAL_CAPTURE')
            self.snapshots, self.manifest = document(encoded(payload['snapshots'])), document(encoded(payload['manifest']))
            require(self.manifest == dict(purpose=PURPOSE, contract=self.binding,
                ready_set=digest(encoded(self.ready)), capture_set=digest(encoded(self.snapshots)),
                files={slot: self.snapshots[slot]['body']['payload']['files'] for slot in SLOTS}), 'FLEET_MANIFEST_BINDING')
            local = {name: (self.root / 'objects' / name).read_bytes()
                     for name in self.expected['participants'][self.slot]['files']}
            require(inventory(local) == self.manifest['files'][self.slot], 'FLEET_LOCAL_BYTES_CHANGED')
            self.check()
            return self.sign(phase, digest(encoded(self.responses['CAPTURED'])),
                             dict(manifest=digest(encoded(self.manifest)), lease=self.lease))
        require(self.state == 'SEALED' and set(payload) == {'seals'}, 'FLEET_PHASE')
        seal_hash = sealed(payload['seals'], self.ready, self.snapshots, self.manifest, self.expected)
        require(payload['seals'][self.slot] == self.responses['SEALED'], 'FLEET_LOCAL_SEAL')
        self.check()
        self.release_once()
        return self.sign(phase, digest(encoded(self.responses['SEALED'])), dict(seal_set=seal_hash))

    def release_once(self):
        require(not self.release_attempted, 'FLEET_RELEASE_ALREADY_ATTEMPTED')
        self.release_attempted = True
        self.barrier.__exit__(None, None, None)
        self.entered = False

    def abort(self, reason, original=None):
        if self.state in ('FAILED', 'RELEASED'):
            return
        self.state = 'FAILED'
        self.failure = reason
        self.cleanup_errors = []
        try:
            private_write(self.root, 'failed.json', encoded(dict(result='FAILED', error_type=reason,
                operation=self.expected['operation'], capture_permitted=False)))
        except BaseException as error:
            self.cleanup_errors.append('JOURNAL_' + type(error).__name__)
        self.barrier_release = 'NOT_ENTERED'
        if self.entered:
            self.barrier_release = 'UNKNOWN'
            try:
                self.release_once()
                self.barrier_release = 'RELEASED'
            except BaseException as error:
                self.cleanup_errors.append('BARRIER_' + type(error).__name__)
        try:
            private_write(self.root, 'cleanup.json', encoded(dict(barrier=self.barrier_release,
                errors=self.cleanup_errors, operation=self.expected['operation'])))
        except BaseException as error:
            self.cleanup_errors.append('CLEANUP_JOURNAL_' + type(error).__name__)
        if original is not None:
            for detail in self.cleanup_errors:
                original.add_note('FLEET_CLEANUP_' + detail)


def receive(descriptor, deadline):
    parts, required = bytearray(), 4
    while len(parts) < required:
        remaining = deadline - time.monotonic()
        require(remaining > 0 and select.select([descriptor], [], [], remaining)[0], 'FLEET_CHANNEL_EXPIRED')
        raw = os.read(descriptor, required - len(parts))
        require(bool(raw), 'FLEET_CONTROLLER_LOST')
        parts.extend(raw)
        if len(parts) == 4 and required == 4:
            length = struct.unpack('!I', parts)[0]
            require(0 < length <= LIMIT, 'FLEET_FRAME_BOUNDS')
            required = 4 + length
    return document(bytes(parts[4:]))


def send(descriptor, value, deadline):
    raw = encoded(value)
    require(len(raw) <= LIMIT, 'FLEET_FRAME_BOUNDS')
    pending = memoryview(struct.pack('!I', len(raw)) + raw)
    blocking = os.get_blocking(descriptor)
    os.set_blocking(descriptor, False)
    try:
        while pending:
            remaining = deadline - time.monotonic()
            require(remaining > 0 and select.select([], [descriptor], [], remaining)[1], 'FLEET_CHANNEL_EXPIRED')
            try:
                count = os.write(descriptor, pending)
            except BlockingIOError:
                continue
            require(count > 0, 'FLEET_SEND_FAILED')
            pending = pending[count:]
    finally:
        os.set_blocking(descriptor, blocking)


def serve(participant, incoming, outgoing):
    from .capture_process import hard_deadline
    with hard_deadline(max(.001, participant.deadline - time.monotonic()) + .25):
        try:
            while participant.state != 'RELEASED':
                request = receive(incoming, participant.deadline)
                response = participant.run(request)
                send(outgoing, response, participant.deadline)
        except BaseException as error:
            reason = str(error)
            participant.abort(reason if re.fullmatch('[A-Z][A-Z0-9_]{0,95}', reason) else type(error).__name__, error)
            raise
        finally:
            participant.abort('CHANNEL_ENDED_WITHOUT_COMPLETE_RELEASE')


@contextmanager
def session(participant):
    try:
        yield participant
    finally:
        participant.abort('SESSION_ENDED_WITHOUT_COMPLETE_RELEASE')
