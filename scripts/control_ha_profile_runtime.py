"""Observe an existing profile runtime without importing packages or running site hooks."""
import argparse
import base64
import csv
from email.parser import BytesParser
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import time

from scripts import build_profile_snapshot_launcher as launcher

EXPECTED = dict(rns='1.5.1', cryptography='46.0.7', pyserial='3.5', cffi='2.1.1', pycparser='3.0')
PROBE = '''import json,os,pathlib,sys
print(json.dumps(dict(executable=sys.executable,target=str(pathlib.Path(sys.executable).resolve(strict=True)),
    version=list(sys.version_info[:3]),implementation=sys.implementation.name,uid=os.getuid(),gid=os.getgid(),
    groups=sorted(os.getgroups()),isolated=sys.flags.isolated,no_site=sys.flags.no_site,
    no_user_site=sys.flags.no_user_site,no_bytecode=sys.dont_write_bytecode,path=sys.path)))
'''


def require(condition):
    if not condition:
        raise ValueError('PROFILE_RUNTIME_OBSERVATION_REFUSED')


def bounded_tree(root, *, clock=time.monotonic):
    start = clock()
    files, directories, size = 0, 0, 0
    for directory, children, names in os.walk(root, followlinks=False):
        directories += 1
        require(directories <= 2048 and clock() - start < 15)
        require(not Path(directory).is_symlink())
        for name in children:
            require(not (Path(directory) / name).is_symlink())
        for name in names:
            target = Path(directory) / name
            info = target.lstat()
            require(not target.is_symlink() and target.is_file() and 0 <= info.st_size <= 32 * 1024 * 1024)
            files += 1
            size += info.st_size
            require(files <= 12000 and size <= 256 * 1024 * 1024 and clock() - start < 15)
    require(files > 0)
    return dict(files=files, directories=directories, bytes=size)


def metadata(raw):
    require(len(raw) <= 1048576)
    message = BytesParser().parsebytes(raw, headersonly=True)
    require(len(message.get_all('Name', [])) == len(message.get_all('Version', [])) == 1)
    name = message['Name'].lower().replace('_', '-')
    version = message['Version']
    require(name and version and len(name) <= 128 and len(version) <= 128)
    return name, version


def records(raw, site, root, files, account):
    require(len(raw) <= 4 * 1024 * 1024)
    seen, hashed, unhashed = set(), 0, 0
    external_files = {}
    for row in csv.reader(io.StringIO(raw.decode('utf-8'))):
        require(len(row) == 3 and row[0] and row[0] not in seen and len(seen) < 12000)
        seen.add(row[0])
        require(not Path(row[0]).is_absolute() and '\x00' not in row[0])
        target = Path(os.path.normpath(site / row[0]))
        require(target.is_relative_to(root) and target != root)
        key = str(target.relative_to(root))
        pin = files.get(key)
        if pin is None:
            require(target.name != 'RECORD' and target.is_file() and target.stat().st_size <= 32 * 1024 * 1024)
            pin = launcher.pinned_file(target, account, executable=False)
            external_files[key] = pin
        if row[1]:
            algorithm, separator, encoded = row[1].partition('=')
            require(algorithm == 'sha256' and separator and len(encoded) == 43)
            expected = base64.b64decode(encoded + '=', altchars=b'-_', validate=True)
            require(len(expected) == 32 and expected.hex() == pin['sha256'] and row[2].isascii() and
                    row[2].isdigit() and int(row[2]) == pin['metadata']['size'])
            hashed += 1
        else:
            require(not row[2] and (target.suffix == '.pyc' or target.name == 'RECORD'))
            unhashed += 1
    require(hashed > 0)
    return dict(hashed_files=hashed, unhashed_record_or_bytecode=unhashed, external_files=external_files)


