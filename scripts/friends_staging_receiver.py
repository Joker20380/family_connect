"""Inert, hash-pinned staging receiver. Never executes an uploaded artifact."""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import sys
import time

ROOT = Path('/opt/apps/family_connect/restricted-materials-stage-20261001')
MANIFEST = '.staging-manifest.json'
RECEIPT = '.staging-ready.json'


class StagingError(Exception):
    pass


class PhaseTimeout(StagingError):
    pass


class HashMismatch(StagingError):
    pass


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def fsync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def durable(path, value):
    pending = path.with_name(path.name + '.pending')
    descriptor = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(encoded(value))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(pending, path)
    fsync_directory(path.parent)


@contextlib.contextmanager
def deadline(seconds):
    def expired(signum, frame):
        raise PhaseTimeout()
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def hash_file(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise StagingError()
        digest = hashlib.sha256()
        while chunk := stream.read(65536):
            digest.update(chunk)
        return digest.hexdigest()


def validate(request, root):
    if type(request.get('version')) is not int or request['version'] != 1 or request.get('role') not in ('ru', 'nl'):
        raise StagingError()
    for name in ('destination', 'attempt'):
        if not re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}', request.get(name, '')):
            raise StagingError()
    parent = Path(request['parent'])
    if parent != parent.resolve(strict=True) or root.resolve() not in parent.parents:
        raise StagingError()
    if any(path.is_symlink() for path in (parent, *parent.parents)):
        raise StagingError()
    if parent.stat().st_uid != os.geteuid() or parent.stat().st_mode & 0o022:
        raise StagingError()
    items = request['items']
    if not isinstance(items, list) or not 1 <= len(items) <= 64:
        raise StagingError()
    names = set()
    total = 0
    for item in items:
        name = item['artifact_id']
        if not re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9_.-]{0,100}', name) or name in names:
            raise StagingError()
        if not re.fullmatch('[a-f0-9]{64}', item['sha256']):
            raise StagingError()
        if type(item['bytes']) is not int or not 0 <= item['bytes'] <= 64 * 1024**2:
            raise StagingError()
        if item['mode'] not in (0o600, 0o700):
            raise StagingError()
        for key in ('transfer_seconds', 'validation_seconds'):
            if not 0 < item[key] <= 300:
                raise StagingError()
        total += item['transfer_seconds'] + item['validation_seconds'] + request['commit_seconds']
        names.add(name)
    if total > 600 or not 0 < request['commit_seconds'] <= 30:
        raise StagingError()
    return parent


def identity(request):
    return dict(version=request['version'], role=request['role'], items=[{key:item[key] for key in ('artifact_id','bytes','sha256','mode')} for item in request['items']])


def inspect(parent, destination, request):
    target = parent / destination
    if not target.exists():
        return dict(state='PARTIAL' if list(parent.glob('.' + destination + '.partial-*')) else 'ABSENT')
    if target.is_symlink() or not target.is_dir():
        raise StagingError()
    metadata = target / MANIFEST
    if not metadata.is_file() or metadata.is_symlink() or json.loads(metadata.read_bytes()) != identity(request):
        raise StagingError()
    allowed = {item['artifact_id'] for item in request['items']} | {MANIFEST, RECEIPT}
    if set(path.name for path in target.iterdir()) - allowed:
        raise StagingError()
    for item in request['items']:
        path = target / item['artifact_id']
        with deadline(item['validation_seconds']):
            if path.stat().st_size != item['bytes'] or hash_file(path) != item['sha256'] or stat.S_IMODE(path.stat().st_mode) != item['mode']:
                raise HashMismatch()
    ready = target / RECEIPT
    if not ready.is_file():
        return dict(state='PARTIAL', detail='COMPLETE_BUT_UNACCEPTED')
    if ready.is_symlink():
        raise StagingError()
    receipt = json.loads(ready.read_bytes())
    if receipt['state'] != 'READY' or receipt['inventory'] != identity(request):
        raise StagingError()
    return dict(state='READY', receipt=receipt)


def promote(temporary, target):
    if target.exists():
        raise StagingError()
    os.rename(temporary, target)
    fsync_directory(target.parent)


