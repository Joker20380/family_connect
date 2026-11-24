"""Read-only OWNER admission bindings; never an all-writer or capture permit."""
import hashlib
import http.client
import json
from pathlib import PurePosixPath
import re
import resource
import signal
import socket
import sys
import time

NAMES = ('fc-control-plane-0-console-1', 'fc-control-plane-0-system_publisher-1')
LIMIT = 1024 * 1024
GATE = 'FC_CONTROL_CAPTURE_GATE'
TOP = 'top?ps_args=-eo%20uid,gid,pid,ppid'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def pairs(entries):
    result = {}
    for name, value in entries:
        require(name not in result, 'DUPLICATE_FIELD')
        result[name] = value
    return result


class DockerRead(http.client.HTTPConnection):
    def __init__(self):
        super().__init__('localhost', timeout=3)

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect('/var/run/docker.sock')


def read(endpoint):
    names = '|'.join(re.escape(name) for name in NAMES)
    require(re.fullmatch(r'/containers/(?:(?:' + names + r')/json|[0-9a-f]{64}/(?:json|' +
                         re.escape(TOP) + r'))', endpoint), 'READ_SCOPE')
    connection = DockerRead()
    try:
        connection.request('GET', endpoint)
        response = connection.getresponse()
        require(response.status == 200, 'DOCKER_READ_FAILED')
        raw = response.read(LIMIT + 1)
        require(len(raw) <= LIMIT, 'READ_BOUNDS')
        return json.loads(raw, object_pairs_hook=pairs)
    finally:
        connection.close()


def absolute(value):
    require(type(value) is str and value.startswith('/') and str(PurePosixPath(value)) == value and
            not value.startswith('//') and '..' not in PurePosixPath(value).parts, 'ABSOLUTE_PATH')
    return PurePosixPath(value)


def binding(item, name):
    require(name in NAMES and item['Name'] == '/' + name, 'CONTAINER_SCOPE')
    require(re.fullmatch('[0-9a-f]{64}', item['Id']) and
            re.fullmatch('sha256:[0-9a-f]{64}', item['Image']), 'CONTAINER_ID')
    config, state, host = item['Config'], item['State'], item['HostConfig']
    require(config['Labels']['com.docker.compose.project'] == 'fc-control-plane-0' and
            config['Labels']['com.docker.compose.service'] == name[len('fc-control-plane-0-'):-2], 'PROJECT_SCOPE')
    require(state['Running'] is True and state['Paused'] is False and state['Restarting'] is False and
            type(state['Pid']) is int and state['Pid'] > 0, 'RUNNING_REQUIRED')
    require(type(state['StartedAt']) is str and re.fullmatch(r'[0-9TZ:.+\-]{20,40}', state['StartedAt']) and
            type(item['RestartCount']) is int and item['RestartCount'] >= 0 and
            type(host['ReadonlyRootfs']) is bool, 'RUNTIME_SHAPE')
    environment = config['Env']
    require(type(environment) is list and len(environment) <= 256 and
            all(type(entry) is str and '=' in entry for entry in environment), 'ENVIRONMENT_SHAPE')
    variables = pairs(entry.split('=', 1) for entry in environment)
    gate = variables.get(GATE)
    require(gate is None or bool(gate), 'EMPTY_GATE')
    if gate is not None:
        absolute(gate)
    require(type(item['Mounts']) is list and len(item['Mounts']) <= 64, 'MOUNT_BOUNDS')
    mounts, destinations, covering = [], set(), []
    for mount in item['Mounts']:
        destination = absolute(mount['Destination'])
        require(str(destination) not in destinations and type(mount['RW']) is bool and
                mount['Type'] in ('volume', 'bind', 'tmpfs'), 'MOUNT_SHAPE')
        destinations.add(str(destination))
        source = mount.get('Source', '')
        require(type(source) is str, 'MOUNT_SOURCE')
        if mount['Type'] != 'tmpfs':
            absolute(source)
        mounts.append(dict(destination_sha256=digest(str(destination)), source_sha256=digest(source),
                           type=mount['Type'], rw=mount['RW']))
        if gate is not None and PurePosixPath(gate).is_relative_to(destination):
            covering.append((len(destination.parts), mount))
    gate_mount = None
    if covering:
        mount = max(covering, key=lambda entry: entry[0])[1]
        gate_mount = dict(type=mount['Type'], rw=mount['RW'], backing_path_sha256=digest(
            str(PurePosixPath(mount.get('Source', '')) / PurePosixPath(gate).relative_to(mount['Destination']))))
    return dict(name=name, id=item['Id'], image=item['Image'], pid=state['Pid'], started_at=state['StartedAt'],
                restart_count=item['RestartCount'], configured_user_sha256=digest(config['User']),
                argv_sha256=digest([config['Entrypoint'], config['Cmd']]), environment_sha256=digest(environment),
                labels_sha256=digest(config['Labels']), mounts=sorted(mounts, key=lambda entry: entry['destination_sha256']),
                host_config_sha256=digest(host), readonly_rootfs=host['ReadonlyRootfs'],
                user_namespace_mode_sha256=digest(host.get('UsernsMode', '')),
                gate_configured=gate is not None, gate_path_sha256=digest(gate) if gate is not None else None,
                gate_mount=gate_mount)


