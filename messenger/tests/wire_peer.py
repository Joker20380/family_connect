"""Synthetic loopback-only peer for a two-process RNS/LXMF acceptance test."""
import json
import os
from pathlib import Path
import sys

import LXMF
import RNS
from messenger.chat import Chat
from messenger.store import Store

role, directory, port = sys.argv[1:]
root=Path(directory);root.mkdir(mode=0o700)
config=root/'rns';config.mkdir(mode=0o700)
interface=(f'type = TCPServerInterface\nlisten_ip = 127.0.0.1\nlisten_port = {port}' if role=='server'
           else f'type = TCPClientInterface\ntarget_host = 127.0.0.1\ntarget_port = {port}')
(config/'config').write_text('[reticulum]\nshare_instance = No\nenable_transport = No\n[logging]\nloglevel = 0\n[interfaces]\n[[loopback]]\nenabled = Yes\n'+interface+'\n')
RNS.Reticulum(configdir=str(config),loglevel=0)
store=Store(root/'chat',os.urandom(32)) # Ephemeral synthetic key, never a user store.
chat=Chat(store)
router=LXMF.LXMRouter(storagepath=str(root/'router'),autopeer=False,delivery_limit=8)
source=chat.attach(router)
def emit(value):print(json.dumps(value),flush=True)
emit(dict(public=chat.public.hex()))
for line in sys.stdin:
    request=json.loads(line)
    if request['op']=='trust':
        chat.trust_contact(bytes.fromhex(request['public']));emit(True)
    elif request['op']=='announce':source.announce();emit(True)
    elif request['op']=='send':
        peer=bytes.fromhex(request['peer'])
        ident=chat.queue(peer,request['text']);chat.send(router,source,ident);emit(ident)
    elif request['op']=='messages':
        emit([{k:m[k] for k in ('id','text','status','outgoing')} for m in store.messages()])
