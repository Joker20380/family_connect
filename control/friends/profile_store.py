"""Root-controlled profile transactions; publisher materials are read-only ports."""
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import struct
import sys
import time

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from .restricted import MAX_TEST_LIFETIME, directory, timestamp_ns, utc


class ProfileError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(condition, code):
    if not condition:
        raise ProfileError(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def parse(raw, limit=49152):
    def pairs(items):
        value = {}
        for name, item in items:
            require(name not in value, 'INVALID_JSON')
            value[name] = item
        return value
    def invalid(value):
        raise ProfileError('INVALID_JSON')
    require(type(raw) is bytes and 0 < len(raw) <= limit, 'INVALID_JSON')
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid, parse_float=invalid)
    except (ValueError, UnicodeError, RecursionError):
        raise ProfileError('INVALID_JSON') from None


def metadata(info):
    return dict(uid=info.st_uid, gid=info.st_gid, mode=stat.S_IMODE(info.st_mode))


def identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def extended_metadata(descriptor):
    require(not os.listxattr(descriptor), 'EXTENDED_METADATA_UNSUPPORTED')
    flags = bytearray(struct.calcsize('L'))
    try:
        fcntl.ioctl(descriptor, 0x80006601 | (len(flags) << 16), flags, True)
    except OSError as error:
        require(error.errno in (errno.ENOTTY, errno.EOPNOTSUPP), 'EXTENDED_METADATA_UNSUPPORTED')
    else:
        structural = 0x80000 | (0x1000 if stat.S_ISDIR(os.fstat(descriptor).st_mode) else 0)
        require(not int.from_bytes(flags, sys.byteorder) & ~structural, 'EXTENDED_METADATA_UNSUPPORTED')


def absolute(path):
    require(isinstance(path, Path) and path.is_absolute() and str(path) == os.path.normpath(path)
            and '..' not in path.parts, 'INVALID_FIXED_PATH')


def parents(path, *, publisher_parent=None):
    absolute(path)
    result = {}
    for parent in path.parents:
        info = parent.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0, 'UNSAFE_PARENT')
        require(not info.st_mode & 0o002, 'UNSAFE_PARENT')
        if info.st_mode & 0o020:
            require(publisher_parent is not None and str(parent) == publisher_parent['path'] and
                    dict(metadata(info), device=info.st_dev, inode=info.st_ino) ==
                    {key: value for key, value in publisher_parent.items() if key != 'path'}, 'UNSAFE_PARENT')
        descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            extended_metadata(descriptor)
        finally:
            os.close(descriptor)
        result[str(parent)] = (info.st_dev, info.st_ino, *metadata(info).values())
    require(path.parent.resolve(strict=True) == path.parent, 'UNSAFE_PARENT')
    return result


def read_regular(path, expected, limit, *, publisher_parent=None, empty=False):
    before_parents = parents(path, publisher_parent=publisher_parent)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and metadata(before) == expected,
                'FILE_METADATA_MISMATCH')
        extended_metadata(stream.fileno())
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
        require(identity(before) == identity(after) and metadata(after) == expected, 'FILE_CHANGED_DURING_READ')
    require(len(raw) <= limit and (empty or bool(raw)), 'FILE_SIZE_INVALID')
    require(parents(path, publisher_parent=publisher_parent) == before_parents, 'UNSAFE_PARENT')
    return raw


def crl_material(raw, authority, now, *, expired_predecessor=False):
    try:
        value = x509.load_pem_x509_crl(raw)
        require(value.public_bytes(Encoding.PEM) == raw and value.issuer == authority.subject and
                value.is_signature_valid(authority.public_key()), 'CRL_INVALID')
        require(value.last_update_utc <= utc(now) and (utc(now) < value.next_update_utc or expired_predecessor) and
                0 < (value.next_update_utc - value.last_update_utc).total_seconds() <= MAX_TEST_LIFETIME,
                'CRL_INVALID')
        number = value.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
        require(type(number) is int and 0 <= number < 2**63, 'CRL_INVALID')
        return value, number
    except (ValueError, TypeError, x509.ExtensionNotFound):
        raise ProfileError('CRL_INVALID') from None


