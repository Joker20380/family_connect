"""Build a fixed snapshot launcher; operator inputs and pins stay private."""
import argparse
import ast
import base64
import configparser
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import shlex
import stat
import struct
import subprocess


INVALID = 'SNAPSHOT_PYTHON_EXECUTABLE_INVALID'
VERSION = 'SNAPSHOT_PYTHON_VERSION_MISMATCH'
ARGV = 'SNAPSHOT_LAUNCHER_ARGV_MISMATCH'
UNSAFE = 'BLOCKED_SNAPSHOT_RUNTIME_UNSAFE'
DEPENDENCIES = {'rns': ('RNS', '1.5.1'), 'cryptography': ('cryptography', '46.0.7'),
                'pyserial': ('serial', '3.5')}
ORIGINAL_COMMAND = 'restricted-sync'
OPTIONS = ('restrict', 'no-agent-forwarding', 'no-port-forwarding', 'no-pty',
           'no-user-rc', 'no-X11-forwarding')
PROBE = ('import json,os,pathlib,platform,sys;'
         'print(json.dumps(dict(executable=str(pathlib.Path(sys.executable).resolve(strict=True)),'
         'version=list(sys.version_info[:3]),implementation=platform.python_implementation(),'
         'executable_access=os.access(sys.executable,os.X_OK))))')
RUNTIME_PROBE = '''import importlib, importlib.metadata, json, os, platform, site, sys
dependencies = {}
for name, module in [('rns', 'RNS'), ('cryptography', 'cryptography'), ('pyserial', 'serial')]:
    distribution = importlib.metadata.distribution(name)
    records = [item for item in distribution.files if item.name == 'RECORD']
    if len(records) != 1:
        raise ValueError('distribution inventory')
    dependencies[name] = dict(version=distribution.version,
        origin=importlib.import_module(module).__file__,
        record=str(distribution.locate_file(records[0])))
print(json.dumps(dict(executable=sys.executable, prefix=sys.prefix, base_prefix=sys.base_prefix,
    version=list(sys.version_info[:3]), implementation=platform.python_implementation(),
    user_site=site.ENABLE_USER_SITE, user_path=site.getusersitepackages(), path=sys.path,
    isolated=sys.flags.isolated, no_bytecode=sys.dont_write_bytecode,
    pythonpath=os.environ.get('PYTHONPATH'), dependencies=dependencies)))
'''


class LauncherError(ValueError):
    pass


def require(condition, code=INVALID):
    if not condition:
        raise LauncherError(code)


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result)
            result[key] = value
        return result
    def invalid(value):
        raise LauncherError(INVALID)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


@dataclass(frozen=True)
class Account:
    uid: int
    gid: int
    groups: tuple

    @classmethod
    def lookup(cls, name):
        entry = pwd.getpwnam(name)
        return cls(entry.pw_uid, entry.pw_gid, tuple(sorted(os.getgrouplist(name, entry.pw_gid))))

    def enter(self):
        if os.geteuid() == 0:
            os.setgroups(self.groups)
            os.setgid(self.gid)
            os.setuid(self.uid)
        else:
            require(self.uid == os.geteuid() and self.gid == os.getegid() and
                    set(self.groups) == set(os.getgroups()) | {os.getegid()})


def absolute(value, code=INVALID):
    require(type(value) is str and re.fullmatch(r'/[A-Za-z0-9_./-]+', value), code)
    require(value == os.path.normpath(value) and not value.startswith('//') and
            '..' not in Path(value).parts, code)
    return Path(value)


def metadata(info):
    return dict(uid=info.st_uid, gid=info.st_gid, mode=stat.S_IMODE(info.st_mode),
                device=info.st_dev, inode=info.st_ino, nlink=info.st_nlink,
                size=info.st_size, mtime_ns=info.st_mtime_ns, ctime_ns=info.st_ctime_ns)


def permission(info, account, bit):
    shift = 6 if info.st_uid == account.uid else 3 if info.st_gid in account.groups else 0
    return info.st_mode & (bit << shift) == bit << shift


