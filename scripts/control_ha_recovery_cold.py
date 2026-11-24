"""Run the recovery kit in a retained image rootfs, offline and without host source."""
import os
from pathlib import Path
import stat
import subprocess

from scripts import control_ha_recovery_kit as kit

CUSTODY_FILES = tuple(role + suffix for role in ('stores', 'RU', 'node-RU', 'node-NL1', 'node-NL2', 'worker', 'mailbox')
                     for suffix in ('.aesgcm', '.key', '.checkpoint.json'))
SHELL = '''set -eu
umask 077
/usr/local/bin/python -I /kit-bootstrap.py /kit.tar /kit-checkpoint.json /work/restored > /work/restore.json
/usr/local/bin/python -I -m venv /work/venv
/work/venv/bin/python -I -m pip --isolated --disable-pip-version-check install --no-cache-dir --no-index --find-links /work/restored/wheels --require-hashes --only-binary=:all: -r /work/restored/requirements-hashed.txt > /work/install.log 2>&1
/work/venv/bin/python -I -m pip --isolated --disable-pip-version-check check > /work/check.log 2>&1
mkdir -m 700 /work/probes
PYTHONPATH=/work/restored/source /work/venv/bin/python -B -m scripts.control_ha_recovery_probe /custody /work/probes
'''


def command(rootfs, work, archive, checkpoint, bootstrap, custody):
    return ['/usr/bin/bwrap', '--unshare-all', '--die-with-parent', '--new-session', '--clearenv',
        '--cap-drop', 'ALL', '--ro-bind', str(rootfs), '/', '--tmpfs', '/app', '--tmpfs', '/tmp',
        '--bind', str(work), '/work', '--ro-bind', str(archive), '/kit.tar',
        '--ro-bind', str(checkpoint), '/kit-checkpoint.json', '--ro-bind', str(bootstrap), '/kit-bootstrap.py',
        '--ro-bind', str(custody), '/custody', '--proc', '/proc', '--dev', '/dev',
        '--setenv', 'PATH', '/usr/local/bin:/usr/bin:/bin', '--setenv', 'HOME', '/work',
        '--setenv', 'LC_ALL', 'C', '--setenv', 'PYTHONDONTWRITEBYTECODE', '1',
        '--chdir', '/work', '/bin/sh', '-c', SHELL]


def private_input(path):
    info = path.lstat()
    kit.require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1 and
                stat.S_IMODE(info.st_mode) == 0o600, 'PRIVATE_INPUT')


def qualify(rootfs, work, archive, checkpoint, bootstrap, custody):
    paths = [Path(value) for value in (rootfs, work, archive, checkpoint, bootstrap, custody)]
    kit.require(os.getuid() != 0 and all(path.is_absolute() and '..' not in path.parts and
        not any(parent.is_symlink() for parent in (path, *path.parents)) for path in paths), 'COLD_PATH')
    rootfs, work, archive, checkpoint, bootstrap, custody = paths
    kit.require(rootfs.name == 'rootfs' and (rootfs / 'usr/local/bin/python3.13').is_file(), 'RETAINED_PYTHON_IMAGE')
    kit.require({path.name for path in custody.iterdir()} == set(CUSTODY_FILES), 'CUSTODY_SCOPE')
    for path in [archive, checkpoint, bootstrap, *(custody / name for name in CUSTODY_FILES)]:
        private_input(path)
    pins = kit.document(checkpoint.read_bytes())
    kit.require(kit.digest(bootstrap.read_bytes()) == pins['bootstrap_sha256'], 'BOOTSTRAP_PIN')
    kit.verify(archive.read_bytes(), pins)
    work.mkdir(mode=0o700)
    try:
        result = subprocess.run(command(*paths), env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'},
                                capture_output=True, timeout=240)
    except subprocess.TimeoutExpired:
        raise ValueError('COLD_DEADLINE') from None
    kit.private_file(work / 'execution.log', result.stdout + result.stderr)
    kit.require(result.returncode == 0, 'COLD_EXECUTION_REFUSED')
    receipt = kit.document(result.stdout)
    kit.require(receipt['result'] == 'COLD_RECOVERY_SOURCE_DEPENDENCIES_PASS' and receipt['dispatch_calls'] == 0 and
                receipt['activation'] is False and receipt['full_recovery'] is False, 'COLD_RECEIPT')
    receipt.update(source_commit=pins['source_commit'], kit_sha256=pins['archive_sha256'],
                   network='unshared', docker_used=False)
    kit.private_file(work / 'receipt.json', kit.encoded(receipt))
    return receipt
