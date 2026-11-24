import subprocess
import sys

import pytest

from control.friends import transport_gateway
from test_transport_enforcement import engine, envelope, event, registry, policy


def test_deadline_crossing_between_tcp_and_awg_converges(engine, registry):
    gateway, current, live, initial = engine
    event(registry)
    gateway.accept(envelope(registry))
    original = gateway.run
    crossed = []

    def crossing(arguments):
        if arguments[1] == 'show' and not crossed:
            current[0] += policy.LEASE_SECONDS
            crossed.append(True)
        return original(arguments)

    gateway.run = crossing
    gateway.apply()
    assert initial['public_key'] not in live['awg']
    assert all(item['id'] != initial['tcp_id'] for item in live['tcp'])
    assert gateway.load()['records'][initial['device']]['applied']['allowed'] is False
    event(registry, event_id='event-restored-after-crossing', now=current[0], paid_until=current[0]+7200)
    gateway.accept(envelope(registry, current[0]))
    gateway.apply()
    assert initial['public_key'] in live['awg']
    assert any(item['id'] == initial['tcp_id'] for item in live['tcp'])
    restarts = live['restarts']
    gateway.apply()
    assert live['restarts'] == restarts


def test_watcher_restart_preflight_can_take_registration_lock(engine, registry, monkeypatch):
    gateway, current, live, initial = engine
    event(registry)
    gateway.accept(envelope(registry))
    original = gateway.run
    checked = []

    def preflight(arguments):
        if arguments[:2] == ['systemctl', 'is-active']:
            current[0] += policy.LEASE_SECONDS
        if arguments[:2] == ['systemctl', 'restart']:
            subprocess.run([sys.executable, '-c',
                'import fcntl,sys; handle=open(sys.argv[1],"a"); fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)',
                str(gateway.root/'registration.lock')], check=True, timeout=2)
            checked.append(True)
        return original(arguments)

    gateway.run = preflight
    monkeypatch.setattr(transport_gateway, 'Gateway', lambda *args, **kwargs: gateway)
    def done(value):
        if value == 'WATCHDOG=1':
            raise InterruptedError('fixture completed')

    monkeypatch.setattr(transport_gateway, 'notify', done)
    with pytest.raises(InterruptedError, match='fixture completed'):
        transport_gateway.watch(gateway.gateway)
    assert checked