def profile_material(raw, now, *, expired_predecessor=False):
    try:
        value = parse(raw)
        require(type(value) is dict and {'authority', 'revocations', 'family', 'gateway', 'minimum_crl'} <= set(value),
                'PROFILE_INVALID')
        require(all(type(value[name]) is str and re.fullmatch('[0-9a-f]{32}', value[name])
                    for name in ('family', 'gateway')), 'PROFILE_INVALID')
        require(type(value['minimum_crl']) is int and 0 <= value['minimum_crl'] < 2**63, 'PROFILE_INVALID')
        authority = x509.load_pem_x509_certificate(value['authority'].encode())
        require(authority.public_bytes(Encoding.PEM) == value['authority'].encode() and
                isinstance(authority.public_key(), Ed25519PublicKey), 'PROFILE_INVALID')
        authority.verify_directly_issued_by(authority)
        require(authority.extensions.get_extension_for_class(x509.BasicConstraints).value.ca, 'PROFILE_INVALID')
        usage = authority.extensions.get_extension_for_class(x509.KeyUsage).value
        require(usage.key_cert_sign and usage.crl_sign and authority.not_valid_before_utc <= utc(now) and
                (utc(now) < authority.not_valid_after_utc or expired_predecessor), 'PROFILE_INVALID')
        crl, number = crl_material(value['revocations'].encode(), authority, now, expired_predecessor=expired_predecessor)
        require(value['minimum_crl'] <= number, 'CRL_FLOOR_AHEAD')
        return value, authority, crl, number
    except ProfileError:
        raise
    except Exception:
        raise ProfileError('PROFILE_INVALID') from None


def renewal_target(current, incoming, now, *, expired_predecessor=False):
    previous, old_authority, old_crl, old_number = profile_material(current, now, expired_predecessor=expired_predecessor)
    target, new_authority, new_crl, new_number = profile_material(incoming, now)
    require(all(target[name] == previous[name] for name in ('family', 'gateway')), 'PROFILE_BINDING_CHANGED')
    require(old_authority.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo) ==
            new_authority.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo), 'PROFILE_ISSUER_CHANGED')
    require(new_number >= max(old_number, previous['minimum_crl']), 'CRL_ROLLBACK_REJECTED')
    require(new_crl.last_update_utc >= old_crl.last_update_utc, 'CRL_ROLLBACK_REJECTED')
    require(new_number != old_number or target['revocations'] == previous['revocations'], 'CRL_PAYLOAD_CONFLICT')
    target['minimum_crl'] = new_number
    return encode(target)


def floor_target(current, now):
    profile, _, _, number = profile_material(current, now)
    return encode(dict(profile, minimum_crl=number))


def exact_crl_target(current, payload, now):
    profile, authority, previous, old_number = profile_material(current, now)
    incoming, number = crl_material(payload, authority, now)
    require(number > max(old_number, profile['minimum_crl']) and
            incoming.last_update_utc >= previous.last_update_utc, 'CRL_ROLLBACK_REJECTED')
    return encode(dict(profile, revocations=payload.decode(), minimum_crl=number))


@dataclass(frozen=True, repr=False)
class DirectoryPort:
    path: Path
    expected: dict
    publisher_parent: dict
    publisher_contract: tuple

    def contract(self):
        require(bool(self.publisher_contract), 'PUBLISHER_CONTRACT_REQUIRED')
        result = []
        for spelling, expected_hash, expected_metadata in self.publisher_contract:
            path = Path(spelling)
            raw = read_regular(path, expected_metadata, 64 * 1024 * 1024, publisher_parent=self.publisher_parent)
            require(digest(raw) == expected_hash, 'PUBLISHER_CONTRACT_CHANGED')
            result.append((spelling, expected_hash, expected_metadata))
        return encode(result)

    def snapshot(self, profile, now, *, previous=None):
        require(self.path.parent == Path(self.publisher_parent['path']), 'PUBLISHER_BOUNDARY_CHANGED')
        contract = self.contract()
        raw = read_regular(self.path, self.expected, 8192, publisher_parent=self.publisher_parent)
        try:
            directory(raw, profile['family'], profile['gateway'], now_ns=int(Decimal(str(now)) * 1_000_000_000))
            value = parse(raw, 8192)
        except Exception:
            raise ProfileError('DIRECTORY_INVALID') from None
        require(self.contract() == contract, 'PUBLISHER_CONTRACT_CHANGED')
        current = dict(sha256=digest(raw), family=profile['family'], gateway=profile['gateway'],
                       issued=timestamp_ns(value['issued_at']), expires=timestamp_ns(value['expires_at']),
                       contract_sha256=digest(contract))
        if previous is not None:
            require(all(current[name] == previous[name] for name in ('family', 'gateway', 'contract_sha256')),
                    'DIRECTORY_BINDING_CHANGED')
            require(current['issued'] >= previous['issued'] and current['expires'] >= previous['expires'],
                    'DIRECTORY_TIME_ROLLBACK')
            require(current['sha256'] == previous['sha256'] or current['issued'] > previous['issued'],
                    'DIRECTORY_GENERATION_CONFLICT')
        return raw, current

    def read(self, profile, now):
        return self.snapshot(profile, now)[1]

    def after(self, previous, profile, now):
        return self.snapshot(profile, now, previous=previous)[1]


