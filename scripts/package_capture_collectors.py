"""Prepare pinned collector source candidates; never install, read state or dispatch work."""
import argparse
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 256 * 1024
ADMISSION = {
    'control/capture_gate.py': 'da28d940e2e17e2dbb1fbbde8cc04c59d29cffc8762ada717135504e2ffa4906',
    'control_plane/fc_control_plane/capture.py': '0cb1ad0190ddc0d0043c93df80a72f751627a29d054ef104fcf5d1732dca434b',
    'control_plane/collector_admission.py': 'bdb9e7711cb21a889a42f663bea49fc2bab371aba5b74eacdce9c4b849954721',
    'control_plane/collector_binding.py': 'f29de5251582210cd25287cc8f2ed37df3e9993da4c5b0ff2e10b71be67f84d6',
}
ADMISSION_HISTORY = {
    'control_plane/fc_control_plane/capture.py': ('d4f5a258232d505f3ded09b7ce16a58f013a48dd451fa878d2a191c42ac7d60d',),
    'control_plane/collector_admission.py': ('1e2e52abb618b620f9ba1e38dc9011d0143021d98cb3e5bfa535a3f79669808f',),
}
ENTRIES = {
    'control_plane/monitor_inventory.py': ('2b56e0c3504e28bf644e17cf0cc4c14d5106c9862a9af80e97c8d7d62b490fd7',
                                         '8856e4454d4ecf68895a22a0d2cff0c87353d91b4ea5500c03383b8cd7aa3923'),
    'control_plane/collect_inventory.py': ('a848b67feb86d8fa89722327c43539456ef20cb4cac60b4e2caefccc52e9b976',
                                         '92650e6c8863945c20816a4c2e0b93bdb6b23e136c83c514bdd98f6031c4cfb1',
                                         'd3ed036ccd4824e93c50ab8a5fcd26a243664671f8620e245f4b2adba8d16a4a'),
    'control_plane/collect_technical_metadata.py': ('6442b9463082a7f2b19914a1e8df8e51ad3d6c85ccdc37c710bf8f323f806423',
                                                 '3c8495b7fc1a025f5fd4496d1d0ce341e50d43ccc86de5b1c4c7df9a0d066913'),
    'control_plane/probe_network.py': ('cabe6f1a49f80e6aa9afff8d8f813c921a191a40eb61f7313af110a8037e64eb',
                                     '19ed2bf5e2769cc4f5f1b5bd2b94b4ac74212ecd0059d95f5ff8af6c6cd3f9bf',
                                     '0adde03f5dc2a01756c42c5335f8cf4ff53f8c9d8651a4a3f0b9fa36d8f4407a'),
}
ROLES = {
    'inventory': ('control_plane/monitor_inventory.py', 'control_plane/collect_inventory.py',
                  'control_plane/collect_technical_metadata.py'),
    'probe': ('control_plane/probe_network.py',),
}
COMMON = ('control_plane/apps/console/collector.py', 'control_plane/apps/__init__.py',
          'control_plane/apps/console/__init__.py', 'control_plane/fc_control_plane/__init__.py')
DEPENDENCIES = {
    'inventory': ('control/friends/__init__.py', 'control/friends/pseudonyms.py',
                  'control_plane/collect_technical_metadata.py',
                  *('control_plane/apps/console/' + name + '_collector.py' for name in
                    ('metrics', 'transport', 'subscription', 'technical_metadata'))),
    'probe': ('control_plane/apps/console/network_probe.py',),
}
NAMESPACE_FILES = ('control/__init__.py', 'control_plane/__init__.py')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(raw):
    return None if raw is None else hashlib.sha256(raw).hexdigest()


