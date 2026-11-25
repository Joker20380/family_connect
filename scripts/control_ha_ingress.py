"""Expiring console TCP admission in its own network namespace, never the host firewall."""
import argparse
import hashlib
import http.client
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import time
import uuid

from scripts.control_ha_owner_replacement import Docker, configuration, equivalent, record
from scripts.control_ha_owner_upgrade import docker, require, workload

LABEL = 'family-connect.ha-ingress-helper'
PREFIX = 'fc_ha_ingress_'
ENTRYPOINT = ['/usr/sbin/nft', '-j', '-n', '-f', '-']
TOOL_ENV = ['PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin']


def build_tool():
    executable = Path('/usr/sbin/nft')
    dependencies = subprocess.run(['ldd', str(executable)], capture_output=True, text=True, check=True).stdout
    require('not found' not in dependencies, 'MISSING_NFT_DEPENDENCY')
    paths = {str(executable), *re.findall(r'(/[^\s()]+)', dependencies)}
    require('/lib64/ld-linux-x86-64.so.2' in paths and 2 <= len(paths) <= 24, 'NFT_PLATFORM')
    payload, manifest = {}, {}
    for name in sorted(paths):
        require(name == str(executable) or name.startswith(('/usr/lib/x86_64-linux-gnu/', '/lib64/')), 'NFT_LIBRARY_PATH')
        source = Path(name).resolve(strict=True)
        info = source.stat()
        raw = source.read_bytes()
        require(info.st_uid == 0 and not info.st_mode & 0o022 and raw.startswith(b'\x7fELF') and
                len(raw) <= 8 * 1024 * 1024, 'NFT_LIBRARY')
        payload['rootfs' + name] = raw
        manifest[name] = hashlib.sha256(raw).hexdigest()
    payload['Dockerfile'] = ('FROM scratch\nCOPY rootfs/ /\nENTRYPOINT ' + json.dumps(ENTRYPOINT) + '\n').encode()
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for name, raw in sorted(payload.items()):
            member = tarfile.TarInfo(name)
            member.mode, member.size = (0o644 if name == 'Dockerfile' else 0o755), len(raw)
            archive.addfile(member, io.BytesIO(raw))
    context = output.getvalue()
    require(len(context) <= 32 * 1024 * 1024, 'NFT_CONTEXT_SIZE')
    image = docker('build', '--pull=false', '--network=none', '--quiet', '-', data=context).decode().strip()
    require(re.fullmatch('sha256:[0-9a-f]{64}', image), 'NFT_IMAGE')
    return dict(image=image, files=manifest, context_sha256=hashlib.sha256(context).hexdigest())


def table_name(token):
    require(type(token) is str and re.fullmatch('[0-9a-f]{32}', token), 'INGRESS_TOKEN')
    return PREFIX + token


def expression():
    return [dict(match=dict(op='==', left={'payload': {'protocol': 'tcp', 'field': 'dport'}}, right='@ports')),
            dict(match=dict(op='==', left={'&': [{'payload': {'protocol': 'tcp', 'field': 'flags'}}, {'|': [2, 16]}]}, right=2)),
            {'counter': None}, {'reject': {'type': 'tcp reset'}}]


def create_request(token, seconds):
    name = table_name(token)
    require(type(seconds) is int and 1 <= seconds <= 5, 'INGRESS_DEADLINE')
    return {'nftables': [
        {'create': {'table': dict(family='inet', name=name)}},
        {'add': {'chain': dict(family='inet', table=name, name='input', type='filter', hook='input', prio=-50, policy='accept')}},
        {'add': {'set': dict(family='inet', table=name, name='ports', type='inet_service', flags=['timeout'],
                            timeout=seconds, elem=[{'elem': {'val': 8000, 'timeout': seconds}}])}},
        {'add': {'rule': dict(family='inet', table=name, chain='input', comment=token, expr=expression())}}]}