def processes(value, main_pid):
    require(value['Titles'] == ['UID', 'GID', 'PID', 'PPID'], 'PROCESS_COLUMNS')
    rows = value['Processes']
    require(type(rows) is list and 0 < len(rows) <= 128, 'PROCESS_BOUNDS')
    records = []
    for row in rows:
        require(type(row) is list and len(row) == 4 and
                all(type(field) is str and re.fullmatch(r'[0-9]{1,10}', field) for field in row), 'PROCESS_FIELDS')
        uid, gid, pid, parent = map(int, row)
        require(pid > 0, 'PROCESS_PID')
        records.append(dict(uid=uid, gid=gid, pid=pid, parent=parent))
    require(len({row['pid'] for row in records}) == len(records) and
            any(row['pid'] == main_pid for row in records), 'PROCESS_IDENTITY')
    return dict(records=sorted(records, key=lambda row: row['pid']),
                host_uid_gid=sorted({(row['uid'], row['gid']) for row in records}))


def collect():
    started = time.time_ns()
    before = {name: binding(read('/containers/' + name + '/json'), name) for name in NAMES}
    observed = {name: processes(read('/containers/' + item['id'] + '/' + TOP), item['pid'])
                for name, item in before.items()}
    after = {name: binding(read('/containers/' + name + '/json'), name) for name in NAMES}
    require(before == after, 'BINDING_CHANGED')
    reasons = ['LOADED_SOURCE_NOT_ATTESTED', 'GATE_INODES_NOT_ATTESTED', 'USER_NAMESPACE_MAPPING_NOT_ATTESTED',
               'MANUAL_AND_EXTERNAL_WRITERS_NOT_ATTESTED', 'IN_FLIGHT_NOT_ATTESTED']
    if any(not item['gate_configured'] for item in before.values()):
        reasons.append('GATE_NOT_CONFIGURED')
    if any(item['gate_mount'] is None or not item['gate_mount']['rw'] or item['gate_mount']['type'] == 'tmpfs'
           for item in before.values()):
        reasons.append('WRITABLE_NON_TMPFS_GATE_MOUNT_NOT_OBSERVED')
    identities = {identity for item in observed.values() for identity in item['host_uid_gid']}
    if len(identities) != 1:
        reasons.append('DIFFERENT_HOST_PROCESS_IDENTITIES')
    return dict(schema=1, node='OWNER', started_at_ns=started, finished_at_ns=time.time_ns(),
                containers=[dict(binding=before[name], processes=observed[name]) for name in NAMES],
                observation_sha256=digest(before), binding_observations_equal=True, unresolved=reasons,
                all_writers_qualified=False, capture_permitted=False, services_changed=False, commands_executed_in_containers=False)


def main():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    require(signal.getsignal(signal.SIGALRM) == signal.SIG_DFL and
            signal.SIGALRM not in signal.pthread_sigmask(signal.SIG_BLOCK, []) and
            signal.getitimer(signal.ITIMER_REAL) == (0, 0), 'ALARM_NOT_EXCLUSIVE')
    signal.alarm(30)
    try:
        print(json.dumps(collect(), sort_keys=True))
    except (ValueError, KeyError, TypeError, OSError, http.client.HTTPException):
        print('OWNER_ADMISSION_PREFLIGHT_REFUSED', file=sys.stderr)
        raise SystemExit(1) from None
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    main()
