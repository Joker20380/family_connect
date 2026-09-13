import os
import sqlite3
import pytest
import RNS
import LXMF
from cryptography.exceptions import InvalidTag
from messenger import codec
from messenger.chat import Chat
from messenger.store import Store


@pytest.fixture(scope='module', autouse=True)
def reticulum(tmp_path_factory):
    config = tmp_path_factory.mktemp('chat-rns')
    (config/'config').write_text('[reticulum]\nshare_instance = No\nenable_transport = No\n[logging]\nloglevel = 0\n[interfaces]\n')
    RNS.Reticulum(configdir=str(config), loglevel=0)


@pytest.fixture
def pair(tmp_path):
    key = os.urandom(32)
    a, b = Store(tmp_path/'alice', key), Store(tmp_path/'bob', os.urandom(32))
    alice, bob = Chat(a), Chat(b)
    alice.trust_contact(bob.public);bob.trust_contact(alice.public)
    yield alice, bob, key, tmp_path
    a.close();b.close()


def test_bidirectional_signed_text_and_upstream_decode(pair):
    alice,bob,_,_=pair
    for sender,receiver in ((alice,bob),(bob,alice)):
        ident=sender.queue(receiver.address,'Привет из Гента 👋')
        token,raw=sender.store.begin_attempt(ident)
        assert receiver.receive(raw)
        assert not receiver.receive(raw)
        RNS.Identity.remember(None,sender.address,sender.public)
        upstream=LXMF.LXMessage.unpack_from_bytes(raw)
        assert upstream.signature_validated and upstream.content.decode()=='Привет из Гента 👋'
        assert sender.store.finish_attempt(ident,token,delivered=True)
        with pytest.raises(ValueError):sender.store.begin_attempt(ident)
    assert len(alice.store.messages())==len(bob.store.messages())==2


def test_restart_preserves_identity_contacts_pending_and_dedupe(pair):
    alice,bob,key,root=pair
    public=alice.public
    ident=alice.queue(bob.address,'offline message')
    old,raw=alice.store.begin_attempt(ident)
    assert bob.receive(raw)
    alice.store.close()
    reopened=Store(root/'alice',key)
    try:
        resumed=Chat(reopened)
        assert resumed.public==public and bob.address in resumed.contacts()
        token,retry=reopened.begin_attempt(ident)
        assert retry==raw and token!=old
        assert not reopened.finish_attempt(ident,old,delivered=True)
        assert not bob.receive(retry)
        assert reopened.finish_attempt(ident,token,delivered=True)
        assert reopened.messages()[0]['status']=='delivered'
    finally:reopened.close()


@pytest.mark.parametrize('position',[0,16,32,-1])
def test_tampering_never_enters_history(pair,position):
    alice,bob,_,_=pair
    ident=alice.queue(bob.address,'authenticated text')
    _,raw=alice.store.begin_attempt(ident)
    changed=bytearray(raw);changed[position]^=1
    with pytest.raises(ValueError):bob.receive(bytes(changed))
    assert bob.store.messages()==[]


def test_unknown_sender_and_size_limits(pair):
    alice,bob,_,_=pair
    stranger=RNS.Identity()
    with pytest.raises(ValueError):bob.receive(codec.pack(stranger,bob.public,'unknown'))
    for text in ('','я'*2049):
        with pytest.raises(ValueError):alice.queue(bob.address,text)
    with pytest.raises(ValueError):alice.queue(b'0'*16,'unknown recipient')


def test_storage_encryption_wrong_key_and_row_swap(pair):
    alice,bob,key,root=pair
    for text in ('SECRET-ONE-'+ 'a'*50,'SECRET-TWO-'+ 'b'*50):alice.queue(bob.address,text)
    private=alice.identity.get_private_key().hex().encode()
    alice.store.close()
    for file in (root/'alice').iterdir():
        raw=file.read_bytes()
        assert b'SECRET-ONE-' not in raw and b'SECRET-TWO-' not in raw and private not in raw
    with pytest.raises(InvalidTag):Store(root/'alice',os.urandom(32))
    with sqlite3.connect(root/'alice/history.sqlite') as db:
        rows=db.execute("SELECT id,sealed FROM records WHERE id LIKE 'message:%'").fetchall()
        db.execute('UPDATE records SET sealed=? WHERE id=?',(rows[0][1],rows[1][0]))
    reopened=Store(root/'alice',key)
    try:
        with pytest.raises(InvalidTag):reopened.messages()
    finally:reopened.close()


def test_duplicate_dispatch_and_stale_failure(pair):
    alice,bob,_,_=pair
    ident=alice.queue(bob.address,'once')
    old,_=alice.store.begin_attempt(ident)
    with pytest.raises(ValueError):alice.store.begin_attempt(ident)
    assert alice.store.finish_attempt(ident,old,delivered=False)
    current,_=alice.store.begin_attempt(ident)
    assert not alice.store.finish_attempt(ident,old,delivered=False)
    assert alice.store.finish_attempt(ident,current,delivered=True)
    assert not alice.store.finish_attempt(ident,current,delivered=False)


def test_private_directory_and_single_owner(pair):
    alice,bob,key,root=pair
    with pytest.raises(BlockingIOError):Store(root/'alice',key)
    unsafe=root/'unsafe';unsafe.mkdir(mode=0o755)
    with pytest.raises(ValueError):Store(unsafe,key)
    link=root/'link';link.symlink_to(root/'alice',target_is_directory=True)
    with pytest.raises(ValueError):Store(link,key)


def test_concurrent_duplicate_receives_are_atomic(pair):
    from concurrent.futures import ThreadPoolExecutor
    alice,bob,_,_=pair
    ident=alice.queue(bob.address,'parallel duplicate')
    _,raw=alice.store.begin_attempt(ident)
    with ThreadPoolExecutor(max_workers=4) as executor:
        assert sorted(executor.map(bob.receive,[raw]*4))==[False,False,False,True]
    assert len(bob.store.messages())==1


@pytest.mark.parametrize('payload', [
    [1.0,b'',b'configuration',{1:'execute'}],
    [1.0,b'attachment',b'text',{}],
    [float('nan'),b'',b'text',{}],
    [1.0,b'',b'\xff',{}],
])
def test_signed_non_text_payloads_rejected(pair,payload):
    import hashlib
    import RNS.vendor.umsgpack as msgpack
    alice,bob,_,_=pair
    body=msgpack.packb(payload)
    hashed=bob.address+alice.address+body
    raw=bob.address+alice.address+alice.identity.sign(hashed+hashlib.sha256(hashed).digest())+body
    with pytest.raises(ValueError):bob.receive(raw)
    assert not bob.store.messages()
