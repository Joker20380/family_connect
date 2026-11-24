"""Explicit pinned one-shot receiver admission; no installation, retry or remote cancellation."""
import argparse
from contextlib import ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import stat
import subprocess
import sys
import zipfile

from .capture_gate import Busy, Gate, GateError

ENTRIES = {
    'awg-register': ('register', 'script', ('register',), True),
    'mailbox-membership': ('chat-sync', 'script', (), False),
    'profile-snapshot': ('restricted-sync', 'archive', (), False),
    'profile-launcher': ('restricted-sync', 'profile-launcher', (), False),
    'fleet-agent': ('fleet-v1', 'script', (), False),
}
BOOTSTRAP = '''import json, os, runpy, sys, types
descriptor, spelling, kind, arguments, libraries, profile_command = json.loads(sys.argv[1])
if kind == 'profile-launcher':
    native_exec = os.execve
    def snapshot_exec(executable, argv, environment):
        expected_environment = {'PATH': '/usr/bin:/bin', 'LANG': 'C',
                                'SSH_ORIGINAL_COMMAND': 'restricted-sync'}
        if (executable != profile_command[0] or argv != profile_command or
                environment != expected_environment or os.getcwd() != '/'):
            raise ValueError('CAPTURE_PROFILE_EXEC')
        os.set_inheritable(libraries[0], True)
        native_exec(executable, [*argv[:-1], '/proc/self/fd/' + str(libraries[0])], environment)
    os.execve = snapshot_exec
else:
    sys.path[:0] = ['/proc/self/fd/' + str(item) for item in libraries]
sys.argv = [spelling, *arguments]
if kind == 'archive':
    runpy.run_path('/proc/self/fd/' + str(descriptor), run_name='__main__')
else:
    module = types.ModuleType('__main__')
    module.__file__ = spelling
    module.__package__ = None
    sys.modules['__main__'] = module
    with os.fdopen(descriptor, 'rb') as source:
        code = compile(source.read(), spelling, 'exec')
    exec(code, module.__dict__)
'''


def require(condition):
    if not condition:
        raise ValueError('CAPTURE_BINDING_REFUSED')


def unique(pairs):
    value = {}
    for name, item in pairs:
        require(name not in value)
        value[name] = item
    return value


def absolute(spelling):
    require(type(spelling) is str and spelling.startswith('/') and
            spelling == os.path.normpath(spelling) and not spelling.startswith('//'))
    path = Path(spelling)
    require(all(not item.is_symlink() for item in (path, *path.parents)))
    return path


def identity(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_uid, info.st_gid,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def pinned(stack, spelling, digest, limit, *, private=False):
    path = absolute(spelling)
    require(type(digest) is str and re.fullmatch('[0-9a-f]{64}', digest))
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
    stack.callback(os.close, descriptor)
    before = os.fstat(descriptor)
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
            before.st_uid in (0, os.geteuid()) and not before.st_mode & 0o7022 and
            0 < before.st_size <= limit)
    if private:
        require(before.st_uid == os.geteuid() and stat.S_IMODE(before.st_mode) == 0o600)
    with os.fdopen(os.dup(descriptor), 'rb') as source:
        raw = source.read(limit + 1)
    require(len(raw) <= limit and hashlib.sha256(raw).hexdigest() == digest and
            identity(os.fstat(descriptor)) == identity(before) and
            identity(path.stat(follow_symlinks=False)) == identity(before))
    snapshot = os.memfd_create('fc-capture-source', os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
    stack.callback(os.close, snapshot)
    with os.fdopen(os.dup(snapshot), 'wb') as output:
        output.write(raw)
    os.lseek(snapshot, 0, os.SEEK_SET)
    fcntl.fcntl(snapshot, fcntl.F_ADD_SEALS,
                fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL)
    return snapshot, raw


def archive(descriptor):
    with os.fdopen(os.dup(descriptor), 'rb') as source:
        with zipfile.ZipFile(source) as bundle:
            names = bundle.namelist()
            require(names and len(names) == len(set(names)))
            require(all(not name.startswith('/') and '..' not in Path(name).parts for name in names))
    os.lseek(descriptor, 0, os.SEEK_SET)


def load(stack, path, digest):
    _, raw = pinned(stack, str(path), digest, 65536, private=True)
    binding = json.loads(raw, object_pairs_hook=unique)
    require(type(binding) is dict and set(binding) ==
            {'schema', 'kind', 'capture_gate', 'entry_path', 'entry_sha256', 'libraries'} and
            type(binding['schema']) is int and binding['schema'] == 1 and
            type(binding['kind']) is str and binding['kind'] in ENTRIES)
    command, form, arguments, local = ENTRIES[binding['kind']]
    original = os.environ.get('SSH_ORIGINAL_COMMAND')
    require(original == command or (local and original is None and not os.environ.get('SSH_CONNECTION')))
    gate = Gate(absolute(binding['capture_gate']))
    entry, native = pinned(stack, binding['entry_path'], binding['entry_sha256'], 32 * 1024 * 1024)
    if form == 'archive':
        archive(entry)
    else:
        compile(native, binding['entry_path'], 'exec')
    require(type(binding['libraries']) is list and len(binding['libraries']) <= 8)
    paths, libraries = {binding['entry_path']}, []
    for library in binding['libraries']:
        require(type(library) is dict and set(library) == {'path', 'sha256'} and
                type(library['path']) is str and library['path'] not in paths)
        paths.add(library['path'])
        descriptor, _ = pinned(stack, library['path'], library['sha256'], 32 * 1024 * 1024)
        archive(descriptor)
        libraries.append(descriptor)
    profile_command = None
    if form == 'profile-launcher':
        from .capture_profile import command
        profile_command = command(native, binding['libraries'], sys.executable)
    return gate, (entry, binding['entry_path'], form, arguments, libraries, profile_command)


def run(gate, invocation):
    entry, spelling, form, arguments, libraries, profile_command = invocation
    with gate.operation():
        process = subprocess.Popen([sys.executable, '-I', '-B', '-c', BOOTSTRAP,
                                    json.dumps((entry, spelling, form, arguments, libraries, profile_command))],
                                   pass_fds=(entry, *libraries))
        outcome = process.wait()
        if outcome != 0:
            raise GateError('CAPTURE_NATIVE_UNSETTLED')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--binding-sha256', required=True)
    args = parser.parse_args(argv)
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    try:
        with ExitStack() as stack:
            gate, invocation = load(stack, args.binding, args.binding_sha256)
            run(gate, invocation)
        return 0
    except Busy:
        print('CAPTURE_BUSY', file=sys.stderr)
        return 75
    except (Exception, KeyboardInterrupt):
        print('CAPTURE_RECEIVER_REFUSED', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
