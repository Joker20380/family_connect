"""Fixed bounded archive handoff; privileged execution never accepts a source path."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import pwd
import select
import stat
import subprocess
import sys
import tarfile
import tempfile
import time

MAX_ARCHIVE = 80 * 1024 * 1024
MAX_PAYLOAD = 128 * 1024 * 1024
PREFIX = 'FamilyConnect-MESH-system-amd64/'


def extract_verified(raw, expected, destination):
    sys.dont_write_bytecode = True
    if len(raw) != expected['size'] or len(raw) > MAX_ARCHIVE or hashlib.sha256(raw).hexdigest() != expected['sha256']:
        raise ValueError('Embedded system archive mismatch')
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        if len(names) > 8192 or len(names) != len(set(names)):
            raise ValueError('Invalid system archive inventory')
        total = 0
        for member in members:
            name = member.name
            if (not member.isfile() or not name.startswith(PREFIX) or
                    any(part in ('', '.', '..') for part in name.split('/')) or
                    member.mode & ~0o755 or member.size < 0 or member.size > 64 * 1024 * 1024):
                raise ValueError('Unsafe system archive member')
            total += member.size
            if total > MAX_PAYLOAD:
                raise ValueError('Oversized system payload')
        archive.extractall(destination, filter='data')
    bundle = destination / PREFIX.rstrip('/')
    script = bundle / 'install.py'
    if hashlib.sha256(script.read_bytes()).hexdigest() != expected['installer_sha256']:
        raise ValueError('Unexpected fixed installer')
    spec = importlib.util.spec_from_file_location('verified_system_installer', script)
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    manifest, payload = installer.verify(bundle)
    if manifest['build_id'] != expected['build_id'] or manifest['source_digest'] != expected['source_digest']:
        raise ValueError('Embedded system build mismatch')
    return bundle


def receive(size):
    if type(size) is not int or not 0 < size <= MAX_ARCHIVE:
        raise ValueError('Invalid system payload size')
    deadline = time.monotonic() + 60
    result = bytearray()
    while len(result) <= size:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([0], [], [], remaining)[0]:
            raise ValueError('System setup input timed out')
        block = os.read(0, min(65536, size + 1 - len(result)))
        if not block:
            if len(result) != size:
                raise ValueError('Incomplete system setup input')
            return bytes(result)
        result.extend(block)
    raise ValueError('Unexpected system setup input')


def root_main(expected):
    uid = os.environ.get('PKEXEC_UID', '')
    if (sys.argv[1:] or os.geteuid() != 0 or not uid.isascii() or not uid.isdecimal() or
            str(int(uid)) != uid or not 1 <= int(uid) < 2**31):
        raise ValueError('Explicit non-root pkexec caller required')
    pwd.getpwuid(int(uid))
    sys.dont_write_bytecode = True
    os.umask(0o077)
    raw = receive(expected['size'])
    with tempfile.TemporaryDirectory(prefix='family-connect-root-setup-', dir='/var/tmp') as temporary:
        destination = Path(temporary)
        if destination.stat().st_uid != 0 or stat.S_IMODE(destination.stat().st_mode) != 0o700:
            raise ValueError('Unsafe privileged snapshot')
        bundle = extract_verified(raw, expected, destination)
        result = subprocess.run(['/usr/bin/python3', '-I', '-S', str(bundle / 'install.py')],
                                stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                env={'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LC_ALL': 'C'}, timeout=240)
        if result.returncode:
            raise ValueError('System installation refused: ' + result.stderr[-1500:])
        print(result.stdout.strip(), flush=True)