def inspect_table(value, token):
    name = table_name(token)
    require(set(value) == {'nftables'} and type(value['nftables']) is list and
            all(type(row) is dict and len(row) == 1 for row in value['nftables']), 'INGRESS_TABLE_SHAPE')
    rows = [row for row in value['nftables'] if 'metainfo' not in row]
    require(len(rows) == 4 and all(len(row) == 1 for row in rows), 'INGRESS_TABLE_SHAPE')
    objects = {next(iter(row)): next(iter(row.values())) for row in rows}
    require(set(objects) == {'table', 'chain', 'set', 'rule'}, 'INGRESS_OBJECTS')
    table, chain, ports, rule = (objects[key] for key in ('table', 'chain', 'set', 'rule'))
    for item, allowed in ((table, {'family', 'name', 'handle'}),
                          (chain, {'family', 'table', 'name', 'type', 'hook', 'prio', 'policy', 'handle'}),
                          (ports, {'family', 'table', 'name', 'type', 'flags', 'timeout', 'elem', 'handle'}),
                          (rule, {'family', 'table', 'chain', 'comment', 'expr', 'handle'})):
        require(set(item) <= allowed, 'INGRESS_UNEXPECTED_FIELD')
    require(table['family'] == 'inet' and table['name'] == name and
            all(item['family'] == 'inet' and item['table'] == name for item in (chain, ports, rule)), 'INGRESS_TABLE_BINDING')
    require(chain['name'] == 'input' and chain['type'] == 'filter' and chain['hook'] == 'input' and
            chain['prio'] == -50 and chain['policy'] == 'accept', 'INGRESS_CHAIN')
    require(ports['name'] == 'ports' and ports['type'] == 'inet_service' and ports['flags'] == ['timeout'] and
            type(ports['timeout']) is int and 1 <= ports['timeout'] <= 5, 'INGRESS_SET')
    observed = json.loads(json.dumps(rule['expr']))
    require(len(observed) == 4 and set(observed[2]) == {'counter'} and
            type(observed[2].get('counter')) is dict, 'INGRESS_COUNTER')
    counter = observed[2]['counter']
    require(set(counter) == {'packets', 'bytes'} and all(type(amount) is int and amount >= 0 for amount in counter.values()),
            'INGRESS_COUNTER_VALUES')
    observed[2] = {'counter': None}
    require(rule['chain'] == 'input' and rule['comment'] == token and observed == expression(), 'INGRESS_RULE')
    elements = ports.get('elem', [])
    require(type(elements) is list and len(elements) <= 1, 'INGRESS_ELEMENTS')
    remaining = 0
    if elements:
        element = elements[0]['elem']
        require(set(elements[0]) == {'elem'} and set(element) <= {'val', 'timeout', 'expires'} and
                element['val'] == 8000 and element.get('timeout', ports['timeout']) == ports['timeout'] and
                type(element['expires']) in (int, float) and 0 <= element['expires'] <= ports['timeout'], 'INGRESS_ELEMENT')
        remaining = element['expires']
    return dict(remaining_seconds=remaining, lease_seconds=ports['timeout'], rejected_packets=counter['packets'])


def request_scope(request):
    rows = request['nftables']
    require(set(request) == {'nftables'} and type(rows) is list and len(rows) in (1, 4), 'NFT_REQUEST_SCOPE')
    command = rows[0]
    require(len(command) == 1 and next(iter(command)) in ('create', 'list', 'delete'), 'NFT_REQUEST_SCOPE')
    action = next(iter(command))
    target = command[action]['table']
    token = target['name'].removeprefix(PREFIX)
    require(target == dict(family='inet', name=table_name(token)), 'NFT_REQUEST_SCOPE')
    expected = create_request(token, rows[2]['add']['set']['timeout']) if action == 'create' else {'nftables': [command]}
    require(request == expected and set(command[action]) == {'table'}, 'NFT_REQUEST_SCOPE')


