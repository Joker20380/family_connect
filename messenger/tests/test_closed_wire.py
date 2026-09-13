import json
import os
import socket
import time
from pathlib import Path
from messenger.chat import Chat
from messenger.store import Store
from messenger.codec import address
from messenger.tests.test_offline import Peer


def test_closed_ingress_quota_restart_and_mailbox(tmp_path):
    publics=[]
    for name in ('alice','bob','stranger'):
        root=tmp_path/name;root.mkdir(mode=0o700)
        key=os.urandom(32)
        with os.fdopen(os.open(root/'synthetic.key',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:f.write(key)
        store=Store(root/'chat',key)
        try:publics.append(Chat(store).public)
        finally:store.close()
    allowfile=tmp_path/'allowed.json';allowfile.write_text(json.dumps([p.hex() for p in publics[:2]]))
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    peers=[]
    def start(role,name):
        peer=Peer(role,tmp_path/name,port,script='closed_peer.py',extra=[str(allowfile)])
        peers.append(peer);return peer
    try:
        node=start('node','node');node_public=node.info['public']
        alice=start('client','alice');bob=start('client','bob');stranger=start('client','stranger')
        for peer in (alice,bob,stranger):
            peer.call('relay',public=node_public);peer.call('trust',public=publics[1].hex())
        bob.call('trust',public=publics[0].hex());bob.close()
        for _ in range(3):node.call('announce');time.sleep(.25)
        ident=alice.call('queue',peer=address(publics[1]).hex(),text='CLOSED-SPOOL-SECRET-ONE')
        other=stranger.call('queue',peer=address(publics[1]).hex(),text='untrusted sender')
        assert stranger.call('publish',id=other)=={'error':'access_denied'}
        assert node.call('stats')['count']==0
        assert alice.call('native') is True
        assert node.call('stats')['count']==0
        assert alice.call('publish',id=ident) is True
        assert alice.call('messages')[0]['status']=='relayed'
        assert alice.call('publish',id=ident) is True # Same ciphertext, lost-ACK retry.
        assert node.call('stats')['count']==1
        excess=alice.call('queue',peer=address(publics[1]).hex(),text='over quota')
        assert alice.call('publish',id=excess)=={'error':'full'}
        assert alice.call('messages')[1]['status']=='queued'
        alice.close();stranger.close();node.close()
        assert b'CLOSED-SPOOL-SECRET-ONE' not in (tmp_path/'node/spool/spool.sqlite').read_bytes()
        node=start('node','node');assert node.info['public']==node_public
        assert node.call('stats')['count']==1
        alice=start('client','alice');alice.call('relay',public=node_public)
        bob=start('client','bob');bob.call('relay',public=node_public)
        for _ in range(3):node.call('announce');time.sleep(.25)
        assert alice.call('publish',id=ident) is True
        assert node.call('stats')['count']==1
        assert bob.call('fetch')==dict(stored=1,duplicates=0,rejected=0,purged=1)
        assert bob.call('messages')[0]['text']=='CLOSED-SPOOL-SECRET-ONE'
        assert node.call('stats')['count']==0
        assert alice.call('publish',id=excess) is True
        assert node.call('stats')['count']==1
    finally:
        for peer in reversed(peers):peer.close()
