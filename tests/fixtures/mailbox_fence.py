"""Isolated native mailbox; a disposable controller is not the admission owner."""
import json
import os
from pathlib import Path
import socket
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import RNS
from messenger.codec import address, PUT_PATH
from messenger.relay import ClosedRelay, Spool
from scripts import control_ha_legacy_support as admission
from scripts.control_ha_mailbox_fence import SupportFence


root = Path(sys.argv[1])
os.umask(0o077)
runtime = root / 'runtime'
runtime.mkdir()
(runtime / 'config').write_text('[reticulum]\nshare_instance = No\nenable_transport = No\n'
                               '[logging]\nloglevel = -1\n[interfaces]\n')
rns = RNS.Reticulum(configdir=str(runtime), loglevel=-1)
support, peer = RNS.Identity(), RNS.Identity()
spool = Spool(root / 'spool')
relay = ClosedRelay(RNS.Identity(), spool, allowed_public=[support.get_public_key(), peer.get_public_key()])
fence = SupportFence(relay, support.get_public_key(), 'a' * 64, admission.binding(os.getpid()))
try:
    with socket.socket(socket.AF_UNIX) as server:
        server.bind(str(root / 'control.sock'))
        server.listen()
        server.settimeout(15)
        (root / 'ready').touch()
        while True:
            with server.accept()[0] as client:
                client.settimeout(4)
                command = json.loads(client.makefile('rb').readline(4096))
                action = command['action']
                try:
                    if action == 'hold':
                        fence.install()
                        result = fence.drain(1)
                    elif action == 'status':
                        result = fence.observe()
                    elif action == 'abort':
                        result = dict(restored=fence.abort(command['generation']))
                    elif action in ('put-support', 'put-peer'):
                        sender, recipient = (support, peer) if action == 'put-support' else (peer, support)
                        blob = address(recipient.get_public_key()) + os.urandom(160)
                        result = relay.respond(PUT_PATH, blob, None, sender, 0)[:1]
                    elif action == 'stop':
                        result = spool.stats()
                        result.pop('bytes')
                    else:
                        raise ValueError('UNKNOWN_ACTION')
                except ValueError as error:
                    result = dict(error=str(error))
                client.sendall(json.dumps(result).encode() + b'\n')
                if action == 'stop':
                    break
finally:
    if fence.phase in ('HELD', 'ABORTING'):
        assert fence.abort('a' * 64)
    spool.close()
    RNS.Reticulum.exit_handler()
