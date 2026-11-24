"""Explicit admission wrapper for a pinned renewal capsule; no installation or capture."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import resource
import stat
import sys

ENTRIES = {'renewal': 'renewal_cli', 'online': 'online_cli', 'node': 'node',
           'scheduled': 'scheduled_evaluate'}


def require(condition):
    if not condition:
        raise ValueError('CAPTURE_KIT_REFUSED')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result)
        result[key] = value
    return result


def read_pinned(path, expected, limit):
    require(type(expected) is str and re.fullmatch('[0-9a-f]{64}', expected))
    require(path.is_absolute() and all(not parent.is_symlink() for parent in (path, *path.parents)))
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        info = os.fstat(descriptor)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and
                info.st_uid == os.geteuid() and not stat.S_IMODE(info.st_mode) & 0o022 and
                0 < info.st_size <= limit)
        with os.fdopen(os.dup(descriptor), 'rb') as stream:
            raw = stream.read(limit + 1)
        require(len(raw) <= limit and digest(raw) == expected)
        return raw, descriptor
    except BaseException:
        os.close(descriptor)
        raise


def load_kit(source, expected, entry):
    raw, descriptor = read_pinned(source.parent / 'source-manifest.json', expected, 1024 * 1024)
    os.close(descriptor)
    manifest = json.loads(raw, object_pairs_hook=unique)
    require(type(manifest) is dict and manifest.get('binding') == 'unbound' and
            manifest.get('production_configuration') == 'absent' and
            'operation_permit' in manifest and manifest['operation_permit'] is None)
    files = manifest.get('source_files')
    require(type(files) is dict and {'capture_entry.py', entry + '.py', 'production_transport.py'} <= files.keys())
    require({path.name for path in source.iterdir()} == set(files))
    canonical = json.dumps(files, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    require(digest(canonical) == manifest.get('source_sha256') and type(manifest.get('files')) is dict)
    for name, expected_hash in files.items():
        require(type(name) is str and re.fullmatch(r'[a-z_]+\.py', name))
        require(manifest['files'].get('renewal/' + name) == expected_hash)
        _, descriptor = read_pinned(source / name, expected_hash, 1024 * 1024)
        os.close(descriptor)
    require(manifest['files'].get('api.pyz') == manifest.get('api_sha256'))
    _, descriptor = read_pinned(source.parent / 'api.pyz', manifest['api_sha256'], 16 * 1024 * 1024)
    return descriptor


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--capture-gate', type=Path, required=True)
    parser.add_argument('--entry', choices=sorted(ENTRIES), required=True)
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    descriptor = None
    original_path, original_argv = sys.path[:], sys.argv[:]
    try:
        require(sys.flags.isolated and args.arguments[:1] == ['--'])
        os.umask(0o077)
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        sys.dont_write_bytecode = True
        source = Path(__file__).absolute().parent
        entry = ENTRIES[args.entry]
        descriptor = load_kit(source, args.manifest_sha256, entry)
        sys.path[:0] = [str(source), '/proc/self/fd/' + str(descriptor)]
        import control.capture_gate as capture
        require(capture.__file__ == '/proc/self/fd/' + str(descriptor) + '/control/capture_gate.py')
        from control.capture_gate import Busy, Gate, GateError
        try:
            with Gate(args.capture_gate).operation():
                module = importlib.import_module(entry)
                sys.argv = [str(source / (entry + '.py')), *args.arguments[1:]]
                try:
                    outcome = module.main()
                except SystemExit as error:
                    if error.code not in (None, 0):
                        raise
                    outcome = 0
                if outcome not in (None, 0):
                    raise SystemExit(outcome if type(outcome) is int else 1)
            return 0
        except Busy:
            print(json.dumps(dict(result='FAIL_CLOSED', cause='CAPTURE_BUSY', automatic_retry=False)))
            return 75
        except GateError:
            print(json.dumps(dict(result='FAIL_CLOSED', cause='CAPTURE_REFUSED', automatic_retry=False)))
            return 1
    except Exception:
        print(json.dumps(dict(result='FAIL_CLOSED', cause='CAPTURE_KIT_REFUSED', automatic_retry=False)))
        return 1
    finally:
        sys.path[:], sys.argv[:] = original_path, original_argv
        if descriptor is not None:
            os.close(descriptor)


if __name__ == '__main__':
    raise SystemExit(main())
