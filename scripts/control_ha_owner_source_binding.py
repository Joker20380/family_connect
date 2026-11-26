"""GET-only OWNER source/dispatcher observation; never approval or a loaded-code attestation."""
import ast
import base64
import hashlib
import http.client
import io
import json
from pathlib import Path, PurePosixPath
import re
import resource
import shlex
import signal
import sys
import tarfile
import time
from urllib.parse import quote

from scripts import control_ha_owner_admission_preflight as preflight

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    'control/capture_gate.py',
    'control_plane/manage.py',
    'control_plane/fc_control_plane/capture.py',
    'control_plane/fc_control_plane/db_backend/__init__.py',
    'control_plane/fc_control_plane/db_backend/base.py',
    'control_plane/fc_control_plane/middleware.py',
    'control_plane/fc_control_plane/settings.py',
    'control_plane/fc_control_plane/wsgi.py',
    'control_plane/apps/console/backend.py',
    'control_plane/apps/console/support.py',
    'control_plane/apps/console/system_publisher.py',
    'control_plane/apps/console/management/commands/publish_system_messages.py',
)
OPTIONAL = {'control/capture_gate.py', 'control_plane/fc_control_plane/capture.py',
            'control_plane/fc_control_plane/db_backend/__init__.py',
            'control_plane/fc_control_plane/db_backend/base.py'}
IMAGES = dict(zip(preflight.NAMES, (
    'sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a',
    'sha256:50de6f25a04c1127b127b3278314619c69eddeec229d0d4ad9b7e67c1d2ffeab',
)))
FILE_LIMIT = 256 * 1024
ARCHIVE_LIMIT = FILE_LIMIT + 64 * 1024
TOKENS = {'python', 'python3', 'sh', 'bash', 'gunicorn', 'manage.py', 'fc_control_plane.wsgi:application',
          'migrate', 'seed_demo', 'collectstatic', 'publish_system_messages', 'shell', 'sleep'}
require = preflight.require


def source_record(raw):
    if raw is None:
        return dict(present=False, sha256=None, bytes=0, capture_syntax_mentioned=False)
    require(type(raw) is bytes and 0 < len(raw) <= FILE_LIMIT, 'SOURCE_BOUNDS')
    try:
        tree = ast.parse(raw.decode('utf-8'))
    except (ValueError, SyntaxError, UnicodeError, RecursionError):
        raise ValueError('SOURCE_SYNTAX') from None
    mention = any((isinstance(node, ast.ImportFrom) and node.module in
                   ('control.capture_gate', 'fc_control_plane.capture', 'capture')) or
                  (isinstance(node, ast.Constant) and node.value in
                   ('FC_CONTROL_CAPTURE_GATE', 'fc_control_plane.middleware.CaptureAdmission'))
                  for node in ast.walk(tree))
    return dict(present=True, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), capture_syntax_mentioned=mention)


def candidate():
    result = {}
    for name in SOURCES:
        path = ROOT / name
        require(all(not item.is_symlink() for item in (path, *path.parents)), 'CANDIDATE_SYMLINK')
        with path.open('rb') as source:
            result[name] = source_record(source.read(FILE_LIMIT + 1))
    return result


def command_record(arguments):
    require(arguments is None or (type(arguments) is list and len(arguments) <= 128 and
            all(type(value) is str and len(value) <= 16384 for value in arguments)), 'COMMAND_SHAPE')
    mentions, parsed = set(), True
    for argument in arguments or []:
        try:
            words = shlex.split(argument)
        except ValueError:
            parsed = False
            continue
        mentions.update(word for word in words if word in TOKENS)
    return dict(sha256=preflight.digest(arguments), known_token_mentions=sorted(mentions), lexically_parsed=parsed,
                dispatch_coverage_proved=False)


