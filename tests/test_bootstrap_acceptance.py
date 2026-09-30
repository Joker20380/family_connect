import copy
import importlib.util
from pathlib import Path

import pytest


path = Path(__file__).resolve().parents[1] / 'pilot/android-telemost/bootstrap_acceptance.py'
spec = importlib.util.spec_from_file_location('bootstrap_acceptance', path)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def evidence():
    prepared = [{'event': 'bootstrap_cache_stored'}, {'event': 'android_exit', 'code': 0}]
    recovered = [{'event': name} for name in [
        'android_start', 'bootstrap_normal_control_unavailable', 'bootstrap_cache_loaded',
        'bootstrap_carrier_connected', 'bootstrap_family_auth', 'bootstrap_descriptor_received',
        'bootstrap_closed_before_dedicated', 'start', 'connected', 'family_auth', 'mux_open']]
    recovered[0].update(network='cellular', android='12', abi='arm64-v8a', model='Redmi Note 9 Pro')
    next(row for row in recovered if row['event'] == 'start')['room_method'] = 'cached bootstrap Telemost rendezvous'
    next(row for row in recovered if row['event'] == 'family_auth')['accepted'] = True
    recovered += [{'event': 'mux_https', 'passed': True, 'end_site_tls_verified': True, 'http_status': 200, 'stream_id': index} for index in range(4)]
    recovered += [{'event': 'mux_dns', 'passed': True, 'query_type': query, 'rcode': code, 'nxdomain': code == 3} for query, code in [(1, 0), (28, 0), (1, 3)]]
    recovered += [{'event': 'mux_result', 'status': 'PASS'}, {'event': 'android_exit', 'code': 0, 'cancelled': False}]
    gateway = [{'event': name} for name in ['bootstrap_seed_ready', 'bootstrap_family_auth', 'CREATING', 'CREATED', 'GATEWAY_JOINING', 'READY', 'CLIENT_ISSUED', 'bootstrap_handoff', 'family_auth', 'ACTIVE', 'dedicated_resources_closed']]
    return prepared, recovered, gateway


def test_acceptance_requires_complete_evidence():
    assert runner.validate(*evidence(), restarted=True)['bootstrap'] == 'PASS'
    with pytest.raises(RuntimeError):
        runner.validate(*evidence(), restarted=False)


@pytest.mark.parametrize('event', [
    'bootstrap_normal_control_unavailable', 'bootstrap_cache_loaded', 'bootstrap_carrier_connected',
    'bootstrap_family_auth', 'bootstrap_descriptor_received', 'bootstrap_closed_before_dedicated',
    'connected', 'family_auth', 'mux_result', 'android_exit'])
def test_missing_recovery_proof_is_not_pass(event):
    prepared, recovered, gateway = evidence()
    recovered = [row for row in recovered if row['event'] != event]
    with pytest.raises(RuntimeError):
        runner.validate(prepared, recovered, gateway, restarted=True)


@pytest.mark.parametrize('event', ['bootstrap_seed_ready', 'bootstrap_family_auth', 'READY', 'ACTIVE', 'dedicated_resources_closed'])
def test_gateway_proof_required(event):
    prepared, recovered, gateway = evidence()
    gateway = [row for row in gateway if row['event'] != event]
    with pytest.raises(RuntimeError):
        runner.validate(prepared, recovered, gateway, restarted=True)


def test_order_ordinary_control_manual_room_and_failed_dns_rejected():
    original = evidence()
    for fault in ['order', 'refresh', 'manual', 'dns', 'https', 'wifi']:
        prepared, recovered, gateway = copy.deepcopy(original)
        if fault == 'order': gateway[5], gateway[6] = gateway[6], gateway[5]
        if fault == 'refresh': recovered.append({'event': 'bootstrap_cache_stored'})
        if fault == 'manual': next(row for row in recovered if row['event'] == 'start')['room_method'] = 'operator-provided disposable room'
        if fault == 'dns': recovered = [row for row in recovered if row.get('query_type') != 28]
        if fault == 'https': next(row for row in recovered if row['event'] == 'mux_https')['passed'] = False
        if fault == 'wifi': recovered[0]['network'] = 'wifi'
        with pytest.raises(RuntimeError): runner.validate(prepared, recovered, gateway, restarted=True)
