"""Single-operation CRL maintenance; no registry, issuer, restart or general write API."""
import base64
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal
import fcntl
import errno
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import re
import secrets
import shlex
import stat
import struct
import sys
import time
import zipfile

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding

from .restricted import MAX_TEST_LIFETIME, directory, utc

CONFIGURATION_PATH = Path('/etc/fc-restricted-maintenance.json')
PERMIT_FIELDS = frozenset(('schema operation_id action expected_profile_sha256 expected_directory_sha256 '
    'expected_embedded_crl_sha256 expected_embedded_crl_number expected_minimum_crl request_sha256 '
    'target_crl_sha256 target_crl_number target_minimum_crl not_before not_after').split())
STATES = frozenset('PREPARED APPLYING COMMITTED IDEMPOTENT ROLLED_BACK UNKNOWN CONFLICT'.split())
CONFIG_FIELDS = frozenset(('profile directory sync_lock operations journal_key package_sha256 operation_id '
    'profile_uid profile_gid profile_mode directory_uid directory_gid directory_mode lock_uid lock_gid lock_mode '
    'material_boundary').split())
CODES = frozenset(('PASS IDEMPOTENT INVALID_PERMIT INVALID_REQUEST MAINTENANCE_PRECONDITION_CHANGED '
    'CRL_PAYLOAD_CONFLICT PROFILE_VALIDATION_FAILED DIRECTORY_VALIDATION_FAILED APPLY_FAILED '
    'MAINTENANCE_ROLLED_BACK MAINTENANCE_ROLLBACK_FAILED MAINTENANCE_STATE_CONFLICT READBACK_MISMATCH '
    'MATERIAL_METADATA_MISMATCH MATERIAL_EXTENDED_METADATA_UNSUPPORTED MATERIAL_TEMP_METADATA_FAILED '
    'MAINTENANCE_ROUTE_UNAVAILABLE').split())


class MaintenanceError(ValueError):
    def __init__(self, code):
        self.code = code if code in CODES else 'APPLY_FAILED'
        super().__init__(self.code)


def require(condition, code):
    if not condition:
        raise MaintenanceError(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def strict(raw, limit, code):
    def pairs(items):
        result = {}
        for name, value in items:
            require(name not in result, code)
            result[name] = value
        return result
    def nonfinite(value):
        raise MaintenanceError(code)
    def finite(value):
        number = float(value)
        require(math.isfinite(number), code)
        return number
    require(type(raw) is bytes and 0 < len(raw) <= limit, code)
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite, parse_float=finite)
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        raise MaintenanceError(code) from None


def validate_permit(value):
    code = 'INVALID_PERMIT'
    require(type(value) is dict and set(value) == PERMIT_FIELDS, code)
    require(type(value['schema']) is int and value['schema'] == 1, code)
    require(type(value['operation_id']) is str and re.fullmatch(r'restricted_maintenance_[0-9a-f]{32}', value['operation_id']), code)
    require(value['action'] in ('reconcile_current_floor', 'apply_exact_crl'), code)
    for name in PERMIT_FIELDS:
        if name.endswith('_sha256'):
            require(type(value[name]) is str and re.fullmatch('[0-9a-f]{64}', value[name]), code)
        if name.endswith(('_number', '_crl')) or name in ('not_before', 'not_after'):
            require(type(value[name]) is int and 0 <= value[name] < 2**63, code)
    require(0 < value['not_after'] - value['not_before'] <= 300, code)
    require(value['target_minimum_crl'] == value['target_crl_number'], code)
    if value['action'] == 'reconcile_current_floor':
        require(value['target_crl_number'] == value['expected_embedded_crl_number'] and
                value['target_crl_sha256'] == value['expected_embedded_crl_sha256'] and
                value['expected_minimum_crl'] <= value['target_minimum_crl'], code)
    else:
        require(value['target_crl_number'] > max(value['expected_embedded_crl_number'], value['expected_minimum_crl']), code)
    return value


def request_payload(raw):
    value = strict(raw, 20000, 'INVALID_REQUEST')
    require(type(value) is dict and set(value) == {'revocations'} and type(value['revocations']) is str, 'INVALID_REQUEST')
    payload = value['revocations'].encode()
    require(0 < len(payload) <= 16384, 'INVALID_REQUEST')
    return payload


