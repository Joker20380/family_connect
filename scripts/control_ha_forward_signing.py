"""Offline owner review/signature workflow; never capture, import, deployment or trust enrolment."""
import argparse
from contextlib import contextmanager, ExitStack
import hashlib
import json
import os
from pathlib import Path
import resource
import stat
import sys
import time

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from scripts import control_ha_forward_checkpoint as forward
from scripts.control_ha_import import ImportRejected, require


METADATA = ('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_gid', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')


def metadata(info):
    return tuple(getattr(info, name) for name in METADATA)


@contextmanager
def private_parent(path):
    path = Path(path)
    require(path.is_absolute() and path.name and '..' not in path.parts and len(path.parts) <= 64,
            'SIGNING_PATH')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    with ExitStack() as stack:
        parent = os.open('/', flags)
        stack.callback(os.close, parent)
        for part in path.parts[1:-1]:
            parent = os.open(part, flags, dir_fd=parent)
            stack.callback(os.close, parent)
        info = os.fstat(parent)
        require(info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700, 'SIGNING_PARENT')
        yield parent, path.name


def read_private(path, maximum, *, expected=None, exact=None):
    if expected is not None:
        require(forward.hexadecimal(expected), 'SIGNING_PIN_FORMAT')
    with private_parent(path) as (parent, name):
        descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent)
        with os.fdopen(descriptor, 'rb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode) and before.st_uid == os.geteuid() and before.st_nlink == 1
                    and stat.S_IMODE(before.st_mode) == 0o600 and 0 < before.st_size <= maximum
                    and (exact is None or before.st_size == exact), 'SIGNING_FILE')
            raw = stream.read(maximum + 1)
            after = os.fstat(stream.fileno())
            require(metadata(before) == metadata(after) and len(raw) == before.st_size, 'SIGNING_INPUT_CHANGED')
            require(metadata(after) == metadata(os.stat(name, dir_fd=parent, follow_symlinks=False)),
                    'SIGNING_INPUT_REPLACED')
    require(expected is None or hashlib.sha256(raw).hexdigest() == expected, 'SIGNING_INPUT_PIN')
    return raw


def write_signature(path, signature):
    require(type(signature) is bytes and len(signature) == 64, 'SIGNING_OUTPUT_FORMAT')
    with private_parent(path) as (parent, name):
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
        with os.fdopen(os.open(name, flags, 0o600, dir_fd=parent), 'wb') as output:
            require(output.write(signature) == len(signature), 'SIGNING_SHORT_WRITE')
            output.flush()
            os.fsync(output.fileno())
            info = os.fstat(output.fileno())
            require(stat.S_IMODE(info.st_mode) == 0o600 and info.st_uid == os.geteuid()
                    and info.st_nlink == 1 and info.st_size == 64
                    and metadata(info) == metadata(os.stat(name, dir_fd=parent, follow_symlinks=False)),
                    'SIGNING_OUTPUT_CHANGED')
        os.fsync(parent)
        with private_parent(path) as (current_parent, _name):
            before, after = os.fstat(parent), os.fstat(current_parent)
            require((before.st_dev, before.st_ino) == (after.st_dev, after.st_ino), 'SIGNING_PARENT_CHANGED')


def check_request(request, trusted_key, request_sha256, trusted_key_sha256, minimum_sequence, now):
    document = forward.checked_request(request)
    require(forward.hexadecimal(request_sha256) and forward.digest(request) == request_sha256,
            'SIGNING_REQUEST_PIN')
    require(type(trusted_key) is bytes and len(trusted_key) == 32 and forward.hexadecimal(trusted_key_sha256)
            and forward.digest(trusted_key) == trusted_key_sha256, 'SIGNING_TRUST_PIN')
    require(forward.integer(minimum_sequence) and document['sequence'] > minimum_sequence, 'SIGNING_REPLAY_FLOOR')
    require(forward.integer(now, document['captured_at']) and now < document['expires_at'], 'SIGNING_TIME')
    require(trusted_key_sha256 != document['issuer_public_sha256'], 'SIGNING_DEDICATED_KEY_REQUIRED')
    return document


def execute(args, *, clock=None):
    clock = time.time if clock is None else clock
    request = read_private(args.request, forward.MAX_REQUEST, expected=args.request_sha256)
    trusted_key = read_private(args.trusted_key, 32, exact=32, expected=args.trusted_key_sha256)

    def checked():
        return check_request(request, trusted_key, args.request_sha256, args.trusted_key_sha256,
                             args.minimum_sequence, int(clock()))

    document = checked()
    signature = None
    result = 'FORWARD_REQUEST_REVIEWED_NOT_APPROVED'
    if args.command == 'sign':
        require(args.confirm_offline_only, 'SIGNING_SCOPE_CONFIRMATION')
        require('update-signing' not in Path(args.key_file).parts, 'SIGNING_RELEASE_KEY_FORBIDDEN')
        seed = read_private(args.key_file, 32, exact=32)
        signer = Ed25519PrivateKey.from_private_bytes(seed)
        require(signer.public_key().public_bytes_raw() == trusted_key, 'SIGNING_KEY_MISMATCH')
        checked()
        signature = signer.sign(forward.DOMAIN + request)
        Ed25519PublicKey.from_public_bytes(trusted_key).verify(signature, forward.DOMAIN + request)
        checked()
        write_signature(args.output, signature)
        checked()
        result = 'FORWARD_OFFLINE_SIGNATURE_WRITTEN'
    elif args.command == 'verify':
        signature = read_private(args.signature, 64, exact=64, expected=args.signature_sha256)
        Ed25519PublicKey.from_public_bytes(trusted_key).verify(signature, forward.DOMAIN + request)
        checked()
        result = 'FORWARD_OFFLINE_SIGNATURE_VALID'
    else:
        require(args.command == 'review', 'SIGNING_COMMAND')
    return dict(result=result, purpose=forward.PURPOSE, action=forward.ACTION,
                request_sha256=args.request_sha256, trusted_key_sha256=args.trusted_key_sha256,
                signature_sha256=forward.digest(signature) if signature is not None else None,
                sequence=document['sequence'], minimum_sequence=args.minimum_sequence,
                captured_at=document['captured_at'], expires_at=document['expires_at'],
                independent_approval_established=False, trust_enrolled=False, replay_floor_updated=False,
                material_validation_performed=False, capture_permitted=False,
                database_import_authorized=False, activation_authorized=False)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ImportRejected('SIGNING_ARGUMENTS')


def parser():
    result = Parser(description=__doc__)
    commands = result.add_subparsers(dest='command', required=True)
    for command in ('review', 'sign', 'verify'):
        action = commands.add_parser(command)
        action.add_argument('--request', type=Path, required=True)
        action.add_argument('--request-sha256', required=True)
        action.add_argument('--trusted-key', type=Path, required=True)
        action.add_argument('--trusted-key-sha256', required=True)
        action.add_argument('--minimum-sequence', type=int, required=True)
        if command == 'sign':
            action.add_argument('--key-file', type=Path, required=True)
            action.add_argument('--output', type=Path, required=True)
            action.add_argument('--confirm-offline-only', action='store_true')
        if command == 'verify':
            action.add_argument('--signature', type=Path, required=True)
            action.add_argument('--signature-sha256', required=True)
    return result


def main(argv=None):
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    try:
        receipt = execute(parser().parse_args(argv))
        print(json.dumps(receipt, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, AttributeError, KeyError, OverflowError, RecursionError,
            ImportRejected, InvalidSignature):
        print('FORWARD_SIGNING_REFUSED', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
