"""Reference RNS identities and independent WireGuard keys, without networking.

POSIX storage is for the Linux reference integration only. Native applications
must supply their OS secure storage; this module never exports private keys as
part of enrollment. Corrupt or unsafe existing stores fail closed.
"""
import base64
import json
import os
import secrets
import stat
from contextlib import contextmanager
from pathlib import Path

import RNS
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

BINDING_DOMAIN = b'family-connect/transport-key-binding/v1\x00'


def _b64(raw):
    return base64.b64encode(raw).decode('ascii')


def _decode(value, size):
    if type(value) is not str or len(value) > 256:
        raise ValueError('invalid public field')
    try:
        raw = base64.b64decode(value, validate=True)
    except ValueError:
        raise ValueError('invalid public encoding') from None
    if len(raw) != size or _b64(raw) != value:
        raise ValueError('invalid public field')
    return raw


def _binding(public_identity, wireguard_public_key, challenge, audience):
    _decode(public_identity, 64)
    _decode(wireguard_public_key, 32)
    _decode(challenge, 32)
    # Audience is a server-configured protocol identifier, never a request URL.
    if type(audience) is not str or audience not in {'family-connect/enrollment/v1'}:
        raise ValueError('invalid enrollment audience')
    return dict(schema_version=1, public_identity=public_identity,
                wireguard_public_key=wireguard_public_key, challenge=challenge,
                audience=audience, transport='wireguard')


def _message(binding):
    return BINDING_DOMAIN + json.dumps(binding, sort_keys=True, separators=(',', ':')).encode()


class DeviceIdentity:
    """Private material is deliberately omitted from repr and public enrollment."""

    def __init__(self, identity, wireguard_key):
        self._identity = identity
        self._wireguard_key = wireguard_key

    @classmethod
    def generate(cls):
        return cls(RNS.Identity(), X25519PrivateKey.generate())

    @property
    def reference(self):
        return self._identity.hash.hex()

    @property
    def public_identity(self):
        return _b64(self._identity.get_public_key())

    @property
    def wireguard_public_key(self):
        return _b64(self._wireguard_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw))

    def prove_transport_key(self, challenge, audience='family-connect/enrollment/v1'):
        binding = _binding(self.public_identity, self.wireguard_public_key, challenge, audience)
        return {**binding, 'signature': _b64(self._identity.sign(_message(binding)))}


def verify_transport_key_proof(proof, *, expected_challenge,
                               audience='family-connect/enrollment/v1'):
    """Verify ownership only, NOT entitlement or single-use challenge consumption.

The registration service MUST fetch a live challenge from its own database,
atomically consume it, and authorize entitlement before registering this key.
An identity signature binds a claimed WG public key; the WG handshake separately
proves possession of the WG private key.
"""
    fields = {'schema_version', 'public_identity', 'wireguard_public_key',
              'challenge', 'audience', 'transport', 'signature'}
    if type(proof) is not dict or set(proof) != fields:
        raise ValueError('invalid ownership proof')
    if type(proof['schema_version']) is not int or proof['schema_version'] != 1:
        raise ValueError('unsupported ownership schema')
    if proof['transport'] != 'wireguard':
        raise ValueError('unsupported transport')
    binding = _binding(proof['public_identity'], proof['wireguard_public_key'],
                       proof['challenge'], proof['audience'])
    _decode(expected_challenge, 32)
    if binding['challenge'] != expected_challenge or binding['audience'] != audience:
        raise ValueError('ownership challenge mismatch')
    identity = RNS.Identity(create_keys=False)
    identity.load_public_key(_decode(binding['public_identity'], 64))
    if not identity.validate(_decode(proof['signature'], 64), _message(binding)):
        raise ValueError('invalid ownership signature')
    return identity.hash.hex()


@contextmanager
def _private_directory(path):
    if os.name != 'posix':
        raise RuntimeError('native secure storage required on this platform')
    path = Path(path)
    try:
        path.mkdir(mode=0o700)
    except FileExistsError:
        pass
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError('unsafe identity directory')
        yield fd
    finally:
        os.close(fd)


def _read_key(directory, name, size):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
            raise ValueError('unsafe private key file')
        raw = os.read(fd, size + 1)
        if len(raw) != size:
            raise ValueError('invalid private key file')
        return raw
    finally:
        os.close(fd)


def _create_key(directory, name, raw):
    # Publish a fully written file without overwriting another process's key.
    temporary = '.key-' + secrets.token_hex(16)
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 0o600, dir_fd=directory)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, name, src_dir_fd=directory, dst_dir_fd=directory,
                follow_symlinks=False)
    finally:
        os.unlink(temporary, dir_fd=directory)
        os.fsync(directory)


def load_or_create(path):
    """Persist independent keys atomically under a caller-owned POSIX directory.

The parent must be trusted application storage. Never pass a shared temporary
or remotely supplied path. The lock serializes first enrollment across processes.
Missing transport key may be regenerated; an existing corrupt key is never reset.
"""
    import fcntl
    with _private_directory(path) as directory:
        lock = os.open('.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                       0o600, dir_fd=directory)
        try:
            info = os.fstat(lock)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
                raise ValueError('unsafe identity lock')
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                raw = _read_key(directory, 'reticulum.key', 64)
            except FileNotFoundError:
                # A partial store with a transport key must never silently acquire
                # a replacement identity after loss of the permanent identity.
                try:
                    os.stat('wireguard.key', dir_fd=directory, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    raise ValueError('missing permanent identity') from None
                raw = RNS.Identity().get_private_key()
                _create_key(directory, 'reticulum.key', raw)
            identity = RNS.Identity(create_keys=False)
            if not identity.load_private_key(raw):
                raise ValueError('invalid permanent identity')
            try:
                wg_raw = _read_key(directory, 'wireguard.key', 32)
            except FileNotFoundError:
                wg_raw = X25519PrivateKey.generate().private_bytes_raw()
                _create_key(directory, 'wireguard.key', wg_raw)
            return DeviceIdentity(identity, X25519PrivateKey.from_private_bytes(wg_raw))
        finally:
            os.close(lock)
