"""Independent exact-byte reader for a stopped support component, never restore or approve."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

LIMIT = 32 * 1024 * 1024


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def unique(items):
    result = {}
    for name, value in items:
        require(name not in result, 'DUPLICATE_FIELD')
        result[name] = value
    return result


def raw(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and
            not any(item.is_symlink() for item in (path, *path.parents)), 'INPUT_PATH')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW), 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= LIMIT, 'INPUT_TYPE')
        data = stream.read(LIMIT + 1)
        after = os.fstat(stream.fileno())
    require(len(data) == before.st_size and (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'INPUT_CHANGED')
    return data


def check(snapshot_path, expected, plan_path):
    payload = raw(snapshot_path)
    require(hashlib.sha256(payload).hexdigest() == expected, 'SNAPSHOT_DIGEST')
    snapshot = json.loads(payload, object_pairs_hook=unique)
    require(set(snapshot) == {'schema', 'purpose', 'source_roots', 'entries', 'boundary', 'writer_evidence',
            'plan_sha256', 'pending_history', 'history_settled', 'fleet_capture', 'recovery_authorized',
            'captured_at_ns'}, 'SNAPSHOT_FIELDS')
    plan_raw = raw(plan_path)
    plan = json.loads(plan_raw, object_pairs_hook=unique)
    require(snapshot['schema'] == 1 and snapshot['purpose'] ==
            'family-connect/stopped-support-component/v1/not-fleet-capture' and
            snapshot['plan_sha256'] == hashlib.sha256(plan_raw).hexdigest() and
            all(snapshot[name] is False for name in ('history_settled', 'fleet_capture', 'recovery_authorized')),
            'SNAPSHOT_SCOPE')
    arguments = plan['new_argv']
    roots = {}
    for name, option in (('store', '--store'), ('runtime', '--runtime'), ('key', '--key')):
        require(arguments.count(option) == 1, 'PLAN_ARGUMENT')
        roots[name] = arguments[arguments.index(option) + 1]
    roots.update(gate=plan['gate'], recovery=plan['root'], authority=plan['start_authority'])
    for name in ('operation', 'pending-before', 'reclosure', 'stop-intent', 'stopped'):
        roots['stop-' + name] = str(Path(snapshot_path).parent / (name + '.json'))
    require(snapshot['source_roots'] == roots, 'ROOT_COVERAGE')
    entries = snapshot['entries']
    require(type(entries) is dict and 0 < len(entries) <= 4096, 'ENTRY_BOUNDS')
    observed, bytes_total = set(), 0

    def visit(name, path):
        nonlocal bytes_total
        require(name in entries and name not in observed and not path.is_symlink(), 'ENTRY_COVERAGE')
        observed.add(name)
        entry, information = entries[name], path.stat()
        signature = [getattr(information, field) for field in ('st_dev', 'st_ino', 'st_uid', 'st_gid',
                     'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')]
        require(entry['path'] == str(path) and entry['stamp'] == signature, 'ENTRY_BINDING')
        if stat.S_ISDIR(information.st_mode):
            require(set(entry) == {'path', 'stamp', 'kind', 'children'} and entry['kind'] == 'directory',
                    'DIRECTORY_FIELDS')
            children = sorted(child.name for child in path.iterdir())
            require(entry['children'] == children, 'DIRECTORY_COVERAGE')
            for child in children:
                visit(name + '/' + child, path / child)
        else:
            require(set(entry) == {'path', 'stamp', 'kind', 'body', 'sha256'} and entry['kind'] == 'file', 'FILE_FIELDS')
            data = base64.b64decode(entry['body'], validate=True)
            require(hashlib.sha256(data).hexdigest() == entry['sha256'] and data == raw(path), 'FILE_BYTES')
            bytes_total += len(data)
            require(bytes_total <= 16 * 1024 * 1024, 'TOTAL_BYTES')

    for name, value in roots.items():
        visit(name, Path(value))
    require(observed == set(entries), 'EXTRA_ENTRIES')
    pending = sorted(name for name in entries if name.startswith('gate/pending/'))
    require(pending == snapshot['pending_history'] and
            {'gate/pending/' + name for name in plan['pending']} <= set(pending), 'PENDING_COVERAGE')
    for name in pending:
        require(base64.b64decode(entries[name]['body'], validate=True) == b'family-connect/capture-operation/v1\n',
                'PENDING_BYTES')
    proof = snapshot['boundary']['absence']
    accepted = json.loads(raw(Path(plan['root']) / 'accepted.json'), object_pairs_hook=unique)
    authority = json.loads(raw(plan['start_authority']), object_pairs_hook=unique)
    require(proof['reason'] == 'CLEAN_UNIT_EXIT' and proof['graceful_exit_proven'] is True and
            proof['old_binding'] == accepted['binding'] == authority['binding'] and
            accepted['archive_sha256'] == authority['archive_sha256'], 'ACCEPTED_AUTHORITY_BINDING')
    require(type(snapshot['captured_at_ns']) is int and type(snapshot['boundary']['started_at_ns']) is int and
            0 < snapshot['boundary']['started_at_ns'] <= snapshot['captured_at_ns'] and
            snapshot['boundary']['history_settled'] is False and proof['settlement_proven'] is False and
            proof['boot'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip(), 'CLOSED_INTERVAL_BINDING')
    require(plan['unit'] == 'family-connect-support.service' or re.fullmatch(
            r'fc-ha-support-replace-(?:test|fixture)-[0-9a-f]{32}\.service', plan['unit']), 'UNIT_SCOPE')
    command = ['systemctl', *(['--user'] if plan['user'] else []), 'show', plan['unit'],
               '--property=MainPID,ControlPID,ExecMainPID,ExecMainCode,ExecMainStatus,ControlGroup']
    state = dict(line.split('=', 1) for line in subprocess.check_output(command, text=True, timeout=10).splitlines())
    require(state['MainPID'] == state['ControlPID'] == '0' and state['ExecMainPID'] == str(accepted['binding']['pid'])
            and state['ExecMainCode'] == '1' and state['ExecMainStatus'] == '0', 'CURRENT_CLEAN_EXIT_REQUIRED')
    for name in {state['ControlGroup'], plan['before']['ControlGroup']} - {''}:
        directory = Path('/sys/fs/cgroup') / name.lstrip('/')
        if directory.exists():
            require(not any(path.read_text().strip() for path in directory.rglob('cgroup.procs')), 'CGROUP_WRITER')
    for name, digest in proof['history'].items():
        require(name in ('accepted.json', 'handoff-open.json', 'plan.json') and
                hashlib.sha256(raw(Path(plan['root']) / name)).hexdigest() == digest, 'HISTORY_BINDING')
    original_history = json.loads(raw(roots['stop-pending-before']), object_pairs_hook=unique)
    require(original_history['history_settled'] is False and original_history['binding'] == accepted['binding'],
            'PRESTOP_HISTORY_BINDING')
    for name, entry in original_history['entries'].items():
        if name != 'pending':
            data = base64.b64decode(entry['body'], validate=True)
            require(data == b'family-connect/capture-operation/v1\n' and
                    hashlib.sha256(data).hexdigest() == entry['sha256'], 'PRESTOP_HISTORY_BYTES')
    require({'pending/' + name for name in plan['pending']} <= set(original_history['entries']), 'PRESTOP_HISTORY_COVERAGE')
    ticket = json.loads(raw(Path(plan['root']) / 'handoff-ticket.json'), object_pairs_hook=unique)['ticket']
    remote = snapshot['boundary']['mailbox']
    require(remote['unit_verified'] is True and remote['restart_guard_verified'] is True and
            remote['controller_uid'] == os.geteuid() and
            remote['observed']['ticket'] == ticket and remote['observed']['fence']['new_link_admission'] == 'CLOSED' and
            remote['observed']['fence']['opening_invalidated'] is True and
            remote['observed']['fence']['in_process_drained'] is True and
            remote['observed']['fence']['accepted_target_work'] == 0, 'MAILBOX_BINDING')
    return dict(result='SUPPORT_COMPONENT_BYTES_VERIFIED_NOT_FLEET_BACKUP', sha256=expected,
                entries=len(entries), bytes=bytes_total, pending=len(pending), history_settled=False,
                pending_before=len(original_history['entries']) - 1, independent_custody=False, recovery_authorized=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.snapshot, args.sha256, args.plan), sort_keys=True))


if __name__ == '__main__':
    main()
