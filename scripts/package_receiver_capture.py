"""Build the reviewed receiving-maintenance delta over the exact installed RU archive."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = Path('deploy/friends/restricted/receiver-capture-v1.json')
PATCH = Path('deploy/friends/restricted/receiver-capture-v1.patch')
UNIT = Path('deploy/friends/restricted/http-graceful-stop.conf')
MODIFIED = frozenset(('friends_http.py', 'scripts/service_notices.py',
    'control/friends/diagnostics.py', 'control/friends/technical_metadata.py',
    'control/friends/chat_sync.py', 'control/friends/transport_membership.py'))
ADDED = frozenset(('control/capture_gate.py', 'control/friends/http_lifecycle.py'))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read_file(path, maximum=2 * 1024 * 1024):
    path = Path(path).absolute()
    require(all(not item.is_symlink() for item in (path, *path.parents)), 'SYMLINK_INPUT')
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
    with os.fdopen(descriptor, 'rb') as source:
        require(stat.S_ISREG(os.fstat(source.fileno()).st_mode), 'REGULAR_INPUT_REQUIRED')
        raw = source.read(maximum + 1)
    require(len(raw) <= maximum, 'INPUT_TOO_LARGE')
    return raw


def inventory(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        require(0 < len(entries) <= 128, 'ARCHIVE_ENTRY_LIMIT')
        names = [entry.filename for entry in entries]
        require(len(names) == len(set(names)), 'DUPLICATE_MEMBER')
        require(sum(entry.file_size for entry in entries) <= 8 * 1024 * 1024, 'EXPANDED_SIZE_LIMIT')
        for entry in entries:
            name = entry.filename.rstrip('/')
            require(name and not name.startswith('/') and '\\' not in name
                    and all(part not in ('', '.', '..') for part in name.split('/')), 'UNSAFE_MEMBER')
            require(not stat.S_ISLNK(entry.external_attr >> 16) and not entry.flag_bits & 1,
                    'UNSUPPORTED_MEMBER')
        return entries, {entry.filename: archive.read(entry) for entry in entries}


def build(baseline, output, *, source=ROOT):
    source, output = Path(source), Path(output)
    require(not output.exists() and not output.is_symlink(), 'OUTPUT_EXISTS')
    require(all(not parent.is_symlink() for parent in output.absolute().parents), 'OUTPUT_SYMLINK')
    contract_raw = read_file(source / CONTRACT)
    contract = json.loads(contract_raw)
    require(contract['schema'] == 1 and set(contract['before']) == set(contract['after']) == MODIFIED
            and set(contract['added']) == ADDED, 'CONTRACT_SCOPE')
    raw = read_file(baseline)
    require(digest(raw) == contract['baseline_sha256'], 'INSTALLED_ARCHIVE_PIN')
    entries, before = inventory(raw)
    require(MODIFIED <= before.keys() and not ADDED & before.keys(), 'BASELINE_SCOPE')
    require(all(digest(before[name]) == expected for name, expected in contract['before'].items()),
            'INSTALLED_MEMBER_PIN')
    patch = read_file(source / PATCH)
    unit = read_file(source / UNIT)
    require(digest(patch) == contract['patch_sha256'] and digest(unit) == contract['unit_sha256'],
            'DELTA_PIN')
    replacements = {name: read_file(source / name) for name in ADDED}
    require(all(digest(replacements[name]) == expected for name, expected in contract['added'].items()),
            'ADDED_SOURCE_PIN')
    with tempfile.TemporaryDirectory(prefix='fc-receiver-overlay-') as directory:
        work = Path(directory)
        stage = work / 'stage'
        stage.mkdir(mode=0o700)
        for name in MODIFIED:
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(before[name])
        delta = work / 'reviewed.patch'
        delta.write_bytes(patch)
        for check in (True, False):
            command = ['git', 'apply', '--whitespace=error-all']
            if check:
                command.append('--check')
            subprocess.run([*command, str(delta)], cwd=stage, check=True, capture_output=True, timeout=10)
        require({str(path.relative_to(stage)) for path in stage.rglob('*') if path.is_file()} == MODIFIED,
                'PATCH_SCOPE')
        for name, expected in contract['after'].items():
            replacements[name] = read_file(stage / name)
            require(digest(replacements[name]) == expected, 'PATCH_RESULT_PIN')
    for name, content in replacements.items():
        compile(content, name, 'exec')
    with io.BytesIO() as buffer:
        with zipfile.ZipFile(buffer, 'w') as candidate:
            for entry in entries:
                candidate.writestr(entry, replacements.get(entry.filename, before[entry.filename]))
            for name in sorted(ADDED):
                entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                candidate.writestr(entry, replacements[name])
        candidate_raw = buffer.getvalue()
    _, after = inventory(candidate_raw)
    require(after.keys() == before.keys() | ADDED, 'CANDIDATE_SCOPE')
    require(all(after[name] == content for name, content in before.items() if name not in MODIFIED),
            'UNRELATED_BYTES_CHANGED')
    receipt = dict(schema=1, baseline_sha256=digest(raw), candidate_sha256=digest(candidate_raw),
        contract_sha256=digest(contract_raw), patch_sha256=digest(patch), unit_sha256=digest(unit),
        before={name: digest(content) for name, content in before.items()},
        after={name: digest(content) for name, content in after.items()},
        modified=sorted(MODIFIED), added=sorted(ADDED), removed=[], installed=False,
        scope='Receiving maintenance only; legacy data/policy retained; not all-writer capture permission')
    output.mkdir(mode=0o700)
    for name, content in (('friends-http.pyz', candidate_raw), ('http-graceful-stop.conf', unit),
                          ('receipt.json', (json.dumps(receipt, sort_keys=True, indent=2) + '\n').encode())):
        descriptor = os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'wb') as target:
            target.write(content)
            target.flush()
            os.fsync(target.fileno())
    for path in (output, output.parent):
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.baseline, args.output)
    print(json.dumps({name: result[name] for name in
        ('baseline_sha256', 'candidate_sha256', 'modified', 'added', 'removed', 'installed')}))


if __name__ == '__main__':
    main()
