import copy
import importlib.util
from pathlib import Path
import sys

import pytest


def validator():
    path = Path(__file__).resolve().parents[1] / 'pilot/android-telemost/mux_acceptance.py'
    spec = importlib.util.spec_from_file_location('mux_acceptance', path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module.validate_mux_evidence


def evidence():
    android = [{'event': 'family_auth', 'accepted': True},
               {'event': 'android_start', 'network': 'cellular'},
               {'event': 'mux_result', 'status': 'PASS'}]
    android += [{'event': 'mux_https', 'stream_id': index * 2 + 1,
                 'passed': True, 'end_site_tls_verified': True, 'http_status': 200} for index in range(4)]
    android += [{'event': 'mux_dns', 'query_type': kind, 'nxdomain': index == 2,
                 'rcode': 3 if index == 2 else 0, 'passed': True} for index, kind in enumerate([1, 28, 1])]
    android += [{'event': 'mux_dns_guard', 'phase': 'enabled', 'negative_probe_blocked': True},
                {'event': 'mux_dns_guard', 'phase': 'final', 'post_probe_calls': 0},
                {'event': 'mux_open', 'simultaneous': 4}]
    gateway = [{'event': 'family_auth', 'accepted': True},
               {'event': 'mux_gateway', 'stats': {'ActiveSockets': 0, 'ActiveStreams': 0, 'RetainedBytes': 0}}]
    return android, gateway


def test_mux_public_positive_fixture():
    assert validator()('public', *evidence())['status'] == 'PASS'


@pytest.mark.parametrize('failure', ['wifi', 'two_sessions', 'missing_dns', 'tls', 'duplicate_stream', 'sockets', 'buffers', 'failed', 'streams', 'sequential', 'dns_leak', 'negative_probe'])
def test_mux_evidence_rejects_incomplete_acceptance(failure):
    android, gateway = copy.deepcopy(evidence())
    if failure == 'wifi':
        android[1]['network'] = 'wifi'
    elif failure == 'two_sessions':
        gateway.append({'event': 'family_auth', 'accepted': True})
    elif failure == 'missing_dns':
        android.pop(9)
    elif failure == 'tls':
        android[3]['end_site_tls_verified'] = False
    elif failure == 'duplicate_stream':
        android[4]['stream_id'] = android[3]['stream_id']
    elif failure == 'sockets':
        gateway[1]['stats']['ActiveSockets'] = 1
    elif failure == 'buffers':
        gateway[1]['stats']['RetainedBytes'] = 1
    elif failure == 'streams':
        gateway[1]['stats']['ActiveStreams'] = 1
    elif failure == 'sequential':
        android[-1]['simultaneous'] = 1
    elif failure == 'dns_leak':
        android[-2]['post_probe_calls'] = 1
    elif failure == 'negative_probe':
        android[-3]['negative_probe_blocked'] = False
    else:
        android[2]['status'] = 'FAIL'
    with pytest.raises(RuntimeError):
        validator()('public', android, gateway)


@pytest.mark.parametrize('failure', [None, 'short_bulk', 'short_interactive', 'duplicate_stream', 'cross_stream', 'no_progress', 'isolation'])
def test_mux_mixed_acceptance(failure):
    android, gateway = evidence()
    android[-1]['simultaneous'] = 5
    bulk = {'event': 'mux_bulk', 'passed': True, 'seconds': 301, 'bytes_each_direction': 10485760}
    interactive = {'event': 'mux_interactive', 'passed': True, 'seconds': 305}
    small = [{'event': 'mux_stream', 'passed': True, 'stream': {'ID': 3+index*2, 'Sent': 25600, 'Received': 25600}} for index in range(4)]
    isolation = [{'event': 'mux_isolation', 'passed': True} for _ in range(3)]
    if failure == 'short_bulk':
        bulk['seconds'] = 299
    elif failure == 'short_interactive':
        interactive['seconds'] = 299
    elif failure == 'duplicate_stream':
        small[1]['stream']['ID'] = 3
    elif failure == 'cross_stream':
        small[0]['stream']['Received'] = 0
    elif failure == 'no_progress':
        small[0]['stream'].update(Sent=128, Received=128)
    elif failure == 'isolation':
        isolation[0]['passed'] = False
    android += [bulk, interactive, *small, *isolation]
    if failure is None:
        assert validator()('mixed', android, gateway)['status'] == 'PASS'
    else:
        with pytest.raises(RuntimeError):
            validator()('mixed', android, gateway)