def dependencies(inventory, files, account, minor):
    root = Path(inventory['root'])
    site = root / 'lib' / ('python' + minor) / 'site-packages'
    found = {}
    for name in files:
        path = root / name
        if path.name != 'METADATA' or not path.parent.name.endswith('.dist-info') or path.parent.parent != site:
            continue
        require(path.stat().st_size <= 1048576)
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == files[name]['sha256'])
        distribution, version = metadata(raw)
        if distribution not in EXPECTED:
            continue
        require(distribution not in found)
        record = path.parent / 'RECORD'
        key = str(record.relative_to(root))
        require(key in files and record.stat().st_size <= 4 * 1024 * 1024)
        raw = record.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == files[key]['sha256'])
        found[distribution] = dict(version=version, expected=EXPECTED[distribution],
            matches_lock=version == EXPECTED[distribution], record_sha256=files[key]['sha256'],
            **records(raw, site, root, files, account))
    require(set(found) == set(EXPECTED))
    startup = {}
    for name, pin in files.items():
        relative = (root / name).relative_to(site)
        if (len(relative.parts) == 1 and relative.suffix == '.pth') or relative.parts[0].split('.')[0] in (
                'sitecustomize', 'usercustomize'):
            startup[name] = pin['sha256']
    return found, startup


def observe(executable, account, minor, *, run=subprocess.run):
    minor = launcher.selected_minor(minor)
    root = launcher.absolute(executable).parent.parent
    site = root / 'lib' / ('python' + minor) / 'site-packages'
    before_bounds = bounded_tree(site)
    executable_pin = launcher.entrypoint_pin(executable, account)
    inventory, files = launcher.venv_inventory(executable, account, python_minor=minor)
    packages, startup = dependencies(inventory, files, account, minor)
    result = run([executable, '-I', '-S', '-B', '-c', PROBE], capture_output=True, timeout=15,
                 cwd='/', env={'PATH': '/usr/bin:/bin', 'LANG': 'C'}, preexec_fn=account.enter)
    require(result.returncode == 0 and not result.stderr and 0 < len(result.stdout) <= 16384)
    runtime = launcher.strict_json(result.stdout)
    require(type(runtime) is dict and set(runtime) == {'executable', 'target', 'version', 'implementation',
        'uid', 'gid', 'groups', 'isolated', 'no_site', 'no_user_site', 'no_bytecode', 'path'})
    require(runtime['executable'] == executable and runtime['target'] == executable_pin['target'] and
            runtime['implementation'] == 'cpython' and type(runtime['version']) is list and
            len(runtime['version']) == 3 and all(type(number) is int for number in runtime['version']) and
            runtime['version'][:2] == [int(part) for part in minor.split('.')])
    require(type(runtime['uid']) is int and runtime['uid'] == account.uid and
            type(runtime['gid']) is int and runtime['gid'] == account.gid and
            type(runtime['groups']) is list and all(type(group) is int for group in runtime['groups']) and
            runtime['groups'] == sorted(account.groups) and
            all(type(runtime[name]) is int and runtime[name] == 1 for name in ('isolated', 'no_site', 'no_user_site')) and
            runtime['no_bytecode'] is True and type(runtime['path']) is list and runtime['path'] and
            all(type(path) is str and path.startswith('/') and 'site-packages' not in Path(path).parts
                for path in runtime['path']))
    require(bounded_tree(site) == before_bounds)
    require(launcher.venv_inventory(executable, account, python_minor=minor)[0] == inventory and
            launcher.entrypoint_pin(executable, account) == executable_pin)
    require(all(launcher.pinned_file(root / name, account, executable=False) == pin
                for package in packages.values() for name, pin in package['external_files'].items()))
    return dict(schema=1, classification='RUNTIME_BINDINGS_OBSERVED', runtime=runtime,
        executable=executable_pin, venv=inventory, dependencies=packages, startup_files=startup,
        all_selected_versions_match=all(item['matches_lock'] for item in packages.values()),
        package_imports_executed=False, site_hooks_executed=False, capture_permitted=False,
        independent_approval=False, observed_at_ns=time.time_ns())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', required=True)
    parser.add_argument('--account', required=True)
    parser.add_argument('--python-minor', choices=('3.12', '3.14'), required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(observe(args.executable, launcher.Account.lookup(args.account), args.python_minor), sort_keys=True))
    except Exception:
        print(json.dumps(dict(classification='RUNTIME_OBSERVATION_REFUSED', capture_permitted=False)))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
