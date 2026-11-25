"""Replace already stopped OWNER containers; never drain, start, stop or restore data."""
import argparse
import copy
import fcntl
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import resource
import stat
import sys
import time
from urllib.parse import quote
import uuid

from scripts import control_ha_owner_activation_plan as plan

require = plan.require
digest = plan.observer.digest
PURPOSE = 'family-connect/stopped-owner-replacement/v1'
ENDPOINT_CONFIG = ('IPAMConfig', 'Links', 'Aliases', 'DriverOpts', 'GwPriority')
ENDPOINT_RUNTIME = ('NetworkID', 'EndpointID', 'Gateway', 'IPAddress', 'IPPrefixLen',
                    'IPv6Gateway', 'GlobalIPv6Address', 'GlobalIPv6PrefixLen', 'MacAddress', 'DNSNames')


def identifier(value):
    require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'CONTAINER_ID')
    return value


def stopped(item):
    state = item['State']
    require(state['Status'] in ('created', 'exited') and state['Running'] is False and
            state['Paused'] is False and state['Restarting'] is False and state['Dead'] is False and
            type(state['Pid']) is int and state['Pid'] == 0 and not item.get('ExecIDs'), 'STOPPED_REQUIRED')


def configuration(item):
    return {field: copy.deepcopy(item[field]) for field in plan.CONFIG_FIELDS}


def endpoints(item):
    networks = item['NetworkSettings']['Networks']
    require(type(networks) is dict and bool(networks), 'NETWORKS_REQUIRED')
    result = {}
    for name, settings in networks.items():
        require(type(name) is str and name and type(settings) is dict and
                set(settings) <= set(ENDPOINT_CONFIG + ENDPOINT_RUNTIME) and
                not settings.get('Links') and
                re.fullmatch('[0-9a-f]{64}', settings['NetworkID']), 'UNREVIEWED_ENDPOINT')
        result[name] = {key: copy.deepcopy(settings[key]) for key in ENDPOINT_CONFIG if key in settings}
    return result


def payload(item):
    host, config = item['HostConfig'], item['Config']
    require(not host.get('AutoRemove') and not host.get('Privileged') and not host.get('VolumesFrom') and
            not host.get('PublishAllPorts') and not host.get('Links') and not host.get('ContainerIDFile') and
            host['ReadonlyRootfs'] is True and not config.get('MacAddress'), 'UNREVIEWED_HOST_CONFIG')
    networks = endpoints(item)
    require(host['NetworkMode'] in networks and host['NetworkMode'] not in ('host', 'none', 'bridge') and
            all(not str(host.get(key, '')).startswith('container:') for key in ('PidMode', 'IpcMode')),
            'UNREVIEWED_NAMESPACE')
    declared = set((host.get('Tmpfs') or {}).keys())
    for bind in host.get('Binds') or []:
        parts = bind.split(':')
        require(len(parts) in (2, 3), 'BIND_SYNTAX')
        declared.add(parts[1])
    for mount in host.get('Mounts') or []:
        require(mount['Type'] in ('bind', 'volume', 'tmpfs') and
                (mount['Type'] == 'tmpfs' or bool(mount.get('Source'))), 'ANONYMOUS_MOUNT')
        declared.add(mount['Target'])
    require(set(config.get('Volumes') or {}) <= declared and
            all(mount['Destination'] in declared for mount in item['Mounts']), 'UNBOUND_MOUNT')
    require('HostConfig' not in config and 'NetworkingConfig' not in config, 'CONFIG_FIELDS')
    for name, settings in networks.items():
        settings['NetworkID'] = item['NetworkSettings']['Networks'][name]['NetworkID']
    return dict(copy.deepcopy(config), HostConfig=copy.deepcopy(host),
                NetworkingConfig={'EndpointsConfig': networks})