def fsync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def absolute(path):
    require(isinstance(path, Path) and path.is_absolute() and '..' not in path.parts, 'INVALID_PERMIT')


def root_parents(path):
    absolute(path)
    for parent in (path.parent, *path.parent.parents):
        info = parent.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022,
                'MAINTENANCE_STATE_CONFLICT')


def read_control(path, limit, *, mode=0o600):
    require(os.geteuid() == 0, 'INVALID_PERMIT')
    root_parents(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as source:
        info = os.fstat(source.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == info.st_gid == 0 and
                stat.S_IMODE(info.st_mode) == mode, 'MAINTENANCE_STATE_CONFLICT')
        raw = source.read(limit + 1)
    require(0 < len(raw) <= limit, 'MAINTENANCE_STATE_CONFLICT')
    return raw


def atomic_control(path, raw):
    require(os.geteuid() == 0, 'INVALID_PERMIT')
    root_parents(path)
    if path.exists() or path.is_symlink():
        read_control(path, 1024 * 1024)
    pending = path.with_name('.' + path.name + '.' + secrets.token_hex(12))
    descriptor = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        os.replace(pending, path)
        fsync_directory(path.parent)
    finally:
        if pending.exists():
            pending.unlink()


def metadata(info):
    return dict(uid=info.st_uid, gid=info.st_gid, mode=stat.S_IMODE(info.st_mode),
                device=info.st_dev, inode=info.st_ino)


def extended_metadata(descriptor):
    code = 'MATERIAL_EXTENDED_METADATA_UNSUPPORTED'
    try:
        require(not os.listxattr(descriptor), code)
        flags = bytearray(struct.calcsize('L'))
        try:
            fcntl.ioctl(descriptor, 0x80006601 | (len(flags) << 16), flags, True)
        except OSError as error:
            require(error.errno in (errno.ENOTTY, errno.EOPNOTSUPP), code)
        else:
            require(not int.from_bytes(flags, sys.byteorder) & ~0x80000, code)
    except OSError:
        raise MaintenanceError(code) from None


@dataclass(frozen=True, repr=False)
class Configuration:
    profile: Path
    directory: Path
    sync_lock: Path
    operations: Path
    journal_key: bytes
    profile_uid: int
    profile_gid: int
    profile_mode: int
    directory_uid: int
    directory_gid: int
    directory_mode: int
    lock_uid: int
    lock_gid: int
    lock_mode: int
    material_boundary: dict
    max_attempts: int = 1

    def expected(self, path):
        for name in ('profile', 'directory', 'lock'):
            if path == getattr(self, 'sync_lock' if name == 'lock' else name):
                return {field: getattr(self, name + '_' + field) for field in ('uid', 'gid', 'mode')}
        raise MaintenanceError('MATERIAL_METADATA_MISMATCH')

    def parents(self, path):
        code = 'MATERIAL_METADATA_MISMATCH'
        boundary = Path(self.material_boundary['path'])
        absolute(path)
        require(path != boundary and path.is_relative_to(boundary), code)
        root_parents(boundary)
        info = boundary.lstat()
        require(stat.S_ISDIR(info.st_mode) and metadata(info) == {key: value for key, value in
                self.material_boundary.items() if key != 'path'}, code)
        require(info.st_uid in (0, self.profile_uid) and not info.st_mode & 0o022, code)
        result = {}
        for parent in (path.parent, *path.parent.parents):
            if not parent.is_relative_to(boundary):
                break
            current = parent.lstat()
            require(stat.S_ISDIR(current.st_mode) and current.st_uid in (0, self.profile_uid) and
                    not current.st_mode & 0o022 and current.st_dev == info.st_dev, code)
            result[str(parent)] = metadata(current)
        require(path.parent.resolve(strict=True) == path.parent, code)
        for line in Path('/proc/self/mountinfo').read_text().splitlines():
            mounted = Path(re.sub(r'\\([0-7]{3})', lambda match: chr(int(match[1], 8)), line.split()[4]))
            require(mounted == boundary or not mounted.is_relative_to(boundary), code)
        return result

    def verify_material_fd(self, path, descriptor):
        info = os.fstat(descriptor)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and
                all(metadata(info)[key] == value for key, value in self.expected(path).items()) and
                info.st_dev == self.material_boundary['device'], 'MATERIAL_METADATA_MISMATCH')
        extended_metadata(descriptor)
        return info

    def read_material(self, path, limit):
        try:
            self.parents(path)
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(descriptor, 'rb') as source:
                info = self.verify_material_fd(path, source.fileno())
                require(metadata(path.lstat()) == metadata(info) and not path.is_symlink(), 'MATERIAL_METADATA_MISMATCH')
                raw = source.read(limit + 1)
            require(len(raw) <= limit and (bool(raw) or path == self.sync_lock), 'MATERIAL_METADATA_MISMATCH')
            return raw
        except OSError:
            raise MaintenanceError('MATERIAL_METADATA_MISMATCH') from None

    def contract(self):
        return dict(paths={name: str(getattr(self, name)) for name in ('profile', 'directory', 'sync_lock', 'operations')},
                    materials={name: self.expected(getattr(self, name)) for name in ('profile', 'directory', 'sync_lock')},
                    boundary=self.material_boundary, max_attempts=self.max_attempts)

    def material_snapshot(self):
        for path, limit in ((self.profile, 49152), (self.directory, 8192), (self.sync_lock, 4096)):
            self.read_material(path, limit)
        parents = {str(path): self.parents(path) for path in (self.profile, self.directory, self.sync_lock)}
        return dict(before_profile_uid=self.profile_uid, before_profile_gid=self.profile_gid,
                    before_profile_mode=self.profile_mode, target_profile_uid=self.profile_uid,
                    target_profile_gid=self.profile_gid, target_profile_mode=self.profile_mode,
                    directory_uid=self.directory_uid, directory_gid=self.directory_gid, directory_mode=self.directory_mode,
                    lock_uid=self.lock_uid, lock_gid=self.lock_gid, lock_mode=self.lock_mode,
                    lock_sha256=digest(self.read_material(self.sync_lock, 4096)),
                    lock_inode=self.sync_lock.lstat().st_ino, directory_inode=self.directory.lstat().st_ino,
                    material_boundary_metadata_sha256=digest(encode(parents)))

    def validate(self):
        require(os.geteuid() == 0 and type(self.journal_key) is bytes and len(self.journal_key) == 32 and
                type(self.max_attempts) is int and self.max_attempts in (1, 2), 'INVALID_PERMIT')
        for name in ('profile', 'directory', 'lock'):
            for field in ('uid', 'gid'):
                value = getattr(self, name + '_' + field)
                require(type(value) is int and 0 <= value < 2**32 - 1, 'INVALID_PERMIT')
            require(type(getattr(self, name + '_mode')) is int and getattr(self, name + '_mode') == 0o600, 'INVALID_PERMIT')
        require(type(self.material_boundary) is dict and set(self.material_boundary) ==
                {'path', 'uid', 'gid', 'mode', 'device', 'inode'}, 'INVALID_PERMIT')
        require(type(self.material_boundary['path']) is str, 'INVALID_PERMIT')
        boundary = Path(self.material_boundary['path'])
        absolute(boundary)
        for name in ('uid', 'gid', 'mode', 'device', 'inode'):
            require(type(self.material_boundary[name]) is int and self.material_boundary[name] >= 0, 'INVALID_PERMIT')
        paths = (self.profile, self.directory, self.sync_lock, self.operations)
        for path in paths:
            absolute(path)
        require(len(set(paths)) == 4 and not self.operations.is_relative_to(boundary), 'INVALID_PERMIT')
        for path in paths[:3]:
            require(not path.is_relative_to(self.operations), 'INVALID_PERMIT')
        root_parents(self.operations / 'placeholder')
        info = self.operations.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == info.st_gid == 0 and
                stat.S_IMODE(info.st_mode) == 0o700, 'MAINTENANCE_STATE_CONFLICT')
        try:
            self.read_material(self.sync_lock, 4096)
        except MaintenanceError as error:
            if error.code == 'MATERIAL_EXTENDED_METADATA_UNSUPPORTED':
                raise
            raise MaintenanceError('MAINTENANCE_ROUTE_UNAVAILABLE') from None
        self.material_snapshot()

    @contextmanager
    def lock(self):
        try:
            self.parents(self.sync_lock)
            descriptor = os.open(self.sync_lock, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK)
        except (OSError, MaintenanceError):
            raise MaintenanceError('MAINTENANCE_ROUTE_UNAVAILABLE') from None
        try:
            try:
                self.verify_material_fd(self.sync_lock, descriptor)
                require(self.sync_lock.lstat().st_ino == os.fstat(descriptor).st_ino, 'MATERIAL_METADATA_MISMATCH')
            except MaintenanceError:
                raise MaintenanceError('MAINTENANCE_ROUTE_UNAVAILABLE') from None
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise MaintenanceError('MAINTENANCE_PRECONDITION_CHANGED') from None
            yield
        finally:
            os.close(descriptor)


