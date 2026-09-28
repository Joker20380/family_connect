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
                {'event': 'mux_dns_guard', 'phase': 'final', 'post_probe_calls': 0}]
    gateway = [{'event': 'family_auth', 'accepted': True},
               {'event': 'mux_gateway', 'stats': {'ActiveSockets': 0, 'RetainedBytes': 0}}]
    return android, gateway


def test_mux_public_positive_fixture():
    assert validator()('public', *evidence())['status'] == 'PASS'


@pytest.mark.parametrize('failure', ['wifi', 'two_sessions', 'missing_dns', 'tls', 'duplicate_stream', 'sockets', 'buffers', 'failed'])
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
    else:
        android[2]['status'] = 'FAIL'
    with pytest.raises(RuntimeError):
        validator()('public', android, gateway)