class Transport:
    def __init__(self, target, image, root):
        require(re.fullmatch('[0-9a-f]{64}', target) and re.fullmatch('sha256:[0-9a-f]{64}', image), 'INGRESS_IDS')
        self.target, self.image, self.root = target, image, Path(root)
        require(self.root.is_absolute() and self.root.is_dir() and self.root.stat().st_uid == os.geteuid() and
                self.root.stat().st_mode & 0o777 == 0o700 and
                not any(path.is_symlink() for path in (self.root, *self.root.parents)), 'PRIVATE_JOURNAL')
        self.api, self.helpers, self.unconfirmed = Docker(), [], False
        image_info = self.api.request('GET', '/images/' + image + '/json')
        require(image_info['Id'] == image and image_info['Config']['Entrypoint'] == ENTRYPOINT and
                image_info['Config'].get('Env') == TOOL_ENV and
                not any(image_info['Config'].get(key) for key in ('Volumes', 'Cmd', 'User', 'WorkingDir')),
                'INGRESS_TOOL_IMAGE')
        self.before = self.api.inspect(target)
        require(self.before['State']['Running'] and not self.before['State']['Paused'] and
                not self.before['State']['Restarting'] and self.before['HostConfig']['NetworkMode'] not in ('host', 'none') and
                not self.before['HostConfig']['NetworkMode'].startswith('container:') and
                bool(self.before['NetworkSettings']['SandboxID']), 'ISOLATED_TARGET_REQUIRED')
        self.exclusive()

    def exclusive(self):
        for entry in self.api.request('GET', '/containers/json'):
            if entry['Id'] == self.target or entry['Id'] in self.helpers:
                continue
            item = self.api.inspect(entry['Id'])
            require(item is not None, 'NETWORK_MEMBER_UNKNOWN')
            require(item['NetworkSettings']['SandboxID'] != self.before['NetworkSettings']['SandboxID'],
                    'SHARED_TARGET_NETWORK')
            mode = item['HostConfig']['NetworkMode']
            if mode.startswith('container:'):
                parent = self.api.inspect(mode.removeprefix('container:'))
                require(parent is not None and parent['Id'] != self.target, 'SHARED_TARGET_NETWORK')

    def runtime(self):
        item = self.api.inspect(self.target)
        require(item['State']['Running'] and not item['State']['Paused'] and not item['State']['Restarting'] and
                item['State']['Pid'] == self.before['State']['Pid'] and
                item['State']['StartedAt'] == self.before['State']['StartedAt'] and
                item['RestartCount'] == self.before['RestartCount'] and
                item['NetworkSettings']['SandboxID'] == self.before['NetworkSettings']['SandboxID'], 'INGRESS_RUNTIME_CHANGED')

    def finished(self):
        for identifier in self.helpers:
            item = self.api.inspect(identifier)
            require(item is not None and item['Config']['Labels'].get(LABEL) == self.target and
                    not item['State']['Running'] and item['State']['Status'] == 'exited', 'HELPER_RESULT_UNKNOWN')

    def run(self, request):
        request_scope(request)
        require(not self.unconfirmed, 'INGRESS_OPERATION_UNCONFIRMED')
        self.finished()
        self.runtime()
        self.exclusive()
        name = 'fc-ha-ingress-' + uuid.uuid4().hex
        record(self.root, 'intent-' + name, dict(name=name, target=self.target, image=self.image,
                                               request_sha256=hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()))
        self.unconfirmed = True
        identifier = docker('create', '--name', name, '--pull=never', '--interactive', '--network', 'container:' + self.target,
            '--label', LABEL + '=' + self.target, '--read-only', '--cap-drop', 'ALL', '--cap-add', 'NET_ADMIN',
            '--security-opt', 'no-new-privileges', '--pids-limit', '8', '--memory', '64m', '--restart', 'no', self.image).decode().strip()
        require(re.fullmatch('[0-9a-f]{64}', identifier), 'HELPER_ID')
        self.helpers.append(identifier)
        record(self.root, 'helper-' + identifier, dict(id=identifier, name=name, target=self.target, image=self.image,
                                                     request_sha256=hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()))
        helper = self.api.inspect(identifier)
        host = helper['HostConfig']
        require(host['NetworkMode'] == 'container:' + self.target and host['ReadonlyRootfs'] and
                not host['Privileged'] and not host['PidMode'] and host['CapDrop'] == ['ALL'] and
                host['CapAdd'] == ['CAP_NET_ADMIN'] and not helper['Mounts'] and helper['Image'] == self.image and
                helper['Config']['Entrypoint'] == ENTRYPOINT and
                helper['Config'].get('Env') == TOOL_ENV and
                not any(helper['Config'].get(key) for key in ('Cmd', 'User', 'WorkingDir', 'Tty')) and
                host['RestartPolicy']['Name'] == 'no' and host['SecurityOpt'] == ['no-new-privileges'] and
                host['Memory'] == 64 * 1024 * 1024 and host['PidsLimit'] == 8 and
                not host.get('Devices') and not host.get('DeviceRequests'), 'HELPER_SCOPE')
        result = docker('start', '--attach', '--interactive', identifier, data=json.dumps(request).encode(), timeout=10)
        self.finished()
        item = self.api.inspect(identifier)
        require(item['State']['ExitCode'] == 0 and not item['State']['OOMKilled'], 'NFT_REQUEST_FAILED')
        self.runtime()
        value = json.loads(result) if result.strip() else {}
        record(self.root, 'result-' + identifier, value)
        self.unconfirmed = False
        return value

    def cleanup_helpers(self):
        for identifier in self.helpers:
            item = self.api.inspect(identifier)
            require(item is not None and item['Config']['Labels'].get(LABEL) == self.target and
                    not item['State']['Running'] and item['State']['Status'] in ('created', 'exited'), 'HELPER_CLEANUP_UNKNOWN')
            self.api.remove(identifier)
        self.helpers.clear()