def archive_file(raw, header, name):
    require(type(raw) is bytes and 0 < len(raw) <= ARCHIVE_LIMIT and type(header) is str and
            len(header) <= 8192, 'ARCHIVE_BOUNDS')
    try:
        metadata = json.loads(base64.b64decode(header, validate=True), object_pairs_hook=preflight.pairs)
        require(type(metadata) is dict and metadata['name'] == PurePosixPath(name).name and
                type(metadata['size']) is int and 0 < metadata['size'] <= FILE_LIMIT and
                metadata.get('linkTarget', '') == '' and type(metadata['mode']) is int and
                0 <= metadata['mode'] <= 0o777, 'ARCHIVE_METADATA')
        with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
            members = archive.getmembers()
            require(len(members) == 1, 'ARCHIVE_MEMBERS')
            member = members[0]
            require(member.name == metadata['name'] and member.isfile() and not member.linkname and
                    member.size == metadata['size'] and member.mode == metadata['mode'], 'ARCHIVE_FILE')
            with archive.extractfile(member) as source:
                contents = source.read(FILE_LIMIT + 1)
            require(len(contents) == member.size, 'ARCHIVE_SIZE')
            return contents
    except (KeyError, TypeError, tarfile.TarError, UnicodeError):
        raise ValueError('ARCHIVE_REFUSED') from None


class Reader:
    def __init__(self):
        self.containers = set()
        self.executions = set()

    def request(self, endpoint, *, archive_name=None):
        allowed = {'/containers/' + name + '/json' for name in preflight.NAMES}
        allowed.update('/containers/' + container + '/json' for container in self.containers)
        allowed.update('/exec/' + execution + '/json' for execution in self.executions)
        if archive_name is not None:
            require(archive_name in SOURCES, 'ARCHIVE_SCOPE')
            allowed = {'/containers/' + container + '/archive?path=' + quote('/app/' + archive_name, safe='')
                       for container in self.containers}
        require(endpoint in allowed, 'READ_SCOPE')
        connection = preflight.DockerRead()
        try:
            connection.request('GET', endpoint)
            response = connection.getresponse()
            if response.status == 404 and archive_name in OPTIONAL:
                return None
            require(response.status == 200, 'DOCKER_READ_FAILED')
            limit = ARCHIVE_LIMIT if archive_name else preflight.LIMIT
            raw = response.read(limit + 1)
            require(len(raw) <= limit, 'READ_BOUNDS')
            if archive_name:
                return archive_file(raw, response.getheader('X-Docker-Container-Path-Stat'), archive_name)
            return json.loads(raw, object_pairs_hook=preflight.pairs)
        finally:
            connection.close()

    def inspect(self, name):
        return self.request('/containers/' + name + '/json')

    def source(self, container, name):
        return self.request('/containers/' + container + '/archive?path=' + quote('/app/' + name, safe=''),
                            archive_name=name)

    def execution(self, execution):
        return self.request('/exec/' + execution + '/json')


def selected(item, name):
    binding = preflight.binding(item, name)
    require(binding['image'] == IMAGES[name], 'INSTALLED_IMAGE_CHANGED')
    executions = item.get('ExecIDs')
    executions = [] if executions is None else executions
    require(type(executions) is list and len(executions) <= 64 and len(set(executions)) == len(executions) and
            all(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) for value in executions), 'EXEC_IDS')
    workdir = item['Config']['WorkingDir']
    preflight.absolute(workdir)
    return dict(binding=binding, executions=sorted(executions), working_directory_sha256=preflight.digest(workdir),
                entrypoint=command_record(item['Config']['Entrypoint']), command=command_record(item['Config']['Cmd']))


def covering_mount(item, name):
    path = PurePosixPath('/app/' + name)
    covering = [mount for mount in item['Mounts'] if path.is_relative_to(preflight.absolute(mount['Destination']))]
    if not covering:
        return dict(kind='container_rootfs', readonly=item['HostConfig']['ReadonlyRootfs'])
    mount = max(covering, key=lambda entry: len(PurePosixPath(entry['Destination']).parts))
    return dict(kind=mount['Type'], readonly=not mount['RW'], destination_sha256=preflight.digest(mount['Destination']),
                source_sha256=preflight.digest(mount.get('Source', '')))