def atomic_material_replace(config, raw, *, before_replace):
    path = config.profile
    config.read_material(path, 49152)
    parents = config.parents(path)
    parent_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    pending = '.' + path.name + '.' + secrets.token_hex(12)
    try:
        require(metadata(os.fstat(parent_fd)) == parents[str(path.parent)], 'MATERIAL_METADATA_MISMATCH')
        descriptor = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent_fd)
        with os.fdopen(descriptor, 'wb') as output:
            try:
                os.fchown(output.fileno(), config.profile_uid, config.profile_gid)
                os.fchmod(output.fileno(), config.profile_mode)
                config.verify_material_fd(path, output.fileno())
            except (OSError, MaintenanceError):
                raise MaintenanceError('MATERIAL_TEMP_METADATA_FAILED') from None
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        require(config.parents(path) == parents, 'MATERIAL_METADATA_MISMATCH')
        before_replace()
        require(config.parents(path) == parents, 'MATERIAL_METADATA_MISMATCH')
        descriptor = os.open(pending, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
        with os.fdopen(descriptor, 'rb') as source:
            config.verify_material_fd(path, source.fileno())
            require(source.read(len(raw) + 1) == raw, 'MATERIAL_TEMP_METADATA_FAILED')
        os.replace(pending, path.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        os.fsync(parent_fd)
        require(config.read_material(path, 49152) == raw, 'MATERIAL_METADATA_MISMATCH')
    finally:
        try:
            os.unlink(pending, dir_fd=parent_fd)
        except FileNotFoundError:
            pass
        os.close(parent_fd)


def profile_material(raw, directory_raw, now):
    code = 'PROFILE_VALIDATION_FAILED'
    try:
        profile = strict(raw, 49152, code)
        require(type(profile) is dict and all(name in profile for name in
                ('authority', 'revocations', 'minimum_crl', 'family', 'gateway')), code)
        require(type(profile['minimum_crl']) is int and 0 <= profile['minimum_crl'] < 2**63, code)
        require(all(type(profile[name]) is str and re.fullmatch('[0-9a-f]{32}', profile[name])
                    for name in ('family', 'gateway')), code)
        authority = x509.load_pem_x509_certificate(profile['authority'].encode())
        require(authority.public_bytes(Encoding.PEM) == profile['authority'].encode(), code)
        require(isinstance(authority.public_key(), Ed25519PublicKey), code)
        authority.verify_directly_issued_by(authority)
        require(authority.extensions.get_extension_for_class(x509.BasicConstraints).value.ca, code)
        usage = authority.extensions.get_extension_for_class(x509.KeyUsage).value
        require(usage.key_cert_sign and usage.crl_sign, code)
        require(authority.not_valid_before_utc <= utc(now) < authority.not_valid_after_utc, code)
        previous, number = validated_crl(profile['revocations'].encode(), authority, now)
        require(number >= profile['minimum_crl'], code)
    except Exception:
        raise MaintenanceError(code) from None
    try:
        directory(directory_raw, profile['family'], profile['gateway'], now_ns=int(Decimal(str(now)) * 1_000_000_000))
    except Exception:
        raise MaintenanceError('DIRECTORY_VALIDATION_FAILED') from None
    return profile, authority, previous, number


def validated_crl(raw, authority, now):
    value = x509.load_pem_x509_crl(raw)
    require(value.public_bytes(Encoding.PEM) == raw, 'PROFILE_VALIDATION_FAILED')
    require(value.is_signature_valid(authority.public_key()) and value.issuer == authority.subject, 'PROFILE_VALIDATION_FAILED')
    require(value.last_update_utc <= utc(now) < value.next_update_utc and
            0 < (value.next_update_utc - value.last_update_utc).total_seconds() <= MAX_TEST_LIFETIME,
            'PROFILE_VALIDATION_FAILED')
    number = value.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
    require(type(number) is int and 0 <= number < 2**63, 'PROFILE_VALIDATION_FAILED')
    return value, number


class Operation:
    def __init__(self, config, permit, *, clock=time.time):
        self.config = config
        self.permit = strict(encode(validate_permit(permit)), 8192, 'INVALID_PERMIT')
        self.clock = clock
        self.root = config.operations / self.permit['operation_id']

    def _save(self, journal, state):
        require(state in STATES, 'MAINTENANCE_STATE_CONFLICT')
        journal['state'] = state
        raw = encode(journal)
        envelope = dict(journal=journal, mac=hmac.new(self.config.journal_key, raw, hashlib.sha256).hexdigest())
        atomic_control(self.root / 'journal.json', encode(envelope))

    def _load(self, request):
        code = 'MAINTENANCE_STATE_CONFLICT'
        require(stat.S_IMODE(self.root.lstat().st_mode) == 0o700 and not self.root.is_symlink(), code)
        envelope = strict(read_control(self.root / 'journal.json', 16384), 16384, code)
        require(type(envelope) is dict and set(envelope) == {'journal', 'mac'}, code)
        journal = envelope['journal']
        require(type(envelope['mac']) is str and hmac.compare_digest(envelope['mac'],
                hmac.new(self.config.journal_key, encode(journal), hashlib.sha256).hexdigest()), code)
        require(journal['state'] in STATES and journal['permit_sha256'] == digest(encode(self.permit)) and
                journal['request_sha256'] == digest(request), code)
        require(read_control(self.root / 'permit.json', 8192) == encode(self.permit) and
                read_control(self.root / 'request.json', 20000) == request, code)
        for name, field, limit in (('before-profile.json', 'before_profile_sha256', 49152),
                                   ('before-directory.json', 'before_directory_sha256', 8192),
                                   ('target-profile.json', 'target_profile_sha256', 49152)):
            require(digest(read_control(self.root / name, limit)) == journal[field], code)
        require(journal['configuration_sha256'] == digest(encode(self.config.contract())), code)
        self._unchanged_metadata(journal)
        return journal

    def _unchanged_metadata(self, journal):
        try:
            require(self.config.material_snapshot() == journal['material_metadata'], 'MAINTENANCE_STATE_CONFLICT')
        except (MaintenanceError, OSError):
            raise MaintenanceError('MAINTENANCE_STATE_CONFLICT') from None
        require(digest(self.config.read_material(self.config.directory, 8192)) ==
                journal['before_directory_sha256'], 'MAINTENANCE_STATE_CONFLICT')

    def _validate(self):
        try:
            self.config.validate()
        except (MaintenanceError, OSError):
            if self.root.exists() or self.root.is_symlink():
                raise MaintenanceError('MAINTENANCE_STATE_CONFLICT') from None
            raise

    def _prepare(self, request):
        permit, config = self.permit, self.config
        now = self.clock()
        require(permit['not_before'] <= now < permit['not_after'], 'INVALID_PERMIT')
        profile_raw = config.read_material(config.profile, 49152)
        directory_raw = config.read_material(config.directory, 8192)
        require(digest(profile_raw) == permit['expected_profile_sha256'] and
                digest(directory_raw) == permit['expected_directory_sha256'], 'MAINTENANCE_PRECONDITION_CHANGED')
        profile, authority, previous, old_number = profile_material(profile_raw, directory_raw, now)
        require(old_number == permit['expected_embedded_crl_number'] and
                digest(profile['revocations'].encode()) == permit['expected_embedded_crl_sha256'] and
                profile['minimum_crl'] == permit['expected_minimum_crl'], 'MAINTENANCE_PRECONDITION_CHANGED')
        payload = request_payload(request)
        try:
            incoming, number = validated_crl(payload, authority, now)
            require(incoming.last_update_utc >= previous.last_update_utc, 'PROFILE_VALIDATION_FAILED')
        except Exception:
            raise MaintenanceError('PROFILE_VALIDATION_FAILED') from None
        if number == old_number and payload != profile['revocations'].encode():
            raise MaintenanceError('CRL_PAYLOAD_CONFLICT')
        require(digest(request) == permit['request_sha256'] and digest(payload) == permit['target_crl_sha256'] and
                number == permit['target_crl_number'], 'INVALID_REQUEST')
        if permit['action'] == 'reconcile_current_floor':
            require(number == old_number and payload == profile['revocations'].encode(), 'CRL_PAYLOAD_CONFLICT')
        else:
            require(number > max(old_number, profile['minimum_crl']), 'MAINTENANCE_PRECONDITION_CHANGED')
        target = dict(profile, minimum_crl=permit['target_minimum_crl'])
        if permit['action'] == 'apply_exact_crl':
            target['revocations'] = payload.decode()
        target_raw = encode(target)
        require(len(target_raw) <= 49152, 'PROFILE_VALIDATION_FAILED')
        material_metadata = config.material_snapshot()
        self.root.mkdir(mode=0o700)
        fsync_directory(config.operations)
        for name, raw in (('permit.json', encode(permit)), ('request.json', request),
                          ('before-profile.json', profile_raw), ('before-directory.json', directory_raw),
                          ('target-profile.json', target_raw)):
            atomic_control(self.root / name, raw)
        journal = dict(schema=1, permit_sha256=digest(encode(permit)), request_sha256=digest(request),
            before_profile_sha256=digest(profile_raw), before_directory_sha256=digest(directory_raw),
            target_profile_sha256=digest(target_raw), expected_crl_number=old_number, target_crl_number=number,
            expected_minimum_crl=profile['minimum_crl'], target_minimum_crl=target['minimum_crl'],
            target_payload_sha256=digest(payload), attempt_count=0, replace_started=False, committed_write=False,
            applied_at=None, material_metadata=material_metadata,
            configuration_sha256=digest(encode(config.contract())))
        self._save(journal, 'PREPARED')
        return journal

    def _target(self, journal):
        self._unchanged_metadata(journal)
        config = self.config
        raw = config.read_material(config.profile, 49152)
        directory_raw = config.read_material(config.directory, 8192)
        require(digest(raw) == journal['target_profile_sha256'] and
                digest(directory_raw) == journal['before_directory_sha256'], 'READBACK_MISMATCH')
        profile, _, _, number = profile_material(raw, directory_raw, self.clock())
        require(number == journal['target_crl_number'] and profile['minimum_crl'] == journal['target_minimum_crl'] and
                digest(profile['revocations'].encode()) == journal['target_payload_sha256'], 'READBACK_MISMATCH')
        return dict(schema=1, result='PASS', operation_safe_label='maintenance_' + digest(self.permit['operation_id'].encode())[:12],
            crl_number=number, payload_sha256=journal['target_payload_sha256'], minimum_crl=profile['minimum_crl'],
            profile_sha256=digest(raw), directory_sha256=digest(directory_raw),
            directory_base64=base64.b64encode(directory_raw).decode(), applied_at=journal['applied_at'])

    def _complete(self, journal, *, duplicate=False):
        response = self._target(journal)
        if journal['applied_at'] is None:
            journal['applied_at'] = int(self.clock())
        journal['committed_write'] = True
        response.update(result='IDEMPOTENT' if duplicate else 'PASS', applied_at=journal['applied_at'])
        atomic_control(self.root / 'response.json', encode(response))
        self._save(journal, 'IDEMPOTENT' if duplicate else 'COMMITTED')
        return response

    def _rollback(self, journal):
        try:
            self._unchanged_metadata(journal)
            current = digest(self.config.read_material(self.config.profile, 49152))
            require(current in (journal['before_profile_sha256'], journal['target_profile_sha256']), 'MAINTENANCE_ROLLBACK_FAILED')
            def rollback_ready():
                self._unchanged_metadata(journal)
                require(digest(self.config.read_material(self.config.profile, 49152)) == current,
                        'MAINTENANCE_ROLLBACK_FAILED')
            if current != journal['before_profile_sha256']:
                atomic_material_replace(self.config, read_control(self.root / 'before-profile.json', 49152),
                                        before_replace=rollback_ready)
            require(digest(self.config.read_material(self.config.profile, 49152)) == journal['before_profile_sha256'] and
                    digest(self.config.read_material(self.config.directory, 8192)) == journal['before_directory_sha256'],
                    'MAINTENANCE_ROLLBACK_FAILED')
            profile_material(self.config.read_material(self.config.profile, 49152), self.config.read_material(self.config.directory, 8192), self.clock())
            self._save(journal, 'ROLLED_BACK')
        except Exception:
            self._save(journal, 'UNKNOWN')
            raise MaintenanceError('MAINTENANCE_ROLLBACK_FAILED') from None
        raise MaintenanceError('MAINTENANCE_ROLLED_BACK')

    def execute(self, request):
        request_payload(request)
        self._validate()
        with self.config.lock():
            journal = self._load(request) if self.root.exists() or self.root.is_symlink() else self._prepare(request)
            current = digest(self.config.read_material(self.config.profile, 49152))
            current_directory = digest(self.config.read_material(self.config.directory, 8192))
            require(current_directory == journal['before_directory_sha256'], 'MAINTENANCE_STATE_CONFLICT')
            if journal['state'] in ('COMMITTED', 'IDEMPOTENT', 'APPLYING', 'UNKNOWN') and current == journal['target_profile_sha256']:
                return self._complete(journal, duplicate=True)
            require(journal['state'] in ('PREPARED', 'APPLYING', 'UNKNOWN') and
                    current == journal['before_profile_sha256'] and not journal['committed_write'] and
                    not journal['replace_started'] and journal['attempt_count'] < self.config.max_attempts,
                    'MAINTENANCE_STATE_CONFLICT')
            require(self.permit['not_before'] <= self.clock() < self.permit['not_after'], 'INVALID_PERMIT')
            profile_material(self.config.read_material(self.config.profile, 49152), self.config.read_material(self.config.directory, 8192), self.clock())
            journal['attempt_count'] += 1
            self._save(journal, 'PREPARED')
            def prepared():
                self._unchanged_metadata(journal)
                require(self._load(request) == journal, 'MAINTENANCE_STATE_CONFLICT')
                require(digest(self.config.read_material(self.config.profile, 49152)) == journal['before_profile_sha256'] and
                        digest(self.config.read_material(self.config.directory, 8192)) == journal['before_directory_sha256'],
                        'MAINTENANCE_PRECONDITION_CHANGED')
                require(self.permit['not_before'] <= self.clock() < self.permit['not_after'], 'INVALID_PERMIT')
                profile_material(self.config.read_material(self.config.profile, 49152), self.config.read_material(self.config.directory, 8192), self.clock())
                journal['replace_started'] = True
                self._save(journal, 'APPLYING')
            try:
                atomic_material_replace(self.config, read_control(self.root / 'target-profile.json', 49152), before_replace=prepared)
                return self._complete(journal)
            except Exception as error:
                if not journal['replace_started']:
                    self._save(journal, 'CONFLICT')
                    raise MaintenanceError(error.code if isinstance(error, MaintenanceError) else 'APPLY_FAILED') from None
                self._rollback(journal)

    def reconcile(self, request):
        self._validate()
        with self.config.lock():
            journal = self._load(request)
            require(journal['state'] in ('COMMITTED', 'IDEMPOTENT', 'APPLYING', 'UNKNOWN'), 'MAINTENANCE_STATE_CONFLICT')
            return self._complete(journal, duplicate=True)


def sanitized(response):
    return {name: value for name, value in response.items() if name in (
        'schema', 'result', 'operation_safe_label', 'crl_number', 'payload_sha256', 'minimum_crl',
        'profile_sha256', 'directory_sha256', 'applied_at')}


def trusted_readback(response):
    from .paid_canary_crl import TrustedReadback
    require(type(response) is dict and type(response.get('schema')) is int and response['schema'] == 1 and
            response.get('result') in ('PASS', 'IDEMPOTENT'), 'READBACK_MISMATCH')
    try:
        raw = base64.b64decode(response['directory_base64'], validate=True)
        require(0 < len(raw) <= 8192 and digest(raw) == response['directory_sha256'], 'READBACK_MISMATCH')
        require(type(response['crl_number']) is int and type(response['minimum_crl']) is int and
                0 <= response['crl_number'] == response['minimum_crl'] < 2**63 and
                re.fullmatch('[0-9a-f]{64}', response['payload_sha256']), 'READBACK_MISMATCH')
        return TrustedReadback(response['crl_number'], response['payload_sha256'], response['minimum_crl'], raw)
    except Exception:
        raise MaintenanceError('READBACK_MISMATCH') from None


def credential_line(public_key, python_path, package_path, source=None):
    require(type(public_key) is str and re.fullmatch(r'ssh-ed25519 [A-Za-z0-9+/]{68}', public_key), 'INVALID_REQUEST')
    for path in (python_path, package_path):
        require(type(path) is str and re.fullmatch(r'/[A-Za-z0-9_./-]+', path) and '..' not in Path(path).parts, 'INVALID_REQUEST')
    require(re.fullmatch(r'python(?:3(?:\.[0-9]+)?)?', Path(python_path).name), 'INVALID_REQUEST')
    require(package_path.endswith('.pyz'), 'INVALID_REQUEST')
    options = ['restrict', 'no-pty', 'no-port-forwarding', 'no-agent-forwarding', 'no-X11-forwarding', 'no-user-rc']
    if source is not None:
        import ipaddress
        require(type(source) is str and str(ipaddress.ip_network(source, strict=True)) == source, 'INVALID_REQUEST')
        options.append('from="' + source + '"')
    command = shlex.join(['/usr/bin/timeout', '--signal=KILL', '35', python_path, '-I', '-B', package_path])
    options.append('command="' + command + '"')
    return (','.join(options) + ' ' + public_key + '\n').encode()


def remove_credential(configuration, line):
    require(type(configuration) is bytes and type(line) is bytes and line.endswith(b'\n'), 'INVALID_REQUEST')
    require(configuration.splitlines(keepends=True).count(line) == 1, 'MAINTENANCE_STATE_CONFLICT')
    return b''.join(item for item in configuration.splitlines(keepends=True) if item != line)


def load_configuration(permit, package):
    require(os.geteuid() == 0, 'INVALID_PERMIT')
    value = strict(read_control(CONFIGURATION_PATH, 8192), 8192, 'INVALID_PERMIT')
    require(type(value) is dict and set(value) == CONFIG_FIELDS, 'INVALID_PERMIT')
    require(value['operation_id'] == permit['operation_id'], 'INVALID_PERMIT')
    require(digest(read_control(package, 1048576, mode=0o400)) == value['package_sha256'], 'INVALID_PERMIT')
    for field in ('profile', 'directory', 'sync_lock', 'operations', 'journal_key'):
        require(type(value[field]) is str, 'INVALID_PERMIT')
        absolute(Path(value[field]))
    config = Configuration(profile=Path(value['profile']), directory=Path(value['directory']),
        sync_lock=Path(value['sync_lock']), operations=Path(value['operations']),
        journal_key=read_control(Path(value['journal_key']), 32),
        **{name: value[name] for name in ('profile_uid', 'profile_gid', 'profile_mode',
            'directory_uid', 'directory_gid', 'directory_mode', 'lock_uid', 'lock_gid', 'lock_mode',
            'material_boundary')})
    config.validate()
    return config


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        require(not os.environ.get('SSH_ORIGINAL_COMMAND'), 'INVALID_REQUEST')
        require(not args or args in (['--help'], ['--manifest']), 'INVALID_REQUEST')
        package = Path(sys.argv[0]).absolute()
        with zipfile.ZipFile(package) as archive:
            permit = strict(archive.read('operation-permit.json'), 8192, 'INVALID_PERMIT')
            if args:
                print(encode(dict(schema=1, binding='unbound' if permit is None else 'single_operation',
                    operation_permit='absent' if permit is None else 'embedded',
                    production_configuration='absent',
                    usage='--help | --manifest; bound invocation accepts only exact stdin')).decode())
                return 0
        validate_permit(permit)
        config = load_configuration(permit, package)
        response = Operation(config, permit).execute(sys.stdin.buffer.read(20001))
        sys.stdout.buffer.write(encode(response) + b'\n')
        return 0
    except Exception as error:
        code = error.code if isinstance(error, MaintenanceError) else 'APPLY_FAILED'
        print(encode(dict(schema=1, result=code)).decode())
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
