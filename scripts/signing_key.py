"""Local signing-key sources. Never prints passwords, key bytes or CLI diagnostics."""
import base64
import getpass
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import tarfile

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

LIMIT = 16 * 1024 * 1024


def arguments(parser):
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument('--key', type=Path)
    sources.add_argument('--vault', type=Path)
    parser.add_argument('--vault-entry')
    parser.add_argument('--vault-member')
    parser.add_argument('--vault-public-key', type=Path)
    parser.add_argument('--vault-password-dialog', action='store_true')


def private_file(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    info = os.fstat(fd)
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or
            info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600):
        os.close(fd)
        raise ValueError('unsafe private file')
    return fd


def archive_key(raw, member):
    path = PurePosixPath(member)
    if path.is_absolute() or '..' in path.parts or str(path) != member:
        raise ValueError('invalid vault member')
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r|gz') as archive:
        key = manifest = None
        total = count = 0
        for item in archive:
            total += item.size
            count += 1
            if item.size < 0 or total > LIMIT or count > 1024:
                raise ValueError('vault archive limit')
            if item.name not in {member, 'PRIVATE-INVENTORY.json'}:
                continue
            if not item.isfile():
                raise ValueError('vault member must be a regular file')
            if item.name == member:
                if key is not None or item.size != 32:
                    raise ValueError('invalid or duplicate signing key')
                key = archive.extractfile(item).read(33)
            else:
                if manifest is not None or item.size > 1024 * 1024:
                    raise ValueError('invalid or duplicate inventory')
                manifest = json.loads(archive.extractfile(item).read())
        if key is None or manifest is None:
            raise ValueError('missing vault key or inventory')
        records = [v for v in manifest['files'] if v['path'] == member]
        if (len(records) != 1 or records[0]['size'] != 32 or
                records[0]['sha256'] != hashlib.sha256(key).hexdigest()):
            raise ValueError('vault inventory mismatch')
        return key


def vault_bytes(args):
    if not args.vault_entry or not args.vault_member or not args.vault_public_key:
        raise ValueError('vault entry, member and public anchor are required')
    if not hasattr(os, 'memfd_create'):
        raise ValueError('vault signing requires Linux memfd')
    import resource
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    database = private_file(args.vault)
    memory = os.memfd_create('fc-signing-attachment', os.MFD_CLOEXEC)
    password = None
    stage = 'password input'
    try:
        if os.fstat(database).st_size > LIMIT:
            raise ValueError('vault size limit')
        if args.vault_password_dialog:
            result = subprocess.run(['/usr/bin/zenity', '--password',
                '--title=Family Connect: master password for local signing'],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=600)
            if result.returncode:
                raise ValueError('password entry cancelled')
            password = result.stdout.rstrip(b'\n')
            result = None
        else:
            # Refuse getpass's insecure non-TTY fallback.
            with open('/dev/tty', 'w') as terminal:
                password = getpass.getpass('KeePassXC master password: ', stream=terminal).encode()
        if not password or b'\n' in password or b'\r' in password:
            raise ValueError('invalid password input')
        stage = 'attachment export'
        result = subprocess.run(['/usr/bin/keepassxc-cli', 'attachment-export', '-q',
            f'/proc/self/fd/{database}', args.vault_entry, 'recovery.tar.gz',
            f'/proc/self/fd/{memory}'], input=password + b'\n',
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            pass_fds=(database, memory), timeout=120)
        password = None
        if result.returncode or os.fstat(memory).st_size > LIMIT:
            raise ValueError('vault export failed')
        stage = 'archive verification'
        os.lseek(memory, 0, os.SEEK_SET)
        with os.fdopen(os.dup(memory), 'rb') as source:
            return archive_key(source.read(LIMIT + 1), args.vault_member)
    except Exception:
        raise ValueError(f'vault signing key unavailable at {stage}; private diagnostics suppressed') from None
    finally:
        password = None
        os.close(database)
        os.close(memory)


def load(args):
    if args.key is not None:
        if args.vault_entry or args.vault_member or args.vault_public_key or args.vault_password_dialog:
            raise ValueError('vault options require --vault')
        fd = private_file(args.key)
        try:
            raw = os.read(fd, 33)
        finally:
            os.close(fd)
    else:
        raw = vault_bytes(args)
    key = Ed25519PrivateKey.from_private_bytes(raw)
    if args.vault is not None:
        anchor = base64.b64decode(args.vault_public_key.read_bytes().strip(), validate=True)
        if key.public_key().public_bytes_raw() != anchor:
            raise ValueError('vault key does not match public anchor')
    return key


def main():
    """Verify source and (vault mode) pinned public key without signing anything."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    arguments(parser)
    load(parser.parse_args())
    print('Signing-key source verified; no signature or private export produced.')


if __name__ == '__main__':
    main()
