"""Real Android Python carrier; OS/JNI socket binding remains device acceptance."""
import importlib
import json
from pathlib import Path
import socket
import time

import pytest
import RNS
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from messenger.mailbox import MailboxError
from messenger.tests.test_offline import Peer, wait_for
from messenger.tests.test_android_bridge import bridge, invoke


class Bindings:
    def __init__(self, allowed=True): self.fds = []; self.allowed = allowed
    def bindSocket(self, fd):
        self.fds.append(fd)
        return self.allowed


def configure(session, callbacks, port=4243):
    public = RNS.Identity().get_public_key().hex()
    session.configure_delivery('127.0.0.1', port, public, callbacks)


def test_carrier_requires_binding_and_shares_control_lease(tmp_path, bridge, monkeypatch):
    transport = importlib.import_module('fc_rns_transport')
    monkeypatch.setattr(transport, '_runtime', object())
    session = bridge.Session(str(tmp_path/'chat'), 'unused', AESGCM(b'x'*32), True)
    callbacks = Bindings(False)
    try:
        configure(session, callbacks)
        assert not callbacks.fds  # Configure alone never opens a socket.
        assert transport._session_lock.acquire(False)
        try:
            with pytest.raises(MailboxError, match='^busy$'): session.carrier.exchange()
            assert not callbacks.fds
        finally: transport._session_lock.release()
        with pytest.raises(MailboxError, match='^unavailable$'): session.carrier.exchange()
        assert len(callbacks.fds) == 1
        assert transport._session_lock.acquire(False)
        transport._session_lock.release()
        destination = session.carrier.source
        assert destination in RNS.Transport.destinations
    finally: session.close()
    assert destination not in RNS.Transport.destinations
    reopened = bridge.Session(str(tmp_path/'chat'), 'unused', AESGCM(b'x'*32), False)
    try: configure(reopened, Bindings(False))
    finally: reopened.close()


@pytest.mark.parametrize('host,port,public', [('example.com',4243,'00'*64),
    ('127.0.0.1',True,'00'*64), ('127.0.0.1',0,'00'*64), ('127.0.0.1',4243,'00')])
def test_invalid_bootstrap_does_not_register_destination(tmp_path, bridge, host, port, public):
    session = bridge.Session(str(tmp_path/'chat'), 'unused', AESGCM(b'x'*32), True)
    before = list(RNS.Transport.destinations)
    try:
        with pytest.raises(ValueError): session.configure_delivery(host,port,public,Bindings())
        assert list(RNS.Transport.destinations) == before
        assert invoke(session,'profile')['ok']
    finally: session.close()


@pytest.mark.parametrize("payload",["text","voice","android_voice"])
def test_android_carrier_real_exchange_cleanup_and_reopen(tmp_path, bridge, monkeypatch, chat_runtime,payload):
    transport = importlib.import_module('fc_rns_transport')
    monkeypatch.setattr(transport, '_runtime', chat_runtime)
    session = bridge.Session(str(tmp_path/'chat'), 'unused', AESGCM(b'x'*32), True)
    peer = node = None
    baseline = list(RNS.Transport.interfaces)
    callbacks = Bindings()
    try:
        profile = invoke(session,'profile')['value']
        allow = tmp_path/'allowed.json'
        # Create receiver identity before starting the closed node.
        from messenger.store import Store
        from messenger.chat import Chat
        receiver_root = tmp_path/'bob'; receiver_root.mkdir()
        key = b'y'*32; (receiver_root/'synthetic.key').write_bytes(key)
        store = Store(receiver_root/'chat', key)
        public = Chat(store).public.hex(); store.close()
        allow.write_text(json.dumps([profile['public'],public]))
        with socket.socket() as probe:
            probe.bind(('127.0.0.1',0)); port=probe.getsockname()[1]
        node = Peer('budget-node',tmp_path/'node',port,script='closed_peer.py',extra=[str(allow)])
        peer = Peer('client',receiver_root,port,script='closed_peer.py',extra=[str(allow)])
        peer.call('relay',public=node.info['public']); peer.call('trust',public=profile['public'])
        card = invoke(session,'preview_contact',public=public)['value']
        assert invoke(session,'trust_contact',public=public,fingerprint=card['fingerprint'])['ok']
        session.configure_delivery('127.0.0.1',port,node.info['public'],callbacks)
        original_exchange = session.carrier.exchange
        failures = []
        def checked_exchange(**kwargs):
            try: return original_exchange(**kwargs)
            except Exception as failure:
                failures.append(repr(failure))
                raise
        monkeypatch.setattr(session.carrier, 'exchange', checked_exchange)
        if payload in ('voice', 'android_voice'):
            import base64
            from messenger.tests.test_edits_voice import long_voice_fixture, android_stopped_voice
            voice = android_stopped_voice() if payload == 'android_voice' else long_voice_fixture()
            result=invoke(session,'queue_audio',address=card['address'],audio=base64.b64encode(voice).decode());assert result['ok'];ident=result['value']
        else:ident=invoke(session,'queue',address=card['address'],text='Android source test')['value']
        session.delivery_update(True,True)
        def exchanged():
            state = invoke(session,'delivery_state')['value']
            assert state['error'] is None, failures
            return state['result'] is not None
        wait_for(exchanged)
        assert invoke(session,'history',address=card['address'],offset=0,limit=50)['value']['messages'][0]['status']=='relayed'
        assert node.call('stats')['count']==1
        node.call('announce'); time.sleep(.3)
        assert peer.call('fetch')['stored']==1
        assert peer.call('messages')[0]['id']==ident
        assert RNS.Transport.interfaces == baseline
        assert len(callbacks.fds)==1
        # Same session opens another bound socket and discovers a fresh path.
        peer.call('queue',peer=profile['address'],text='reply')
        peer.call('batch',ids=[m['id'] for m in peer.call('messages') if m['outgoing']])
        assert invoke(session,'request_sync')['ok']
        wait_for(lambda: len(invoke(session,'history',address=card['address'],offset=0,limit=50)['value']['messages'])==2)
        wait_for(lambda: not invoke(session,'delivery_state')['value']['running'])
        assert node.call('stats')['count']==0
        assert len(callbacks.fds)==2 and RNS.Transport.interfaces==baseline
        assert transport._session_lock.acquire(False); transport._session_lock.release()
    finally:
        session.close()
        if peer: peer.close()
        if node: node.close()
    assert RNS.Transport.interfaces==baseline
