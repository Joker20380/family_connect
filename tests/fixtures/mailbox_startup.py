"""Disposable restart fixture with persistent synthetic state and real native RNS clients."""
import json
import os
from pathlib import Path
import runpy
import signal
import socket
import sys
import threading
import ctypes

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import RNS

from messenger.codec import address
from messenger.relay import Spool
from scripts.control_ha_mailbox_startup import Startup
from scripts import control_ha_mailbox_startup as bootstrap


root, manifest, allowed, owner_uid = sys.argv[1:]
root, manifest, allowed = Path(root), Path(manifest), Path(allowed)
if os.environ.get('FC_TEST_PTRACER_ANY') == '1':
    assert ctypes.CDLL(None, use_errno=True).prctl(0x59616d61, ctypes.c_ulong(-1), 0, 0, 0) == 0
os.umask(0o077)
startup = Startup(manifest, owner_uid=int(owner_uid), fixture=os.environ.get('FC_TEST_ROOT_HANDOFF') == '1')
bootstrap.ACTIVE = startup
publics = [bytes.fromhex(value) for value in json.loads(allowed.read_text())]
with socket.socket() as reservation:
    reservation.bind(('127.0.0.1', 0))
    port = reservation.getsockname()[1]
config = root / 'rns'
config.mkdir(mode=0o700, exist_ok=True)
(config / 'config').write_text('[reticulum]\nshare_instance = No\nenable_transport = No\n'
                             '[logging]\nloglevel = 0\n[interfaces]\n[[loopback]]\nenabled = Yes\n'
                             f'type = TCPServerInterface\nlisten_ip = 127.0.0.1\nlisten_port = {port}\n')
RNS.Reticulum(configdir=str(config), loglevel=0)
key = root / 'synthetic.identity'
identity = RNS.Identity.from_file(str(key)) if key.exists() else RNS.Identity()
if not key.exists():
    identity.to_file(str(key))
spool = Spool(root / 'spool')
relay = startup.create(identity, spool, allowed_public=publics)
Peer = runpy.run_path(str(Path(__file__).with_name('mailbox_links_system.py')))['Peer']
stopped = threading.Event()
signal.signal(signal.SIGTERM, lambda *_: stopped.set())
signal.signal(signal.SIGINT, lambda *_: stopped.set())
control = root / 'control.sock'
if control.exists():
    control.unlink()
try:
    with socket.socket(socket.AF_UNIX) as listener:
        listener.bind(str(control))
        listener.listen(4)
        listener.settimeout(.2)
        print(json.dumps(dict(event='synthetic-ready', pid=os.getpid())), flush=True)
        while not stopped.is_set():
            try:
                connection, _ = listener.accept()
            except socket.timeout:
                continue
            with connection:
                connection.settimeout(30)
                request = json.loads(connection.makefile('rb').readline(16384))
                try:
                    action = request['action']
                    if action == 'status':
                        result = startup.observe()
                        result.update(count=spool.stats()['count'], uid=os.getuid(), gid=os.getgid(),
                                      manifest_writable=os.access(manifest, os.W_OK))
                    elif action == 'open':
                        result = startup.open_for_qualification(request['path'])
                    elif action in ('support', 'peer'):
                        client = Peer('client', root / action, port, allowed)
                        try:
                            relay.destination.announce()
                            assert client.call('connect', public=identity.get_public_key().hex(), name='link') is True
                            recipient = publics[1] if action == 'support' else publics[0]
                            blob = (address(recipient) + os.urandom(160)).hex()
                            result = client.call('request', name='link', blob=blob)
                            if isinstance(result, list):
                                result = result[:1]
                        finally:
                            client.close()
                    elif action == 'stop':
                        result = dict(count=spool.stats()['count'])
                        stopped.set()
                    else:
                        raise ValueError('UNKNOWN_FIXTURE_ACTION')
                except Exception as error:
                    result = dict(error=type(error).__name__, reason=str(error))
                connection.sendall(json.dumps(result, sort_keys=True).encode() + b'\n')
finally:
    RNS.Reticulum.exit_handler()
    spool.close()