def equivalent(actual, expected):
    observed_host = copy.deepcopy(actual['HostConfig'])
    expected_host = copy.deepcopy(expected['HostConfig'])
    if expected_host.get('OomKillDisable') is None and observed_host.get('OomKillDisable') is False:
        observed_host['OomKillDisable'] = expected_host.get('OomKillDisable')
    require(actual['Image'] == expected['Image'] and actual['Config'] == expected['Config'] and
            observed_host == expected_host, 'EFFECTIVE_CONFIG_CHANGED')
    require(sorted(actual['Mounts'], key=lambda mount: mount['Destination']) ==
            sorted(expected['Mounts'], key=lambda mount: mount['Destination']), 'EFFECTIVE_MOUNTS_CHANGED')
    require(endpoints(actual) == endpoints(expected) and
            {name: value['NetworkID'] for name, value in actual['NetworkSettings']['Networks'].items()} ==
            {name: value['NetworkID'] for name, value in expected['NetworkSettings']['Networks'].items()},
            'EFFECTIVE_NETWORK_CONFIG_CHANGED')


class Docker:
    def request(self, method, path, body=None, *, missing=False):
        connection = plan.observer.DockerRead()
        connection.timeout = 10
        try:
            raw = None if body is None else json.dumps(body, allow_nan=False).encode()
            connection.request(method, '/v1.52' + path, body=raw, headers={'Content-Type': 'application/json'})
            response = connection.getresponse()
            data = response.read(plan.LIMIT + 1)
            require(len(data) <= plan.LIMIT, 'DOCKER_RESPONSE_BOUNDS')
            if response.status == 404 and missing:
                return None
            require(response.status in (200, 201, 204), 'DOCKER_REQUEST_FAILED')
            return json.loads(data, object_pairs_hook=plan.observer.pairs) if data else None
        finally:
            connection.close()

    def inspect(self, reference):
        return self.request('GET', '/containers/' + quote(reference, safe='') + '/json', missing=True)

    def create(self, name, config):
        self.request('POST', '/containers/create?name=' + quote(name, safe=''), config)

    def rename(self, container, name):
        self.request('POST', '/containers/' + identifier(container) + '/rename?name=' + quote(name, safe=''))

    def remove(self, container):
        self.request('DELETE', '/containers/' + identifier(container) + '?force=false&v=false')


def record(root, name, value):
    plan.write_private(root / (name + '.json'), value)