def receive(root=ROOT):
    os.umask(0o077)
    output = lambda value: print(json.dumps(value, separators=(',', ':')), flush=True)
    output(dict(event='CONNECTED', at=time.time()))
    request = None
    receipt = None
    record_path = None
    lock = None
    phase = 'manifest'
    try:
        with deadline(10):
            line = sys.stdin.buffer.readline(32769)
        if len(line) > 32768 or not line.endswith(b'\n'):
            raise StagingError()
        request = json.loads(line)
        parent = validate(request, root)
        target = parent / request['destination']
        phase = 'inspection'
        if request.get('inspect_only'):
            output(dict(event='INSPECTED', **inspect(parent, request['destination'], request)))
            return
        lock = os.open(parent / ('.' + request['destination'] + '.lock'), os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        phase = 'lock'
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        phase = 'inspection'
        existing = inspect(parent, request['destination'], request)
        if existing['state'] == 'READY':
            output(dict(event='READY', reused=True, receipt=existing['receipt']))
            return
        if target.exists():
            raise StagingError()
        temporary = parent / ('.' + request['destination'] + '.partial-' + request['attempt'])
        temporary.mkdir(mode=0o700)
        record_path = parent / ('.' + request['destination'] + '.receipt-' + request['attempt'] + '.json')
        if record_path.exists():
            raise StagingError()
        receipt = dict(version=1, role=request['role'], inventory=identity(request), attempt=request['attempt'], state='PARTIAL', stage='manifest', items=[], started=time.time(), timeout_stage=None, exception_class=None)
        durable(temporary / MANIFEST, identity(request))
        durable(record_path, receipt)
        for item in request['items']:
            phase = 'transfer'
            record = dict(host_role=request['role'], artifact_id=item['artifact_id'], local_sha256=item['sha256'], expected_bytes=item['bytes'], remote_temp_path_class='inert_parent/unique_quarantine', bytes_transferred=0, remote_sha256_result=False, atomic_promote_result=False, state='PARTIAL', transfer_start=time.time(), transfer_end=None, timeout_stage=None, exception_class=None)
            record.update(connect_start=request.get('connection', {}).get('start'), connect_end=request.get('connection', {}).get('end'))
            receipt['items'].append(record)
            receipt['stage'] = phase
            durable(record_path, receipt)
            output(dict(event='ITEM', artifact_id=item['artifact_id'], at=record['transfer_start']))
            path = temporary / item['artifact_id']
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, item['mode'])
            with os.fdopen(descriptor, 'wb') as stream:
                with deadline(item['transfer_seconds']):
                    while record['bytes_transferred'] < item['bytes']:
                        chunk = sys.stdin.buffer.read1(min(65536, item['bytes'] - record['bytes_transferred']))
                        if not chunk:
                            raise EOFError()
                        stream.write(chunk)
                        record['bytes_transferred'] += len(chunk)
                        output(dict(event='PROGRESS', artifact_id=item['artifact_id'], bytes=record['bytes_transferred'], at=time.time()))
                record['transfer_end'] = time.time()
                phase = 'fsync'
                output(dict(event='FSYNCING', artifact_id=item['artifact_id'], at=time.time()))
                with deadline(request['commit_seconds']):
                    stream.flush()
                    os.fsync(stream.fileno())
                record['fsync_end'] = time.time()
            phase = 'validation'
            receipt['stage'] = phase
            durable(record_path, receipt)
            output(dict(event='VALIDATING', artifact_id=item['artifact_id'], at=time.time()))
            with deadline(item['validation_seconds']):
                if hash_file(path) != item['sha256']:
                    raise HashMismatch()
            record['remote_sha256_result'] = True
            record['validation_end'] = time.time()
            record['transfer_elapsed_seconds'] = round(record['transfer_end'] - record['transfer_start'], 6)
            record['fsync_elapsed_seconds'] = round(record['fsync_end'] - record['transfer_end'], 6)
            record['validation_elapsed_seconds'] = round(record['validation_end'] - record['fsync_end'], 6)
            durable(record_path, receipt)
            output(dict(event='VERIFIED', artifact_id=item['artifact_id'], at=time.time()))
        phase = 'promotion'
        with deadline(request['commit_seconds']):
            fsync_directory(temporary)
            promote(temporary, target)
            for record in receipt['items']:
                record.update(state='READY', atomic_promote_result=True)
            receipt.update(state='READY', stage='complete', finished=time.time())
            durable(target / RECEIPT, receipt)
            durable(record_path, receipt)
        output(dict(event='READY', reused=False, receipt=receipt))
    except Exception as error:
        if receipt is not None:
            receipt.update(state='PARTIAL', stage=phase, exception_class=type(error).__name__, timeout_stage=phase if isinstance(error, PhaseTimeout) else None, finished=time.time())
            for record in receipt['items']:
                record.update(state='PARTIAL', exception_class=type(error).__name__, timeout_stage=receipt['timeout_stage'], atomic_promote_result=False)
            try:
                durable(record_path, receipt)
            except Exception:
                pass
        output(dict(event='FAILED', stage=phase, exception_class=type(error).__name__, timeout_stage=phase if isinstance(error, PhaseTimeout) else None, receipt=receipt))
        raise SystemExit(1)
    finally:
        if lock is not None:
            os.close(lock)


if __name__ == '__main__':
    receive()