@dataclass(frozen=True, repr=False)
class Locator:
    profile: Path
    lock: Path
    operations: Path
    reader_gid: int
    directory_port: DirectoryPort

    @classmethod
    def load(cls, path):
        info = path.lstat()
        require(info.st_uid == 0 and stat.S_IMODE(info.st_mode) in (0o600, 0o640), 'LOCATOR_METADATA')
        raw = read_regular(path, metadata(info), 16384)
        value = parse(raw, 16384)
        require(type(value) is dict and set(value) == {'schema', 'lock_version', 'profile', 'lock', 'operations',
                'reader_gid', 'directory'}, 'LOCATOR_SCHEMA')
        require(type(value['schema']) is int and value['schema'] == 1 and type(value['lock_version']) is int and
                value['lock_version'] == 1 and type(value['reader_gid']) is int and 0 < value['reader_gid'] < 2**32 - 1,
                'LOCATOR_SCHEMA')
        material = value['directory']
        require(type(material) is dict and set(material) == {'path', 'metadata', 'publisher_parent', 'publisher_contract'},
                'LOCATOR_SCHEMA')
        require(type(material['metadata']) is dict and set(material['metadata']) == {'uid', 'gid', 'mode'} and
                all(type(number) is int and number >= 0 for number in material['metadata'].values()) and
                material['metadata']['mode'] in (0o600, 0o640), 'LOCATOR_SCHEMA')
        boundary = material['publisher_parent']
        require(type(boundary) is dict and set(boundary) == {'path', 'uid', 'gid', 'mode', 'device', 'inode'}, 'LOCATOR_SCHEMA')
        require(boundary['uid'] == 0 and type(boundary['mode']) is int and not boundary['mode'] & 0o002, 'LOCATOR_SCHEMA')
        absolute(Path(boundary['path']))
        contracts = material['publisher_contract']
        require(type(contracts) is list and 0 < len(contracts) <= 8, 'LOCATOR_SCHEMA')
        for contract in contracts:
            require(type(contract) is list and len(contract) == 3 and type(contract[0]) is str and
                    type(contract[1]) is str and re.fullmatch('[0-9a-f]{64}', contract[1]) and
                    type(contract[2]) is dict and set(contract[2]) == {'uid', 'gid', 'mode'} and
                    contract[2]['uid'] == 0 and type(contract[2]['mode']) is int and
                    not contract[2]['mode'] & 0o022, 'LOCATOR_SCHEMA')
        result = cls(Path(value['profile']), Path(value['lock']), Path(value['operations']), value['reader_gid'],
                     DirectoryPort(Path(material['path']), material['metadata'], boundary, tuple(contracts)))
        result.validate_reader()
        return result

    @property
    def profile_metadata(self):
        return dict(uid=0, gid=self.reader_gid, mode=0o640)

    def validate_reader(self):
        paths = (self.profile, self.lock, self.operations, self.directory_port.path)
        require(len(set(paths)) == len(paths), 'LOCATOR_PATH_CONFLICT')
        publisher = Path(self.directory_port.publisher_parent['path'])
        for path in paths:
            absolute(path)
        for path in paths[:3]:
            require(not path.is_relative_to(publisher), 'LOCATOR_PATH_CONFLICT')
        parents(self.profile)
        info = self.profile.parent.lstat()
        require(stat.S_ISDIR(info.st_mode) and metadata(info) == dict(uid=0, gid=self.reader_gid, mode=0o750),
                'PROFILE_PARENT_METADATA')
        read_regular(self.profile, self.profile_metadata, 49152)

    def validate(self):
        self.validate_reader()
        paths = (self.profile, self.lock, self.operations, self.directory_port.path)
        require(len(set(paths)) == len(paths), 'LOCATOR_PATH_CONFLICT')
        publisher = Path(self.directory_port.publisher_parent['path'])
        for path in paths:
            absolute(path)
        for path in paths[:3]:
            require(not path.is_relative_to(publisher), 'LOCATOR_PATH_CONFLICT')
            parents(path)
        for line in Path('/proc/self/mountinfo').read_text().splitlines():
            mounted = Path(re.sub(r'\\([0-7]{3})', lambda match: chr(int(match[1], 8)), line.split()[4]))
            require(not any(mounted.is_relative_to(boundary) for boundary in
                            (self.profile.parent, self.lock.parent, self.operations, publisher)), 'MATERIAL_MOUNT_UNSUPPORTED')
        require(self.profile.parent != self.operations and not self.profile.is_relative_to(self.operations) and
                not self.lock.is_relative_to(self.operations), 'LOCATOR_PATH_CONFLICT')
        info = self.operations.lstat()
        require(stat.S_ISDIR(info.st_mode) and metadata(info) == dict(uid=0, gid=0, mode=0o700), 'JOURNAL_METADATA')
        lock_parent = self.lock.parent.lstat()
        require(metadata(lock_parent) == dict(uid=0, gid=0, mode=0o700), 'LOCK_PARENT_METADATA')
        read_regular(self.lock, dict(uid=0, gid=0, mode=0o600), 4096, empty=True)
        read_regular(self.profile, self.profile_metadata, 49152)
        self.directory_port.contract()


