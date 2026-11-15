"""Replay only an isolated support-store copy; refuse a network-capable namespace."""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import time

from control.friends.pseudonyms import ENVIRONMENT, load, seal, unseal, require
from provisioning.support_worker import SupportStore, SupportOwner
from scripts.prepare_pseudonym_migration import private_bytes


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('database','store-key','new-key','aliases','scratch'):
        parser.add_argument('--'+name,required=True,type=Path)
    args=parser.parse_args()
    require({name for number,name in socket.if_nameindex()} <= {'lo'})
    os.umask(0o077)
    args.scratch.mkdir(mode=0o700,parents=True,exist_ok=False)
    shutil.copyfile(args.database,args.scratch/'history.sqlite')
    (args.scratch/'.lock').touch(mode=0o600)
    storage_key=private_bytes(args.store_key,32);new_key=private_bytes(args.new_key,32)
    aliases=load(args.aliases)
    os.environ[ENVIRONMENT]=str(args.aliases)
    store=SupportStore(args.scratch,storage_key,create=False)
    try:
        owner=SupportOwner(store,store.chat_identity().get_public_key().hex())
        before={row[0]:store._get(row[0]) for row in store._db.execute('SELECT id FROM records')}
        bindings=deepcopy(before['support-bindings'])
        bindings['sequence']+=1;bindings['expires_at']=int(time.time())+90
        bindings['node']['expires_at']=bindings['expires_at']
        for row in bindings['devices']:
            row['pseudonym']=aliases.index['device'][row['pseudonym']]['aliases'][str(aliases.generation)]
        owner.update(unseal(seal(bindings,'support',new_key,aliases),'support',aliases))
        replayed=0
        for name,record in before.items():
            if not name.startswith('support-request:'):continue
            request=record['request'];identity=name.removeprefix('support-request:')
            changed=aliases.index['device'][request['pseudonym']]['aliases'][str(aliases.generation)]
            for recipient in (request['pseudonym'],changed):
                with store._lock,store._db:
                    response=owner.enqueue(recipient,request['address'],identity,
                        request.get('source',request.get('actor')),request['text'],
                        **({'expires_at':request['expires_at']} if 'expires_at' in request else {}))
                require(response['id']==record['id'])
            replayed+=1
        after={row[0]:store._get(row[0]) for row in store._db.execute('SELECT id FROM records')}
        require(before.keys()==after.keys())
        require(all(before[name]==after[name] for name in before if name!='support-bindings'))
        report=dict(requests_replayed=replayed,records_preserved=len(before)-1,
                    pins_preserved=len(before.get('support-threads',{})),messages_sent=0,
                    pending_jobs=sum(name.startswith('subscription-job:') for name in before),
                    baseline_preserved=before.get('subscription-baseline')==after.get('subscription-baseline'),
                    cursor_preserved=before.get('subscription-cursor')==after.get('subscription-cursor'))
        expected=hashlib.sha256(json.dumps(after,sort_keys=True).encode()).digest()
    finally:
        store.close()
    store=SupportStore(args.scratch,storage_key,create=False)
    try:
        restored={row[0]:store._get(row[0]) for row in store._db.execute('SELECT id FROM records')}
        require(hashlib.sha256(json.dumps(restored,sort_keys=True).encode()).digest()==expected)
        report['restart_preserved']=True
    finally:
        store.close()
    print(json.dumps(report,sort_keys=True))


if __name__=='__main__':
    try:
        main()
    except Exception:
        sys.exit('Isolated support rehearsal failed; private inputs withheld.')
