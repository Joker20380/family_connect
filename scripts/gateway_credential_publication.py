"""Credential-only atomic publication; callers must serialize existing sync writers."""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
import subprocess


LIMIT = 49152


class PublicationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Contract:
    uid: int
    gid: int
    parent_uid: int
    parent_gid: int
    parent_mode: int
    mode: int = 0o600


def service_readable(path, uid, gid):
    """Open without reading bytes under the service's exact non-root DAC identity."""
    if uid == 0:
        return False
    if os.geteuid() != 0:
        if (os.geteuid(), os.getegid()) != (uid, gid):
            return False
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            os.close(descriptor)
            return True
        except OSError:
            return False
    command = ['/usr/bin/setpriv', '--reuid', str(uid), '--regid', str(gid), '--clear-groups',
               '/usr/bin/python3', '-I', '-c',
               'import os,sys; fd=os.open(sys.argv[1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK);os.close(fd)', str(path)]
    try:
        return subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, timeout=5).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _metadata(info, contract):
    return (stat.S_ISREG(info.st_mode) and info.st_nlink == 1
            and (info.st_uid, info.st_gid, stat.S_IMODE(info.st_mode))
            == (contract.uid, contract.gid, contract.mode))


def _read(directory, name):
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    with os.fdopen(descriptor, 'rb') as source:
        info = os.fstat(source.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > LIMIT:
            raise PublicationError('invalid_file')
        raw = source.read(LIMIT + 1)
        if not raw or len(raw) > LIMIT:
            raise PublicationError('invalid_file')
        return raw, info


def _same(left, right):
    return (left.st_dev, left.st_ino, left.st_uid, left.st_gid, left.st_mode,
            left.st_size, left.st_mtime_ns, left.st_ctime_ns) == (
                right.st_dev, right.st_ino, right.st_uid, right.st_gid, right.st_mode,
                right.st_size, right.st_mtime_ns, right.st_ctime_ns)


def _receipt(path, record):
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        info = os.fstat(descriptor)
        if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise PublicationError('receipt_directory')
        output = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=descriptor)
        with os.fdopen(output, 'w') as stream:
            json.dump(record, stream, separators=(',', ':'))
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def publish(target, raw, contract, receipt, *, validate, readable=service_readable):
    """Validate first; metadata/read access precede rename; post-rename failures are explicit."""
    target, receipt = Path(target).absolute(), Path(receipt).absolute()
    if receipt.exists() or receipt == target or receipt.parent == target.parent:
        raise PublicationError('receipt_conflict')
    record = dict(version=1, status='FAIL', stage='input', published=False, changed=False,
                  uid=contract.uid, gid=contract.gid, mode=oct(contract.mode),
                  service_readable=False, final_readback=False,
                  timestamp=datetime.now(timezone.utc).isoformat())
    directory, temporary, failure = None, None, None
    try:
        if (type(raw) is not bytes or not 0 < len(raw) <= LIMIT or contract.mode != 0o600
                or contract.uid <= 0 or contract.gid < 0
                or target.parent.resolve() != target.parent):
            raise PublicationError('input')
        record['stage'] = 'receipt_preflight'
        receipt_directory = os.open(receipt.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            info = os.fstat(receipt_directory)
            if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o077:
                raise PublicationError('receipt_directory')
        finally:
            os.close(receipt_directory)
        directory = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        parent = os.fstat(directory)
        if (parent.st_uid, parent.st_gid, stat.S_IMODE(parent.st_mode)) != (
                contract.parent_uid, contract.parent_gid, contract.parent_mode):
            raise PublicationError('parent_contract')
        record['stage'] = 'existing_contract'
        previous, original = _read(directory, target.name)
        if not _metadata(original, contract):
            raise PublicationError('existing_contract')
        record['stage'] = 'validation'
        if validate(raw) is not True:
            raise PublicationError('validation')
        if raw != previous:
            record['stage'] = 'temporary_write'
            temporary = target.name + '.pending-' + secrets.token_hex(16)
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                 0o600, dir_fd=directory)
            with os.fdopen(descriptor, 'wb') as output:
                output.write(raw)
                output.flush()
                record['stage'] = 'temporary_metadata'
                os.fchown(output.fileno(), contract.uid, contract.gid)
                os.fchmod(output.fileno(), contract.mode)
                if not _metadata(os.fstat(output.fileno()), contract):
                    raise PublicationError('temporary_metadata')
                os.fsync(output.fileno())
            record['stage'] = 'temporary_readability'
            if readable(target.parent / temporary, contract.uid, contract.gid) is not True:
                raise PublicationError('temporary_readability')
            checked, info = _read(directory, temporary)
            if checked != raw or not _metadata(info, contract):
                raise PublicationError('temporary_readback')
            record['stage'] = 'concurrent_change'
            current, info = _read(directory, target.name)
            if current != previous or not _same(original, info):
                raise PublicationError('concurrent_change')
            record['stage'] = 'rename'
            os.replace(temporary, target.name, src_dir_fd=directory, dst_dir_fd=directory)
            temporary = None
            record.update(published=True, changed=True, stage='directory_sync')
            os.fsync(directory)
        record['stage'] = 'final_readback'
        final, info = _read(directory, target.name)
        if final != raw or not _metadata(info, contract):
            raise PublicationError('final_readback')
        record['stage'] = 'final_readability'
        if readable(target, contract.uid, contract.gid) is not True:
            raise PublicationError('final_readability')
        record['stage'] = 'final_readback'
        final, info = _read(directory, target.name)
        if final != raw or not _metadata(info, contract):
            raise PublicationError('final_readback')
        record.update(status='PASS', stage='complete', service_readable=True, final_readback=True,
                      sha256=hashlib.sha256(final).hexdigest())
    except Exception:
        failure = PublicationError(record['stage'])
    finally:
        if directory is not None:
            try:
                if temporary is not None:
                    os.unlink(temporary, dir_fd=directory)
                    os.fsync(directory)
            except OSError:
                record['cleanup_failed'] = True
                failure = PublicationError('cleanup')
            finally:
                os.close(directory)
    if failure is not None:
        record['status'] = 'FAIL'
    try:
        _receipt(receipt, record)
    except Exception:
        raise PublicationError('receipt_unavailable; inspect destination before any retry') from None
    if failure is not None:
        raise failure from None
    return record
