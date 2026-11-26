"""One-process startup authority for the HA-02 candidate, never a restart lease."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import runpy
import stat
import sys
import time


REASONS = frozenset(('START_AUTHORITY_PARENT', 'START_AUTHORITY_FILE', 'START_AUTHORITY_CHANGED',
                     'START_AUTHORITY_MISSING'))


def refusal(context, error):
    phase = context.get('phase', 'arguments')
    reason = str(error) if phase == 'authority' and str(error) in REASONS else (
        'CANDIDATE_EXIT' if isinstance(error, SystemExit) else
        'CANDIDATE_EXCEPTION' if phase == 'candidate' else 'STARTUP_INPUT_ERROR')
    result = dict(schema=1, result='START_AUTHORITY_REFUSED', reason=reason, phase=phase,
                  capture_permitted=False, admission_permitted=False)
    try:
        result['binding'] = binding()
        for name in ('archive', 'authority'):
            if name in context:
                result[name + '_path_sha256'] = hashlib.sha256(os.fsencode(context[name])).hexdigest()
        if context.get('archive_sha256'):
            result['archive_sha256'] = context['archive_sha256']
        directory = context.get('diagnostics')
        if directory is not None:
            save_refusal(Path(directory), result)
    except Exception:
        pass
    return result


def save_refusal(directory, result):
    directory = directory.absolute()
    for parent in (directory, *directory.parents):
        info = parent.lstat()
        if not (stat.S_ISDIR(info.st_mode) and info.st_uid in (0, os.geteuid()) and
                (not info.st_mode & 0o022 or info.st_uid == 0 and info.st_mode & stat.S_ISVTX)):
            raise ValueError('UNSAFE_DIAGNOSTIC_DIRECTORY')
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        info = os.fstat(descriptor)
        if info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise ValueError('UNSAFE_DIAGNOSTIC_DIRECTORY')
        with os.scandir(descriptor) as entries:
            for count, _entry in enumerate(entries, 1):
                if count >= 128:
                    raise ValueError('DIAGNOSTIC_DIRECTORY_FULL')
        process = result['binding']
        filename = process['boot'] + '-' + str(process['pid']) + '-' + process['start'] + '.json'
        raw = json.dumps(result, sort_keys=True, separators=(',', ':')).encode() + b'\n'
        if len(raw) > 2048:
            raise ValueError('DIAGNOSTIC_TOO_LARGE')
        output = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o600, dir_fd=descriptor)
        with os.fdopen(output, 'wb') as target:
            target.write(raw)
            target.flush()
            os.fsync(target.fileno())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def binding():
    root = Path('/proc/self')
    return dict(pid=os.getpid(), start=(root / 'stat').read_text().rsplit(')', 1)[1].split()[19],
                boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                command=hashlib.sha256((root / 'cmdline').read_bytes()).hexdigest(),
                cgroup=hashlib.sha256((root / 'cgroup').read_bytes()).hexdigest())


def admitted(path, owner, archive):
    for parent in path.parents:
        info = parent.lstat()
        if not (stat.S_ISDIR(info.st_mode) and info.st_uid in (0, owner) and
                (not info.st_mode & 0o022 or info.st_uid == 0 and info.st_mode & stat.S_ISVTX)):
            raise ValueError('START_AUTHORITY_PARENT')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(descriptor, 'rb') as source:
        info = os.fstat(source.fileno())
        if not (stat.S_ISREG(info.st_mode) and info.st_uid == owner and info.st_nlink == 1 and
                not info.st_mode & 0o022):
            raise ValueError('START_AUTHORITY_FILE')
        value = json.loads(source.read(8193))
    expected = dict(schema=1, binding=binding(), archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
    if value != expected:
        raise ValueError('START_AUTHORITY_CHANGED')


def main(context=None):
    context = {} if context is None else context
    context['phase'] = 'arguments'
    arguments = sys.argv[1:]
    if arguments[:1] == ['--refusal-directory']:
        context['diagnostics'] = arguments[1]
        arguments = arguments[2:]
    archive, authority, owner, *options = arguments
    archive, authority, owner = Path(archive), Path(authority), int(owner)
    context.update(archive=archive, authority=authority, phase='authority')
    deadline = time.monotonic() + 5
    while True:
        try:
            admitted(authority, owner, archive)
            break
        except FileNotFoundError:
            if time.monotonic() >= deadline:
                raise ValueError('START_AUTHORITY_MISSING') from None
            time.sleep(.02)
    context['archive_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
    context['phase'] = 'candidate'
    sys.argv = [str(archive), *options]
    runpy.run_path(str(archive), run_name='__main__')


if __name__ == '__main__':
    context = {}
    try:
        main(context)
    except SystemExit as error:
        if error.code not in (None, 0):
            print(json.dumps(refusal(context, error)), file=sys.stderr, flush=True)
        raise
    except Exception as error:
        print(json.dumps(refusal(context, error)), file=sys.stderr, flush=True)
        raise SystemExit(78) from None
