"""Disposable OWNER image activation/revert; never mount or dispatch production state."""
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time
import uuid

from scripts import control_ha_owner_upgrade as upgrade
from scripts.control_ha_owner_joint_lab import OwnerLab

LABEL = 'family-connect.ha-owner-upgrade'
GATE = '/run/fc-admission/gate'
require = upgrade.require


class Stand:
    def __init__(self, lab, candidates, workloads):
        self.lab, self.candidates, self.workloads = lab, candidates, workloads
        self.containers, self.volumes = [], []
        self.sequence = 0

    def create_volume(self, suffix):
        name = self.lab.name + '-upgrade-' + suffix
        require(name != self.lab.volume and name not in self.volumes, 'VOLUME_COLLISION')
        self.lab.docker('volume', 'create', '--label', LABEL + '=' + self.lab.token, name)
        info = json.loads(self.lab.docker('volume', 'inspect', name))[0]
        require(info['Labels'].get(LABEL) == self.lab.token, 'VOLUME_OWNERSHIP')
        self.volumes.append(name)
        return name

    def owned(self, container):
        require(container in self.containers, 'UNKNOWN_LAB_CONTAINER')
        info = json.loads(self.lab.docker('inspect', container))[0]
        require(info['Config']['Labels'].get(LABEL) == self.lab.token and
                info['HostConfig']['NetworkMode'] in ('none', 'container:' + self.lab.container) and
                not info['HostConfig']['Privileged'] and not info['HostConfig']['PortBindings'], 'LAB_OWNERSHIP')
        return info

    def create(self, role, image, command, *, enabled=False, root=False, invalid=False):
        self.sequence += 1
        arguments = ['create', '--pull=never', '--name', self.lab.name + '-upgrade-' + str(self.sequence),
                     '--label', LABEL + '=' + self.lab.token, '--network', 'container:' + self.lab.container,
                     '--read-only', '--user', '0:0' if root else upgrade.USERS[role], '--cap-drop', 'ALL',
                     '--security-opt', 'no-new-privileges', '--memory', '384m', '--cpus', '1', '--pids-limit', '64',
                     '--tmpfs', '/tmp', '--no-healthcheck', '--workdir', '/app/control_plane',
                     '--env', 'CONTROL_PLANE_MODE=synthetic', '--env', 'POSTGRES_HOST=127.0.0.1',
                     '--env', 'POSTGRES_PASSWORD=' + self.lab.password, '--env', 'DJANGO_SECRET_KEY=' + self.lab.secret,
                     '--env', 'FC_SYSTEM_PUBLISHER_ORIGIN=https://example.invalid', '--env', 'FC_SUPPORT_SOCKET=',
                     '--mount', f'type=volume,source={self.gates[role]},target=/run/fc-admission']
        if role == 'console':
            arguments += ['--mount', f'type=volume,source={self.data},target=/app/control_plane/.local']
        else:
            arguments += ['--mount', f'type=volume,source={self.gates[role]},target=/run/secrets,readonly']
        if root:
            arguments += ['--cap-add', 'CHOWN', '--cap-add', 'SETUID', '--cap-add', 'SETGID']
        if enabled:
            arguments += ['--env', 'FC_CONTROL_CAPTURE_GATE=' + (GATE + '-missing' if invalid else GATE)]
        container = self.lab.docker(*arguments, image, *command).decode().strip()
        self.containers.append(container)
        self.owned(container)
        return container

    def start(self, container):
        self.owned(container)
        self.lab.docker('start', container)

    def wait(self, container, expected=0):
        self.owned(container)
        status = self.lab.docker('wait', container, timeout=90).decode().strip()
        log = self.logs(container)
        require(status == str(expected), 'LAB_EXIT_' + status + '_EXPECTED_' + str(expected))
        return log

    def logs(self, container):
        self.owned(container)
        result = subprocess.run(['docker', '--host', 'unix:///var/run/docker.sock', 'logs', container],
                                capture_output=True, timeout=5, env=self.lab.environment)
        require(result.returncode == 0, 'LAB_LOGS')
        log = result.stdout + result.stderr
        (self.lab.root / (container + '.log')).write_bytes(log)
        return log

    def one(self, role, image, command, *, expected=0, **options):
        container = self.create(role, image, command, **options)
        self.start(container)
        return self.wait(container, expected)

    def stop(self, container):
        self.owned(container)
        self.lab.docker('stop', '--time', '8', container)

    def probe(self, role, code, *, enabled=False, image=None, expected=0):
        return self.one(role, image or self.candidates[role], ['python', '-c', code],
                        enabled=enabled, expected=expected)

    def shell(self, image, code, *, enabled=False, expected=0):
        return self.one('console', image, ['python', 'manage.py', 'shell', '-c', code],
                        enabled=enabled, expected=expected)

    def setup(self):
        self.data = self.create_volume('data')
        self.gates = {role: self.create_volume(role + '-gate') for role in upgrade.ROLES}
        for role, uid in (('console', 10001), ('system_publisher', 1000)):
            code = f'''import os
os.chown('/run/fc-admission', {uid}, {uid})
'''
            if role == 'console':
                code += f"os.chown('/app/control_plane/.local', {uid}, {uid})\n"
            code += f'''os.setgroups([])
os.setgid({uid})
os.setuid({uid})
from control.capture_gate import initialize
initialize({GATE!r})
'''
            if role == 'system_publisher':
                code += "descriptor=os.open('/run/fc-admission/system-publisher.token',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)\nos.write(descriptor,b'0'*64)\nos.close(descriptor)\n"
            self.one(role, self.candidates[role], ['python', '-c', code], root=True)

    def service(self, role, image, enabled):
        container = self.create(role, image, self.workloads[role]['Config']['Cmd'], enabled=enabled)
        self.start(container)
        info = self.owned(container)
        require(info['Config']['Cmd'] == self.workloads[role]['Config']['Cmd'] and
                info['Config']['User'] == self.workloads[role]['Config']['User'] and
                info['Config']['WorkingDir'] == self.workloads[role]['Config']['WorkingDir'], 'WORKLOAD_DRIFT')
        ready = ("import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/health/',timeout=1).read()"
                 if role == 'console' else "from pathlib import Path;assert Path('/tmp/publisher-cycle').is_file()")
        for attempt in range(100):
            self.owned(container)
            result = subprocess.run(['docker', '--host', 'unix:///var/run/docker.sock', 'exec', container,
                                     'python', '-c', ready], capture_output=True, timeout=5, env=self.lab.environment)
            if result.returncode == 0:
                break
            require(self.owned(container)['State']['Running'], 'SERVICE_EXITED')
            time.sleep(.2)
        else:
            raise ValueError('SERVICE_READINESS_TIMEOUT')
        return container

    def admission(self, role):
        code = f'''import signal,time
from pathlib import Path
from control.capture_gate import Gate
signal.alarm(5)
with Gate({GATE!r}).drain(1):
    Path('/tmp/holding').touch()
    time.sleep(3)
'''
        holder = self.create(role, self.candidates[role], ['python', '-c', code])
        self.start(holder)
        for attempt in range(40):
            self.owned(holder)
            result = subprocess.run(['docker', '--host', 'unix:///var/run/docker.sock', 'exec', holder,
                'python', '-c', "from pathlib import Path;assert Path('/tmp/holding').is_file()"],
                capture_output=True, timeout=3, env=self.lab.environment)
            if result.returncode == 0:
                break
            time.sleep(.05)
        else:
            raise ValueError('HOLDER_NOT_READY')
        output = self.one(role, self.candidates[role], ['python', 'manage.py', 'check'], enabled=True, expected=75)
        require(b'CAPTURE_BUSY' in output, 'ADMISSION_NOT_CLOSED')
        require(self.owned(holder)['State']['Running'], 'HOLDER_EXPIRED')
        self.wait(holder)

    def cleanup(self):
        for container in reversed(self.containers):
            self.owned(container)
            self.logs(container)
            self.lab.docker('rm', '-f', container)
        for volume in reversed(self.volumes):
            info = json.loads(self.lab.docker('volume', 'inspect', volume))[0]
            require(info['Labels'].get(LABEL) == self.lab.token, 'VOLUME_OWNERSHIP')
            self.lab.docker('volume', 'rm', volume)
        require(not self.lab.docker('ps', '-aq', '--filter', 'label=' + LABEL + '=' + self.lab.token).strip(),
                'LAB_CONTAINER_LEAK')
        require(not self.lab.docker('volume', 'ls', '-q', '--filter', 'label=' + LABEL + '=' + self.lab.token).strip(),
                'LAB_VOLUME_LEAK')


