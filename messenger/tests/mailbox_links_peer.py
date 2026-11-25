"""Loopback-only, synthetic identities: authenticated native RNS lineage qualification."""
import json
import os
from pathlib import Path
import sys
import threading
import time

import RNS
from LXMF.LXMPeer import LXMPeer

from messenger.codec import identity
from messenger.relay import ClosedRelay, PUT_PATH, Spool
from scripts import control_ha_legacy_support as admission
from scripts.control_ha_mailbox_links import SupportLinkFence


def wait_for(predicate, seconds=8):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.02)
    raise TimeoutError('SYNTHETIC_WIRE_DEADLINE')


def emit(value):
    print(json.dumps(value, default=lambda value: value.hex() if isinstance(value, bytes) else None), flush=True)


role, directory, port, allowfile = sys.argv[1:]
os.umask(0o077)
root = Path(directory)
root.mkdir(mode=0o700, exist_ok=True)
config = root / 'rns'
config.mkdir(mode=0o700, exist_ok=True)
interface = (f'type = TCPServerInterface\nlisten_ip = 127.0.0.1\nlisten_port = {port}' if role == 'node' else
             f'type = TCPClientInterface\ntarget_host = 127.0.0.1\ntarget_port = {port}')
(config / 'config').write_text('[reticulum]\nshare_instance = No\nenable_transport = No\n'
                             '[logging]\nloglevel = 0\n[interfaces]\n[[loopback]]\nenabled = Yes\n' + interface + '\n')
RNS.Reticulum(configdir=str(config), loglevel=0)
keyfile = root / 'synthetic.identity'
local = RNS.Identity.from_file(str(keyfile)) if keyfile.exists() else RNS.Identity()
if not keyfile.exists():
    local.to_file(str(keyfile))
links = {}
fence = None
entered, release = threading.Event(), threading.Event()
pause_next = False
original_log = RNS.log


def pause_dispatch(message, *arguments, **keywords):
    global pause_next
    if pause_next and str(message).startswith('Handling request '):
        pause_next = False
        entered.set()
        if not release.wait(30):
            raise TimeoutError('SYNTHETIC_PAUSE_DEADLINE')
    return original_log(message, *arguments, **keywords)


if role == 'node':
    spool = Spool(root / 'spool')
    relay = ClosedRelay(local, spool, allowed_public=[bytes.fromhex(value) for value in json.loads(Path(allowfile).read_text())])
    RNS.log = pause_dispatch
emit(dict(public=local.get_public_key().hex()))
for line in sys.stdin:
    request = json.loads(line)
    operation = request['op']
    try:
        if operation == 'announce':
            relay.destination.announce()
            result = True
        elif operation == 'stats':
            result = spool.stats()
        elif operation == 'hold':
            fence = SupportLinkFence(relay, bytes.fromhex(request['public']), request['generation'],
                                     admission.binding(os.getpid())).install()
            result = fence.observe()
        elif operation == 'open':
            result = fence.open_after_local_drain(request['generation'])
        elif operation == 'observe':
            result = fence.observe()
        elif operation == 'abort':
            result = fence.abort(request['generation'])
        elif operation == 'arm':
            entered.clear()
            release.clear()
            pause_next = True
            result = True
        elif operation == 'paused':
            result = entered.is_set()
        elif operation == 'release':
            release.set()
            result = True
        elif operation == 'connect':
            destination = RNS.Destination(identity(bytes.fromhex(request['public'])), RNS.Destination.OUT,
                                          RNS.Destination.SINGLE, 'lxmf', 'propagation')
            if not RNS.Transport.has_path(destination.hash):
                RNS.Transport.request_path(destination.hash)
            wait_for(lambda: RNS.Transport.has_path(destination.hash))
            link = RNS.Link(destination)
            wait_for(lambda: link.status == RNS.Link.ACTIVE)
            links[request['name']] = link
            if request.get('identify', True):
                link.identify(local)
                time.sleep(.1)
            result = True
        elif operation == 'identify':
            links[request['name']].identify(local)
            time.sleep(.1)
            result = True
        elif operation == 'request':
            response = []
            complete = threading.Event()

            def received(receipt):
                response.append(receipt.response)
                complete.set()

            def failed(receipt):
                response.append(dict(error='WIRE_REQUEST_FAILED'))
                complete.set()

            path = PUT_PATH if 'blob' in request else LXMPeer.MESSAGE_GET_PATH
            data = bytes.fromhex(request['blob']) if 'blob' in request else [None, [bytes.fromhex(value) for value in request['purge']]]
            receipt = links[request['name']].request(path, data=data, response_callback=received,
                                                    failed_callback=failed, timeout=20)
            if receipt is None or not complete.wait(25):
                raise TimeoutError('SYNTHETIC_REQUEST_DEADLINE')
            result = response[0]
        else:
            raise ValueError('UNKNOWN_SYNTHETIC_OPERATION')
        emit(result)
    except Exception as error:
        emit(dict(error=type(error).__name__, reason=str(error)))
