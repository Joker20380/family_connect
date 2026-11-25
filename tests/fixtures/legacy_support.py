"""Synthetic store and IPC around unchanged installed support main/delivery code."""
import ctypes
import json
import os
from pathlib import Path
import runpy
import socket
import subprocess
import sys
import threading
import time
import types

assert ctypes.CDLL(None, use_errno=True).prctl(0x59616d61, ctypes.c_ulong(-1), 0, 0, 0) == 0
root, source, mode, reader_fd = Path(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4])
sys.path.insert(0, source)
from provisioning import support_worker as worker
from messenger.mailbox import ExchangeResult, SyncResult

store = worker.SupportStore(root / 'store', b's' * 32, create=True)
public = store.chat_identity().get_public_key().hex()
store.close()
(root / 'key').write_bytes(b's' * 32)
(root / 'key').chmod(0o600)


def wait(name):
    (root / name).touch()
    deadline = time.monotonic() + 30
    while not (root / 'release').exists():
        if time.monotonic() > deadline:
            raise TimeoutError('synthetic wait')
        time.sleep(.01)


def refresh(mailbox):
    if mode == 'ipc' and threading.current_thread() is threading.main_thread():
        wait('ipc-entered')
    return {'node': {}}


def exchange(mailbox, **kwargs):
    if mode in ('exchange', 'failure', 'child'):
        if mode == 'child':
            code = ('import sys,time;from pathlib import Path;root=Path(sys.argv[1]);'
                    '(root/"exchange-entered").touch();deadline=time.monotonic()+30\n'
                    'while not (root/"release").exists():\n'
                    ' if time.monotonic()>deadline:raise TimeoutError()\n time.sleep(.01)\n'
                    '(root/"child-finished").touch()')
            subprocess.run([sys.executable, '-I', '-c', code, str(root)], check=True, timeout=32)
        else:
            wait('exchange-entered')
        assert not kwargs['cancel'].is_set()
        with mailbox.owner.store._lock, mailbox.owner.store._db:
            mailbox.owner.store._put('bridge-synthetic', {'completed': True})
        (root / 'committed').touch()
        if mode == 'failure':
            raise OSError('synthetic lost acknowledgement')
    if mode == 'reader':
        import RNS
        from RNS.Interfaces.TCPInterface import TCPClientInterface
        interface = TCPClientInterface(RNS.Transport, {'name': 'synthetic'},
                                       connected_socket=socket.socket(fileno=reader_fd))
        interface.target_ip, interface.target_port = interface.socket.getpeername()
        threading.Thread(target=interface.read_loop, name='chat-route', daemon=True).start()
        (root / 'reader-entered').touch()
    return ExchangeResult(SyncResult(0, 0, 0, 0), 0, 0, False)


worker.SupportMailbox.refresh = refresh
worker.SupportMailbox.exchange = exchange
if mode == 'unknown-thread':
    threading.Thread(target=lambda: wait('unknown-entered'), daemon=True).start()
if mode == 'changed-code':
    worker.DeliveryController.update = lambda self, **kwargs: False
if mode == 'orphan-child':
    subprocess.Popen([sys.executable, '-I', '-c', 'import time;time.sleep(30)'])

original_activate = worker.SupportServer.server_activate


def activate(server):
    original_activate(server)
    if mode == 'module-globals':
        worker.main = types.FunctionType(worker.main.__code__, dict(vars(worker)))
    (root / 'ready').touch()


worker.SupportServer.server_activate = activate
sys.argv = ['support', '--store', str(root / 'store'), '--key', str(root / 'key'),
            '--sender-public', public, '--snapshot', str(root / 'unused-snapshot'),
            '--runtime', str(root / 'runtime'), '--socket', str(root / 'worker.sock'),
            '--snapshot-uid', str(os.getuid())]
if mode.startswith('module'):
    def module_entry(frame, event, argument):
        global worker, original_activate
        if event == 'call' and frame.f_code.co_name == 'main' and frame.f_globals.get('__name__') == '__main__':
            sys.settrace(None)
            worker = sys.modules['__main__']
            worker.SupportMailbox.refresh = refresh
            worker.SupportMailbox.exchange = exchange
            original_activate = worker.SupportServer.server_activate
            worker.SupportServer.server_activate = activate
            assert sys.modules['__mp_main__'] is worker
            assert sys.modules['provisioning.support_worker'] is not worker
            if mode == 'module-ambiguous':
                duplicate = types.ModuleType('synthetic-duplicate')
                duplicate.__dict__.update(vars(worker))
                sys.modules['synthetic-duplicate'] = duplicate
            (root / 'module-shape').touch()
        return module_entry
    sys.settrace(module_entry)
    runpy._run_module_as_main('provisioning.support_worker', alter_argv=False)
else:
    worker.main()
(root / 'finished').touch()
