"""Purpose-separated HA AES key from an encrypted KeePassXC attachment, never a signing key."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import secrets
import subprocess
import tarfile
from types import SimpleNamespace

from scripts.signing_key import LIMIT, private_file, vault_archive

DATABASE = 'Family-Connect.kdbx'
ENTRY = 'HA custody encryption'
ATTACHMENT = 'recovery.tar.gz'
MEMBER = 'ha-custody/aes256gcm.raw'
MANIFEST = 'HA-ENCRYPTION.json'
PURPOSE = 'family-connect/ha-custody-encryption/v1'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def archive(key):
    require(type(key) is bytes and len(key) == 32, 'HA_KEY_LENGTH')
    metadata = dict(purpose=PURPOSE, algorithm='AES-256-GCM', member=MEMBER, bytes=32,
                    sha256=hashlib.sha256(key).hexdigest())
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w:gz') as container:
        for name, data in ((MEMBER, key), (MANIFEST, json.dumps(metadata, sort_keys=True).encode())):
            item = tarfile.TarInfo(name)
            item.size, item.mode = len(data), 0o600
            container.addfile(item, io.BytesIO(data))
    return output.getvalue()


def decode(raw):
    require(type(raw) is bytes and len(raw) <= 8192, 'HA_ARCHIVE_SIZE')
    files = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode='r|gz') as container:
            for item in container:
                require(item.name in (MEMBER, MANIFEST) and item.name not in files and item.isfile() and
                        not item.pax_headers and 0 <= item.size <= 1024, 'HA_ARCHIVE_MEMBER')
                files[item.name] = container.extractfile(item).read(1025)
        require(set(files) == {MEMBER, MANIFEST}, 'HA_ARCHIVE_SET')
        key = files[MEMBER]
        require(len(key) == 32, 'HA_KEY_LENGTH')
        expected = dict(purpose=PURPOSE, algorithm='AES-256-GCM', member=MEMBER, bytes=32,
                        sha256=hashlib.sha256(key).hexdigest())
        require(files[MANIFEST] == json.dumps(expected, sort_keys=True).encode(), 'HA_KEY_PURPOSE_OR_INTEGRITY')
        return key
    except (tarfile.TarError, EOFError, OSError, UnicodeError):
        raise ValueError('HA_ARCHIVE_INVALID') from None


class ConsumerRefused(ValueError):
    def __init__(self, category, exit_status=None):
        super().__init__('HA_MEMORY_CONSUMER_REFUSED')
        self.category, self.exit_status = category, exit_status


def memory_archive(vault, password):
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    require(type(password) is bytes and password and b'\n' not in password and b'\r' not in password,
            'HA_LOCAL_UNLOCK_INPUT')
    database = memory = None
    try:
        database = private_file(vault)
        require(os.fstat(database).st_size <= LIMIT, 'HA_VAULT_SIZE')
        memory = os.memfd_create('fc-ha-consumer', os.MFD_CLOEXEC)
        result = subprocess.run(['/usr/bin/keepassxc-cli', 'attachment-export', '-q',
            f'/proc/self/fd/{database}', ENTRY, ATTACHMENT, f'/proc/self/fd/{memory}'],
            input=password + b'\n', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            pass_fds=(database, memory), timeout=120)
        if result.returncode:
            raise ConsumerRefused('NATIVE_EXIT', result.returncode)
        require(os.fstat(memory).st_size <= 8192, 'HA_ARCHIVE_SIZE')
        os.lseek(memory, 0, os.SEEK_SET)
        return decode(os.read(memory, 8193))
    except ConsumerRefused:
        raise
    except subprocess.TimeoutExpired:
        raise ConsumerRefused('TIMEOUT') from None
    except OSError:
        raise ConsumerRefused('PRIVATE_INPUT_REFUSED') from None
    except ValueError:
        raise ConsumerRefused('FORMAT_REFUSED', 0 if memory is not None else None) from None
    finally:
        for descriptor in (database, memory):
            if descriptor is not None:
                os.close(descriptor)


def load(vault, *, password=None):
    vault = Path(vault)
    require(vault.name == DATABASE, 'HA_VAULT_DATABASE')
    if password is not None:
        return memory_archive(vault, password)
    try:
        raw = vault_archive(SimpleNamespace(vault=vault, vault_entry=ENTRY, vault_password_dialog=True,
            vault_purpose='HA custody encryption — unlock local vault'))
        return decode(raw)
    except Exception:
        raise ValueError('HA_VAULT_KEY_UNAVAILABLE_PRIVATE_DIAGNOSTICS_SUPPRESSED') from None


def prepare(vault, destination):
    vault, destination = Path(vault), Path(destination)
    require(vault.name == DATABASE, 'HA_VAULT_DATABASE')
    require(destination.is_absolute() and not any(item.is_symlink() for item in
            (destination, *destination.parents)), 'HA_CANDIDATE_PATH')
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    descriptor = private_file(vault)
    password = key = payload = None
    memory = None
    try:
        require(os.fstat(descriptor).st_size <= LIMIT, 'HA_VAULT_SIZE')
        encrypted = os.read(descriptor, LIMIT + 1)
        require(len(encrypted) == os.fstat(descriptor).st_size, 'HA_VAULT_CHANGED')
        destination.mkdir(mode=0o700, exist_ok=False)
        require(destination.stat().st_uid == os.getuid() and destination.stat().st_mode & 0o777 == 0o700,
                'HA_CANDIDATE_PERMISSIONS')
        candidate = destination / DATABASE
        output = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(output, 'wb') as stream:
            stream.write(encrypted)
            stream.flush()
            os.fsync(stream.fileno())
        dialog = subprocess.run(['/usr/bin/zenity', '--password',
            '--title=Family Connect: prepare separate HA encryption entry',
            '--text=Unlock Family-Connect.kdbx. Only a new encrypted candidate is modified; '
                   'the current vault is not replaced. No signing key is used.'],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=600)
        require(dialog.returncode == 0, 'HA_LOCAL_UNLOCK_CANCELLED')
        password = dialog.stdout.rstrip(b'\n')
        dialog = None
        require(password and b'\n' not in password and b'\r' not in password, 'HA_LOCAL_UNLOCK_INPUT')

        def cli(*arguments, descriptors=()):
            result = subprocess.run(['/usr/bin/keepassxc-cli', *arguments], input=password + b'\n',
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, pass_fds=descriptors, timeout=120)
            require(result.returncode == 0, 'HA_VAULT_CANDIDATE_COMMAND_REFUSED')

        cli('add', '-q', str(candidate), ENTRY)
        key = secrets.token_bytes(32)
        payload = archive(key)
        memory = os.memfd_create('fc-ha-encryption-attachment', os.MFD_CLOEXEC)
        os.write(memory, payload)
        cli('attachment-import', '-q', str(candidate), ENTRY, ATTACHMENT,
            f'/proc/self/fd/{memory}', descriptors=(memory,))
        os.ftruncate(memory, 0)
        os.lseek(memory, 0, os.SEEK_SET)
        cli('attachment-export', '-q', str(candidate), ENTRY, ATTACHMENT,
            f'/proc/self/fd/{memory}', descriptors=(memory,))
        os.lseek(memory, 0, os.SEEK_SET)
        require(decode(os.read(memory, 8193)) == key, 'HA_CANDIDATE_READBACK')
        os.lseek(descriptor, 0, os.SEEK_SET)
        require(os.read(descriptor, LIMIT + 1) == encrypted and vault.read_bytes() == encrypted,
                'HA_ORIGINAL_VAULT_CHANGED')
        candidate.chmod(0o600)
        check = private_file(candidate)
        try:
            os.fsync(check)
        finally:
            os.close(check)
        return dict(result='HA_ENCRYPTED_VAULT_CANDIDATE_VERIFIED_NOT_ACTIVATED', purpose=PURPOSE,
                    entry=ENTRY, attachment=ATTACHMENT, member=MEMBER, original_preserved=True,
                    independent_custody=False, encrypted_kit=False)
    finally:
        password = key = payload = None
        os.close(descriptor)
        if memory is not None:
            os.close(memory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('check', 'prepare'))
    parser.add_argument('--vault', type=Path,
        default=Path.home() / '.local/share/family-connect-vault' / DATABASE)
    parser.add_argument('--destination', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'check':
            require(args.destination is None, 'HA_CHECK_ARGUMENTS')
            load(args.vault)
            print('HA_WRAPPING_KEY_MEMORY_READ_PASS; no kit or independent custody claimed')
        else:
            require(args.destination is not None, 'HA_CANDIDATE_DESTINATION_REQUIRED')
            print(json.dumps(prepare(args.vault, args.destination), sort_keys=True))
    except Exception:
        parser.exit(1, 'HA_KEY_WORKFLOW_REFUSED; private diagnostics suppressed; preserve any encrypted candidate\n')


if __name__ == '__main__':
    main()
