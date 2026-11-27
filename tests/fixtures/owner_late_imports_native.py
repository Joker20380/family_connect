"""Read-model replay on exact installed images using disposable PostgreSQL, no product mounts."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

CONSOLE = 'sha256:3af9fbf95b36b33f1c0414ac41b84687f502391e311ff0bc35658cbf50da5cb1'
POSTGRES = 'sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73'


def command(arguments, **options):
    return subprocess.run(['docker', *arguments], capture_output=True, timeout=options.pop('timeout', 30),
                          check=True, **options)


def main(output):
    root = Path(output)
    root.mkdir(mode=0o700, exist_ok=False)
    os.umask(0o077)
    repository = Path(__file__).resolve().parents[2]
    test = repository / 'control_plane/tests/test_capture_late_imports.py'
    operation = secrets.token_hex(16)
    database, console = 'fc-ha02-late-pg-' + operation, 'fc-ha02-late-console-' + operation
    label = 'family-connect.causal-lab=' + operation
    shared = ['--network', 'none', '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--label', label]
    containers = []
    try:
        command(['run', '-d', '--name', database, *shared, '--user', '70:70',
            '--tmpfs', '/var/lib/postgresql/data:rw,uid=70,gid=70,mode=700',
            '--tmpfs', '/var/run/postgresql:rw,uid=70,gid=70,mode=775',
            '--tmpfs', '/tmp:rw,uid=70,gid=70,mode=700',
            '-e', 'POSTGRES_USER=fc_control_plane', '-e', 'POSTGRES_DB=fc_control_plane',
            '-e', 'POSTGRES_PASSWORD=synthetic-capture-lab-not-a-secret', POSTGRES])
        containers.append(database)
        deadline = time.monotonic() + 30
        while True:
            ready = subprocess.run(['docker', 'exec', database, 'pg_isready', '-U', 'fc_control_plane'],
                                   capture_output=True, timeout=5)
            if ready.returncode == 0:
                break
            assert time.monotonic() < deadline, 'ISOLATED_POSTGRES_NOT_READY'
            time.sleep(.2)
        setup = '''import json,pathlib,hashlib,sys
from control.capture_gate import initialize
initialize('/run/family-connect-capture')
from fc_control_plane.capture import operation
import pytest
with operation():
    result=pytest.main(['-q','-p','no:cacheprovider','--basetemp=/tmp/fixture',
        'tests/test_capture_late_imports.py'])
sources={str(item.relative_to(pathlib.Path('/app/control_plane'))):hashlib.sha256(item.read_bytes()).hexdigest()
    for item in [pathlib.Path('/app/control_plane/apps/console')/name for name in
        ('inventory.py','probe_inventory.py','subscriptions.py','technical_metadata.py','observability_models.py')]}
print('NATIVE_LOADED_SOURCES='+json.dumps(sources,sort_keys=True))
sys.exit(result)
'''
        arguments = ['create', '--name', console, '--network', 'container:' + database, '--read-only',
            '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--label', label,
            '--tmpfs', '/tmp:rw,uid=10001,gid=10001,mode=700', '--tmpfs', '/run:rw,uid=10001,gid=10001,mode=700',
            '--tmpfs', '/app/control_plane/.local:rw,uid=10001,gid=10001,mode=700',
            '--mount', 'type=bind,source=' + str(test) + ',destination=/app/control_plane/tests/test_capture_late_imports.py,readonly',
            '-e', 'CONTROL_PLANE_MODE=synthetic', '-e', 'DJANGO_SECRET_KEY=synthetic-capture-lab-secret-used-only-in-isolated-fixture-20261127',
            '-e', 'POSTGRES_PASSWORD=synthetic-capture-lab-not-a-secret', '-e', 'POSTGRES_HOST=127.0.0.1',
            '--entrypoint', 'python', CONSOLE, '-B', '-c', setup]
        command(arguments)
        containers.append(console)
        inspected = json.loads(command(['inspect', database, console]).stdout)
        for item in inspected:
            assert item['Config']['Labels']['family-connect.causal-lab'] == operation
            assert not item['HostConfig']['Privileged'] and item['HostConfig']['ReadonlyRootfs']
            assert item['HostConfig']['CapDrop'] == ['ALL'] and not item['HostConfig']['PortBindings']
            assert all(mount['Type'] == 'tmpfs' or
                       mount['Type'] == 'bind' and mount['Source'] == str(test) and not mount['RW']
                       for mount in item['Mounts']), 'UNEXPECTED_MOUNT'
        execution = subprocess.run(['docker', 'start', '-a', console], capture_output=True, timeout=100)
        (root / 'stdout.log').write_bytes(execution.stdout)
        (root / 'stderr.log').write_bytes(execution.stderr)
        assert execution.returncode == 0, 'ISOLATED_CONSOLE_TEST_FAILED'
        final = json.loads(command(['inspect', console]).stdout)[0]
        assert final['State']['Status'] == 'exited' and final['State']['ExitCode'] == 0
        assert b'6 passed' in execution.stdout, 'INCOMPLETE_NATIVE_CHECKS'
        loaded = execution.stdout.split(b'NATIVE_LOADED_SOURCES=', 1)[1].splitlines()[0]
        sources = json.loads(loaded)
        assert all(hashlib.sha256((repository / 'control_plane' / name).read_bytes()).hexdigest() == digest
                   for name, digest in sources.items()), 'BUSINESS_SOURCE_DIFFERENCE'
        result = dict(result='PINNED_IMAGE_READ_MODEL_LATE_REPLAY_PASS', operation=operation,
            console_image=CONSOLE, postgres_image=POSTGRES, tests=6, sources=sources,
            test_sha256=hashlib.sha256(test.read_bytes()).hexdigest(), product_mounts=0,
            production_epoch_fenced=False, capture_permitted=False)
        (root / 'result.json').write_text(json.dumps(result, sort_keys=True))
        print(json.dumps(result, sort_keys=True))
    finally:
        for name in reversed(containers):
            try:
                item = json.loads(command(['inspect', name]).stdout)[0]
                assert item['Config']['Labels']['family-connect.causal-lab'] == operation
                (root / (name + '.inspect.json')).write_text(json.dumps(item, sort_keys=True))
                logs = subprocess.run(['docker', 'logs', name], capture_output=True, timeout=5)
                (root / (name + '.stdout')).write_bytes(logs.stdout)
                (root / (name + '.stderr')).write_bytes(logs.stderr)
                if item['State']['Running']:
                    command(['stop', '--timeout', '10', name], timeout=20)
                command(['rm', name])
            except Exception as error:
                print('OWN_LAB_CLEANUP_FAILED', name, type(error).__name__, file=sys.stderr)
                raise


if __name__ == '__main__':
    main(sys.argv[1])
