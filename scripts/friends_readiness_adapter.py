"""Stdlib bootstrap: persist safe failures even when runtime imports are missing."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import sys
import zipfile

IMPORT_ROOTS = frozenset(('control', 'provisioning', 'clients', 'device_identity',
                          'scripts', 'cryptography', 'RNS', 'serial', 'cffi',
                          '_cffi_backend', 'pycparser')) | sys.stdlib_module_names


def safe_module(value):
    if (type(value) is str and len(value) <= 160
            and re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*', value)
            and value.split('.')[0] in IMPORT_ROOTS):
        return value
    return 'unknown'


def failure_details(error, artifact):
    frames = []
    trace = error.__traceback__
    while trace is not None:
        frame = trace.tb_frame
        filename = frame.f_code.co_filename
        if filename.startswith(str(artifact) + '/'):
            filename = 'artifact/' + filename[len(str(artifact)) + 1:]
        elif filename.startswith(sys.base_prefix + '/lib/python'):
            filename = 'python-runtime/' + Path(filename).name
        else:
            filename = '<external>'
        frames.append(dict(module=safe_module(frame.f_globals.get('__name__')),
                           file=filename, line=trace.tb_lineno))
        trace = trace.tb_next
    known = type(error).__module__ == 'builtins' or type(error).__name__ == 'ProbeFailed'
    return dict(exception_class=type(error).__name__ if known else 'RuntimeError',
                missing_module=safe_module(error.name) if isinstance(error, ImportError) else None,
                importing_module=frames[-1]['module'] if frames else 'unknown',
                import_failure=('transitive' if any(frame['module'].startswith(('control.', 'scripts.', 'device_identity.', 'provisioning.'))
                                                   for frame in frames) else 'entrypoint') if isinstance(error, ImportError) else None,
                frames=frames[-12:])


def persist(directory, value):
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        metadata = os.fstat(descriptor)
        if metadata.st_uid != os.geteuid() or metadata.st_mode & 0o077:
            raise ValueError('Unsafe evidence directory')
        output = os.open('result.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=descriptor)
        with os.fdopen(output, 'w') as stream:
            json.dump(value, stream, separators=(',', ':'))
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    arguments, unrecognized = parser.parse_known_args()
    artifact = Path(sys.argv[0]).resolve()
    record = dict(version=1, timestamp=datetime.now(timezone.utc).isoformat(), passed=False,
                  step='runtime_import', receipt_class='adapter_execution',
                  runtime_artifact=str(artifact), artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),
                  cwd=str(Path.cwd()), isolated=bool(sys.flags.isolated),
                  argv_shape=['python', '-I', '<adapter.pyz>', '--config', '<config>', '--evidence', '<directory>']
                  + (['--check'] if arguments.check else []),
                  search_roots=list(sys.path), python=sys.version.split()[0])
    try:
        arguments.evidence.mkdir(mode=0o700, exist_ok=False)
        parent = os.open(arguments.evidence.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    except OSError:
        print(json.dumps(dict(passed=False, classification='receipt_storage_failed')))
        return 2
    try:
        if unrecognized:
            record['step'] = 'arguments'
            raise ValueError('Unexpected arguments')
        runtime = importlib.import_module('control.friends.readiness_adapter')
        record['step'] = 'inventory'
        with zipfile.ZipFile(artifact) as archive:
            manifest = json.loads(archive.read('adapter-inventory.json'))
            for name, digest in manifest['files'].items():
                if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                    raise ValueError('Runtime inventory mismatch')
        record['source_head'] = manifest['source_head']
        record['step'] = 'configuration'
        config = runtime.configuration(arguments.config, artifact.parent, manifest)
        record['runtime_versions'] = runtime.versions()
        if not arguments.check:
            runtime.execute(config, arguments.evidence, record)
        record.update(passed=True, step='complete')
    except Exception as error:
        record.update(failure_details(error, artifact))
    try:
        persist(arguments.evidence, record)
    except (OSError, ValueError):
        print(json.dumps(dict(passed=False, classification='receipt_storage_failed')))
        return 2
    print(json.dumps(dict(passed=record['passed'], step=record['step'])))
    return 0 if record['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
