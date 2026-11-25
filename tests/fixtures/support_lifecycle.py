"""Owned synthetic support worker using the real CLI, store, delivery and RNS runtime."""
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from control.capture_gate import initialize
from messenger.mailbox import ExchangeResult, SyncResult
from provisioning import support_worker as worker


root, mode = Path(sys.argv[1]), sys.argv[2]
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
    (root / 'store-closed').touch()


worker.SupportStore.close = close
original_initialize = worker.initialize


def runtime(directory):
    result = original_initialize(directory)
    if mode == 'startup':
        pause('startup-entered')
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