def load(root, name):
    path = plan.private_path(root / (name + '.json'))
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_uid == os.geteuid() and before.st_nlink == 1 and
                stat.S_IMODE(before.st_mode) == 0o600 and 0 < before.st_size <= plan.LIMIT, 'PRIVATE_RECORD')
        raw = stream.read(plan.LIMIT + 1)
        after = os.fstat(stream.fileno())
        require((before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                (after.st_size, after.st_mtime_ns, after.st_ctime_ns) and len(raw) == before.st_size,
                'RECORD_CHANGED')
    return plan.read_private(path, hashlib.sha256(raw).hexdigest())


def scope(item, role, *, laboratory=False):
    identifier(item['Id'])
    if laboratory:
        token = item['Config']['Labels'].get('family-connect.ha-owner-replacement')
        require(type(token) is str and re.fullmatch('[0-9a-f]{32}', token) and
                item['Name'] == '/fc-ha-owner-replacement-' + token + '-' + role, 'LAB_SCOPE')
    else:
        require(role in plan.upgrade.ROLES and item['Name'] == '/fc-control-plane-0-' + role + '-1' and
                item['Image'] == plan.upgrade.ROLES[role], 'OWNER_SCOPE')


def prepare(root, original, proposed, role, *, laboratory=False, locked=False):
    root = Path(root)
    plan.private_path(root / 'manifest.json')
    require(set(path.name for path in root.iterdir()) == ({'lock'} if locked else set()), 'JOURNAL_NOT_EMPTY')
    scope(original, role, laboratory=laboratory)
    stopped(original)
    before, after = configuration(original), configuration(proposed)
    if not laboratory:
        require(after == plan.proposed_config(before, after['Image'], role), 'UNREVIEWED_CONFIG_DELTA')
    payload(before)
    payload(after)
    transaction = uuid.uuid4().hex
    name = original['Name'][1:]
    manifest = dict(purpose=PURPOSE, role=role, transaction=transaction, created_ns=time.time_ns(),
                    original_id=original['Id'], name=name, staging=name + '-ha-stage-' + transaction,
                    retained=name + '-ha-retained-' + transaction, current=before, proposed=after)
    record(root, 'manifest', manifest)
    return manifest


class Replacement:
    def __init__(self, root, docker, manifest_sha256):
        self.root, self.docker = Path(root), docker
        self.manifest = plan.read_private(self.root / 'manifest.json', manifest_sha256)
        self.manifest_sha256 = manifest_sha256
        require(self.manifest['purpose'] == PURPOSE, 'JOURNAL_PURPOSE')

    def original(self):
        item = self.docker.inspect(self.manifest['original_id'])
        require(item is not None, 'ORIGINAL_MISSING')
        stopped(item)
        equivalent(item, self.manifest['current'])
        require(item['Name'][1:] in (self.manifest['name'], self.manifest['retained']), 'ORIGINAL_RENAMED_EXTERNALLY')
        return item

    def candidate(self):
        pin = self.root / 'candidate.json'
        if pin.exists():
            candidate_id = identifier(load(self.root, 'candidate')['id'])
            item = self.docker.inspect(candidate_id)
        else:
            item = self.docker.inspect(self.manifest['staging'])
        if item is not None:
            stopped(item)
            equivalent(item, self.manifest['proposed'])
            require(item['Id'] != self.manifest['original_id'] and item['Name'][1:] in
                    (self.manifest['name'], self.manifest['staging']), 'CANDIDATE_BINDING')
            if not pin.exists():
                record(self.root, 'candidate', {'id': identifier(item['Id'])})
        return item

    def mutation(self, name, action, observed):
        if (self.root / (name + '-intent.json')).exists():
            require(observed(), 'UNKNOWN_MUTATION_OUTCOME')
        else:
            record(self.root, name + '-intent', {'at_ns': time.time_ns()})
            try:
                action()
            except (OSError, ValueError, http.client.HTTPException):
                require(observed(), 'UNKNOWN_MUTATION_OUTCOME')
            require(observed(), 'MUTATION_NOT_CONFIRMED')
        if not (self.root / (name + '-done.json')).exists():
            record(self.root, name + '-done', {'at_ns': time.time_ns()})

    def validate_sources(self):
        for mount in self.manifest['proposed']['Mounts']:
            if mount['Type'] == 'bind':
                require(os.path.exists(mount['Source']), 'BIND_SOURCE_MISSING')
        for name, settings in self.manifest['proposed']['NetworkSettings']['Networks'].items():
            network = self.docker.request('GET', '/networks/' + identifier(settings['NetworkID']))
            require(network['Name'] == name and network['Driver'] == 'bridge' and
                    network['Scope'] == 'local' and not network.get('Ingress'), 'NETWORK_CHANGED')
        for expected in (self.manifest['current'], self.manifest['proposed']):
            image = self.docker.request('GET', '/images/' + quote(expected['Image'], safe='') + '/json')
            require(image['Id'] == expected['Image'], 'IMAGE_MISSING')

    def stage(self):
        require(not (self.root / 'revert-intent.json').exists(), 'REVERT_ALREADY_SELECTED')
        original = self.original()
        self.validate_sources()
        candidate = self.candidate()
        if candidate is None:
            require(not (self.root / 'candidate.json').exists(), 'CANDIDATE_REMOVED_EXTERNALLY')
            require(original['Name'] == '/' + self.manifest['name'], 'INCOMPLETE_WITHOUT_CANDIDATE')
            self.mutation('create', lambda: self.docker.create(self.manifest['staging'], payload(self.manifest['proposed'])),
                          lambda: self.candidate() is not None)
            candidate = self.candidate()
        self.original()
        self.mutation('retain', lambda: self.docker.rename(original['Id'], self.manifest['retained']),
                      lambda: self.original()['Name'] == '/' + self.manifest['retained'])
        self.candidate()
        self.mutation('promote', lambda: self.docker.rename(candidate['Id'], self.manifest['name']),
                      lambda: self.candidate()['Name'] == '/' + self.manifest['name'])
        return self.status()

    def revert(self):
        original, candidate = self.original(), self.candidate()
        if candidate is None and (self.root / 'create-intent.json').exists() and not (self.root / 'candidate.json').exists():
            raise ValueError('UNKNOWN_CREATE_OUTCOME')
        observed = {
            'create': candidate is not None,
            'retain': original['Name'] == '/' + self.manifest['retained'],
            'promote': candidate is not None and candidate['Name'] == '/' + self.manifest['name'],
        }
        for name, applied in observed.items():
            if (self.root / (name + '-intent.json')).exists() and not (self.root / (name + '-done.json')).exists():
                require(applied, 'UNKNOWN_FORWARD_MUTATION')
                record(self.root, name + '-done', {'at_ns': time.time_ns()})
        if not (self.root / 'revert-intent.json').exists():
            record(self.root, 'revert-intent', {'at_ns': time.time_ns()})
        if candidate is not None:
            candidate_id = candidate['Id']
            self.mutation('remove', lambda: self.docker.remove(candidate_id),
                          lambda: self.docker.inspect(candidate_id) is None)
        else:
            require(not (self.root / 'candidate.json').exists() or (self.root / 'remove-intent.json').exists(),
                    'CANDIDATE_REMOVED_EXTERNALLY')
        if original['Name'] != '/' + self.manifest['name']:
            self.mutation('restore-name', lambda: self.docker.rename(original['Id'], self.manifest['name']),
                          lambda: self.original()['Name'] == '/' + self.manifest['name'])
        require(self.docker.inspect(self.manifest['name'])['Id'] == original['Id'], 'RESTORE_NOT_CONFIRMED')
        if not (self.root / 'revert-done.json').exists():
            record(self.root, 'revert-done', {'at_ns': time.time_ns()})
        return self.status()

    def status(self):
        original, candidate = self.original(), self.candidate()
        return dict(purpose=PURPOSE, original_id=original['Id'], candidate_id=None if candidate is None else candidate['Id'],
                    journal_sha256=self.manifest_sha256,
                    original_has_name=original['Name'] == '/' + self.manifest['name'],
                    candidate_has_name=candidate is not None and candidate['Name'] == '/' + self.manifest['name'],
                    original_config_sha256=digest(self.manifest['current']),
                    proposed_config_sha256=digest(self.manifest['proposed']),
                    data_restored=False, service_started=False, work_settlement_proven=False,
                    runtime_qualified=False, capture_permitted=False)


def main():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('stage', 'revert', 'status'))
    parser.add_argument('--journal', required=True, type=Path)
    parser.add_argument('--journal-sha256')
    parser.add_argument('--input', type=Path)
    parser.add_argument('--input-sha256')
    parser.add_argument('--role', choices=tuple(plan.upgrade.ROLES))
    args = parser.parse_args()
    try:
        plan.private_path(args.journal / 'manifest.json')
        descriptor = os.open(args.journal / 'lock', os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        with os.fdopen(descriptor, 'wb') as lock:
            info = os.fstat(lock.fileno())
            require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid() and info.st_nlink == 1 and
                    stat.S_IMODE(info.st_mode) == 0o600, 'JOURNAL_LOCK')
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            docker = Docker()
            if not (args.journal / 'manifest.json').exists():
                require(args.action == 'stage' and args.input is not None and args.role is not None, 'INITIAL_INPUT_REQUIRED')
                inputs = plan.read_private(args.input, args.input_sha256)
                require(args.journal_sha256 is None, 'UNEXPECTED_JOURNAL_PIN')
                proposal = plan.proposal(inputs)
                original = docker.inspect(inputs['containers'][args.role]['Id'])
                require(original is not None, 'ORIGINAL_MISSING')
                equivalent(original, proposal['roles'][args.role]['current'])
                after = proposal['roles'][args.role]['proposed']
                prepare(args.journal, original, after, args.role, locked=True)
                journal_pin = hashlib.sha256((args.journal / 'manifest.json').read_bytes()).hexdigest()
            else:
                require(args.input is None and args.input_sha256 is None and args.role is None, 'USE_RETAINED_JOURNAL')
                journal_pin = args.journal_sha256
            print(json.dumps(getattr(Replacement(args.journal, docker, journal_pin), args.action)(), sort_keys=True))
    except (OSError, ValueError, TypeError, KeyError, RecursionError, http.client.HTTPException):
        print('OWNER_REPLACEMENT_REFUSED; retain journal and reconcile before retry', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
