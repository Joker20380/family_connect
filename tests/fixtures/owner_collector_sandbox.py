"""Root-only disposable systemd sandbox checks; never use the installed collector gate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from control.capture_gate import initialize
from provisioning.owner_capture import INSTALLED_GATE


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def probe(gate, writable):
    code = '''import json,os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from control.capture_gate import Busy
from provisioning import owner_capture
owner_capture.INSTALLED_GATE=Path(sys.argv[2])
try:
    with owner_capture.operation():
        assert len(list((owner_capture.INSTALLED_GATE/'pending').iterdir()))==1
    assert not list((owner_capture.INSTALLED_GATE/'pending').iterdir())
    print(json.dumps(dict(result='ADMITTED_AND_SETTLED')))
except Busy:
    print(json.dumps(dict(result='CLOSED_REFUSAL')))
    raise SystemExit(75)
except OSError as error:
    print(json.dumps(dict(result='FILESYSTEM_REFUSAL',errno=error.errno,
        readonly=bool(os.statvfs(owner_capture.INSTALLED_GATE).f_flag & os.ST_RDONLY))))
    raise SystemExit(78)
'''
    result = subprocess.run(['systemd-run', '--unit=fc-ha-collector-sandbox-' + uuid.uuid4().hex,
        '--wait', '--collect', '--pipe', '-p', 'User=root', '-p', 'ProtectSystem=strict',
        '-p', 'PrivateTmp=yes', '-p', 'NoNewPrivileges=yes', '-p', 'ReadWritePaths=' + str(writable),
        str(Path(sys.executable).resolve()), '-I', '-B', '-c', code, str(ROOT), str(gate)],
        capture_output=True, timeout=15, env={name: value for name, value in os.environ.items()
            if name not in ('FC_OWNER_CAPTURE_GATE', 'PYTHONPATH', 'PYTHONHOME')})
    require(len(result.stdout) < 4096, 'PROBE_OUTPUT_BOUNDS')
    return result.returncode, json.loads(result.stdout)


def run():
    require(os.geteuid() == 0, 'ROOT_REQUIRED')
    require(INSTALLED_GATE == Path('/var/lib/fc-support-bindings/capture-owner-collectors'),
            'INSTALLED_WRITABLE_GATE_CONTRACT')
    os.umask(0o077)
    with tempfile.TemporaryDirectory(prefix='fc-ha-collector-sandbox-', dir='/var/lib') as temporary:
        root = Path(temporary)
        writable = root / 'projection'
        writable.mkdir(mode=0o700)
        outside = initialize(root / 'outside-gate')
        inside = initialize(writable / INSTALLED_GATE.name)
        require(probe(outside.directory, writable) ==
                (78, dict(result='FILESYSTEM_REFUSAL', errno=30, readonly=True)), 'MISSING_WRITE_PATH_NOT_REFUSED')
        require(not list((outside.directory / 'pending').iterdir()), 'REFUSAL_CHANGED_MARKERS')
        require(probe(inside.directory, writable) == (0, dict(result='ADMITTED_AND_SETTLED')),
                'WRITABLE_GATE_NOT_SETTLED')
        with inside.drain(.5):
            require(probe(inside.directory, writable) == (75, dict(result='CLOSED_REFUSAL')),
                    'CLOSED_GATE_ADMITTED')
        require(not list((inside.directory / 'pending').iterdir()), 'CLOSED_REFUSAL_CHANGED_MARKERS')
    return dict(result='OWNER_COLLECTOR_NATIVE_SANDBOX_PASS', cases=3, real_dispatch=False,
        real_units_changed=False, installed_gate_used=False,
        source_sha256=hashlib.sha256((ROOT / 'provisioning/owner_capture.py').read_bytes()).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    arguments = parser.parse_args()
    receipt = run()
    with arguments.output.open('x') as stream:
        os.fchmod(stream.fileno(), 0o600)
        json.dump(receipt, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(receipt, sort_keys=True))
