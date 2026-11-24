"""Offline private OWNER configuration proposal; no Docker dispatch or activation permit."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import stat
import sys

from scripts import control_ha_owner_upgrade as upgrade

observer = upgrade.source.preflight
require = observer.require
PURPOSE = 'family-connect/owner-activation-config-proposal/v1/not-executable'
LIMIT = 4 * 1024 * 1024
DESTINATION = '/run/family-connect-capture'
GATES = {
    'console': dict(source='/var/lib/family-connect/capture/owner-console', uid=10001, gid=10001),
    'system_publisher': dict(source='/var/lib/family-connect/capture/owner-publisher', uid=1000, gid=1000),
}
CONFIG_FIELDS = ('Image', 'Config', 'HostConfig', 'Mounts', 'NetworkSettings')
CHANGES = ('Image', 'Config.Image', 'Config.Env', 'HostConfig.Binds', 'Mounts')


def overlaps(first, second):
    first, second = observer.absolute(first), observer.absolute(second)
    return first.is_relative_to(second) or second.is_relative_to(first)


def proposed_config(current, candidate, role):
    gate = GATES[role]
    require(type(current['Config']['Image']) is str and bool(current['Config']['Image']), 'CONFIG_IMAGE')
    require(type(current['NetworkSettings']) is dict and
            type(current['NetworkSettings'].get('Networks')) is dict and
            bool(current['NetworkSettings']['Networks']), 'NETWORK_BINDINGS')
    host = current['HostConfig']
    binds = host.get('Binds')
    require('Binds' in host and (binds is None or type(binds) is list) and
            all(type(item) is str for item in binds or []), 'HOST_BINDS')
    require(not host.get('VolumesFrom'), 'INHERITED_MOUNTS_UNREVIEWED')
    for mount in current['Mounts']:
        require(not overlaps(mount['Destination'], DESTINATION), 'GATE_DESTINATION_OVERLAP')
        if mount.get('Source'):
            require(not overlaps(mount['Source'], gate['source']), 'GATE_SOURCE_OVERLAP')
    for bind in binds or []:
        parts = bind.split(':')
        require(len(parts) in (2, 3), 'BIND_SYNTAX')
        require(not overlaps(parts[1], DESTINATION), 'BIND_OVERLAP')
        if parts[0].startswith('/'):
            require(not overlaps(parts[0], gate['source']), 'BIND_SOURCE_OVERLAP')
        else:
            require(re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]*', parts[0]) and
                    any(mount['Type'] == 'volume' and mount.get('Name') == parts[0] and
                        mount['Destination'] == parts[1] for mount in current['Mounts']), 'NAMED_VOLUME_BINDING')
    for mount in host.get('Mounts') or []:
        require(not overlaps(mount['Target'], DESTINATION), 'STRUCTURED_MOUNT_OVERLAP')
        if mount.get('Source') and mount['Type'] == 'bind':
            require(not overlaps(mount['Source'], gate['source']), 'STRUCTURED_SOURCE_OVERLAP')
    for destination in host.get('Tmpfs') or {}:
        require(not overlaps(destination, DESTINATION), 'TMPFS_OVERLAP')
    result = copy.deepcopy(current)
    result['Image'] = result['Config']['Image'] = candidate
    result['Config']['Env'].append(observer.GATE + '=' + DESTINATION)
    result['HostConfig']['Binds'] = list(binds or []) + [gate['source'] + ':' + DESTINATION + ':rw,rprivate']
    result['Mounts'].append(dict(Type='bind', Source=gate['source'], Destination=DESTINATION,
                                 Mode='rw,rprivate', RW=True, Propagation='rprivate'))
    return result


def proposal(inputs):
    require(type(inputs) is dict and set(inputs) == {'observed_at_ns', 'containers', 'processes',
                                                  'images', 'candidates'}, 'INPUT_FIELDS')
    require(type(inputs['observed_at_ns']) is int and inputs['observed_at_ns'] > 0, 'OBSERVATION_TIME')
    for field in ('containers', 'processes', 'candidates'):
        require(type(inputs[field]) is dict and set(inputs[field]) == set(upgrade.ROLES), 'ROLE_COVERAGE')
    candidates = inputs['candidates']
    require(all(type(image) is str and re.fullmatch(r'sha256:[0-9a-f]{64}', image)
                for image in candidates.values()) and len(set(candidates.values())) == 2 and
            not set(candidates.values()) & set(upgrade.ROLES.values()), 'CANDIDATE_IDS')
    require(type(inputs['images']) is dict and
            set(inputs['images']) == set(upgrade.ROLES.values()) | set(candidates.values()), 'IMAGE_COVERAGE')
    for image_id, image in inputs['images'].items():
        require(image['Id'] == image_id, 'IMAGE_ID_BINDING')
    roles = {}
    for role, baseline_image in upgrade.ROLES.items():
        item = inputs['containers'][role]
        observed = upgrade.workload(item, role)
        identity = observer.processes(inputs['processes'][role], observed['pid'])
        gate = GATES[role]
        require(identity['host_uid_gid'] == [(gate['uid'], gate['gid'])], 'HOST_IDENTITY_CHANGED')
        upgrade.verify(inputs['images'][baseline_image], inputs['images'][candidates[role]])
        current = {field: copy.deepcopy(item[field]) for field in CONFIG_FIELDS}
        proposed = proposed_config(current, candidates[role], role)
        roles[role] = dict(observed=observed, current=current, proposed=proposed,
                          gate=dict(gate, destination=DESTINATION, directory_mode='0700', lock_mode='0600'),
                          rollback_config_sha256=observer.digest(current), changed_fields=list(CHANGES),
                          image_config_sha256=observer.digest(inputs['images'][baseline_image]['Config']),
                          candidate_layers_sha256=observer.digest(inputs['images'][candidates[role]]['RootFS']))
    for value in roles.values():
        for mount in value['current']['Mounts']:
            if mount.get('Source'):
                require(all(not overlaps(mount['Source'], gate['source']) for gate in GATES.values()),
                        'OTHER_ROLE_GATE_SOURCE_OVERLAP')
    return dict(purpose=PURPOSE, observed_at_ns=inputs['observed_at_ns'],
                input_sha256=observer.digest(inputs), roles=roles, executable=False,
                independent_approval=False, gate_inodes_attested=False, existing_work_settled=False,
                runtime_qualified=False, capture_permitted=False, deployed=False)


def validate(plan, inputs):
    expected = proposal(inputs)
    require(observer.digest(plan) == observer.digest(expected), 'UNREVIEWED_CONFIG_DELTA')
    return dict(purpose=PURPOSE, proposal_sha256=observer.digest(plan), input_sha256=plan['input_sha256'],
                roles={role: dict(baseline_image=value['current']['Image'],
                                  candidate_image=value['proposed']['Image'],
                                  current_sha256=observer.digest(value['current']),
                                  proposed_sha256=observer.digest(value['proposed']),
                                  changed_fields=value['changed_fields'], uid=value['gate']['uid'],
                                  gid=value['gate']['gid']) for role, value in plan['roles'].items()},
                executable=False, independent_approval=False, runtime_qualified=False,
                capture_permitted=False, deployed=False)


def private_path(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and
            all(not parent.is_symlink() for parent in (path, *path.parents)), 'PRIVATE_PATH')
    info = path.parent.stat()
    require(info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700, 'PRIVATE_PARENT')
    return path


def read_private(path, expected):
    require(type(expected) is str and re.fullmatch('[0-9a-f]{64}', expected), 'INPUT_PIN')
    path = private_path(path)
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_uid == os.geteuid() and before.st_nlink == 1 and
                stat.S_IMODE(before.st_mode) == 0o600 and 0 < before.st_size <= LIMIT, 'PRIVATE_INPUT')
        raw = stream.read(LIMIT + 1)
        after = os.fstat(stream.fileno())
        fields = ('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_gid', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
        require(all(getattr(before, field) == getattr(after, field) for field in fields) and len(raw) == before.st_size and
                hashlib.sha256(raw).hexdigest() == expected, 'INPUT_CHANGED')
    return json.loads(raw, object_pairs_hook=observer.pairs,
                      parse_constant=lambda value: require(False, 'NONFINITE_JSON'))


def write_private(path, plan):
    path = private_path(path)
    raw = json.dumps(plan, sort_keys=True, indent=2, allow_nan=False).encode() + b'\n'
    require(len(raw) <= LIMIT, 'OUTPUT_BOUNDS')
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--input-sha256', required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--output', type=Path)
    action.add_argument('--verify', type=Path)
    parser.add_argument('--proposal-sha256')
    args = parser.parse_args()
    try:
        inputs = read_private(args.input, args.input_sha256)
        if args.verify:
            plan = read_private(args.verify, args.proposal_sha256)
        else:
            require(args.proposal_sha256 is None, 'UNEXPECTED_PROPOSAL_PIN')
            plan = proposal(inputs)
        receipt = validate(plan, inputs)
        if args.output:
            write_private(args.output, plan)
        print(json.dumps(receipt, sort_keys=True))
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        print('OWNER_ACTIVATION_PLAN_REFUSED', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
