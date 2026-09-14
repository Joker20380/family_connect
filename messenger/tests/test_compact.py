"""Real RNS traffic comparison and partial batch failure acceptance."""
import json
import os
from pathlib import Path
import socket
import time
import pytest
from messenger.chat import Chat
from messenger.store import Store
from messenger.codec import address
from messenger.mailbox import Mailbox
from messenger.tests.test_offline import Peer


def setup_peers(tmp_path, role):
    publics=[]
    for name in ('alice','bob'):
        root=tmp_path/name;root.mkdir(mode=0o700)
        key=os.urandom(32);(root/'synthetic.key').write_bytes(key)
        store=Store(root/'chat',key)
        try:publics.append(Chat(store).public)
        finally:store.close()
    allow=tmp_path/'allowed.json';allow.write_text(json.dumps([p.hex() for p in publics]))
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    peers=[]
    try:
        for peer_role,name in ((role,'node'),('client','alice'),('client','bob')):
            peers.append(Peer(peer_role,tmp_path/name,port,script='closed_peer.py',extra=[str(allow)]))
        node,alice,bob=peers
        for peer,public in ((alice,publics[1]),(bob,publics[0])):
            peer.call('relay',public=node.info['public']);peer.call('trust',public=public.hex())
        node.call('announce');time.sleep(.3)
        return peers,publics
    except BaseException:
        for peer in reversed(peers):peer.close()
        raise


def measure(peer, action):
    before=peer.call('metrics');start=time.monotonic()
    result=action()
    time.sleep(.1) # Include teardown bytes before sampling counters.
    after=peer.call('metrics')
    return result,dict(tx=after['tx']-before['tx'],rx=after['rx']-before['rx'],seconds=round(time.monotonic()-start,3))


def test_binary_batch_traffic_and_delivery(tmp_path):
    peers,publics=setup_peers(tmp_path,'budget-node')
    node,alice,bob=peers
    report={}
    try:
        _,report['idle_2_seconds']=measure(alice,lambda:time.sleep(2))
        _,report['one_announce']=measure(alice,lambda:node.call('announce'))
        result,report['empty_fetch']=measure(bob,lambda:bob.call('fetch'))
        assert result==dict(stored=0,duplicates=0,rejected=0,purged=0)
        for mode in ('separate','batch'):
            time.sleep(4) # Refill the unchanged four-token admission bucket.
            ids=[alice.call('queue',peer=address(publics[1]).hex(),text='ping') for _ in range(4)]
            def send():
                if mode=='batch':assert alice.call('batch',ids=ids) is True
                else:
                    for ident in ids:assert alice.call('publish',id=ident) is True
            _,report[mode]=measure(alice,send)
            assert node.call('stats')['count']==4
            assert bob.call('fetch')==dict(stored=4,duplicates=0,rejected=0,purged=4)
            assert node.call('stats')['count']==0
        messages=bob.call('messages')
        assert len(messages)==8 and all(m['text']=='ping' for m in messages)
        assert report['batch']['tx']+report['batch']['rx'] < report['separate']['tx']+report['separate']['rx']
        report['saved_fraction']=round(1-(report['batch']['tx']+report['batch']['rx'])/(report['separate']['tx']+report['separate']['rx']),4)
        target=os.environ.get('FC_COMPACT_REPORT')
        if target:Path(target).write_text(json.dumps(report,indent=2)+'\n')
    finally:
        for peer in reversed(peers):peer.close()


def test_partial_batch_failure_retry_preserves_commits(tmp_path):
    peers,publics=setup_peers(tmp_path,'node')
    node,alice,bob=peers
    try:
        ids=[alice.call('queue',peer=address(publics[1]).hex(),text=f'item{i}') for i in range(3)]
        assert alice.call('batch',ids=ids)=={'error':'full'}
        states={m['id']:m['status'] for m in alice.call('messages')}
        assert [states[ident] for ident in ids]==['relayed','queued','queued']
        assert node.call('stats')['count']==1
        assert bob.call('fetch')==dict(stored=1,duplicates=0,rejected=0,purged=1)
        # Same mailbox can reopen after failed batch; ciphertext retries stay valid.
        time.sleep(2)
        assert alice.call('publish',id=ids[1]) is True
        assert bob.call('fetch')==dict(stored=1,duplicates=0,rejected=0,purged=1)
        assert {m['text'] for m in bob.call('messages')}=={'item0','item1'}
    finally:
        for peer in reversed(peers):peer.close()


@pytest.mark.parametrize('ids',[[],['x']*2,['x']*5,'x',[None]])
def test_batch_rejects_unbounded_or_ambiguous_input(ids):
    # Invalid input must fail before touching chat/store or opening a link.
    with pytest.raises(ValueError):Mailbox.publish_many(object(),ids)


def test_cancel_between_messages_keeps_queue_and_releases_link(tmp_path):
    peers,publics=setup_peers(tmp_path,'budget-node')
    node,alice,bob=peers
    try:
        ids=[alice.call('queue',peer=address(publics[1]).hex(),text=f'cancel{i}') for i in range(3)]
        assert alice.call('batch',ids=ids,cancel_after_ack=True)=={'error':'cancelled'}
        states={m['id']:m['status'] for m in alice.call('messages')}
        assert [states[ident] for ident in ids]==['relayed','queued','queued']
        assert node.call('stats')['count']==1
        assert alice.call('batch',ids=ids[1:]) is True
        assert bob.call('fetch')==dict(stored=3,duplicates=0,rejected=0,purged=3)
        assert node.call('stats')['count']==0
    finally:
        for peer in reversed(peers):peer.close()
