"""Isolated native OWNER image checks on a new private copy, never original mounts."""
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import uuid

from scripts import control_ha_owner_capture as capture
from scripts import control_ha_owner_runtime as custody
from scripts.control_ha_owner_collect import policy
from scripts.backup_paid_registry import paid_projection
from scripts.control_ha_installed_inventory import Reader
from scripts.control_ha_live_sqlite import require

LABEL = 'family-connect.ha-owner-offline'


def command(destination, name, *, baseline=None):
    runtime = policy(baseline)
    destination = Path(destination)
    require(destination.is_absolute() and '..' not in destination.parts and ',' not in str(destination), 'PROBE_PATH')
    with Reader().opened(destination) as descriptor:
        info = os.fstat(descriptor)
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and
                stat.S_IMODE(info.st_mode) == 0o700 and os.getuid() != 0, 'PRIVATE_PROBE_REQUIRED')
    require(name.startswith('fc-ha-owner-') and name[12:].isalnum(), 'PROBE_NAME')
    return ['docker', 'run', '--rm', '-i', '--name', name, '--label', LABEL + '=' + name,
            '--network', 'none', '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
            '--pids-limit', '128', '--memory', '256m', '--user', f'{os.getuid()}:{os.getgid()}',
            '--mount', f'type=bind,source={destination},destination=/app/control_plane/.local,readonly',
            '--workdir', '/app/control_plane', '--env', 'PYTHONDONTWRITEBYTECODE=1',
            '--env', 'PYTHONPATH=/app:/app/control_plane', '--entrypoint', 'python', runtime.IMAGES['console'], '-B', '-']


def qualify(value, destination, *, baseline=None):
    runtime = policy(baseline)
    summary, files = runtime.validate(value), runtime.unpack(value)
    destination = Path(destination)
    runtime.restore(value, destination)
    synthetic = destination / 'synthetic'
    synthetic.mkdir(mode=0o700)
    (destination / 'synthetic.sqlite').rename(synthetic / 'registry.sqlite3')
    environments = custody.environments(files, images=runtime.IMAGES)
    observed = value['captured_at_ns'] // 1000000000
    with closing(sqlite3.connect(':memory:')) as database:
        database.deserialize(files['synthetic.sqlite'])
        database.execute('PRAGMA trusted_schema=OFF')
        database.execute('PRAGMA query_only=ON')
        projection = paid_projection(database, observed)
    configuration = dict(environment={name: environments['console'][name] for name in
                         ('CONTROL_PLANE_MODE', 'DJANGO_SECRET_KEY', 'POSTGRES_PASSWORD')},
                         publisher_origin=environments['system_publisher']['FC_SYSTEM_PUBLISHER_ORIGIN'],
                         observed=observed, tables=summary['tables'],
                         paid_projection_sha256=capture.digest(capture.encoded(projection)))
    descriptor = os.open(destination / 'probe.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(capture.encoded(configuration))
        stream.flush()
        os.fsync(stream.fileno())
    probe = Path(__file__).with_name('control_ha_owner_probe.py').read_bytes()
    name = 'fc-ha-owner-' + uuid.uuid4().hex
    try:
        result = subprocess.run(command(destination, name, baseline=baseline), input=probe, capture_output=True, timeout=60)
        require(result.returncode == 0 and len(result.stdout) < 16384, 'NATIVE_CONTAINER_REFUSED')
        receipt = custody.document(result.stdout)
        require(receipt['result'] == 'NATIVE_OWNER_OFFLINE_PASS' and receipt['activation'] is False and
                receipt['pg_pair_fence'] is False and receipt['dispatch_calls'] == 0 and
                receipt['database_unchanged'] is True and
                receipt['sqlite_sha256'] == capture.digest(files['synthetic.sqlite']), 'NATIVE_RECEIPT')
        return dict(receipt, image=runtime.IMAGES['console'], probe_sha256=capture.digest(probe))
    finally:
        inspected = subprocess.run(['docker', 'inspect', name], capture_output=True, timeout=10)
        if inspected.returncode == 0:
            remaining = json.loads(inspected.stdout)
            require(len(remaining) == 1 and remaining[0]['Config']['Labels'].get(LABEL) == name and
                    remaining[0]['Image'] == runtime.IMAGES['console'], 'CLEANUP_OWNERSHIP')
            removed = subprocess.run(['docker', 'rm', '-f', remaining[0]['Id']], capture_output=True, timeout=10)
            require(removed.returncode == 0, 'CLEANUP_REFUSED')
