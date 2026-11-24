"""Cold OWNER dependency checks from restored blobs; no Docker, host source or service start."""
import json
import os
from pathlib import Path
import resource
import subprocess
import sys

try:
    from . import control_ha_owner_images as images
except ImportError:
    import control_ha_owner_images as images

PYTHON_PROBE = '''import ctypes.util,json,os,sqlite3,sys
assert os.getuid()!=0
blocked=[]
def audit(event,args):
    if event.startswith(('socket.connect','socket.getaddrinfo','subprocess.','os.exec','os.spawn')) or event=='os.system':
        blocked.append(event)
        raise RuntimeError('DISPATCH_FORBIDDEN')
sys.addaudithook(audit)
ctypes.util.find_library=lambda name:'libc.so.6' if name=='c' else None
os.environ.update(DJANGO_SETTINGS_MODULE='fc_control_plane.settings',CONTROL_PLANE_MODE='synthetic',
    DJANGO_SECRET_KEY='offline-image-probe-not-production',POSTGRES_PASSWORD='offline-not-production',FC_SUPPORT_SOCKET='')
import django
django.setup()
from apps.console import subscriptions,system_publisher
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import psycopg
signer=Ed25519PrivateKey.generate();message=b'offline-dependency-only'
signer.public_key().verify(signer.sign(message),message)
with sqlite3.connect(':memory:') as database:
    assert database.execute('SELECT 7').fetchone()==(7,)
assert callable(subscriptions.ingest) and system_publisher.Publisher and not blocked
print(json.dumps(dict(result='PYTHON_DEPENDENCIES_PASS',python=sys.version.split()[0],django=django.get_version(),
    psycopg=psycopg.__version__,libpq=psycopg.pq.version(),dispatch_calls=len(blocked),activation=False)))
'''
POSTGRES_PROBE = '''set -eu
export PGHOST=/tmp/fc-work PGUSER=recovery PGDATABASE=postgres
initdb -D /tmp/fc-work/db -U recovery --auth=trust --no-locale > /tmp/fc-work/init.log
start() { pg_ctl -D /tmp/fc-work/db -l /tmp/fc-work/postgres.log -o "-c listen_addresses='' -c unix_socket_directories='/tmp/fc-work' -c fsync=on -c full_page_writes=on -c synchronous_commit=on" -w start > /tmp/fc-work/start.log; }
stop() { pg_ctl -D /tmp/fc-work/db -m fast -w stop > /tmp/fc-work/stop.log; }
start
trap stop EXIT
psql -v ON_ERROR_STOP=1 -c 'CREATE TABLE cold_dependency(value integer PRIMARY KEY); INSERT INTO cold_dependency VALUES(7);' > /tmp/fc-work/sql.log
pg_dump --format=custom > /tmp/fc-work/database.dump
stop
start
test "$(psql -Atc 'SELECT value FROM cold_dependency')" = 7
createdb restored
pg_restore --exit-on-error --single-transaction -d restored /tmp/fc-work/database.dump
test "$(psql -d restored -Atc 'SELECT value FROM cold_dependency')" = 7
printf 'POSTGRES_COLD_RESTORE_PASS\\n'
postgres --version
'''


def limits():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (180, 180))
    resource.setrlimit(resource.RLIMIT_NOFILE, (512, 512))