def pinned_file(path, account, *, executable):
    require(path.resolve(strict=True) == path)
    require(not {'system.posix_acl_access', 'system.posix_acl_default', 'security.capability'} &
            set(os.listxattr(path, follow_symlinks=False)), UNSAFE)
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and not info.st_mode & 0o7022)
    require(permission(info, account, 1 if executable else 4))
    require(all(permission(parent.stat(), account, 1) for parent in path.parents))
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as source:
        require(metadata(os.fstat(source.fileno())) == metadata(info))
        raw = source.read()
    require(metadata(path.stat()) == metadata(info))
    if executable:
        require(raw.startswith(b'\x7fELF'))
    return dict(metadata=metadata(info), sha256=hashlib.sha256(raw).hexdigest())


def secure_ancestors(path, account):
    result = {}
    for parent in path.parents:
        info = parent.lstat()
        require(not {'system.posix_acl_access', 'system.posix_acl_default'} &
                set(os.listxattr(parent, follow_symlinks=False)), UNSAFE)
        require(stat.S_ISDIR(info.st_mode) and not info.st_mode & 0o022 and
                not permission(info, account, 2) and permission(info, account, 1), UNSAFE)
        result[str(parent)] = dict(uid=info.st_uid, gid=info.st_gid,
                                   mode=stat.S_IMODE(info.st_mode), device=info.st_dev, inode=info.st_ino)
    return result


def entrypoint_pin(value, account):
    entrypoint = absolute(value)
    require(re.fullmatch(r'python(?:3(?:\.14)?)?', entrypoint.name))
    current = entrypoint
    links = []
    ancestors = {}
    visited = set()
    for depth in range(9):
        require(current not in visited, UNSAFE)
        visited.add(current)
        ancestors.update(secure_ancestors(current, account))
        info = current.lstat()
        if not stat.S_ISLNK(info.st_mode):
            target = pinned_file(current, account, executable=True)
            require(not permission(info, account, 2), UNSAFE)
            return dict(entrypoint=str(entrypoint), target=str(current), target_pin=target,
                        links=links, ancestors=ancestors)
        require(depth < 8 and info.st_uid != account.uid and info.st_nlink == 1, UNSAFE)
        link = os.readlink(current)
        require(type(link) is str and re.fullmatch(r'[A-Za-z0-9_./-]+', link), UNSAFE)
        if not os.path.isabs(link):
            require('..' not in Path(link).parts and link == os.path.normpath(link), UNSAFE)
        links.append(dict(path=str(current), target=link, metadata=metadata(info)))
        current = absolute(link if os.path.isabs(link) else str(current.parent / link))
    raise LauncherError(UNSAFE)


def inspect_executable(value, account, *, expected_pin=None, run=subprocess.run):
    try:
        path = absolute(value)
        pin = entrypoint_pin(value, account)
        require(expected_pin is None or pin == expected_pin)
        result = run([str(path), '-I', '-B', '-c', PROBE], capture_output=True, timeout=15,
                     cwd='/', env={'PATH': '/usr/bin:/bin', 'LANG': 'C'}, preexec_fn=account.enter)
        require(result.returncode == 0 and not result.stderr and len(result.stdout) <= 2048, VERSION)
        runtime = strict_json(result.stdout)
        require(type(runtime) is dict and set(runtime) ==
                {'executable', 'version', 'implementation', 'executable_access'}, VERSION)
        require(type(runtime['version']) is list and len(runtime['version']) == 3 and
                all(type(number) is int for number in runtime['version']) and
                runtime['version'][:2] == [3, 14] and runtime['implementation'] == 'CPython', VERSION)
        require(runtime['executable'] == pin['target'] and runtime['executable_access'] is True, VERSION)
        require(entrypoint_pin(value, account) == pin, UNSAFE)
        return dict(pin=pin, runtime=runtime)
    except LauncherError:
        raise
    except (OSError, ValueError, subprocess.SubprocessError):
        raise LauncherError(INVALID) from None


