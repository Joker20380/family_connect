"""Python side of the real Android source; device/JNI acceptance is separate."""
import importlib
import json
from pathlib import Path
import sys

import pytest
import RNS
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from messenger.local import LocalChat, LocalError, contact_card


@pytest.fixture
def bridge(monkeypatch, chat_runtime):
    source = Path(__file__).resolve().parents[2] / 'clients/android/app/src/main/python'
    monkeypatch.syspath_prepend(str(source))
    module = importlib.import_module('fc_chat_store')
    # The suite already owns RNS; Android's real singleton is checked on-device.
    monkeypatch.setattr(module, 'initialize', lambda _: None)
    return module


def invoke(session, operation, **arguments):
    return json.loads(session.invoke(operation, json.dumps(arguments)))


def test_java_callback_store_format_matches_desktop(tmp_path, bridge):
    key = bytes(range(32))
    cipher = AESGCM(key)  # Implements the Java callback shape without its key getter.
    assert cipher.encrypt(bytes(range(12)), 'Привет 🙂'.encode(), b'fc-chat-v1:meta').hex() == \
        '979d079b155d12a95df446099119e7f401122ae76e1ee9b7a79a9727cca64570f5'
    session = bridge.Session(str(tmp_path/'chat'), str(tmp_path/'runtime'), cipher, True)
    peer = contact_card(RNS.Identity().get_public_key().hex())
    try:
        profile = invoke(session, 'profile')['value']
        assert invoke(session, 'trust_contact', public=peer['public'], fingerprint=peer['fingerprint'])['ok']
        assert invoke(session, 'queue', address=peer['address'], text='Private 🙂')['ok']
        before = invoke(session, 'history', address=peer['address'], offset=0, limit=50)
        assert before['ok'] and len(before['value']['messages']) == 1
        assert set(before['value']['messages'][0]) == {'id','peer','text','timestamp','outgoing','status'}
    finally:
        session.close()
    with pytest.raises(LocalError):
        LocalChat(tmp_path/'chat', b'x'*32, create=False)
    desktop = LocalChat(tmp_path/'chat', key, create=False)
    try:
        assert desktop.profile() == profile
        assert desktop.history(peer['address']) == before['value']
    finally:
        desktop.close()
    session.close()
    assert invoke(session, 'profile') == {'ok': False, 'error': 'closed'}


@pytest.mark.parametrize('operation,payload', [
    ('close', '{}'), ('__getattribute__', '{}'), ('profile', '{"key":1}'),
    ('configure_delivery', '{}'), ('delivery_update', '{}'),
    ('enrollment_proof', '{}'),
    ('queue', '{"address":1,"address":2,"text":"x"}'), ('history', '[]'),
    ('queue', '{'), ('profile', 'x'*32769), ('profile', '\ud800'),
])
def test_bridge_rejects_non_api_requests_without_tracebacks(tmp_path, bridge, operation, payload):
    session = bridge.Session(str(tmp_path/'chat'), 'unused', AESGCM(b'x'*32), True)
    try:
        assert json.loads(session.invoke(operation, payload)) == {'ok': False, 'error': 'invalid_input'}
        assert invoke(session, 'profile')['ok']
    finally:
        session.close()


def test_cipher_injection_does_not_import_python_cryptography(tmp_path, bridge, monkeypatch):
    cipher = AESGCM(b'x'*32)
    # Force the same missing-module condition as the Android package.
    monkeypatch.setitem(sys.modules, 'cryptography', None)
    monkeypatch.setitem(sys.modules, 'cryptography.hazmat.primitives.ciphers.aead', None)
    session = bridge.Session(str(tmp_path/'chat'), 'unused', cipher, True)
    try:
        assert invoke(session, 'profile')['ok']
    finally:
        session.close()


def test_native_enrollment_proof_is_domain_separated_and_uses_persisted_identity(tmp_path, bridge):
    import base64
    from messenger.admission import message
    device = 'ab' * 16
    nonce = base64.b64encode(b'n' * 32).decode()
    session = bridge.Session(str(tmp_path/'chat'), 'unused', AESGCM(b'x'*32), True)
    try:
        card = invoke(session, 'profile')['value']
        result = json.loads(session.enrollment_proof(device, nonce))
        assert set(result) == {'chat_public', 'chat_signature'}
        assert result['chat_public'] == card['public']
        identity = RNS.Identity(create_keys=False); identity.load_public_key(bytes.fromhex(card['public']))
        signature = bytes.fromhex(result['chat_signature'])
        assert identity.validate(signature, message(card['public'], device, nonce))
        assert not identity.validate(signature, message(card['public'], 'cd'*16, nonce))
    finally: session.close()
    resumed = bridge.Session(str(tmp_path/'chat'), 'unused', AESGCM(b'x'*32), False)
    try: assert json.loads(resumed.enrollment_proof(device, nonce)) == result
    finally: resumed.close()
