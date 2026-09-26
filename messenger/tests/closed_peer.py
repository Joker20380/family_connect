"""Synthetic closed-relay fixture. Test keys only, never production configuration."""
import json
import os
from pathlib import Path
import sys
import time
import threading
from dataclasses import asdict
import RNS
import LXMF
from messenger.chat import Chat
from messenger.store import Store
from messenger.relay import Spool,ClosedRelay
from messenger.mailbox import Mailbox,MailboxError
from messenger.sync import SyncController
from messenger.delivery import DeliveryController

role,directory,port,allowfile=sys.argv[1:]
os.umask(0o077)
root=Path(directory);root.mkdir(mode=0o700,exist_ok=True)
config=root/'rns';config.mkdir(mode=0o700,exist_ok=True)
interface=(f'type = TCPServerInterface\nlisten_ip = 127.0.0.1\nlisten_port = {port}' if role in ('node','budget-node')
           else f'type = TCPClientInterface\ntarget_host = 127.0.0.1\ntarget_port = {port}')
(config/'config').write_text('[reticulum]\nshare_instance = No\nenable_transport = No\n[logging]\nloglevel = 0\n[interfaces]\n[[loopback]]\nenabled = Yes\n'+interface+'\n')
RNS.Reticulum(configdir=str(config),loglevel=0)
keyfile=root/'synthetic.key'
if not keyfile.exists():keyfile.write_bytes(os.urandom(32))
store=Store(root/'chat',keyfile.read_bytes());chat=Chat(store)
if role in ('node','budget-node'):
    spool=(Spool(root/'spool') if role=='budget-node' else
           Spool(root/'spool',max_bytes=10000,max_messages=2,sender_bytes=5000,sender_messages=1))
    relay=ClosedRelay(chat.identity,spool,allowed_public=[bytes.fromhex(x) for x in json.loads(Path(allowfile).read_text())])
    destination=relay.destination
else:
    router=LXMF.LXMRouter(identity=chat.identity,storagepath=str(root/'router'),autopeer=False,delivery_limit=8)
    source=chat.attach(router)
mailbox=None
controller=None
delivery=None
def emit(value):print(json.dumps(value),flush=True)
emit(dict(public=chat.public.hex()))
for line in sys.stdin:
    request=json.loads(line);op=request['op']
    try:
        if op=='announce':destination.announce();result=True
        elif op=='stats':result=spool.stats()
        elif op=='relay':mailbox=Mailbox(chat,source,bytes.fromhex(request['public']));result=True
        elif op=='trust':chat.trust_contact(bytes.fromhex(request['public']));result=True
        elif op=='queue':
            result=chat.queue(bytes.fromhex(request['peer']),request['text'])
            if delivery is not None:delivery.request_sync()
        elif op=='delivery_lifecycle':
            if delivery is None:delivery=DeliveryController(mailbox)
            delivery.update(online=request['online'],foreground=request['foreground']);result=True
        elif op=='delivery_state':
            result=delivery.snapshot()
            if result['result'] is not None:result['result']=asdict(result['result'])
        elif op=='delivery_refresh':result=delivery.request_sync()
        elif op=='delivery_close':result=delivery.close()
        elif op=='publish':mailbox.publish(request['id']);result=True
        elif op=='batch':
            cancel=threading.Event();original=mailbox._request
            def cancel_after_ack(*args,**kwargs):
                response=original(*args,**kwargs)
                cancel.set()
                return response
            if request.get('cancel_after_ack'):mailbox._request=cancel_after_ack
            try:mailbox.publish_many(request['ids'],cancel=cancel);result=True
            finally:mailbox._request=original
        elif op=='lifecycle':
            if controller is None:controller=SyncController(mailbox,cooldown=.1,max_backoff=.4)
            controller.update(online=request['online'],foreground=request['foreground']);result=True
        elif op=='sync_state':
            result=controller.snapshot()
            if result['result'] is not None:result['result']=asdict(result['result'])
        elif op=='sync_close':result=controller.close()
        elif op=='metrics':result=dict(tx=sum(i.txb for i in RNS.Transport.interfaces),rx=sum(i.rxb for i in RNS.Transport.interfaces))
        elif op=='fetch':result=asdict(mailbox.sync(delete_after_store=request.get('delete',True)))
        elif op=='messages':result=[{k:m[k] for k in ('id','text','status','outgoing')} for m in store.messages()]
        elif op=='native':
            with mailbox._connection(5,None) as (link,deadline,cancel):
                RNS.Packet(link,b'X'*128).send();time.sleep(.15)
                resource=RNS.Resource(b'X'*2048,link,timeout=1)
                time.sleep(.3)
            result=True
        else:raise ValueError('Unknown fixture operation')
        emit(result)
    except MailboxError as error:emit({'error':str(error)})
