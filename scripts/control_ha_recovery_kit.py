"""Pinned offline recovery sources/wheels; stdlib bootstrap, never activation authority."""
import email.parser
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tarfile
import zipfile

PURPOSE = 'family-connect/recovery-toolkit/v1/cp313-linux-amd64/offline-only'
LOCKS = ('control/requirements.lock', 'device_identity/requirements.lock', 'deploy/control-ha/requirements.lock')
SCHEMAS = ('deploy/control-ha/sqlite-source-v1.json', 'deploy/control-ha/sqlite-handoff-v2.json')
NATIVE = ('deploy/friends/awg-gateway.py', 'deploy/product-peer-worker/worker.py',
          'clients/desktop/profile_config.py', 'clients/desktop/updates.py')
SOURCE_ROOTS = ('control', 'device_identity', 'scripts', 'provisioning', 'messenger')
BOOTSTRAP = 'scripts/control_ha_recovery_kit.py'
LIMIT = 128 * 1024 * 1024
FILE_LIMIT = 32 * 1024 * 1024
MAX_FILES = 1024


def require(condition, code):
    if not condition:
        raise ValueError(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def pairs(items):
    result = {}
    for name, value in items:
        require(name not in result, 'DUPLICATE_JSON_KEY')
        result[name] = value
    return result


def document(raw):
    require(len(raw) <= 1024 * 1024, 'JSON_BOUNDS')
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: require(False, 'NONFINITE_JSON'))


def path_allowed(name):
    return (type(name) is str and len(name) <= 240 and
            re.fullmatch(r'[a-zA-Z0-9_.-]+(?:/[a-zA-Z0-9_.-]+)*', name) is not None and
            not any(part in ('.', '..') for part in name.split('/')))


def source_allowed(name):
    return path_allowed(name) and (name in LOCKS + SCHEMAS + NATIVE or
        (name.split('/')[0] in SOURCE_ROOTS and name.endswith(('.py', '.sql'))))


