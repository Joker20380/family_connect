"""Disposable image probe; no product mounts, network, database or service startup."""
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from control.capture_gate import initialize
from fc_control_plane import capture


def invoke(arguments, environment):
    return subprocess.run([sys.executable, '-B', '/app/control_plane/manage.py', *arguments],
                          env=environment, capture_output=True, timeout=10)


environment = dict(os.environ)
environment.pop('FC_CONTROL_CAPTURE_GATE', None)
assert Path(capture.__file__) == Path('/app/control_plane/fc_control_plane/capture.py')
with tempfile.TemporaryDirectory(prefix='prepared-owner-') as directory:
    gate = initialize(Path(directory) / 'gate')
    gated = dict(environment, FC_CONTROL_CAPTURE_GATE=str(gate.directory))
    commands = ('migrate', 'collectstatic', 'seed_demo', 'publish_system_messages', 'shell')
    with gate.drain(.1):
        for command in commands:
            result = invoke([command, '--help'], gated)
            assert result.returncode == 75 and result.stderr == b'CAPTURE_BUSY\n' and not result.stdout
    missing = invoke(['--help'], dict(environment, FC_CONTROL_CAPTURE_GATE=directory + '/absent'))
    assert missing.returncode == 1 and missing.stderr == b'CAPTURE_UNAVAILABLE\n' and not missing.stdout
    for settings in (environment, gated):
        result = invoke(['--help'], settings)
        assert result.returncode == 0 and b'Available subcommands:' in result.stdout
    assert not list((gate.directory / 'pending').iterdir())

sources = (
    'control/capture_gate.py', 'control_plane/manage.py',
    'control_plane/fc_control_plane/capture.py', 'control_plane/fc_control_plane/middleware.py',
    'control_plane/fc_control_plane/db_backend/__init__.py', 'control_plane/fc_control_plane/db_backend/base.py',
    'control_plane/fc_control_plane/settings.py', 'control_plane/fc_control_plane/wsgi.py',
    'control_plane/apps/console/backend.py', 'control_plane/apps/console/support.py',
    'control_plane/apps/console/system_publisher.py',
    'control_plane/apps/console/management/commands/publish_system_messages.py',
)
packages = ('asgiref', 'cffi', 'cryptography', 'django', 'gunicorn', 'iniconfig', 'packaging',
            'pluggy', 'psycopg', 'psycopg-binary', 'pycparser', 'pygments', 'pyserial',
            'pytest', 'pytest-django', 'rns', 'sqlparse', 'whitenoise')
print(json.dumps(dict(uid=os.geteuid(), gid=os.getegid(), closed_commands=list(commands),
    missing_gate_refused=True, unconfigured_help=True, admitted_help=True, pending=0,
    python=sys.version.split()[0], sources={name: hashlib.sha256((Path('/app') / name).read_bytes()).hexdigest()
                                         for name in sources},
    packages={name: version(name) for name in packages}), sort_keys=True))