def run(arguments, root, name, timeout=240):
    try:
        result = subprocess.run(arguments, capture_output=True, timeout=timeout, preexec_fn=limits,
                                env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'})
    except subprocess.TimeoutExpired:
        raise ValueError('COLD_BOOTSTRAP_DEADLINE') from None
    images.private_file(root / (name + '.log'), result.stdout + result.stderr)
    images.require(result.returncode == 0, 'COLD_BOOTSTRAP_REFUSED_' + name)
    return result.stdout


def namespace():
    return ['/usr/bin/bwrap', '--unshare-all', '--die-with-parent', '--new-session', '--clearenv',
            '--cap-drop', 'ALL']


def extract_command(binary, layout, bundle, empty_etc):
    return namespace() + ['--ro-bind', '/usr', '/usr', '--symlink', 'usr/lib', '/lib', '--symlink', 'usr/lib64', '/lib64',
        '--symlink', 'usr/bin', '/bin', '--ro-bind', str(empty_etc), '/etc', '--ro-bind', str(binary), '/umoci',
        '--ro-bind', str(layout), '/oci', '--bind', str(bundle), '/bundle', '--tmpfs', '/tmp', '--proc', '/proc',
        '--dev', '/dev', '--setenv', 'PATH', '/usr/bin:/bin', '/umoci', 'unpack', '--rootless', '--image', '/oci:ha-offline', '/bundle/image']


def native_command(rootfs, work, role, identity):
    images.require(role in images.IMAGES, 'COLD_ROLE')
    command = namespace() + ['--ro-bind', str(rootfs), '/', '--tmpfs', '/tmp', '--bind', str(work), '/tmp/fc-work',
        '--ro-bind', str(identity), '/etc/passwd', '--proc', '/proc', '--dev', '/dev', '--setenv', 'PATH', '/usr/local/bin:/usr/bin:/bin',
        '--setenv', 'HOME', '/tmp/fc-work', '--setenv', 'LC_ALL', 'C']
    if role == 'postgres':
        return command + ['--chdir', '/tmp/fc-work', '/bin/sh', '-c', POSTGRES_PROBE]
    return command + ['--setenv', 'PYTHONDONTWRITEBYTECODE', '1', '--setenv', 'PYTHONPATH', '/app:/app/control_plane',
        '--chdir', '/app/control_plane', '/usr/local/bin/python', '-B', '-c', PYTHON_PROBE]


def bootstrap(source, destination):
    source, destination = Path(source), Path(destination)
    images.require(os.getuid() != 0 and source.is_absolute() and destination.is_absolute() and
        '..' not in source.parts and '..' not in destination.parts and
        not any(parent.is_symlink() for base in (source, destination) for parent in (base, *base.parents)), 'COLD_PATH')
    for name, _ in images.FRAMES:
        info = (source / name).lstat()
        images.require((source / name).is_file() and not (source / name).is_symlink() and
                       info.st_uid == os.getuid() and info.st_nlink == 1 and info.st_mode & 0o077 == 0, 'PRIVATE_COLD_INPUT')
    files = {name: (source / name).read_bytes() for name, _ in images.FRAMES}
    images.require(images.digest(files['umoci.deb']) == images.TOOL_SHA, 'TOOL_PACKAGE_PIN')
    checked = images.validate(files['docker-save.tar'])
    destination.mkdir(mode=0o700)
    tool = destination / 'tool'
    run(['/usr/bin/dpkg-deb', '-x', str(source / 'umoci.deb'), str(tool)], destination, 'unpack-tool')
    binary = tool / 'usr/bin/umoci'
    images.require(images.digest(binary.read_bytes()) == images.TOOL_BINARY_SHA, 'TOOL_BINARY_PIN')
    empty_etc = destination / 'empty-etc'
    empty_etc.mkdir(mode=0o700)
    for name in ('resolv.conf', 'hosts', 'hostname'):
        images.private_file(empty_etc / name, b'')
    identity = destination / 'synthetic-passwd'
    images.private_file(identity, f'recovery:x:{os.getuid()}:{os.getgid()}:offline probe:/tmp/fc-work:/bin/sh\n'.encode())
    receipts = {}
    for role, value in checked['roles'].items():
        role_root = destination / role
        role_root.mkdir(mode=0o700)
        layout, bundle, work = (role_root / name for name in ('oci', 'bundle', 'work'))
        for folder in (layout, bundle, work):
            folder.mkdir(mode=0o700)
        (layout / 'blobs/sha256').mkdir(parents=True, mode=0o700)
        manifest = value['manifest']
        normalized = dict(schemaVersion=2, mediaType=images.OCI_MANIFEST,
            config=manifest['config'] | {'mediaType': images.OCI_CONFIG},
            layers=[layer | {'mediaType': images.OCI_LAYER if layer['mediaType'] == images.OCI_LAYER else images.OCI_LAYER + '+gzip'} for layer in manifest['layers']])
        for item in [manifest['config'], *manifest['layers']]:
            name = images.blob_name(item['digest'])
            if not (layout / name).exists():
                images.private_file(layout / name, checked['blobs'][name])
        normalized_raw = images.encoded(normalized)
        selected = dict(mediaType=images.OCI_MANIFEST, digest='sha256:' + images.digest(normalized_raw), size=len(normalized_raw),
                        annotations={'org.opencontainers.image.ref.name': 'ha-offline'})
        normalized_path = layout / images.blob_name(selected['digest'])
        if not normalized_path.exists():
            images.private_file(normalized_path, normalized_raw)
        images.private_file(layout / 'index.json', images.encoded(dict(schemaVersion=2, manifests=[selected])))
        images.private_file(layout / 'oci-layout', images.encoded(dict(imageLayoutVersion='1.0.0')))
        run(extract_command(binary, layout, bundle, empty_etc), role_root, 'unpack-image')
        output = run(native_command(bundle / 'image/rootfs', work, role, identity), role_root, 'native-probe')
        if role == 'postgres':
            lines = output.decode().splitlines()
            images.require(len(lines) == 2 and lines[0] == 'POSTGRES_COLD_RESTORE_PASS' and
                           lines[1].startswith('postgres (PostgreSQL) '), 'POSTGRES_COLD_RECEIPT')
            receipts[role] = dict(result=lines[0], version=lines[1], synthetic_rows=1, activation=False)
        else:
            receipt = images.document(output)
            images.require(receipt['result'] == 'PYTHON_DEPENDENCIES_PASS' and receipt['dispatch_calls'] == 0 and
                           receipt['activation'] is False, 'PYTHON_COLD_RECEIPT')
            receipts[role] = receipt
    result = dict(result='OWNER_IMAGE_COLD_BOOTSTRAP_PASS', archive=checked['summary'], probes=receipts,
                  docker_used=False, source_repository_mounted=False, original_state_mounted=False, network='unshared',
                  production_entrypoints_executed=False, activation=False, full_recovery=False)
    images.private_file(destination / 'receipt.json', images.encoded(result))
    return result


if __name__ == '__main__':
    try:
        images.require(len(sys.argv) == 3, 'COLD_ARGUMENTS')
        print(json.dumps(bootstrap(*sys.argv[1:]), sort_keys=True))
    except Exception as error:
        print(json.dumps(dict(result='COLD_BOOTSTRAP_REFUSED', error=type(error).__name__)), file=sys.stderr)
        raise SystemExit(1) from None
