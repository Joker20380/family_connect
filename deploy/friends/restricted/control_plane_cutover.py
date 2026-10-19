"""Forward-only, resumable installation of the pinned activated-access control plane."""

import argparse
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import tarfile
import tempfile


BASE_SOURCE = '5109a7c92ddd1937fe75ed7199866855a8cc20279bc226c35475d4cc81330145'
BASE_API = {'RU': '12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed',
            'NL': '9faaa1c27f534e71774f5b4f34872e87747f391409c4958562694f07f86d64d1'}
RU_IDLE = ('family-connect-friends-http-candidate.service',
           'family-connect-credential-renewal.timer', 'family-connect-credential-renewal.service',
           'family-connect-restricted-sync.timer', 'family-connect-restricted-sync.service',
           'family-connect-restricted-directory-sync.timer', 'family-connect-restricted-directory-sync.service')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition):
    if not condition:
        raise ValueError('CUTOVER_PRECONDITION_FAILED')


def read(path):
    require(not path.is_symlink())
    if not path.exists():
        return None
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid() and info.st_nlink == 1)
    require(info.st_size <= 5_000_000 and not info.st_mode & 0o022)
    return path.read_bytes()


def atomic(path, raw, mode=0o600):
    require(path.parent.is_dir() and not path.parent.is_symlink())
    descriptor, temporary = tempfile.mkstemp(prefix='.private-beta-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class FileCutover:
    def __init__(self, state, binding, *, fault=lambda stage: None):
        self.state, self.binding, self.fault = Path(state), binding, fault
        self.state.mkdir(mode=0o700, exist_ok=True)
        require(not self.state.is_symlink() and self.state.stat().st_mode & 0o777 == 0o700)

    def prepare(self, writes):
        path = self.state / 'transaction.json'
        existing = read(path)
        if existing is not None:
            transaction = json.loads(existing)
            require(transaction['binding'] == self.binding)
            require({item['path']: (base64.b64decode(item['after']), item['mode']) for item in transaction['files']}
                    == {str(target): (raw, mode) for target, raw, mode in writes})
            return transaction
        files = []
        for index, (target, raw, mode) in enumerate(writes):
            before = read(target)
            if before is not None:
                atomic(self.state / ('before-' + str(index)), before)
            files.append(dict(path=str(target), before=None if before is None else digest(before),
                              after=base64.b64encode(raw).decode(), after_sha256=digest(raw), mode=mode))
        require(len({item['path'] for item in files}) == len(files))
        transaction = dict(schema=1, binding=self.binding, phase='PREPARED', files=files)
        self.fault('before-prepare-commit')
        atomic(path, canonical(transaction))
        self.fault('after-prepare-commit')
        return transaction

    def apply(self, transaction):
        require(transaction == json.loads(read(self.state / 'transaction.json')))
        require(transaction['binding'] == self.binding)
        require(transaction['phase'] in ('PREPARED', 'FILES_COMMITTED'))
        for item in transaction['files']:
            current = read(Path(item['path']))
            require((None if current is None else digest(current)) in (item['before'], item['after_sha256']))
        for index, item in enumerate(transaction['files']):
            target = Path(item['path'])
            current = read(target)
            if current is None or digest(current) != item['after_sha256']:
                self.fault('before-file-' + str(index))
                atomic(target, base64.b64decode(item['after']), item['mode'])
                self.fault('after-file-' + str(index))
            require(digest(read(target)) == item['after_sha256'])
            require(target.stat().st_mode & 0o777 == item['mode'])
        transaction = dict(transaction, phase='FILES_COMMITTED')
        self.fault('before-commit-receipt')
        atomic(self.state / 'transaction.json', canonical(transaction))
        self.fault('after-commit-receipt')
        require(json.loads(read(self.state / 'transaction.json')) == transaction)
        return transaction


def load_capsule(path, expected):
    require(digest(read(path)) == expected)
    with tarfile.open(path, 'r:gz') as archive:
        members = archive.getmembers()
        require(all(member.isfile() and 0 <= member.size < 5_000_000 for member in members))
        require(len({member.name for member in members}) == len(members))
        content = {member.name: archive.extractfile(member).read() for member in members}
    manifest = json.loads(content['manifest.json'])
    require(manifest['admission_mode'] == 'all_activated' and manifest['authority_days'] == 90)
    require(set(content) == {'manifest.json', 'bridge-access-v2.pyz'} |
            {'management/' + name for name in manifest['source_files']})
    require(digest(content['bridge-access-v2.pyz']) == manifest['api_sha256'])
    require(digest(canonical(manifest['source_files'])) == manifest['source_sha256'])
    require(all('/' not in name and name.endswith('.py') and not name.startswith('.') and
                digest(content['management/' + name]) == expected
                for name, expected in manifest['source_files'].items()))
    return manifest, content


def backup_database(source_path, backup):
    if backup.exists():
        require(read(backup) is not None)
        with sqlite3.connect(backup.as_uri() + '?mode=ro', uri=True) as existing:
            require(existing.execute('PRAGMA quick_check').fetchone()[0] == 'ok')
        return
    descriptor, temporary = tempfile.mkstemp(prefix='.database-evidence-', dir=backup.parent)
    os.close(descriptor)
    try:
        with sqlite3.connect(source_path.as_uri() + '?mode=ro', uri=True) as source:
            with sqlite3.connect(temporary) as destination:
                source.backup(destination)
                require(destination.execute('PRAGMA quick_check').fetchone()[0] == 'ok')
        with open(temporary, 'rb') as stream:
            os.fsync(stream.fileno())
        os.replace(temporary, backup)
        descriptor = os.open(backup.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('--role', choices=('RU', 'NL'), required=True)
    parser.add_argument('--capsule', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--operation', required=True)
    parser.add_argument('--peers-quiesced-receipt', type=Path, required=True)
    args = parser.parse_args()
    import re
    require(os.geteuid() == 0 and re.fullmatch('[a-z0-9-]{16,96}', args.operation))
    manifest, content = load_capsule(args.capsule, args.sha256)
    peers = json.loads(read(args.peers_quiesced_receipt))
    import time
    require(peers['operation_id'] == args.operation and peers['capsule_sha256'] == args.sha256
            and peers['RU_writers_quiesced'] is True and peers['NL_staged'] is True
            and 0 <= time.time() - peers['observed_at'] < 120)
    if args.role == 'RU':
        for unit in RU_IDLE:
            state = subprocess.check_output(['systemctl', 'show', unit, '--property=ActiveState', '--value'],
                                            text=True, timeout=10).strip()
            require(state in ('inactive', 'failed'))
    root = Path('/opt/apps/family_connect/friends-restricted')
    renewal = root / 'renewal'
    state = root / ('private-beta-cutover-' + args.operation)
    binding = dict(role=args.role, operation_id=args.operation, capsule_sha256=args.sha256)
    cutover = FileCutover(state, binding)
    config_path = renewal / 'node.json'
    baseline_path = state / 'baseline-node.json'
    if read(baseline_path) is None:
        config = json.loads(read(config_path))
        require(config['source_sha256'] == BASE_SOURCE and config['api_sha256'] == BASE_API[args.role])
        require(all(digest(read(renewal / name)) == expected for name, expected in config['source_files'].items()))
        atomic(baseline_path, canonical(config))
    baseline = json.loads(read(baseline_path))
    require(baseline['role'] == args.role)
    lock = os.open(Path(baseline['state']) / 'operation.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(lock)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1
                and info.st_mode & 0o777 == 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not (Path(baseline['state']) / 'owner.json').exists())
        require(not (Path(baseline['state']) / 'authority-request.json').exists())
        api = root.parent / 'friends-access' / ('private-beta-' + manifest['api_sha256'] + '.pyz')
        writes = [(api, content['bridge-access-v2.pyz'], 0o600)]
        writes += [(renewal / name, content['management/' + name], 0o600) for name in manifest['source_files']]
        config = dict(baseline, source_files=manifest['source_files'], source_sha256=manifest['source_sha256'],
                      api_archive=str(api), api_sha256=manifest['api_sha256'], admission_mode='all_activated')
        if args.role == 'RU':
            controller_path = state / 'baseline-controller.json'
            if read(controller_path) is None:
                atomic(controller_path, read(renewal / 'controller.json'))
            controller = dict(json.loads(read(controller_path)), nl_source_sha256=manifest['source_sha256'])
            writes.extend([(renewal / 'controller.json', canonical(controller), 0o600),
                           (Path(baseline['live']) / 'admission.json', canonical(dict(version=2, eligibility='all_activated')), 0o600)])
            dropin = Path('/etc/systemd/system/family-connect-friends-http-candidate.service.d')
            require(dropin.is_dir() and not dropin.is_symlink())
            body = '[Service]\nExecStart=\nExecStart=/opt/apps/family_connect/friends-access/venv/bin/python -I ' + str(api) + ' --port 18086\n'
            writes.append((dropin / 'zz-private-beta-existing-users.conf', body.encode(), 0o644))
            backup = state / 'database-evidence.db'
            backup_database(Path(baseline['database']), backup)
        writes.append((config_path, canonical(config), 0o600))
        transaction = cutover.apply(cutover.prepare(writes))
        receipt = dict(binding, result=transaction['phase'], credentials_changed=False,
                       database_restored=False, services_started=False, source_sha256=manifest['source_sha256'])
        atomic(state / 'receipt.json', canonical(receipt))
        print(canonical(receipt).decode())
    finally:
        os.close(lock)


if __name__ == '__main__':
    main()
