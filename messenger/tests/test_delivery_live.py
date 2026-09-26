"""Real local RNS exchange, synthetic identities only."""
from messenger.codec import address
from messenger.tests.test_compact import setup_peers
from messenger.tests.test_offline import wait_for


def test_outbox_drains_and_offline_recipient_fetches_without_resending(tmp_path):
    peers, publics = setup_peers(tmp_path, 'budget-node')
    node, alice, bob = peers
    try:
        ids = [alice.call('queue', peer=address(publics[1]).hex(), text=f'hello {i}')
               for i in range(5)]
        alice.call('delivery_lifecycle', online=True, foreground=True)
        wait_for(lambda: node.call('stats')['count'] == 5)
        wait_for(lambda: not alice.call('delivery_state')['running'])
        state = alice.call('delivery_state')
        assert state['attempts'] == 2 and not state['pending']
        assert all(m['status'] == 'relayed' for m in alice.call('messages'))
        assert bob.call('messages') == []
        bob.call('delivery_lifecycle', online=True, foreground=True)
        wait_for(lambda: node.call('stats')['count'] == 0)
        wait_for(lambda: not bob.call('delivery_state')['running'])
        messages = bob.call('messages')
        assert {m['id'] for m in messages} == set(ids)
        assert all(m['status'] == 'received' and not m['outgoing'] for m in messages)
        alice.call('delivery_refresh')
        wait_for(lambda: alice.call('delivery_state')['attempts'] == 3)
        wait_for(lambda: not alice.call('delivery_state')['running'])
        assert node.call('stats')['count'] == 0
        assert all(m['status'] == 'relayed' for m in alice.call('messages'))
        assert alice.call('delivery_close') and bob.call('delivery_close')
    finally:
        for peer in reversed(peers): peer.close()
