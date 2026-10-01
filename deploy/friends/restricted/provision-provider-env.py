"""Owner-interactive, offline-only provider input. Never starts a service."""
import getpass
import os
from pathlib import Path
import resource
import stat
import subprocess
import sys
import warnings


DESTINATION = Path('/opt/apps/family_connect/friends-restricted')
VARIABLE = 'YANDEX_TELEMOST_OAUTH_TOKEN'
UNITS = ('family-connect-restricted-bootstrap.service',
         'family-connect-restricted-sync.service',
         'family-connect-restricted-sync.timer')


def provider_value(value):
    if not value or any(character in value for character in '\r\n\0') or len(value.encode('utf-8')) > 4096:
        raise ValueError('provider configuration rejected')
    return value


def encode(value):
    value = provider_value(value)
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    return (VARIABLE + '="' + escaped + '"\n').encode('utf-8')


def parse(raw):
    text = raw.decode('utf-8')
    prefix = VARIABLE + '="'
    if not text.startswith(prefix) or not text.endswith('"\n'):
        raise ValueError('provider configuration rejected')
    encoded = text[len(prefix):-2]
    characters = []
    escaped = False
    for character in encoded:
        if escaped:
            if character not in ('\\', '"'):
                raise ValueError('provider configuration rejected')
            characters.append(character)
            escaped = False
        elif character == '\\':
            escaped = True
        elif character == '"':
            raise ValueError('provider configuration rejected')
        else:
            characters.append(character)
    if escaped:
        raise ValueError('provider configuration rejected')
    value = provider_value(''.join(characters))
    if encode(value) != raw:
        raise ValueError('provider configuration rejected')
    return value


def safe_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    metadata = os.fstat(descriptor)
    if metadata.st_uid != 0 or metadata.st_mode & 0o022:
        os.close(descriptor)
        raise ValueError('unsafe configuration directory')
    return descriptor


def validate(directory):
    descriptor = os.open('provider.env', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    with os.fdopen(descriptor, 'rb') as source:
        metadata = os.fstat(source.fileno())
        if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != 0 or metadata.st_gid != 0
                or stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_nlink != 1):
            raise ValueError('unsafe provider configuration')
        parse(source.read(16385))


def write_new(directory, value):
    raw = encode(value)
    parse(raw)
    descriptor = os.open('provider.env', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=directory)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            os.fchmod(output.fileno(), 0o600)
            os.fchown(output.fileno(), 0, 0)
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        os.fsync(directory)
        validate(directory)
    except BaseException:
        os.unlink('provider.env', dir_fd=directory)
        os.fsync(directory)
        raise


def runtime_guard():
    for unit in UNITS:
        result = subprocess.run(['systemctl', 'show', unit, '-p', 'LoadState'],
                                capture_output=True, text=True, timeout=10)
        if result.stdout.strip() != 'LoadState=not-found':
            raise ValueError('restricted service configuration changed; stop')


def main():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.umask(0o077)
    if os.geteuid() != 0 or os.getegid() != 0 or len(sys.argv) != 1:
        raise ValueError('root interactive execution required')
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        raise ValueError('interactive terminal required; no fallback input')
    runtime_guard()
    parent = safe_directory(DESTINATION.parent)
    try:
        try:
            os.mkdir(DESTINATION.name, 0o700, dir_fd=parent)
        except FileExistsError:
            pass
        directory = os.open(DESTINATION.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=parent)
    finally:
        os.close(parent)
    try:
        metadata = os.fstat(directory)
        if metadata.st_uid != 0 or metadata.st_gid != 0 or stat.S_IMODE(metadata.st_mode) != 0o700:
            raise ValueError('unsafe provider destination')
        try:
            os.stat('provider.env', dir_fd=directory, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError('provider configuration already exists; not overwritten')
        with warnings.catch_warnings():
            warnings.simplefilter('error', getpass.GetPassWarning)
            value = getpass.getpass('Yandex Telemost OAuth (hidden; paste token, then Enter): ')
        runtime_guard()
        write_new(directory, value)
        del value
    finally:
        os.close(directory)
    print('Provider configuration: exists=yes owner=root mode=0600 nonempty=yes schema=PASS')
    print('No service started; no provider request made. Notify the operator without sending the token.')


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt):
        print('Provider input stopped; no token displayed. Do not retry without checking file state.', file=sys.stderr)
        sys.exit(1)
