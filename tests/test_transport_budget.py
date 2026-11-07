from copy import deepcopy
import base64
import fcntl
import json
import subprocess
import sys
import time

import pytest

from control.friends import transport_gateway as module
from test_transport_enforcement import engine, envelope, event, registry


def test_full_inventory_noop_uses_three_queries_and_no_actuation(engine, registry):
    gateway, current, live, initial = engine
    snapshot = envelope(registry)
    for index in range(2, 64):
        decision = deepcopy(snapshot['decisions'][0])
        decision.update(device=f'{index:032x}', public_key=base64.b64encode(index.to_bytes(32, 'big')).decode(),
                        tcp_id=f'00000000-0000-4000-8000-{index:012x}')
        snapshot['decisions'].append(decision)
    gateway.accept(snapshot)
    gateway.apply()
    live['calls'].clear()
    gateway.apply()
    assert len(live['calls']) == 3
    assert all('set' not in call and 'restart' not in call for call in live['calls'])
    assert len(gateway.load()['records']) == 63
    assert gateway.metrics['result'] == 'complete'
    assert gateway.metrics['total'] < module.OPERATION_SECONDS


def test_lock_wait_consumes_operation_budget(engine, monkeypatch):
    gateway = engine[0]
    original = module.Operation
    monkeypatch.setattr(module, 'Operation', lambda: original(.12))
    with (gateway.root/'application.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        started = time.monotonic()
        with pytest.raises(TimeoutError, match='TRANSPORT_OPERATION_DEADLINE'):
            gateway.apply()
        assert time.monotonic()-started < .5
    assert gateway.metrics['result'] == 'error'


def test_child_and_descendant_cannot_apply_after_timeout(tmp_path):
    marker = tmp_path/'late-write'
    operation = module.Operation(.12)
    token = module.CURRENT_OPERATION.set(operation)
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            module.execute([sys.executable, '-c',
                'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",'
                '"import time,pathlib,sys; time.sleep(.4); pathlib.Path(sys.argv[1]).touch()",sys.argv[1]]); time.sleep(5)', str(marker)])
    finally:
        module.CURRENT_OPERATION.reset(token)
    time.sleep(.5)
    assert not marker.exists()


def test_commands_share_remaining_budget():
    token = module.CURRENT_OPERATION.set(module.Operation(.25))
    started = time.monotonic()
    try:
        module.execute([sys.executable, '-c', 'import time;time.sleep(.15)'])
        with pytest.raises(subprocess.TimeoutExpired):
            module.execute([sys.executable, '-c', 'import time;time.sleep(.15)'])
    finally:
        module.CURRENT_OPERATION.reset(token)
    assert time.monotonic()-started < .5


def test_failed_complete_query_is_not_empty_or_success(engine, registry):
    gateway, current, live, initial = engine
    gateway.accept(envelope(registry))
    original = gateway.run
    def malformed(arguments):
        if 'inbounduser' in arguments:
            return b'{"error":"unavailable"}'
        return original(arguments)
    gateway.run = malformed
    with pytest.raises(ValueError, match='INVALID_TCP_READBACK'):
        gateway.apply()
    assert gateway.load()['records'][initial['device']]['applied'] is None


def test_exact_xray_empty_protobuf_response(engine):
    gateway = engine[0]
    gateway.run = lambda arguments: b'{}\n\n'
    with gateway.operation():
        assert gateway.tcp_snapshot() == ({}, {})


def test_transport_pins_are_exact_and_complete():
    from control_plane.collect_inventory import HOSTS, transport_pin
    pins = {host: str(index)*64 for index, host in enumerate(HOSTS, 1)}
    for host in HOSTS:
        assert transport_pin(dict(archives=pins), host) == pins[host]
    with pytest.raises(ValueError):
        transport_pin(dict(archives={next(iter(HOSTS)): 'a'*64}), next(iter(HOSTS)))
    with pytest.raises(ValueError):
        transport_pin(dict(archives={**pins, next(iter(HOSTS)): '*'}), next(iter(HOSTS)))
