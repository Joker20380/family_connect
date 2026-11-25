"""Native stopped-container replacement faults on owned synthetic state only."""
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
import uuid

from control.capture_gate import initialize
from scripts import control_ha_owner_replacement as replacement

LABEL = 'family-connect.ha-owner-replacement'
CANDIDATE = 'sha256:2162635c93cf7cdf376aa7a0cb6189ff8a4f8105f4c26aea6d28e63ccfb93a79'
CODE = '''import json, os, signal, sqlite3, sys, time
signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(0))
with sqlite3.connect('/product/state.sqlite') as connection:
    connection.execute('CREATE TABLE IF NOT EXISTS events (sequence INTEGER PRIMARY KEY)')
    connection.execute('INSERT INTO events DEFAULT VALUES')
    count = connection.execute('SELECT COUNT(*) FROM events').fetchone()[0]
if os.environ.get('FC_CONTROL_CAPTURE_GATE'):
    from control.capture_gate import Gate
    with Gate(os.environ['FC_CONTROL_CAPTURE_GATE']).operation() as operation:
        operation.uncertain()
print(json.dumps({'committed': count}), flush=True)
while True:
    time.sleep(1)
'''


class InterruptedDocker(replacement.Docker):
    def __init__(self, failure):
        self.failure = failure

    def interrupt(self, name):
        if self.failure == name:
            os.kill(os.getpid(), signal.SIGKILL)

    def create(self, name, config):
        super().create(name, config)
        self.interrupt('create')

    def rename(self, container, name):
        super().rename(container, name)
        self.interrupt('retain' if '-ha-retained-' in name else 'promote-or-restore')

    def remove(self, container):
        super().remove(container)
        self.interrupt('remove')


