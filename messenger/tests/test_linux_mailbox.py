import json
import base64
from pathlib import Path
import socket
import threading
import time

import RNS
import pytest

from messenger.local import LocalChat
from messenger.tests.test_offline import Peer
from provisioning.chat_transport import SystemMailbox
from messenger.tests.test_linux_owner import owner_factory


@pytest.mark.parametrize('mode', [None, 16, 7, 8, 9])
def test_two_owners_real_mailbox_and_recipient_storage_ack(tmp_path, chat_runtime, mode):
    alice = LocalChat(tmp_path / 'alice', b'a' * 32, create=True, platform='linux', version=2011)
    bob = LocalChat(tmp_path / 'bob', b'b' * 32, create=True, platform='android', version=118)
    alice._chat.durable_delivery = bob._chat.durable_delivery = True
    for sender, recipient in ((alice, bob), (bob, alice)):
        card = recipient.profile()
        sender.trust_contact(card['public'], card['fingerprint'])
    allowed = tmp_path / 'allowed.json'
    allowed.write_text(json.dumps([alice.profile()['public'], bob.profile()['public']]))
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    node = Peer('budget-node', tmp_path / 'node', port, script='closed_peer.py', extra=[str(allowed)])
    baseline = list(RNS.Transport.interfaces)
    lease = dict(host='127.0.0.1', port=port, public_key=node.info['public'], expires_at=int(time.time()) + 120)
    send = SystemMailbox(alice._chat, lease, chat_runtime)
    receive = SystemMailbox(bob._chat, lease, chat_runtime)
    try:
        if mode is None:
            message = alice.queue(bob.profile()['address'], 'Byte-exact Привет ' + 'Ж' * 500)
        else:
            raw = ((Path(__file__).parent / 'fixtures/voice-tone.opus').read_bytes() if mode == 16
                   else bytes({7: 200, 8: 300, 9: 400}[mode]))
            arguments = dict(address=bob.profile()['address'], audio=base64.b64encode(raw).decode())
            message = (alice.queue_audio(**arguments) if mode == 16 else
                       alice.queue_radio(**arguments, mode=mode, confirmed=True))
        assert send.exchange(timeout=20).relayed == 1
        assert alice.history(bob.profile()['address'])['messages'][0]['status'] == 'relayed'
        assert receive.exchange(timeout=20).received.stored == 1
        assert send.exchange(timeout=20).received.stored >= 0
        actual = alice.history(bob.profile()['address'])['messages'][0]
        assert actual['status'] == 'recipient_stored'
        assert actual['id'] == message
        assert bob.history(alice.profile()['address'])['messages'][0]['text'] == actual['text']
        if mode is not None:
            received = bob.audio(message)
            assert received['mode'] == mode and base64.b64decode(received['audio']) == raw
        assert send.route == receive.route == 'SYSTEM'
        assert list(RNS.Transport.interfaces) == baseline
        cancelled = threading.Event()
        cancelled.set()
        from messenger.mailbox import MailboxError
        with pytest.raises(MailboxError, match='cancelled'):
            send.exchange(cancel=cancelled)
        assert list(RNS.Transport.interfaces) == baseline
    finally:
        send.close()
        receive.close()
        alice.close()
        bob.close()
        node.close()


def test_background_owner_receives_without_visible_ui_and_persists_notification_receipt(tmp_path, owner_factory, chat_runtime):
    alice, bob = owner_factory('background-alice'), owner_factory('background-bob')
    first, second = alice.open(create=True), bob.open(create=True)
    alice.invoke('trust_contact', public=second['public'], fingerprint=second['fingerprint'])
    bob.invoke('trust_contact', public=first['public'], fingerprint=first['fingerprint'])
    bob.invoke('inbox')
    allowed = tmp_path / 'background-allowed.json'
    allowed.write_text(json.dumps([first['public'], second['public']]))
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    node = Peer('budget-node', tmp_path / 'background-node', port, script='closed_peer.py', extra=[str(allowed)])
    lease = dict(host='127.0.0.1', port=port, public_key=node.info['public'], expires_at=int(time.time()) + 120)
    sender = SystemMailbox(alice.local._chat, lease, chat_runtime)
    try:
        message = alice.invoke('queue', address=second['address'], text='Hidden-window real mailbox delivery')
        assert sender.exchange(timeout=20).relayed == 1
        bob.node = lease
        bob.carrier = bob.local.attach_carrier(lambda chat: SystemMailbox(chat, lease, chat_runtime))
        bob.tick(online=True, visible=False, background=True)
        deadline = time.monotonic() + 25
        while not bob.invoke('inbox') and time.monotonic() < deadline:
            time.sleep(.05)
        inbox = bob.invoke('inbox')
        assert [item['id'] for item in inbox] == [message]
        assert not inbox[0]['notified'] and not inbox[0]['read']
        batch = bob.invoke('notification_snapshot')['batches'][0]
        assert 'Hidden-window' not in json.dumps(batch)
        bob.invoke('notification_posted', peer=batch['peer'], receipts=batch['receipts'])
        bob.invoke('background_delivery', enabled=False)
        bob.tick(online=True, visible=False, background=True)
        bob.close()
        assert bob.open() == second
        assert bob.invoke('inbox')[0]['notified'] and not bob.invoke('inbox')[0]['read']
    finally:
        sender.close()
        bob.close()
        node.close()