def venv_inventory(entrypoint, account):
    root = absolute(entrypoint).parent.parent
    require(Path(entrypoint).parent.name == 'bin', UNSAFE)
    secure_ancestors(root / 'pyvenv.cfg', account)
    configuration = pinned_file(root / 'pyvenv.cfg', account, executable=False)
    require(not permission((root / 'pyvenv.cfg').stat(), account, 2), UNSAFE)
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string('[venv]\n' + (root / 'pyvenv.cfg').read_text())
    require(parser.get('venv', 'include-system-site-packages').lower() == 'false' and
            parser.get('venv', 'version').startswith('3.14.') and
            Path(parser.get('venv', 'home')).is_absolute(), UNSAFE)
    site_packages = root / 'lib' / 'python3.14' / 'site-packages'
    secure_ancestors(site_packages / 'inventory', account)
    files = {}
    directories = {}
    for directory, children, names in os.walk(site_packages, followlinks=False):
        path = Path(directory)
        info = path.lstat()
        require(stat.S_ISDIR(info.st_mode) and not info.st_mode & 0o022 and
                not permission(info, account, 2) and permission(info, account, 5), UNSAFE)
        directories[str(path.relative_to(root))] = metadata(info)
        for name in children:
            require(not (path / name).is_symlink(), UNSAFE)
        for name in names:
            member = path / name
            require(not permission(member.lstat(), account, 2), UNSAFE)
            files[str(member.relative_to(root))] = pinned_file(member, account, executable=False)
    require(files and directories, UNSAFE)
    inventory_hash = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return dict(root=str(root), configuration=configuration, directories=directories,
                inventory_sha256=inventory_hash, file_count=len(files)), files


def validate_runtime(runtime, inventory, files, entrypoint):
    require(type(runtime) is dict and set(runtime) == {'executable', 'prefix', 'base_prefix', 'version',
            'implementation', 'user_site', 'user_path', 'path', 'isolated', 'no_bytecode',
            'pythonpath', 'dependencies'}, UNSAFE)
    require(type(runtime['version']) is list and len(runtime['version']) == 3 and
            all(type(number) is int for number in runtime['version']) and
            runtime['version'][:2] == [3, 14] and runtime['implementation'] == 'CPython', VERSION)
    root = Path(inventory['root'])
    require(runtime['executable'] == entrypoint and Path(runtime['prefix']).resolve() == root and
            Path(runtime['base_prefix']).resolve() != root, UNSAFE)
    require(runtime['user_site'] is False and runtime['isolated'] == 1 and
            runtime['no_bytecode'] is True and runtime['pythonpath'] is None, UNSAFE)
    base = absolute(runtime['base_prefix'], UNSAFE).resolve(strict=True)
    allowed = {str(base / 'lib' / 'python314.zip'), str(base / 'lib' / 'python3.14'),
               str(base / 'lib' / 'python3.14' / 'lib-dynload'),
               str(root / 'lib' / 'python3.14' / 'site-packages')}
    require(type(runtime['path']) is list and set(runtime['path']) <= allowed and
            str(root / 'lib' / 'python3.14' / 'site-packages') in runtime['path'] and
            runtime['user_path'] not in runtime['path'], UNSAFE)
    require(type(runtime['dependencies']) is dict and set(runtime['dependencies']) == set(DEPENDENCIES), UNSAFE)
    for name, dependency in runtime['dependencies'].items():
        require(type(dependency) is dict and set(dependency) == {'version', 'origin', 'record'} and
                dependency['version'] == DEPENDENCIES[name][1], UNSAFE)
        for field in ('origin', 'record'):
            member = absolute(dependency[field], UNSAFE)
            require(member.is_relative_to(root) and str(member.relative_to(root)) in files, UNSAFE)
        require(Path(dependency['record']).name == 'RECORD' and
                Path(dependency['record']).parent.name.endswith('.dist-info'), UNSAFE)


