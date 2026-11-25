"""Compose existing short OWNER guards with a read-only publication database boundary."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import time

from scripts import control_ha_dispatcher_hold as dispatcher
from scripts import control_ha_ingress as ingress
from scripts.control_ha_owner_images import IMAGES
from scripts.control_ha_owner_admission_preflight import DockerRead
from scripts.control_ha_owner_replacement import Docker, configuration, equivalent, record
from scripts.control_ha_owner_upgrade import require, workload


def decode_stream(raw):
    require(len(raw) <= 64 * 1024, 'EXEC_OUTPUT_SIZE')
    streams = {1: bytearray(), 2: bytearray()}
    while raw:
        require(len(raw) >= 8 and raw[0] in streams and raw[1:4] == b'\x00\x00\x00', 'EXEC_STREAM_HEADER')
        length = int.from_bytes(raw[4:8], 'big')
        require(length <= len(raw) - 8, 'EXEC_STREAM_TRUNCATED')
        streams[raw[0]].extend(raw[8:8 + length])
        raw = raw[8 + length:]
    return bytes(streams[1]), bytes(streams[2])


def execute_source(api, target, raw, root):
    command = ['python', '-I', '-B', '-c', raw.decode('utf-8')]
    record(root, 'exec-intent', dict(target=target, source_sha256=hashlib.sha256(raw).hexdigest()))
    result = api.request('POST', '/containers/' + target + '/exec', dict(Cmd=command, User='console', Privileged=False,
        AttachStdout=True, AttachStderr=True, AttachStdin=False, Tty=False))
    identifier = result['Id']
    require(type(identifier) is str and re.fullmatch('[a-f0-9]{64}', identifier), 'EXEC_ID')
    record(root, 'exec-created', dict(id=identifier, target=target))
    endpoint = '/exec/' + identifier
    item = api.request('GET', endpoint + '/json')
    config = item['ProcessConfig']
    require(item['ContainerID'] == target and not item['Running'] and config['entrypoint'] == command[0] and
            config['arguments'] == command[1:] and config['user'] == 'console' and
            not config['privileged'] and not config['tty'], 'EXEC_SCOPE')
    record(root, 'exec-start-intent', dict(id=identifier, target=target, observed_at_ns=time.time_ns()))
    connection = DockerRead()
    connection.timeout = 8
    try:
        connection.request('POST', '/v1.52' + endpoint + '/start', body=b'{"Detach":false,"Tty":false}',
                           headers={'Content-Type': 'application/json'})
        response = connection.getresponse()
        require(response.status == 200, 'EXEC_START_RESPONSE')
        stdout, stderr = decode_stream(response.read(64 * 1024 + 1))
    finally:
        connection.close()
    item = api.request('GET', endpoint + '/json')
    record(root, 'exec-result', dict(id=identifier, target=target, running=item['Running'], exit_code=item['ExitCode'],
                                   stdout=stdout.decode('utf-8'), stderr=stderr.decode('utf-8')))
    require(item['ContainerID'] == target and not item['Running'] and item['ExitCode'] == 0 and not stderr,
            'EXEC_RESULT_UNCONFIRMED')
    return stdout


def scheduler_idle(binding):
    parent = binding['pid']
    children = Path(f'/proc/{parent}/task/{parent}/children').read_text().split()
    require(len(children) <= 1, 'UNSETTLED_PUBLISHER_CHILDREN')
    result = []
    for child in children:
        observed, state = dispatcher.process(int(child))
        command = (Path('/proc') / child / 'cmdline').read_bytes()
        require(observed['parent'] == parent and observed['uid'] == binding['uid'] and
                observed['cgroup_sha256'] == binding['cgroup_sha256'] and state in ('R', 'S', 'D') and
                command in (b'sleep\x0010\x00', b'/bin/sleep\x0010\x00', b'/usr/bin/sleep\x0010\x00') and
                not Path(f'/proc/{child}/task/{child}/children').read_text().split(), 'UNSETTLED_PUBLISHER_CHILD')
        require(dispatcher.process(int(child))[0] == observed, 'PUBLISHER_CHILD_CHANGED')
        result.append(observed)
    return result


def validate_receipt(value, started, finished):
    require(value['purpose'] == 'family-connect/owner-publication-pg-boundary/v1' and
            value['external_settlement_proven'] is False and value['capture_permitted'] is False and
            value['rollback_acknowledged'] is True and value['timeout_ms'] == 2000 and
            started <= value['locked_at_ns'] <= value['observed_at_ns'] <= value['released_at_ns'] <=
            value['finished_at_ns'] <= finished and value['released_at_ns'] - value['locked_at_ns'] < 2_000_000_000,
            'PUBLICATION_RECEIPT_BOUNDARY')
    require(set(value['message_counts']) == {'draft', 'queued', 'unknown', 'refused', 'published'} and
            all(type(count) is int and count >= 0 for count in value['message_counts'].values()) and
            value['message_counts']['unknown'] == 0, 'PUBLICATION_RECEIPT_UNCERTAIN')


def probe(root, image):
    require(root.is_absolute() and root.is_dir() and not any(root.iterdir()) and
            root.stat().st_uid == os.geteuid() and root.stat().st_mode & 0o777 == 0o700 and
            not any(path.is_symlink() for path in (root, *root.parents)), 'PRIVATE_EMPTY_JOURNAL')
    progress = dict(stage='preflight')
    try:
        return _probe(root, image, progress)
    except Exception as error:
        reason = str(error)
        record(root, 'abort', dict(stage=progress['stage'], reason=reason if re.fullmatch('[A-Z_]{1,80}', reason)
            else type(error).__name__, observed_at_ns=time.time_ns(), capture_permitted=False,
            guards_release_requires_readback=True))
        raise


def _probe(root, image, progress):
    api = Docker()
    before = {role: api.inspect('fc-control-plane-0-' + role + '-1') for role in IMAGES}
    for role, item in before.items():
        require(item is not None and item['Image'] == IMAGES[role] and item['State']['Running'] and
                not item['State']['Paused'] and not item['State']['Restarting'] and
                item['State']['Health']['Status'] == 'healthy', 'OWNER_BASELINE')
    console = before['console']
    workload(console, 'console')
    require(console['NetworkSettings']['Ports'] == {'8000/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '8765'}]} and
            ingress.health_status() == 200, 'CONSOLE_HEALTH_BEFORE')
    publisher, binding = dispatcher.publisher_binding()
    require(publisher['Id'] == before['system_publisher']['Id'], 'PUBLISHER_CHANGED')
    raw = Path(__file__).with_name('control_ha_publication_fence.py').read_bytes()
    require(0 < len(raw) < 64 * 1024, 'PUBLICATION_SOURCE_SIZE')
    record(root, 'before', before)
    record(root, 'source', dict(sha256=hashlib.sha256(raw).hexdigest(), dispatcher=binding, helper_image=image))
    journal = root / 'ingress'
    journal.mkdir(mode=0o700)
    transport = ingress.Transport(console['Id'], image, journal)
    progress['stage'] = 'publisher_hold'
    with dispatcher.Hold(binding, seconds=12) as held:
        progress['stage'] = 'publisher_idle'
        children = scheduler_idle(binding)
        progress['stage'] = 'console_ingress'
        with ingress.Lease(transport) as closed:
            held.check()
            closed.check()
            progress['stage'] = 'database_exec'
            started = time.time_ns()
            result = execute_source(api, console['Id'], raw, root)
            finished = time.time_ns()
            require(len(result) <= 16 * 1024, 'PUBLICATION_RESPONSE_SIZE')
            value = json.loads(result)
            record(root, 'database', value)
            progress['stage'] = 'database_validation'
            validate_receipt(value, started, finished)
            held.check()
            closed.check()
    progress['stage'] = 'resume_readback'
    require(held.statuses == [0, 0] and ingress.health_status() == 200, 'GUARD_RELEASE_UNCONFIRMED')
    after_publisher, after_binding = dispatcher.publisher_binding()
    require(after_publisher['Id'] == publisher['Id'] and after_binding == binding, 'PUBLISHER_RESUME_CHANGED')
    health = {}
    for role, previous in before.items():
        current = api.inspect(previous['Id'])
        equivalent(current, configuration(previous))
        require(all(current['State'][field] == previous['State'][field]
                    for field in ('Pid', 'StartedAt', 'Running', 'Paused', 'Restarting')) and
                current['RestartCount'] == previous['RestartCount'] and
                current['State']['Health']['Status'] == 'healthy', 'OWNER_RUNTIME_CHANGED')
        health[role] = dict(id=current['Id'], image=current['Image'], healthy=True, restarts=current['RestartCount'])
    receipt = dict(database=value, observed_at_ns=time.time_ns(), health=health, scheduler_children=children,
                   helper_exit_codes=held.statuses, console_health_before_after=200, guards_released=True,
                   runtime_and_configuration_unchanged=True, external_settlement_proven=False,
                   support_settlement_proven=False, manual_admission_closed=False, capture_permitted=False)
    record(root, 'receipt', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journal', type=Path, required=True)
    parser.add_argument('--ingress-image', required=True)
    args = parser.parse_args()
    receipt = probe(args.journal, args.ingress_image)
    print(json.dumps(dict(guards_released=receipt['guards_released'],
        runtime_and_configuration_unchanged=receipt['runtime_and_configuration_unchanged'],
        external_settlement_proven=False, capture_permitted=False), sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('OWNER publication probe refused or unconfirmed; preserve journals, no capture or retry permission.') from None