class Lease:
    def __init__(self, transport, *, seconds=5, token=None):
        self.transport, self.seconds = transport, seconds
        self.token = token or uuid.uuid4().hex
        self.name = table_name(self.token)
        self.request = create_request(self.token, seconds)
        self.attempted, self.active = False, False

    def observe(self):
        return inspect_table(self.transport.run({'nftables': [{'list': {'table': dict(family='inet', name=self.name)}}]}), self.token)

    def __enter__(self):
        require(not self.attempted, 'NO_INGRESS_RETRY')
        record(self.transport.root, self.name, dict(token=self.token, target=self.transport.target, seconds=self.seconds,
                                                  observed_at_ns=time.time_ns()))
        self.deadline = time.monotonic() + self.seconds
        self.attempted = True
        self.transport.run(self.request)
        self.active = True
        try:
            self.check()
        except BaseException:
            if not self.transport.unconfirmed:
                self.release()
            raise
        return self

    def check(self):
        require(self.active and time.monotonic() < self.deadline, 'INGRESS_LEASE_EXPIRED')
        observed = self.observe()
        require(observed['lease_seconds'] == self.seconds and observed['remaining_seconds'] > 0 and
                time.monotonic() < self.deadline, 'INGRESS_LEASE_EXPIRED')
        return observed

    def release(self):
        require(not self.transport.unconfirmed, 'INGRESS_OPERATION_UNCONFIRMED')
        self.transport.finished()
        self.observe()
        self.transport.run({'nftables': [{'delete': {'table': dict(family='inet', name=self.name)}}]})
        self.active = False
        self.transport.cleanup_helpers()

    def __exit__(self, *_):
        self.release()


def health_status():
    client = http.client.HTTPConnection('127.0.0.1', 8765, timeout=1)
    try:
        client.request('GET', '/health/', headers={'Connection': 'close'})
        response = client.getresponse()
        require(len(response.read(4097)) <= 4096, 'HEALTH_RESPONSE_SIZE')
        return response.status
    except (OSError, http.client.HTTPException):
        return None
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journal', type=Path, required=True)
    parser.add_argument('--image', required=True)
    args = parser.parse_args()
    require(args.journal.is_absolute() and args.journal.is_dir() and not any(args.journal.iterdir()) and
            not any(path.is_symlink() for path in (args.journal, *args.journal.parents)) and
            args.journal.stat().st_uid == os.geteuid() and args.journal.stat().st_mode & 0o777 == 0o700,
            'PRIVATE_EMPTY_JOURNAL')
    item = Docker().inspect('fc-control-plane-0-console-1')
    workload(item, 'console')
    require(item['State']['Health']['Status'] == 'healthy', 'CONSOLE_NOT_HEALTHY')
    require(item['NetworkSettings']['Ports'] == {'8000/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '8765'}]},
            'CONSOLE_PORT_BINDING')
    require(health_status() == 200, 'CONSOLE_HEALTH_BEFORE')
    transport = Transport(item['Id'], args.image, args.journal)
    record(args.journal, 'before', item)
    started_at_ns = time.time_ns()
    with Lease(transport) as lease:
        require(health_status() is None, 'CONSOLE_NEW_REQUEST_ADMITTED')
        observed = lease.check()
        require(observed['rejected_packets'] > 0, 'CONSOLE_NO_REJECTION')
    require(health_status() == 200, 'CONSOLE_HEALTH_AFTER')
    after = transport.api.inspect(item['Id'])
    require(after['State']['Health']['Status'] == 'healthy', 'CONSOLE_NOT_HEALTHY_AFTER')
    equivalent(after, configuration(item))
    transport.runtime()
    receipt = dict(started_at_ns=started_at_ns, observed_at_ns=time.time_ns(), expired_or_removed=True,
                   new_http_request_refused=True, health_before_after=200, observation=observed,
                   runtime_unchanged=True, work_settlement_proven=False, capture_permitted=False)
    record(args.journal, 'receipt', receipt)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError):
        raise SystemExit('Console ingress lease refused or unconfirmed; retain all helper/journal identities, do not retry.') from None