def inspect_runtime(value, account, *, expected_pin=None, run=subprocess.run):
    try:
        entrypoint_pin(value, account)
        inventory, files = venv_inventory(value, account)
        require(expected_pin is None or inventory == expected_pin['venv'], UNSAFE)
        executable = inspect_executable(value, account,
            expected_pin=expected_pin['executable'] if expected_pin else None, run=run)
        result = run([value, '-I', '-B', '-c', RUNTIME_PROBE], capture_output=True, timeout=30,
                     cwd='/', env={'PATH': '/usr/bin:/bin', 'LANG': 'C'}, preexec_fn=account.enter)
        require(result.returncode == 0 and not result.stderr and len(result.stdout) <= 16384, UNSAFE)
        runtime = strict_json(result.stdout)
        validate_runtime(runtime, inventory, files, value)
        require(venv_inventory(value, account)[0] == inventory and
                entrypoint_pin(value, account) == executable['pin'], UNSAFE)
        pin = dict(executable=executable['pin'], venv=inventory, runtime=runtime)
        require(expected_pin is None or pin == expected_pin, UNSAFE)
        return dict(classification='PINNED_EXISTING_VENV_READY', pin=pin)
    except LauncherError:
        raise
    except (OSError, ValueError, KeyError, TypeError, configparser.Error, subprocess.SubprocessError):
        raise LauncherError(UNSAFE) from None


def expected_argv(python_executable, snapshot_package):
    executable = absolute(python_executable)
    require(re.fullmatch(r'python(?:3(?:\.14)?)?', executable.name))
    return [str(executable), '-I', '-B', str(absolute(snapshot_package, ARGV))]


def render_argv(argv, *, read_only):
    require(type(read_only) is bool, ARGV)
    require(type(argv) is list and len(argv) == 4 and all(type(item) is str for item in argv), ARGV)
    require(argv == expected_argv(argv[0], argv[-1]), ARGV)
    command = shlex.join(argv)
    require(shlex.split(command) == argv, ARGV)
    require(len(f'#!{argv[0]} -I\n'.encode()) <= 127, ARGV)
    return (f'#!{argv[0]} -I\n'
            'import json\nimport os\nimport shlex\nimport sys\n'
            f'COMMAND = {command!r}\nREAD_ONLY = {read_only!r}\n'
            'if len(sys.argv) != 1 or os.environ.get("SSH_ORIGINAL_COMMAND") != "restricted-sync":\n'
            '    raise SystemExit(126)\n'
            'if READ_ONLY:\n'
            '    def unique(items):\n'
            '        result = {}\n'
            '        for key, value in items:\n'
            '            if key in result:\n'
            '                raise ValueError("duplicate")\n'
            '            result[key] = value\n'
            '        return result\n'
            '    request = sys.stdin.buffer.read(20001)\n'
            '    try:\n'
            '        value = json.loads(request, object_pairs_hook=unique)\n'
            '        valid = len(request) <= 20000 and type(value) is dict and value == '\
            '{"schema": 1, "operation": "READ_ONLY_SECURITY_SNAPSHOT"} and type(value["schema"]) is int\n'
            '    except (ValueError, TypeError):\n'
            '        valid = False\n'
            '    if not valid:\n'
            '        raise SystemExit(126)\n'
            '    descriptor = os.memfd_create("snapshot-request", os.MFD_CLOEXEC)\n'
            '    with os.fdopen(descriptor, "w+b") as stream:\n'
            '        stream.write(request)\n'
            '        stream.flush()\n'
            '        stream.seek(0)\n'
            '        os.dup2(stream.fileno(), 0, inheritable=True)\n'
            'arguments = shlex.split(COMMAND)\n'
            'os.chdir("/")\n'
            'os.execve(arguments[0], arguments, {"PATH": "/usr/bin:/bin", "LANG": "C", '
            '"SSH_ORIGINAL_COMMAND": "restricted-sync"})\n').encode()