def read_source(path, optional=False):
    require(path.is_absolute() and '..' not in path.parts, 'SOURCE_PATH')
    with ExitStack() as stack:
        descriptor = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
        stack.callback(os.close, descriptor)
        try:
            for part in path.parts[1:-1]:
                descriptor = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
                stack.callback(os.close, descriptor)
            descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
            stack.callback(os.close, descriptor)
        except FileNotFoundError:
            if optional:
                return None
            raise ValueError('SOURCE_MISSING') from None
        before = os.fstat(descriptor)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_uid in (0, os.geteuid()) and
                not before.st_mode & 0o7002 and 0 <= before.st_size <= LIMIT, 'SOURCE_SHAPE')
        with os.fdopen(os.dup(descriptor), 'rb') as handle:
            raw = handle.read(LIMIT + 1)
        after = os.fstat(descriptor)
        fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_mode', 'st_nlink', 'st_uid')
        require(len(raw) == before.st_size and all(getattr(before, name) == getattr(after, name) for name in fields),
                'SOURCE_CHANGED')
        return raw


def snapshot(baseline, role):
    require(role in ROLES, 'COLLECTOR_ROLE')
    names = set(ROLES[role]) | set(COMMON) | set(DEPENDENCIES[role]) | set(ADMISSION) | set(NAMESPACE_FILES)
    optional = set(ADMISSION) | set(NAMESPACE_FILES)
    return {name: read_source(baseline / name, name in optional) for name in sorted(names)}


def build(baseline, role, pins, output, source=ROOT):
    require(output.is_absolute() and not output.resolve().is_relative_to(baseline.resolve()) and
            not output.resolve().is_relative_to(source.resolve()), 'OUTPUT_SCOPE')
    before = snapshot(baseline, role)
    require(type(pins) is dict and set(pins) == set(before) and
            all(value is None or (type(value) is str and re.fullmatch('[a-f0-9]{64}', value)) for value in pins.values()),
            'PIN_COVERAGE')
    require(pins == {name: digest(raw) for name, raw in before.items()}, 'BASELINE_PIN')
    require(all(before[name] is None for name in NAMESPACE_FILES), 'UNREVIEWED_NAMESPACE_INITIALIZER')
    require(all(pins[name] in ENTRIES[name] for name in ROLES[role]), 'UNREVIEWED_ENTRYPOINT')
    require(all(pins[name] in (None, expected, *ADMISSION_HISTORY.get(name, ()))
                for name, expected in ADMISSION.items()), 'UNREVIEWED_ADMISSION')
    replacements = dict(ADMISSION) | {name: ENTRIES[name][1] for name in ROLES[role]}
    after = {name: raw for name, raw in before.items() if raw is not None}
    for name, expected in replacements.items():
        raw = read_source(source / name)
        require(digest(raw) == expected, 'CANDIDATE_PIN')
        compile(raw, name, 'exec')
        after[name] = raw
    require(pins == {name: digest(raw) for name, raw in snapshot(baseline, role).items()}, 'BASELINE_CHANGED')
    receipt = dict(schema=1, baseline='owner-user-collectors-mandatory-v1', role=role,
                   before=pins, after={name: digest(raw) for name, raw in after.items()},
                   changed=sorted(name for name, raw in after.items() if digest(raw) != pins[name]),
                   installed=False, capture_permitted=False, runtime_qualified=False)
    receipt['restore_on_rollback'] = {name: pins[name] for name in receipt['changed'] if before[name] is not None}
    receipt['remove_on_rollback'] = [name for name in receipt['changed'] if before[name] is None]
    rollback = {'rollback/' + name: before[name] for name in receipt['restore_on_rollback']}
    contents = after | rollback | {'manifest.json': (json.dumps(receipt, sort_keys=True, indent=2) + '\n').encode()}
    with output.open('xb') as handle:
        os.fchmod(handle.fileno(), 0o600)
        with zipfile.ZipFile(handle, 'w', compression=zipfile.ZIP_STORED) as archive:
            for name, raw in sorted(contents.items()):
                entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, raw)
    return receipt | dict(sha256=digest(output.read_bytes()))


def unique(pairs):
    values = dict(pairs)
    require(len(values) == len(pairs), 'DUPLICATE_PIN')
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--role', choices=ROLES, required=True)
    parser.add_argument('--pins', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        pins = json.loads(read_source(args.pins), object_pairs_hook=unique)
        receipt = build(args.baseline, args.role, pins, args.output)
    except (OSError, ValueError, SyntaxError):
        parser.exit(1, 'COLLECTOR_CANDIDATE_REFUSED\n')
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