def execution_record(item, expected, container):
    require(item['ID'] == expected and item['ContainerID'] == container and type(item['Running']) is bool and
            type(item['Pid']) is int and item['Pid'] >= 0 and
            type(item['ExitCode']) is int and item['ExitCode'] >= 0, 'EXEC_BINDING')
    require(not item['Running'] or item['Pid'] > 0, 'EXEC_PID')
    config = item['ProcessConfig']
    require(type(config) is dict and type(config['entrypoint']) is str and type(config['arguments']) is list,
            'EXEC_COMMAND')
    return dict(id=expected, running=item['Running'], pid=item['Pid'], exit_code=item['ExitCode'],
                process_config_sha256=preflight.digest(config), command=command_record([config['entrypoint'], *config['arguments']]))


def collect(reader=None, expected_sources=None):
    reader = Reader() if reader is None else reader
    expected_sources = candidate() if expected_sources is None else expected_sources
    require(set(expected_sources) == set(SOURCES), 'CANDIDATE_COVERAGE')
    started = time.time_ns()
    before_raw = {name: reader.inspect(name) for name in preflight.NAMES}
    before = {name: selected(item, name) for name, item in before_raw.items()}
    reader.containers.update(item['binding']['id'] for item in before.values())
    reader.executions.update(execution for item in before.values() for execution in item['executions'])
    snapshots, executions = [], {}
    for repetition in range(2):
        snapshot = {}
        for name, item in before.items():
            snapshot[name] = {source: source_record(reader.source(item['binding']['id'], source)) for source in SOURCES}
        snapshots.append(snapshot)
        if repetition == 0:
            executions = {name: [execution_record(reader.execution(execution), execution, item['binding']['id'])
                                for execution in item['executions']] for name, item in before.items()}
    after = {name: selected(reader.inspect(item['binding']['id']), name) for name, item in before.items()}
    require(before == after and snapshots[0] == snapshots[1], 'INSTALLED_BINDING_CHANGED')
    containers = []
    for name, item in before.items():
        sources = {source: dict(**record, candidate_sha256=expected_sources[source]['sha256'],
                               candidate_match=record['sha256'] == expected_sources[source]['sha256'],
                               mount=covering_mount(before_raw[name], source))
                   for source, record in snapshots[0][name].items()}
        containers.append(dict(name=name, runtime=item, sources=sources, execution_observations=executions[name]))
    return dict(schema=1, node='OWNER', started_at_ns=started, finished_at_ns=time.time_ns(), containers=containers,
                candidate_source_set_sha256=preflight.digest(expected_sources),
                observed_source_set_sha256=preflight.digest(snapshots[0]), observations_equal=True,
                syntax_mentions_are_not_coverage=True, unresolved=['LOADED_BYTES_NOT_ATTESTED',
                    'MANUAL_DISPATCH_NOT_CLOSED', 'DIRECT_ORM_NOT_COVERED', 'EXTERNAL_COMPLETION_NOT_ATTESTED',
                    'NAMESPACE_AND_GATE_BINDINGS_NOT_APPROVED', 'INDEPENDENT_APPROVAL_REQUIRED'],
                capture_permitted=False, all_writers_qualified=False, services_changed=False,
                commands_executed_in_containers=False)


def main():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    require(signal.getsignal(signal.SIGALRM) == signal.SIG_DFL and
            signal.SIGALRM not in signal.pthread_sigmask(signal.SIG_BLOCK, []) and
            signal.getitimer(signal.ITIMER_REAL) == (0, 0), 'ALARM_NOT_EXCLUSIVE')
    signal.alarm(30)
    try:
        print(json.dumps(collect(), sort_keys=True))
        return 0
    except (ValueError, KeyError, TypeError, OSError, http.client.HTTPException):
        print('OWNER_SOURCE_BINDING_REFUSED', file=sys.stderr)
        return 1
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    raise SystemExit(main())
