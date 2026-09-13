"""Operator diagnostic peer; permanent synthetic pilot state, no Android UI.

Never use its adjacent storage.key layout for user chats. Used only with the two
operator-created diagnostic identities for this closed Amsterdam acceptance.
"""
import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys

import LXMF
import RNS
from messenger.chat import Chat
from messenger.store import Store
from messenger.mailbox import Mailbox,MailboxError


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--directory',required=True);parser.add_argument('--bootstrap',required=True)
    args=parser.parse_args();os.umask(0o077)
    root=Path(args.directory)
    bootstrap=json.loads(Path(args.bootstrap).read_text())
    if bootstrap['server']!='186.246.45.246' or bootstrap['port']!=4243:
        raise ValueError('Diagnostic peer restricted to Amsterdam pilot')
    config=root/'rns';config.mkdir(mode=0o700,exist_ok=True)
    (config/'config').write_text('[reticulum]\nshare_instance = No\nenable_transport = No\n[logging]\nloglevel = 0\n[interfaces]\n[[Amsterdam-mailbox]]\nenabled = Yes\ntype = TCPClientInterface\ntarget_host = 186.246.45.246\ntarget_port = 4243\n')
    RNS.Reticulum(configdir=str(config),loglevel=0)
    store=Store(root/'chat',(root/'storage.key').read_bytes());chat=Chat(store)
    router=LXMF.LXMRouter(identity=chat.identity,storagepath=str(root/'router'),autopeer=False,delivery_limit=8)
    source=chat.attach(router)
    mailbox=Mailbox(chat,source,bytes.fromhex(bootstrap['public_key']))
    if RNS.Destination.hash(mailbox.node,'lxmf','propagation').hex()!=bootstrap['destination']:
        raise ValueError('Bootstrap identity mismatch')
    def emit(value):print(json.dumps(value),flush=True)
    emit(dict(public=chat.public.hex()))
    for line in sys.stdin:
        request=json.loads(line);op=request['op']
        try:
            if op=='trust':result=chat.trust_contact(bytes.fromhex(request['public'])).hex()
            elif op=='queue':result=chat.queue(bytes.fromhex(request['peer']),request['text'])
            elif op=='publish':mailbox.publish(request['id'],timeout=30);result=True
            elif op=='batch':mailbox.publish_many(request['ids'],timeout=30);result=True
            elif op=='fetch':result=asdict(mailbox.sync(timeout=30))
            elif op=='messages':result=[{k:m[k] for k in ('id','text','status','outgoing')} for m in store.messages()]
            elif op=='metrics':
                result=dict(messages=[dict(id=m['id'],text_bytes=len(m['text'].encode()),
                    lxmf_bytes=len(bytes.fromhex(m['packed'])),
                    ciphertext_bytes=len(bytes.fromhex(m.get('relay_blob','')))) for m in store.messages()],
                    tx_bytes=sum(getattr(i,'txb',0) for i in RNS.Transport.interfaces),
                    rx_bytes=sum(getattr(i,'rxb',0) for i in RNS.Transport.interfaces))
            else:raise ValueError('Unknown diagnostic command')
            emit(result)
        except MailboxError as error:emit(dict(error=str(error)))


if __name__=='__main__':main()