def run(candidates):
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    before = {role: upgrade.source.preflight.read('/containers/fc-control-plane-0-' + role + '-1/json')
              for role in upgrade.ROLES}
    bindings = {role: upgrade.workload(item, role) for role, item in before.items()}
    for role in upgrade.ROLES:
        upgrade.verify(upgrade.image(upgrade.ROLES[role]), upgrade.image(candidates[role]))
    started = time.time_ns()
    root = Path(tempfile.gettempdir()) / ('fc-owner-upgrade-' + uuid.uuid4().hex)
    with OwnerLab(root) as lab:
        stand = Stand(lab, candidates, before)
        try:
            stand.setup()
            stand.shell(upgrade.ROLES['console'], 'from apps.console.backend import seed_fixture;seed_fixture()')
            old_console = stand.service('console', upgrade.ROLES['console'], False)
            old_publisher = stand.service('system_publisher', upgrade.ROLES['system_publisher'], False)
            migrations = lab.docker('exec', lab.container, 'psql', '-U', 'fc_control_plane', '-d',
                'fc_control_plane', '-Atc', 'SELECT app,name FROM django_migrations ORDER BY app,name')
            stand.stop(old_publisher)
            stand.stop(old_console)
            current_console = stand.service('console', candidates['console'], True)
            current_publisher = stand.service('system_publisher', candidates['system_publisher'], True)
            write = '''from django.contrib.sessions.backends.db import SessionStore
from apps.console import backend
session=SessionStore();session['upgrade_probe']='acknowledged';session.save()
with backend.registry(write=True) as database:
    database.execute("UPDATE control_plane_devices SET label='upgrade-ack' WHERE rowid=(SELECT min(rowid) FROM control_plane_devices)")
'''
            stand.shell(candidates['console'], write, enabled=True)
            for role in upgrade.ROLES:
                stand.admission(role)
            stand.stop(current_publisher)
            stand.stop(current_console)
            stand.one('console', candidates['console'], before['console']['Config']['Cmd'],
                      enabled=True, invalid=True, expected=1)
            stand.shell(candidates['console'], "raise RuntimeError('isolated-unknown-operation')", enabled=True, expected=1)
            pending = f'''from pathlib import Path
from control.capture_gate import Gate,GateError
assert len(list(Path({GATE!r},'pending').iterdir()))==1
try:
    with Gate({GATE!r}).drain(1):pass
except GateError:pass
else:raise AssertionError('Unsettled operation was accepted')
'''
            pending += f'''import hashlib
print(hashlib.sha256(b''.join(item.name.encode()+item.read_bytes() for item in sorted(Path({GATE!r},'pending').iterdir()))).hexdigest())
'''
            pending_before = stand.probe('console', pending)
            reverted_console = stand.service('console', upgrade.ROLES['console'], False)
            reverted_publisher = stand.service('system_publisher', upgrade.ROLES['system_publisher'], False)
            readback = '''from django.contrib.sessions.models import Session
from apps.console import backend
assert [item.get_decoded().get('upgrade_probe') for item in Session.objects.all()]==['acknowledged']
with backend.registry() as database:
    assert database.execute("SELECT count(*) FROM control_plane_devices WHERE label='upgrade-ack'").fetchone()[0]==1
from django.db.migrations.executor import MigrationExecutor
from django.db import connection
executor=MigrationExecutor(connection)
assert not executor.migration_plan(executor.loader.graph.leaf_nodes())
'''
            stand.shell(upgrade.ROLES['console'], readback)
            require(stand.probe('console', pending) == pending_before, 'UNCERTAINTY_CHANGED')
            require(lab.docker('exec', lab.container, 'psql', '-U', 'fc_control_plane', '-d',
                'fc_control_plane', '-Atc', 'SELECT app,name FROM django_migrations ORDER BY app,name') == migrations,
                'MIGRATION_SET_CHANGED')
            for role, uid in (('console', 10001), ('system_publisher', 1000)):
                stand.probe(role, f'''import os,stat
from pathlib import Path
assert os.getuid()=={uid}
root=Path({GATE!r})
assert stat.S_IMODE(root.stat().st_mode)==0o700 and root.stat().st_uid=={uid}
assert all(stat.S_IMODE((root/name).stat().st_mode)==0o600 for name in ('admission.lock','operations.lock'))
''')
            stand.stop(reverted_publisher)
            stand.stop(reverted_console)
        finally:
            stand.cleanup()
    after = {role: upgrade.workload(upgrade.source.preflight.read(
        '/containers/fc-control-plane-0-' + role + '-1/json'), role) for role in upgrade.ROLES}
    require(after == bindings, 'INSTALLED_WORKLOAD_CHANGED')
    return dict(result='ISOLATED_OWNER_UPGRADE_REVERT_PASS', started_at_ns=started,
                finished_at_ns=time.time_ns(), baseline_images=upgrade.ROLES, candidate_images=candidates,
                installed_bindings=bindings, installed_unchanged=True, same_effective_commands=True,
                acknowledged_pg_and_sqlite_preserved=True, failed_activation_reverted=True,
                migration_set_unchanged=True,
                uncertainty_preserved=True, owned_containers_and_volumes_removed=True,
                private_logs=str(root), production_data_used=False, external_dispatch=False,
                independently_approved=False, deployed=False, capture_permitted=False)


if __name__ == '__main__':
    os.umask(0o077)
    evidence = Path(sys.argv[1])
    candidates = {role: json.loads((evidence / (role + '-image.json')).read_text())['candidate_image']
                  for role in upgrade.ROLES}
    print(json.dumps(run(candidates), sort_keys=True))