def atomic_profile_replace(config, raw, *, before_replace, error_type=ProfileError):
    """The shared same-directory replacement primitive, called under the writer lock."""
    def check(condition, code):
        if not condition:
            raise error_type(code)
    path = config.profile
    config.read_material(path, 49152)
    before_parents = config.parents(path)
    parent_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    pending = '.' + path.name + '.' + secrets.token_hex(12)
    try:
        opened = os.fstat(parent_fd)
        check((opened.st_dev, opened.st_ino) == (path.parent.stat().st_dev, path.parent.stat().st_ino),
              'MATERIAL_METADATA_MISMATCH')
        descriptor = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent_fd)
        with os.fdopen(descriptor, 'wb') as output:
            try:
                os.fchown(output.fileno(), config.profile_uid, config.profile_gid)
                os.fchmod(output.fileno(), config.profile_mode)
                config.verify_material_fd(path, output.fileno())
            except (OSError, ValueError):
                raise error_type('MATERIAL_TEMP_METADATA_FAILED') from None
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        check(config.parents(path) == before_parents, 'MATERIAL_METADATA_MISMATCH')
        before_replace()
        check(config.parents(path) == before_parents, 'MATERIAL_METADATA_MISMATCH')
        descriptor = os.open(pending, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
        with os.fdopen(descriptor, 'rb') as source:
            config.verify_material_fd(path, source.fileno())
            check(source.read(len(raw) + 1) == raw, 'MATERIAL_TEMP_METADATA_FAILED')
        os.replace(pending, path.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        os.fsync(parent_fd)
        check(config.read_material(path, 49152) == raw, 'MATERIAL_METADATA_MISMATCH')
    finally:
        try:
            os.unlink(pending, dir_fd=parent_fd)
        except FileNotFoundError:
            pass
        os.close(parent_fd)


class ProfileStore:
    def __init__(self, locator, *, clock=time.time):
        self.locator, self.clock = locator, clock
        self.profile = locator.profile
        self.profile_uid, self.profile_gid, self.profile_mode = 0, locator.reader_gid, 0o640
        self._locked = None

    def parents(self, path):
        require(path == self.profile, 'PROFILE_PATH_FORBIDDEN')
        result = parents(path)
        require(metadata(path.parent.lstat()) == dict(uid=0, gid=self.profile_gid, mode=0o750),
                'PROFILE_PARENT_METADATA')
        return result

    def verify_material_fd(self, path, descriptor):
        require(path == self.profile, 'PROFILE_PATH_FORBIDDEN')
        info = os.fstat(descriptor)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and metadata(info) == self.locator.profile_metadata,
                'FILE_METADATA_MISMATCH')
        extended_metadata(descriptor)

    def read_material(self, path, limit):
        self.parents(path)
        return read_regular(path, self.locator.profile_metadata, limit)

    def read(self):
        return self.read_material(self.profile, 49152)

    @contextmanager
    def lock(self):
        require(os.geteuid() == 0 and self._locked is None, 'PROFILE_LOCK_REQUIRED')
        self.locator.validate()
        lock = self.locator.lock
        before_parents = parents(lock)
        descriptor = os.open(lock, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            info = os.fstat(descriptor)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and
                    metadata(info) == dict(uid=0, gid=0, mode=0o600) and identity(info) == identity(lock.lstat()),
                    'PROFILE_LOCK_INVALID')
            extended_metadata(descriptor)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ProfileError('PROFILE_TRANSACTION_BUSY') from None
            self._locked = (descriptor, info, before_parents)
            yield self
        finally:
            self._locked = None
            os.close(descriptor)

    def replace(self, raw, *, expected, permit):
        require(self._locked is not None, 'PROFILE_LOCK_REQUIRED')
        descriptor, lock_info, lock_parents = self._locked
        def ready():
            require(parents(self.locator.lock) == lock_parents and
                    identity(self.locator.lock.lstat()) == identity(lock_info) and
                    identity(os.fstat(descriptor)) == identity(lock_info), 'PROFILE_LOCK_INVALID')
            require(self.read() == expected, 'PROFILE_CAS_FAILED')
            permit()
        ready()
        atomic_profile_replace(self, raw, before_replace=ready)

    def transact(self, operation, action, *, expected_sha256, payload=None, permit, persist):
        require(action in ('credential_renewal', 'reconcile_current_floor', 'apply_exact_crl'), 'PROFILE_ACTION_FORBIDDEN')
        require(type(operation) is str and re.fullmatch('[a-zA-Z0-9_-]{16,96}', operation), 'PROFILE_OPERATION_INVALID')
        with self.lock():
            before = self.read()
            require(digest(before) == expected_sha256, 'PROFILE_CAS_FAILED')
            profile = profile_material(before, self.clock())[0]
            directory_before = self.locator.directory_port.read(profile, self.clock())
            if action == 'credential_renewal':
                target = renewal_target(before, payload, self.clock())
            elif action == 'reconcile_current_floor':
                require(payload is None, 'PROFILE_ACTION_FORBIDDEN')
                target = floor_target(before, self.clock())
            else:
                target = exact_crl_target(before, payload, self.clock())
            target_profile = profile_material(target, self.clock())[0]
            require(len(target) <= 49152, 'PROFILE_INVALID')
            record = dict(schema=1, operation=operation, action=action, before_sha256=digest(before),
                          target_sha256=digest(target), metadata=self.locator.profile_metadata,
                          directory_before=directory_before)
            def ready():
                permit()
                profile_material(self.read(), self.clock())
                profile_material(target, self.clock())
                self.locator.directory_port.after(directory_before, profile, self.clock())
            ready()
            persist(dict(record, state='PREPARED'), before, target)
            replaced = False
            try:
                persist(dict(record, state='REPLACING'), before, target)
                self.replace(target, expected=before, permit=ready)
                replaced = True
                directory_after = self.locator.directory_port.after(directory_before, target_profile, self.clock())
                profile_material(self.read(), self.clock())
                result = dict(record, state='COMMITTED', directory_after=directory_after)
                persist(result, before, target)
                return result
            except Exception:
                current = self.read()
                if current == target and (replaced or target != before):
                    self.replace(before, expected=target, permit=lambda: None)
                    persist(dict(record, state='ROLLED_BACK'), before, target)
                elif current == before:
                    persist(dict(record, state='NOT_APPLIED'), before, target)
                else:
                    persist(dict(record, state='UNKNOWN'), before, target)
                    raise ProfileError('PROFILE_ROLLBACK_CONFLICT') from None
                raise
