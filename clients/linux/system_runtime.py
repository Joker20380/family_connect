"""Isolated packaged interpreter paths and shared installation exclusion."""
import fcntl
import importlib
import json
import os
from pathlib import Path
import runpy
import stat
import sys
import sysconfig

LOCK = '/run/family-connect-system-install.lock'
ENTRIES = {'mesh': 'helper', 'auto': 'auto_service.py',
           'chat-direct': 'chat_direct_host.py', 'chat-mesh': 'mesh_chat_service.py'}


def configure(root=None):
    root = Path(root or Path(__file__).resolve().parent)
    library = sysconfig.get_path('stdlib')
    sys.path[:] = [str(root), str(root / 'vendor'), library,
                   str(Path(library) / 'lib-dynload')]
    sys.dont_write_bytecode = True
    record = json.loads((root / 'python-runtime.json').read_text())
    if record['python'] != list(sys.version_info[:2]):
        raise ValueError('System Python ABI does not match the component')
    return root


def shared_gate():
    descriptor = os.open(LOCK, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1 or
                stat.S_IMODE(info.st_mode) != 0o600):
            raise ValueError('Unsafe system install lock')
        fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def check(root):
    modules = ('backend', 'mesh_service', 'auto_service', 'auto_normal_worker',
               'chat_direct_host', 'mesh_chat_service', 'device_identity.friends',
               'provisioning.support', 'messenger.codec', 'cryptography', 'cffi',
               'pydantic', 'httpx', 'RNS', 'LXMF')
    for name in modules:
        module = importlib.import_module(name)
        if not Path(module.__file__).resolve().is_relative_to(root):
            raise ValueError('Import escaped the packaged runtime: ' + name)
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    from device_identity.device import DeviceIdentity
    from mesh_chat_service import packaged_anchor
    public = Ed25519PrivateKey.generate().public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    if len(public) != 32 or not DeviceIdentity or len(packaged_anchor(root / 'update.pub')) != 44:
        raise ValueError('Runtime crypto/anchor readback failed')
    print(json.dumps(dict(runtime=2, imports='PASS', python=list(sys.version_info[:2]))))


def main():
    root = configure()
    if sys.argv[1:] == ['--check']:
        check(root)
        return
    if len(sys.argv) < 2 or sys.argv[1] not in ENTRIES:
        raise ValueError('Fixed system entrypoint required')
    descriptor = shared_gate()
    try:
        entry = ENTRIES[sys.argv[1]]
        sys.argv = [str(root / entry), *sys.argv[2:]]
        runpy.run_path(str(root / entry), run_name='__main__')
    finally:
        os.close(descriptor)


if __name__ == '__main__':
    main()
