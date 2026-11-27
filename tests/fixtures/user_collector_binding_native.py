"""Root-only fresh-process checks in disposable mount and network namespaces."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from control.capture_gate import initialize
from control_plane import collector_binding as binding


def child(directory, fault, entry):
    subprocess.run(['mount', '--bind', str(directory / 'home'), '/home'], check=True)
    subprocess.run(['mount', '--bind', str(directory / 'etc'), '/etc'], check=True)
    application = binding.INSTALLED_APP
    filename = binding.INSTALLED_BINDING
    role = 'probe' if entry == 'probe_network' else 'inventory'
    gate = directory / role
    lock = None
    if fault == 'closed':
        lock = (gate / 'admission.lock').open('rb')
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    elif fault in ('missing-gate', 'replacement-gate'):
        gate.rename(directory / (role + '-retained'))
        if fault == 'replacement-gate':
            initialize(gate)
            for target in [gate, *gate.iterdir()]:
                os.chown(target, 1000, 1000)
    elif fault == 'invalid-gate':
        gate.chmod(0o755)
    elif fault == 'missing-binding':
        filename.unlink()
    elif fault == 'changed-source':
        target = application / 'control_plane/collect_inventory.py'
        target.write_bytes(target.read_bytes() + b'\n')
    elif fault == 'incomplete-source':
        (application / 'control_plane/apps/console/metrics_collector.py').unlink()
    code = '''
import importlib, os, sys
sys.path.insert(0, '/home/joker/PycharmProjects/family_connect')
from control.capture_gate import GateError
from control_plane.collector_binding import operation
def forbidden(*args, **kwargs):
    raise AssertionError('dispatch before admission')
import subprocess
subprocess.run = forbidden
try:
    if sys.argv[1] == 'normal':
        with operation(sys.argv[3]):
            pass
        print('NORMAL_ADMISSION')
    else:
        module = importlib.import_module('control_plane.' + sys.argv[2])
        if sys.argv[2] in ('monitor_inventory', 'probe_network'):
            module.cycle()
        elif sys.argv[2] == 'collect_inventory':
            module.collect(None, None)
        else:
            module.collect()
        raise AssertionError('invalid installation admitted')
except GateError:
    print('REFUSED_BEFORE_IO')
'''
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith('PYTHON') and key != 'FC_CONTROL_CAPTURE_GATE'}
    result = subprocess.run(['/usr/bin/python3', '-I', '-B', '-c', code, fault, entry, role],
                            env=environment, user=1000, group=1000, extra_groups=[],
                            capture_output=True, text=True, cwd='/', timeout=5)
    expected = 'NORMAL_ADMISSION' if fault == 'normal' else 'REFUSED_BEFORE_IO'
    assert result.returncode == 0 and result.stdout.strip() == expected, (fault, entry, result.stderr)
    if lock is not None:
        arguments = ['gateway-ru'] if entry == 'collect_inventory' else []
        result = subprocess.run(['/usr/bin/python3', '-B', str(application / ('control_plane/' + entry + '.py')),
            *arguments], env=environment, user=1000, group=1000, extra_groups=[], cwd='/',
            capture_output=True, text=True, timeout=5)
        assert result.returncode == 75 and result.stderr.strip() == 'CAPTURE_BUSY', (entry, result.stderr)
    assert not (application / 'control_plane/.local').exists()
    print(json.dumps(dict(fault=fault, entry=entry, result='PASS', capture_permitted=False)))


def main():
    assert os.geteuid() == 0
    os.umask(0o022)
    if len(sys.argv) > 1 and sys.argv[1] == '--child':
        child(Path(sys.argv[2]), sys.argv[3], sys.argv[4])
        return
    rows = []
    for fault in ('normal', 'closed', 'missing-gate', 'replacement-gate', 'invalid-gate',
                  'missing-binding', 'changed-source', 'incomplete-source'):
        for entry in ('monitor_inventory', 'collect_inventory', 'collect_technical_metadata', 'probe_network'):
            with tempfile.TemporaryDirectory(prefix='fc-user-collector-qualification-') as temporary:
                directory = Path(temporary)
                directory.chmod(0o755)
                application = directory / binding.INSTALLED_APP.relative_to('/')
                for name in binding.SOURCE_NAMES:
                    target = application / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT / name, target)
                    os.chown(target, 1000, 1000)
                    target.chmod(0o644)
                gates = {role: initialize(directory / role) for role in binding.ROLES}
                for gate in gates.values():
                    for target in [gate.directory, *gate.directory.iterdir()]:
                        os.chown(target, 1000, 1000)
                filename = directory / binding.INSTALLED_BINDING.relative_to('/')
                filename.parent.mkdir(parents=True)
                value = dict(schema=1, baseline=binding.BASELINE, application=str(binding.INSTALLED_APP), uid=1000,
                    sources={name: hashlib.sha256((application / name).read_bytes()).hexdigest() for name in binding.SOURCE_NAMES},
                    gates={role: dict(directory=str(gate.directory), pins=gate.pins) for role, gate in gates.items()})
                filename.write_text(json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n')
                filename.chmod(0o644)
                result = subprocess.run(['unshare', '--mount', '--net', '--propagation', 'private',
                    sys.executable, '-I', '-B', __file__, '--child', temporary, fault, entry],
                    capture_output=True, text=True, timeout=10)
                assert result.returncode == 0, (fault, entry, result.stderr)
                rows.append(json.loads(result.stdout))
    print(json.dumps(dict(cases=rows, count=len(rows), result='PASS', capture_permitted=False), sort_keys=True))


if __name__ == '__main__':
    main()
