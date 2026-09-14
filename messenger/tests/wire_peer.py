"""Synthetic loopback-only peer for a two-process RNS/LXMF acceptance test."""
import json
import os
from pathlib import Path
import sys
import time
import threading
from dataclasses import asdict
from messenger.mailbox import Mailbox, MailboxError

import LXMF
import RNS
from messenger.chat import Chat
from messenger.store import Store

role, directory, port = sys.argv[1:]
root=Path(directory);root.mkdir(mode=0o700,exist_ok=True)
os.umask(0o077)
config=root/'rns';config.mkdir(mode=0o700,exist_ok=True)
interface=(f'type = TCPServerInterface\nlisten_ip = 127.0.0.1\nlisten_port = {port}' if role in ('server','node')
           else f'type = TCPClientInterface\ntarget_host = 127.0.0.1\ntarget_port = {port}')
(config/'config').write_text('[reticulum]\nshare_instance = No\nenable_transport = No\n[logging]\nloglevel = 0\n[interfaces]\n[[loopback]]\nenabled = Yes\n'+interface+'\n')
RNS.Reticulum(configdir=str(config),loglevel=0)
# Synthetic fixture only: persist test keys so process restarts can be exercised.
# Real applications must supply Store keys from a separate keystore.
keyfile=root/'synthetic.key'
if not keyfile.exists():keyfile.write_bytes(os.urandom(32))
store=Store(root/'chat',keyfile.read_bytes())
chat=Chat(store)
# Exercise real PoW validation with one worker and no process-spawn amplification.
import LXMF.LXStamper as stamper
stamper.job_linux=stamper.job_simple
stamper.job_linux_managed=stamper.job_simple
router=LXMF.LXMRouter(identity=chat.identity,storagepath=str(root/'router'),autopeer=False,
                     delivery_limit=8,propagation_limit=8,propagation_cost=13)
source=chat.attach(router)
if role=='node':
    router.set_authentication(required=True)
    router.set_message_storage_limit(kilobytes=64)
    router.enable_propagation()
sync_result={'state':'idle'}
mailbox=None
write_failure=False
original_add=store.add
def guarded_add(*args,**kwargs):
    if write_failure:raise OSError('synthetic storage failure')
    return original_add(*args,**kwargs)
store.add=guarded_add
def emit(value):print(json.dumps(value),flush=True)
emit(dict(public=chat.public.hex(),node=router.propagation_destination.hash.hex()))
for line in sys.stdin:
    request=json.loads(line)
    if request['op']=='trust':
        chat.trust_contact(bytes.fromhex(request['public']));emit(True)
    elif request['op']=='announce':
        if role=='node':router.propagation_destination.announce(app_data=router.get_propagation_node_app_data())
        else:source.announce()
        emit(True)
    elif request['op']=='send':
        peer=bytes.fromhex(request['peer'])
        ident=chat.queue(peer,request['text']);chat.send(router,source,ident,via_relay=request.get('via_relay',False));emit(ident)
    elif request['op']=='messages':
        emit([{k:m[k] for k in ('id','text','status','outgoing')} for m in store.messages()])
    elif request['op']=='relay':
        router.set_outbound_propagation_node(bytes.fromhex(request['node']))
        if 'public' in request:mailbox=Mailbox(chat,source,bytes.fromhex(request['public']))
        emit(True)
    elif request['op']=='fetch':
        sync_result={'state':'running'}
        delete=request.get('delete',False)
        def fetch(delete):
            global sync_result
            try:sync_result=dict(state='complete',**asdict(mailbox.sync(delete_after_store=delete)))
            except MailboxError as error:sync_result={'state':str(error)}
            except OSError:sync_result={'state':'storage_error'}
            except Exception as error:sync_result={'state':'internal_error','error':type(error).__name__}
        threading.Thread(target=fetch,args=(delete,),daemon=True).start();emit(True)
    elif request['op']=='sync':
        emit(dict(sync_result,complete='complete',denied='access_denied'))
    elif request['op']=='fail_writes':
        write_failure=request['enabled'];emit(True)
    elif request['op']=='allow':
        from messenger.codec import identity
        router.allow(identity(bytes.fromhex(request['public'])).hash);emit(True)
    elif request['op']=='stats':
        emit(dict(count=len(router.propagation_entries),bytes=router.message_storage_size()))
    elif request['op']=='clean_quota':
        router.set_message_storage_limit(kilobytes=request['kilobytes'])
        router.clean_message_store();emit(True)
    elif request['op']=='expire':
        # Age only synthetic filenames, then run the unchanged upstream cleaner.
        for entry in router.propagation_entries.values():
            path=Path(entry[1]);parts=path.name.split('_')
            parts[1]=str(time.time()-LXMF.LXMRouter.MESSAGE_EXPIRY-10)
            aged=path.with_name('_'.join(parts));path.rename(aged);entry[1]=str(aged)
        router.clean_message_store();emit(True)
