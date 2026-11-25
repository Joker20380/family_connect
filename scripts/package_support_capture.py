"""Pinned installed-shape support archives; never installs, stops or migrates a service."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import zipfile


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = Path('deploy/support-chat/support-capture-v1.json')
MODIFIED = frozenset(('messenger/routed.py', 'provisioning/subscription_notifications.py',
                      'provisioning/support_worker.py'))
ADDED = frozenset(('control/capture_gate.py', 'provisioning/support_capture.py',
                   'provisioning/support_lifecycle.py'))
ENTRYPOINT = b'from provisioning.support_worker import main\nmain()\n'
LIMIT = 512 * 1024


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def read_file(path):
    path = Path(path).absolute()
    require(not any(item.is_symlink() for item in (path, *path.parents)), 'SOURCE_SYMLINK')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(descriptor, 'rb') as source:
        before = os.fstat(source.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size <= LIMIT,
                'SOURCE_SHAPE')
        raw = source.read(LIMIT + 1)
        after = os.fstat(source.fileno())
        require((before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                (after.st_size, after.st_mtime_ns, after.st_ctime_ns) and len(raw) == before.st_size,
                'SOURCE_CHANGED_DURING_READ')
        return raw


def contract(source):
    value = json.loads(read_file(source / CONTRACT))
    require(type(value) is dict and set(value) == {'schema', 'baseline', 'candidate'} and
            value['schema'] == 1 and type(value['schema']) is int, 'CONTRACT_SCHEMA')
    for mapping in (value['baseline'], value['candidate']):
        require(type(mapping) is dict, 'CONTRACT_MAPPING')
        for name, expected in mapping.items():
            require(type(name) is str and not Path(name).is_absolute() and
                    all(part not in ('', '.', '..') for part in name.split('/')) and
                    '\\' not in name and name.endswith('.py'), 'CONTRACT_PATH')
            require(type(expected) is str and len(expected) == 64 and
                    all(character in '0123456789abcdef' for character in expected), 'CONTRACT_DIGEST')
    require(len(value['baseline']) == 19 and MODIFIED <= value['baseline'].keys() and
            not ADDED & value['baseline'].keys() and set(value['candidate']) == MODIFIED | ADDED,
            'CONTRACT_CLOSURE')
    return value


def archive(content):
    members = dict(content)
    members['__main__.py'] = ENTRYPOINT
    members['source-manifest.json'] = encode({name: digest(raw) for name, raw in sorted(content.items())})
    for name in list(members):
        for parent in Path(name).parents:
            if parent != Path('.'):
                members[str(parent) + '/'] = b''
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED) as output:
        for name, raw in sorted(members.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (0o40755 if name.endswith('/') else 0o100644) << 16
            output.writestr(info, raw)
    return buffer.getvalue()


def build(baseline, output, source=ROOT):
    baseline, output, source = Path(baseline).absolute(), Path(output).absolute(), Path(source).absolute()
    binding = contract(source)
    require(not any(item.is_symlink() for item in (baseline, *baseline.parents)), 'BASELINE_SYMLINK')
    require(baseline.is_dir(), 'BASELINE_DIRECTORY')
    require({path.relative_to(baseline).as_posix() for path in baseline.rglob('*.py')} ==
            set(binding['baseline']), 'BASELINE_CLOSURE')
    original = {}
    for name, expected in binding['baseline'].items():
        raw = read_file(baseline / name)
        require(digest(raw) == expected, 'BASELINE_DIGEST')
        original[name] = raw
    content = dict(original)
    for name, expected in binding['candidate'].items():
        raw = read_file(source / name)
        require(digest(raw) == expected, 'CANDIDATE_DIGEST')
        content[name] = raw
    require(sum(map(len, content.values())) <= 2 * 1024 * 1024, 'SOURCE_TOTAL_LIMIT')
    for name, raw in content.items():
        compile(raw, name, 'exec')
    baseline_raw, candidate_raw = archive(original), archive(content)
    receipt = dict(schema=1, baseline_sha256=digest(baseline_raw), candidate_sha256=digest(candidate_raw),
                   modified=sorted(MODIFIED), added=sorted(ADDED), removed=[], preserved=16,
                   baseline_files=binding['baseline'], files={name: digest(raw) for name, raw in content.items()})
    require(not any(item.is_symlink() for item in (output, *output.parents)), 'OUTPUT_SYMLINK')
    output.mkdir(mode=0o700, exist_ok=False)
    for name, raw in (('baseline.pyz', baseline_raw), ('candidate.pyz', candidate_raw),
                      ('receipt.json', encode(receipt))):
        descriptor = os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'wb') as target:
            target.write(raw)
            target.flush()
            os.fsync(target.fileno())
    for directory in (output, output.parent):
        descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
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
                      ('schema', 'baseline_sha256', 'candidate_sha256', 'modified', 'added', 'removed', 'preserved')},
                     sort_keys=True))


if __name__ == '__main__':
    main()
