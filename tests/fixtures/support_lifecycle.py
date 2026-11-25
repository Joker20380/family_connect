"""Owned synthetic support worker using the real CLI, store, delivery and RNS runtime."""
import os
from pathlib import Path
import subprocess
import sys
import time

archive = os.environ.get('FC_TEST_SUPPORT_ARCHIVE')
sys.path.insert(0, archive or str(Path(__file__).resolve().parents[2]))

from control.capture_gate import initialize
from messenger.mailbox import ExchangeResult, SyncResult
from provisioning import support_worker as worker

if archive:
    import json
    import zipfile
    with zipfile.ZipFile(archive) as package:
        packaged = {(name[:-12] if name.endswith('/__init__.py') else name[:-3]).replace('/', '.')
                    for name in json.loads(package.read('source-manifest.json'))}

    def check_imports():
        for name, module in tuple(sys.modules.items()):
            if name in packaged:
                assert module.__file__.startswith(archive + '/'), name

    check_imports()

root, mode = Path(sys.argv[1]), sys.argv[2]
os.umask(0o077)
gate = initialize(root / 'gate')
store = worker.SupportStore(root / 'store', b's' * 32, create=True)
public = store.chat_identity().get_public_key().hex()
store.close()
(root / 'store.key').write_bytes(b's' * 32)
(root / 'store.key').chmod(0o600)


def pause(name):
    (root / name).touch()
    deadline = time.monotonic() + 90
    while not (root / 'release').exists():
        if time.monotonic() > deadline:
            raise TimeoutError('bounded synthetic wait')
        time.sleep(.01)


def commit(store):
    with store._lock, store._db:
        store._put('lifecycle-synthetic', {'completed': True})
    (root / 'committed').touch()


original_close = worker.SupportStore.close


def close(store):
    original_close(store)
    if (root / 'ready').exists() or (root / 'startup-entered').exists():
        import threading
        assert len(threading.enumerate()) == 1
        assert len(list(Path('/proc/self/task').iterdir())) == 1
    (root / 'store-closed').touch()


worker.SupportStore.close = close
original_initialize = worker.initialize


def runtime(directory):
    result = original_initialize(directory)
    if mode == 'startup':
        pause('startup-entered')
    if mode in ('runtime-async', 'runtime-exit-failure'):
        import RNS
        original_replace = os.replace

        def replace(source, target, *args, **kwargs):
            if mode == 'runtime-async' and str(source).endswith((b'd' * 16).hex() + '.out'):
                pause('runtime-writer-entered')
                (root / 'runtime-writer-finished').touch()
            elif mode == 'runtime-exit-failure' and str(target).endswith('/known_destinations'):
                raise OSError('synthetic support runtime exit failure')
            return original_replace(source, target, *args, **kwargs)

        os.replace = replace
        if mode == 'runtime-async':
            RNS.Identity._remember_ratchet(b'd' * 16, b'r' * 32)
    return result


worker.initialize = runtime
worker.SupportMailbox.refresh = lambda self: {'node': {}}


class Transport:
    def __init__(self, chat, *args):
        self.store = chat.store

    def exchange(self, **kwargs):
        if mode.startswith('exchange'):
            code = ('import os,sys,time;from pathlib import Path;root=Path(sys.argv[1]);'
                    '(root/"child-pid").write_text(str(os.getpid()));deadline=time.monotonic()+90\n'
                    'while not (root/"release").exists():\n'
                    ' if time.monotonic()>deadline:raise TimeoutError()\n'
                    ' time.sleep(.01)\n'
                    '(root/"child-finished").touch()')
            subprocess.run([sys.executable, '-I', '-c', code, str(root)], check=True, timeout=92)
            commit(self.store)
            if mode == 'exchange-failure':
                raise OSError('synthetic lost external acknowledgement')
        return ExchangeResult(SyncResult(0, 0, 0, 0), 0, 0, False)

    def close(self):
        pass


worker.SupportTransport = Transport
original_invoke = worker.SupportOwner.invoke


def invoke(owner, request):
    if mode == 'ipc':
        pause('ipc-entered')
        commit(owner.store)
    return original_invoke(owner, request)


worker.SupportOwner.invoke = invoke
original_activate = worker.SupportServer.server_activate


def activate(server):
    original_activate(server)
    (root / 'ready').touch()


worker.SupportServer.server_activate = activate
worker.main(['--store', str(root / 'store'), '--key', str(root / 'store.key'),
             '--sender-public', public, '--snapshot', str(root / 'unused-snapshot'),
             '--runtime', str(root / 'runtime'), '--socket', str(root / 'worker.sock'),
             '--capture-gate', str(root / 'gate'), '--snapshot-uid', str(os.getuid())])
(root / 'finished').touch()
if archive:
    check_imports()
    (root / 'archive-qualified').touch()