class Stand:
    def __init__(self, root):
        self.root = Path(root)
        replacement.require(self.root.is_absolute() and not self.root.exists() and
                            self.root.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()), 'LAB_ROOT')
        self.root.mkdir(mode=0o700)
        self.token = uuid.uuid4().hex
        self.name = 'fc-ha-owner-replacement-' + self.token
        self.volume = self.name + '-product'
        self.networks = [self.name + '-first', self.name + '-second']
        self.original = None
        self.receipts = []
        self.api = replacement.Docker()
        self.environment = {name: value for name, value in os.environ.items() if not name.startswith('DOCKER_')}

    def docker(self, *arguments, timeout=60):
        result = subprocess.run(['docker', '--host', 'unix:///var/run/docker.sock', *arguments],
                                capture_output=True, timeout=timeout, env=self.environment)
        replacement.require(result.returncode == 0, 'LAB_DOCKER_FAILED')
        return result.stdout

    def setup(self):
        replacement.require(os.geteuid() == 1000, 'LAB_UID')
        for name in self.networks:
            self.docker('network', 'create', '--internal', '--label', LABEL + '=' + self.token, name)
        self.docker('volume', 'create', '--label', LABEL + '=' + self.token, self.volume)
        self.docker('run', '--rm', '--pull=never', '--network=none', '--label', LABEL + '=' + self.token,
                    '--read-only', '--user', '0:0', '--cap-drop', 'ALL', '--cap-add', 'CHOWN',
                    '--security-opt', 'no-new-privileges', '--mount', 'type=volume,source=' + self.volume + ',target=/product',
                    replacement.plan.upgrade.ROLES['system_publisher'], 'python', '-c', "import os;os.chown('/product',1000,1000)")
        self.gate = self.root / 'gate'
        initialize(self.gate)
        token = self.root / 'synthetic-token'
        token.write_bytes(b'synthetic-only')
        token.chmod(0o600)
        with socket.socket() as reservation:
            reservation.bind(('127.0.0.1', 0))
            port = reservation.getsockname()[1]
        self.original = self.docker('create', '--pull=never', '--name', self.name + '-system_publisher',
            '--label', LABEL + '=' + self.token, '--network', self.networks[0], '--network-alias', 'replacement-service',
            '--read-only', '--user', '1000:1000', '--group-add', '100', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--memory', '128m', '--cpus', '0.5', '--pids-limit', '32',
            '--tmpfs', '/tmp:rw,nosuid,size=8m', '--stop-timeout', '17', '--restart', 'unless-stopped',
            '--publish', '127.0.0.1:' + str(port) + ':18080',
            '--health-cmd', 'python -c "raise SystemExit(0)"', '--health-interval', '1s',
            '--mount', 'type=volume,source=' + self.volume + ',target=/product',
            '--mount', 'type=bind,source=' + str(token) + ',target=/run/synthetic-token,readonly',
            '--env', 'FC_REPLACEMENT_FIXTURE=synthetic', replacement.plan.upgrade.ROLES['system_publisher'],
            'python', '-c', CODE).decode().strip()
        self.docker('network', 'connect', '--alias', 'replacement-secondary', self.networks[1], self.original)
        replacement.require(self.run(self.original) == 1, 'BASELINE_WRITE')

    def owned(self, container):
        item = self.api.inspect(container)
        replacement.require(item is not None and item['Config']['Labels'].get(LABEL) == self.token,
                            'LAB_CONTAINER_OWNERSHIP')
        return item

    def run(self, container):
        self.owned(container)
        self.docker('start', container)
        deadline = time.monotonic() + 10
        while self.owned(container)['State']['Health']['Status'] != 'healthy':
            replacement.require(time.monotonic() < deadline, 'LAB_HEALTH_TIMEOUT')
            time.sleep(0.1)
        try:
            replacement.stopped(self.owned(container))
        except ValueError as failure:
            replacement.require(str(failure) == 'STOPPED_REQUIRED', 'LAB_RUNNING_REFUSAL')
        else:
            raise ValueError('LAB_RUNNING_ADMITTED')
        self.docker('stop', '--time', '10', container)
        item = self.owned(container)
        replacement.stopped(item)
        replacement.require(item['State']['ExitCode'] == 0 and not item['State']['OOMKilled'], 'LAB_WORKLOAD_FAILED')
        return json.loads(self.docker('logs', container).splitlines()[-1])['committed']

    def kill_coordinator(self, root, pin, failure, action):
        code = '''import sys
from scripts.control_ha_owner_replacement import Replacement
from tests.fixtures.owner_upgrade.replacement import InterruptedDocker
transaction = Replacement(sys.argv[1], InterruptedDocker(sys.argv[3]), sys.argv[2])
getattr(transaction, sys.argv[4])()
'''
        result = subprocess.run([sys.executable, '-c', code, str(root), pin, failure, action],
                                cwd=Path(__file__).resolve().parents[3], env=self.environment,
                                capture_output=True, timeout=30)
        replacement.record(root, 'child-exit', {'returncode': result.returncode, 'failure': failure, 'action': action})
        replacement.require(result.returncode == -signal.SIGKILL and not result.stdout and not result.stderr,
                            'COORDINATOR_NOT_KILLED_AT_EXPECTED_BOUNDARY')

    def one(self, failure=None, *, reverting=False, execute=False):
        original = self.owned(self.original)
        proposed = replacement.configuration(original)
        proposed['Image'] = proposed['Config']['Image'] = CANDIDATE
        proposed['Config']['Env'].append(replacement.plan.observer.GATE + '=' + replacement.plan.DESTINATION)
        proposed['HostConfig']['Binds'] = [str(self.gate) + ':' + replacement.plan.DESTINATION + ':rw,rprivate']
        proposed['Mounts'].append(dict(Type='bind', Source=str(self.gate), Destination=replacement.plan.DESTINATION,
                                      Mode='rw,rprivate', RW=True, Propagation='rprivate'))
        root = self.root / ('journal-' + str(len(self.receipts)))
        root.mkdir(mode=0o700)
        replacement.prepare(root, original, proposed, 'system_publisher', laboratory=True)
        pin = hashlib.sha256((root / 'manifest.json').read_bytes()).hexdigest()
        transaction = replacement.Replacement(root, self.api, pin)
        interrupted = False
        try:
            if failure and not reverting:
                self.kill_coordinator(root, pin, failure, 'stage')
                interrupted = True
            staged = transaction.stage()
        except Exception:
            replacement.record(root, 'failed-candidate', self.api.inspect(transaction.manifest['staging']))
            raise
        replacement.require(staged['candidate_has_name'] and not staged['original_has_name'], 'STAGE_FAILED')
        committed = None
        if execute:
            committed = self.run(staged['candidate_id'])
            replacement.require(committed == 2 and len(list((self.gate / 'pending').iterdir())) == 1, 'CANDIDATE_WRITE')
        if failure and reverting:
            self.kill_coordinator(root, pin, failure, 'revert')
            interrupted = True
        restored = replacement.Replacement(root, self.api, pin).revert()
        replacement.require(restored['original_has_name'] and restored['candidate_id'] is None and
                            (failure is None or interrupted), 'REVERT_FAILED')
        replacement.equivalent(self.owned(self.original), original)
        if execute:
            replacement.require(self.run(self.original) == 3 and len(list((self.gate / 'pending').iterdir())) == 1,
                                'POST_UPGRADE_DATA_OR_PENDING_LOST')
        receipt = dict(fault=failure, reverting=reverting, recovered_interruption=interrupted,
                       committed_in_candidate=committed, original_id_preserved=True,
                       exact_config_mount_network_policy=True, pending_retained=True, **restored)
        replacement.record(root, 'native-receipt', receipt)
        self.receipts.append(receipt)

    def cleanup(self):
        containers = self.docker('ps', '-aq', '--filter', 'label=' + LABEL + '=' + self.token).decode().split()
        for container in containers:
            self.owned(container)
            self.docker('rm', '-f', container)
        for name in self.networks:
            info = json.loads(self.docker('network', 'inspect', name))[0]
            replacement.require(info['Labels'].get(LABEL) == self.token and not info['Containers'], 'LAB_NETWORK_OWNERSHIP')
            self.docker('network', 'rm', name)
        info = json.loads(self.docker('volume', 'inspect', self.volume))[0]
        replacement.require(info['Labels'].get(LABEL) == self.token, 'LAB_VOLUME_OWNERSHIP')
        self.docker('volume', 'rm', self.volume)


def main():
    stand = Stand(sys.argv[1])
    try:
        stand.setup()
        stand.one(execute=True)
        for failure in ('create', 'retain', 'promote-or-restore'):
            stand.one(failure)
        for failure in ('remove', 'promote-or-restore'):
            stand.one(failure, reverting=True)
        receipt = dict(result='ISOLATED_STOPPED_REPLACEMENT_PASS', cases=len(stand.receipts),
                       working_services_changed=False, capture_permitted=False, receipts=stand.receipts)
        replacement.record(stand.root, 'receipt', receipt)
        print(json.dumps({key: value for key, value in receipt.items() if key != 'receipts'}, sort_keys=True))
    finally:
        stand.cleanup()


if __name__ == '__main__':
    main()