def normalize(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def requirements(sources):
    result = {}
    require(set(LOCKS + SCHEMAS + NATIVE + (BOOTSTRAP,)) <= sources.keys(), 'REQUIRED_SOURCE_MISSING')
    for name in LOCKS:
        for line in sources[name].decode('ascii').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            match = re.fullmatch(r'([a-zA-Z0-9][a-zA-Z0-9_.-]*)==([a-zA-Z0-9][a-zA-Z0-9_.+!-]*)', line)
            require(match is not None, 'UNPINNED_REQUIREMENT')
            package, version = normalize(match[1]), match[2]
            require(package not in result or result[package] == version, 'LOCK_CONFLICT')
            result[package] = version
    require(bool(result), 'EMPTY_REQUIREMENTS')
    return result


def wheel_identity(name, raw):
    require(path_allowed(name) and '/' not in name and name.endswith('.whl') and
            0 < len(raw) <= FILE_LIMIT, 'WHEEL_FILE')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        require(0 < len(members) <= 8192 and len({item.filename for item in members}) == len(members)
                and sum(item.file_size for item in members) <= LIMIT, 'WHEEL_BOUNDS')
        require(all(path_allowed(item.filename.rstrip('/')) and
                    not stat.S_ISLNK(item.external_attr >> 16) for item in members), 'WHEEL_MEMBER')
        metadata = [item for item in members if item.filename.endswith('.dist-info/METADATA')]
        require(len(metadata) == 1 and metadata[0].file_size <= 1024 * 1024, 'WHEEL_METADATA')
        fields = email.parser.BytesParser().parsebytes(archive.read(metadata[0]))
        require(len(fields.get_all('Name', [])) == len(fields.get_all('Version', [])) == 1, 'WHEEL_IDENTITY')
        package, version = normalize(fields['Name']), fields['Version']
        parts = name[:-4].split('-')
        require(len(parts) in (5, 6) and normalize(parts[0]) == package and parts[1] == version,
                'WHEEL_FILENAME_IDENTITY')
        return package, version


def locked_install(sources, wheels):
    expected, selected = requirements(sources), {}
    for name, raw in wheels.items():
        package, version = wheel_identity(name, raw)
        require(package in expected and expected[package] == version and package not in selected, 'WHEEL_LOCK_BINDING')
        selected[package] = digest(raw)
    require(selected.keys() == expected.keys(), 'WHEEL_COVERAGE')
    return ''.join(f'{name}=={version} --hash=sha256:{selected[name]}\n'
                   for name, version in sorted(expected.items())).encode()


def collect_sources(repository, commit):
    require(re.fullmatch('[a-f0-9]{40}', commit) is not None, 'SOURCE_COMMIT')
    listing = subprocess.check_output(['git', 'ls-tree', '-rz', commit, '--',
        *SOURCE_ROOTS, 'deploy/control-ha', *NATIVE], cwd=repository)
    sources = {}
    for item in listing.split(b'\0'):
        if not item:
            continue
        record, raw_name = item.split(b'\t', 1)
        name = raw_name.decode('ascii')
        if not source_allowed(name):
            continue
        mode, kind, identifier = record.decode('ascii').split()
        require(mode in ('100644', '100755') and kind == 'blob', 'SOURCE_REGULAR_FILE')
        size = int(subprocess.check_output(['git', 'cat-file', '-s', identifier], cwd=repository))
        require(size <= FILE_LIMIT, 'SOURCE_SIZE')
        sources[name] = subprocess.check_output(['git', 'cat-file', 'blob', identifier], cwd=repository)
    requirements(sources)
    return sources


def pack(sources, wheels, commit):
    require(type(sources) is dict and type(wheels) is dict and sources and wheels and
            all(source_allowed(name) for name in sources), 'SOURCE_SCOPE')
    require(type(commit) is str and re.fullmatch('[a-f0-9]{40}', commit), 'SOURCE_COMMIT')
    install = locked_install(sources, wheels)
    files = {'source/' + name: raw for name, raw in sources.items()}
    files.update({'wheels/' + name: raw for name, raw in wheels.items()})
    files['requirements-hashed.txt'] = install
    require(len(files) <= MAX_FILES and all(type(raw) is bytes and len(raw) <= FILE_LIMIT
            for raw in files.values()) and sum(map(len, files.values())) <= LIMIT // 2, 'KIT_BOUNDS')
    manifest = encoded(dict(purpose=PURPOSE, source_commit=commit,
        files={name: dict(bytes=len(raw), sha256=digest(raw)) for name, raw in sorted(files.items())}))
    files['manifest.json'] = manifest
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w:', format=tarfile.USTAR_FORMAT) as archive:
        for name, raw in sorted(files.items()):
            info = tarfile.TarInfo(name)
            info.size, info.mode = len(raw), 0o600
            archive.addfile(info, io.BytesIO(raw))
    raw = stream.getvalue()
    require(len(raw) <= LIMIT, 'ARCHIVE_BOUNDS')
    checkpoint = dict(purpose=PURPOSE, source_commit=commit, archive_sha256=digest(raw),
                      manifest_sha256=digest(manifest), bootstrap_sha256=digest(sources[BOOTSTRAP]))
    verify(raw, checkpoint)
    return raw, checkpoint


def verify(raw, checkpoint):
    require(type(checkpoint) is dict and set(checkpoint) == {'purpose', 'source_commit', 'archive_sha256',
            'manifest_sha256', 'bootstrap_sha256'} and checkpoint['purpose'] == PURPOSE, 'CHECKPOINT_SHAPE')
    require(all(type(checkpoint[name]) is str and re.fullmatch('[a-f0-9]{' +
            ('40' if name == 'source_commit' else '64') + '}', checkpoint[name])
            for name in checkpoint if name != 'purpose'), 'CHECKPOINT_PIN')
    require(type(raw) is bytes and 0 < len(raw) <= LIMIT and digest(raw) == checkpoint['archive_sha256'],
            'STALE_OR_CHANGED_KIT')
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        for member in archive:
            require(len(files) < MAX_FILES + 1 and path_allowed(member.name) and member.name not in files and
                    member.isfile() and member.sparse is None and not member.pax_headers and
                    0 <= member.size <= FILE_LIMIT, 'ARCHIVE_MEMBER')
            files[member.name] = archive.extractfile(member).read()
    require('manifest.json' in files, 'MANIFEST_MISSING')
    manifest_raw = files.pop('manifest.json')
    require(digest(manifest_raw) == checkpoint['manifest_sha256'], 'MANIFEST_PIN')
    manifest = document(manifest_raw)
    require(type(manifest) is dict and set(manifest) == {'purpose', 'source_commit', 'files'} and
            manifest['purpose'] == PURPOSE and manifest['source_commit'] == checkpoint['source_commit'] and
            type(manifest['files']) is dict and set(manifest['files']) == set(files), 'MANIFEST_COVERAGE')
    require(all(record == dict(bytes=len(files[name]), sha256=digest(files[name]))
                for name, record in manifest['files'].items()), 'MEMBER_PIN')
    sources = {name.removeprefix('source/'): body for name, body in files.items() if name.startswith('source/')}
    wheels = {name.removeprefix('wheels/'): body for name, body in files.items() if name.startswith('wheels/')}
    require(all(source_allowed(name) for name in sources) and
            len(files) == len(sources) + len(wheels) + 1 and 'requirements-hashed.txt' in files, 'KIT_SCOPE')
    require(locked_install(sources, wheels) == files['requirements-hashed.txt'], 'INSTALL_PIN')
    require(digest(sources[BOOTSTRAP]) == checkpoint['bootstrap_sha256'], 'BOOTSTRAP_PIN')
    return files, dict(result='RECOVERY_KIT_VERIFIED', source_commit=checkpoint['source_commit'],
        source_files=len(sources), wheels=len(wheels), activation=False, full_recovery=False)


def private_file(path, raw):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def restore(raw, checkpoint, destination):
    files, receipt = verify(raw, checkpoint)
    destination = Path(destination)
    require(destination.is_absolute() and '..' not in destination.parts and
            not any(parent.is_symlink() for parent in (destination, *destination.parents)), 'RESTORE_PATH')
    parent = destination.parent.stat()
    require(parent.st_uid == os.getuid() and stat.S_IMODE(parent.st_mode) == 0o700, 'PRIVATE_PARENT')
    destination.mkdir(mode=0o700)
    for name, body in sorted(files.items()):
        target = destination / name
        for parent in reversed(target.parents):
            if destination in parent.parents:
                parent.mkdir(mode=0o700, exist_ok=True)
        private_file(target, body)
        require(digest(target.read_bytes()) == digest(body), 'RESTORE_READBACK')
    private_file(destination / 'receipt.json', encoded(receipt))
    return receipt


if __name__ == '__main__':
    try:
        require(len(sys.argv) == 4, 'RESTORE_ARGUMENTS')
        checkpoint = document(Path(sys.argv[2]).read_bytes())
        require(digest(Path(__file__).read_bytes()) == checkpoint['bootstrap_sha256'], 'BOOTSTRAP_PIN')
        print(json.dumps(restore(Path(sys.argv[1]).read_bytes(), checkpoint, sys.argv[3]), sort_keys=True))
    except Exception as error:
        print(json.dumps(dict(result='RECOVERY_KIT_REFUSED', error=type(error).__name__)), file=sys.stderr)
        raise SystemExit(1) from None
