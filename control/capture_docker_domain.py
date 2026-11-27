"""Finite Docker domain policy and physical lifetime; initial enrollment is a separate gate."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import socket
import http.client
import time

from control.capture_docker import Admission, Engine, Handler, Server, route
from control.capture_domain import ClosedCgroup, LaunchLock
from control.capture_native import fingerprint, record, require


class DomainAdmission(Admission):
    def __init__(self, *args, parent, **kwargs):
        require(re.fullmatch(r'fc[a-z0-9]+\.slice', parent), 'DOCKER_DOMAIN_PARENT')
        self.parent = parent
        super().__init__(*args, **kwargs)

    def enrolled(self, host):
        require(host.get('CgroupParent') == self.parent and
                host.get('RestartPolicy', {}).get('Name', 'no') in ('', 'no') and
                host.get('CgroupnsMode', 'private') == 'private' and
                host.get('PidMode', '') in ('', 'private') and
                host.get('Runtime', '') in ('', 'runc'), 'DOCKER_DOMAIN_NOT_ENROLLED')

    def selected(self, request):
        selected = super().selected(request)
        if not selected:
            return False
        path = route(request)
        body = json.loads(base64.b64decode(request.get('RequestBody') or 'e30=', validate=True))
        if path == '/containers/create':
            self.enrolled(body.get('HostConfig', {}))
        else:
            found = re.fullmatch(r'/containers/([^/]+)(?:/(.*))?', path)
            if found:
                self.enrolled(self.scope.engine.get('/containers/' + found[1] + '/json')['HostConfig'])
                if found[2] == 'update':
                    require(body.get('RestartPolicy', {}).get('Name', 'no') in ('', 'no'),
                            'DOCKER_DOMAIN_AUTORESTART_REFUSED')
                if found[2] == 'exec':
                    require(not body.get('Privileged'), 'DOCKER_DOMAIN_EXEC_PRIVILEGED')
            found = re.fullmatch(r'/exec/([^/]+)/.*', path)
            if found:
                value = self.scope.engine.get('/exec/' + found[1] + '/json')
                require(value.get('ProcessConfig', {}).get('privileged') is False, 'DOCKER_DOMAIN_OLD_EXEC_PRIVILEGE')
                self.enrolled(self.scope.engine.get('/containers/' + value['ContainerID'] + '/json')['HostConfig'])
        return True

    def control(self, command):
        result = super().control(command)
        if command in ('CLOSE', 'CHECK') and result['phase'] == 'CLOSED':
            try:
                deadline = time.monotonic() + 2
                rows = self.scope.engine.get('/containers/json?all=1')
                require(isinstance(rows, list) and len(rows) <= 128, 'DOCKER_DOMAIN_CENSUS_BOUNDS')
                for row in rows:
                    require(time.monotonic() < deadline, 'DOCKER_DOMAIN_CHECK_DEADLINE')
                    if self.scope.container(row['Id']):
                        self.enrolled(self.scope.engine.get('/containers/' + row['Id'] + '/json')['HostConfig'])
                require(time.monotonic() < deadline, 'DOCKER_DOMAIN_CHECK_DEADLINE')
            except BaseException as error:
                self.fail(error)
                raise
        return {**result, 'parent': self.parent, 'initial_admission_coverage_proven': False}


class DomainClient:
    def __init__(self, path, parent):
        self.path, self.parent = str(path), parent
        self.lease = None

    def command(self, command):
        connection = http.client.HTTPConnection('localhost', timeout=4)
        channel = socket.socket(socket.AF_UNIX)
        channel.settimeout(4)
        try:
            channel.connect(self.path)
            connection.sock = channel
            connection.request('POST', '/fc-control', json.dumps(dict(command=command)),
                               {'Content-Type': 'application/json'})
            response = connection.getresponse()
            raw = response.read(4097)
            require(response.status == 200 and len(raw) <= 4096, 'DOCKER_DOMAIN_CONTROL_REFUSED')
            value = json.loads(raw)
            require(value['parent'] == self.parent, 'DOCKER_DOMAIN_PARENT_CHANGED')
            if self.lease is None:
                require(command == 'CLOSE', 'DOCKER_DOMAIN_CLIENT_NO_ADOPTION')
                self.lease = value['lease']
            require(value['lease'] == self.lease, 'DOCKER_DOMAIN_LEASE_CHANGED')
            return value
        finally:
            connection.close()
            channel.close()


class ExecutorBoundary:
    def __init__(self, client, launch, directory, journal):
        require(isinstance(client, DomainClient) and isinstance(launch, LaunchLock), 'DOCKER_EXECUTOR_BINDINGS')
        self.client, self.launch, self.directory = client, launch, Path(directory)
        require(self.directory == Path('/sys/fs/cgroup') / client.parent, 'DOCKER_EXECUTOR_DIRECTORY')
        self.journal = Path(journal)
        self.journal.mkdir(mode=0o700, exist_ok=False)
        self.domain, self.lease, self.failed, self.released = None, None, False, None

    def failure(self, error):
        self.failed = True
        if not (self.journal / 'failed.json').exists():
            try:
                record(self.journal, 'failed.json', dict(reason=str(error), reconciliation_required=True,
                    admission_reopened=False, capture_permitted=False))
            except Exception as cleanup:
                error.add_note('DOCKER_EXECUTOR_FAILURE_RECORD_' + type(cleanup).__name__)

    def acquire(self):
        try:
            require(self.domain is None and self.lease is None and not self.failed, 'DOCKER_EXECUTOR_NO_REENTRY')
            state = self.client.command('CLOSE')
            record(self.journal, 'closed.json', state)
            deadline = time.monotonic() + 5
            while state['pending']:
                require(time.monotonic() < deadline, 'DOCKER_EXECUTOR_PENDING_UNCERTAIN')
                time.sleep(.05)
                state = self.client.command('CHECK')
            self.domain = ClosedCgroup(self.directory, self.launch, self.journal / 'domain')
            self.domain.__enter__()
            self.lease = fingerprint(dict(admission=self.client.lease, domain=self.domain.check()))
            self.check()
            record(self.journal, 'held.json', dict(lease=self.lease, result='ENROLLED_DOMAIN_EMPTY_AND_FROZEN',
                initial_admission_coverage_proven=False, owner_adapter=False, fleet_capture=False))
            return self
        except BaseException as error:
            self.failure(error)
            raise

    def check(self):
        try:
            require(not self.failed and self.domain is not None, 'DOCKER_EXECUTOR_NOT_HELD')
            state = self.client.command('CHECK')
            require(state['phase'] == 'CLOSED' and state['pending'] == 0, 'DOCKER_EXECUTOR_ADMISSION_LOST')
            require(self.lease == fingerprint(dict(admission=state['lease'], domain=self.domain.check())),
                    'DOCKER_EXECUTOR_LEASE_CHANGED')
            return self.lease
        except BaseException as error:
            self.failure(error)
            raise

    def release(self):
        if self.released is not None:
            return self.released
        try:
            self.check()
            record(self.journal, 'release-intent.json', dict(lease=self.lease))
            self.domain.__exit__(None, None, None)
            state = self.client.command('RELEASE')
            require(state['phase'] == 'RELEASED', 'DOCKER_EXECUTOR_RELEASE_UNCONFIRMED')
            released = dict(lease=self.lease, writer_restart='NOT_PERFORMED')
            record(self.journal, 'released.json', released)
            self.released = released
            return self.released
        except BaseException as error:
            self.failure(error)
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('socket', 'engine', 'pidfile', 'journal', 'daemon-config', 'parent'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--protect', action='append', required=True)
    args = parser.parse_args()
    require(os.geteuid() == 0, 'DOCKER_PLUGIN_ROOT_REQUIRED')
    os.umask(0o077)
    admission = DomainAdmission(Engine(args.engine), args.protect, args.pidfile, args.journal,
        config=args.daemon_config, plugin=Path(args.socket).stem, parent=args.parent)
    with Server(args.socket, Handler) as server:
        server.admission = admission
        server.serve_forever(poll_interval=.1)


if __name__ == '__main__':
    main()