def validate_launcher(raw, argv, *, read_only):
    try:
        tree = ast.parse(raw)
        command = next(ast.literal_eval(entry.value) for entry in tree.body
                       if isinstance(entry, ast.Assign) and len(entry.targets) == 1 and
                       isinstance(entry.targets[0], ast.Name) and entry.targets[0].id == 'COMMAND')
        require(shlex.split(command) == argv, ARGV)
        require(raw == render_argv(argv, read_only=read_only), ARGV)
    except (SyntaxError, StopIteration, ValueError, TypeError, IndexError):
        raise LauncherError(ARGV) from None


def build(configuration, account, *, read_only=False, expected_executable_pin=None, run=subprocess.run):
    require(type(configuration) is dict and {'python_executable', 'snapshot_package', 'snapshot_sha256'} <= set(configuration)
            and set(configuration) <= {'python_executable', 'python_version', 'snapshot_package', 'snapshot_sha256'})
    require('python_version' not in configuration or type(configuration['python_version']) is str)
    executable = inspect_runtime(configuration['python_executable'], account,
                                 expected_pin=expected_executable_pin, run=run)
    try:
        package = absolute(configuration['snapshot_package'], ARGV)
        require(package.suffix == '.pyz', ARGV)
        package_pin = pinned_file(package, account, executable=False)
        require(type(configuration['snapshot_sha256']) is str and
                re.fullmatch('[0-9a-f]{64}', configuration['snapshot_sha256']) and
                package_pin['sha256'] == configuration['snapshot_sha256'], ARGV)
    except (OSError, ValueError):
        raise LauncherError(ARGV) from None
    argv = expected_argv(configuration['python_executable'], str(package))
    raw = render_argv(argv, read_only=read_only)
    validate_launcher(raw, argv, read_only=read_only)
    return raw, dict(argv=argv, executable=executable, package=package_pin,
                     launcher_sha256=hashlib.sha256(raw).hexdigest(), read_only=read_only)


def authorized_key_line(launcher_path, public_key):
    path = absolute(launcher_path, ARGV)
    try:
        parts = public_key.split()
        require(len(parts) == 2 and parts[0] == 'ssh-ed25519' and '\n' not in public_key and '\r' not in public_key, ARGV)
        raw = base64.b64decode(parts[1], validate=True)
        require(raw[:4] == struct.pack('>I', 11) and raw[4:15] == b'ssh-ed25519' and
                raw[15:19] == struct.pack('>I', 32) and len(raw) == 51, ARGV)
        command = shlex.join([str(path)])
        require(shlex.split(command) == [str(path)], ARGV)
        return (','.join((*OPTIONS, 'command=' + json.dumps(command))) + ' ' + ' '.join(parts) + '\n').encode()
    except (ValueError, TypeError):
        raise LauncherError(ARGV) from None


def validate_authorized_key_line(raw, launcher_path, public_key):
    require(raw == authorized_key_line(launcher_path, public_key), ARGV)
    command = raw.split(b'command=', 1)[1].split(b' ssh-ed25519 ', 1)[0]
    require(shlex.split(json.loads(command)) == [str(absolute(launcher_path, ARGV))], ARGV)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configuration', type=Path, required=True)
    parser.add_argument('--account', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--pins', type=Path, required=True)
    parser.add_argument('--read-only', action='store_true')
    parser.add_argument('--expected-pins', type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        expected = strict_json(args.expected_pins.read_bytes())['executable']['pin'] if args.expected_pins else None
        raw, pins = build(strict_json(args.configuration.read_bytes()), Account.lookup(args.account),
                          read_only=args.read_only, expected_executable_pin=expected)
        with args.output.open('xb') as output:
            output.write(raw)
        with args.pins.open('x') as output:
            json.dump(pins, output, sort_keys=True)
        print('SNAPSHOT_LAUNCHER_VALIDATED')
        return 0
    except LauncherError as error:
        print(str(error))
        return 1
    except (OSError, ValueError, KeyError):
        print(INVALID)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
