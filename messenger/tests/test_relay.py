import os
from concurrent.futures import ThreadPoolExecutor
import pytest
import RNS
from messenger.relay import Spool,SpoolFull,ClosedRelay,PUT_PATH
from messenger.codec import address
from LXMF.LXMPeer import LXMPeer


def blob(recipient=b'r'*16,size=512):return recipient+os.urandom(size-16)


def test_atomic_limits_duplicate_and_restart(tmp_path):
    path=tmp_path/'spool';sender=b's'*16
    spool=Spool(path,max_bytes=2048,max_messages=4,sender_bytes=2048,sender_messages=4)
    records=[blob() for _ in range(12)]
    def put(data):
        try:spool.put(sender,data);return True
        except SpoolFull:return False
    with ThreadPoolExecutor(max_workers=8) as pool:assert sum(pool.map(put,records))==4
    assert spool.stats()==dict(count=4,bytes=2048)
    ids=spool.get(b'r'*16,[None,None]);body=spool.get(b'r'*16,[[ids[0]],[]])[0]
    assert spool.put(sender,body)==ids[0]
    assert spool.stats()['count']==4
    ceiling=spool.max_pages*4096;spool.close()
    assert (path/'spool.sqlite').stat().st_size<=ceiling
    resumed=Spool(path,max_bytes=2048,max_messages=4,sender_bytes=2048,sender_messages=4)
    try:
        assert resumed.stats()==dict(count=4,bytes=2048)
        resumed.get(b'x'*16,[None,ids[:1]])
        assert resumed.stats()['count']==4
        resumed.get(b'r'*16,[None,ids[:1]])
        resumed.put(sender,blob());assert resumed.stats()['count']==4
    finally:resumed.close()


def test_sender_quota_leaves_space_for_other_member_and_expiry(tmp_path):
    now=[100]
    spool=Spool(tmp_path/'spool',max_bytes=4096,max_messages=8,sender_bytes=512,sender_messages=1,retention=10,clock=lambda:now[0])
    try:
        spool.put(b'a'*16,blob())
        with pytest.raises(SpoolFull):spool.put(b'a'*16,blob())
        spool.put(b'b'*16,blob());assert spool.stats()['count']==2
        now[0]=110;spool.expire();assert spool.stats()['count']==0
        spool.put(b'a'*16,blob())
    finally:spool.close()


def test_access_checks_before_storage_and_no_native_upload_handlers(tmp_path,monkeypatch):
    captured={}
    class Destination:
        IN=0;SINGLE=0;ALLOW_ALL=0
        def __init__(self,*args):pass
        def register_request_handler(self,path,callback,**kwargs):captured[path]=callback
    # Address derivation needs real RNS Destination; create the identities first.
    alice,bob,stranger=RNS.Identity(),RNS.Identity(),RNS.Identity()
    public=[alice.get_public_key(),bob.get_public_key()]
    target=address(public[1])
    import messenger.relay as module
    derive=module.address
    mapped={p:derive(p) for p in public}
    monkeypatch.setattr(module,'address',lambda p:mapped[p])
    monkeypatch.setattr(RNS,'Destination',Destination)
    spool=Spool(tmp_path/'spool')
    try:
        relay=ClosedRelay(RNS.Identity(),spool,allowed_public=public)
        assert set(captured)=={PUT_PATH,LXMPeer.MESSAGE_GET_PATH}
        def send(who,data):return relay.respond(PUT_PATH,data,None,who,0)
        for who in (None,stranger):assert send(who,blob(target))==LXMPeer.ERROR_NO_ACCESS
        assert send(alice,blob(b'z'*16))==['rejected']
        assert spool.stats()['count']==0
        data=blob(target);assert send(alice,data)[0]=='stored'
        assert relay.respond(LXMPeer.MESSAGE_GET_PATH,[None,None],None,alice,0)==[]
        assert len(relay.respond(LXMPeer.MESSAGE_GET_PATH,[None,None],None,bob,0))==1
        for _ in range(3):send(alice,data)
        assert send(alice,data)==['rate_limited']
    finally:spool.close()


def test_sqlite_full_cannot_acknowledge_a_missing_message(tmp_path):
    spool=Spool(tmp_path/'spool',max_bytes=1048576,max_messages=1000,sender_bytes=1048576,sender_messages=1000)
    try:
        pages=spool.db.execute('PRAGMA page_count').fetchone()[0]
        spool.db.execute(f'PRAGMA max_page_count={pages}')
        with pytest.raises(SpoolFull):spool.put(b's'*16,blob(size=4800))
        assert spool.stats()==dict(count=0,bytes=0)
    finally:spool.close()
