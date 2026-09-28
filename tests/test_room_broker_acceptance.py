import copy
import importlib.util
from pathlib import Path

import pytest


def validator():
    path = Path(__file__).resolve().parents[1] / 'pilot/android-telemost/room_broker_acceptance.py'
    spec = importlib.util.spec_from_file_location('room_broker_acceptance', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate


def evidence():
    gateway = [{'event': stage} for stage in ('CREATING', 'CREATED', 'GATEWAY_JOINING', 'READY', 'CLIENT_ISSUED', 'family_auth', 'ACTIVE')]
    android = [{'event': 'start', 'room_method': 'authenticated automatic broker'},
               {'event': 'family_auth', 'accepted': True},
               {'event': 'mux_result', 'status': 'PASS'},
               {'event': 'android_exit', 'code': 0}]
    android += [{'event': 'mux_https', 'passed': True, 'end_site_tls_verified': True, 'http_status': 200} for _ in range(4)]
    return gateway, android


def test_automatic_broker_evidence():
    assert validator()(*evidence())['manual_room'] is False


@pytest.mark.parametrize('mutation', ['missing_ready', 'early_issue', 'manual', 'tls', 'https', 'exit', 'duplicate_create'])
def test_automatic_evidence_fail_closed(mutation):
    gateway, android = copy.deepcopy(evidence())
    if mutation == 'missing_ready':
        gateway.pop(3)
    elif mutation == 'early_issue':
        gateway[3], gateway[4] = gateway[4], gateway[3]
    elif mutation == 'manual':
        android[0]['room_method'] = 'operator-provided disposable room'
    elif mutation == 'tls':
        android[1]['accepted'] = False
    elif mutation == 'https':
        android[-1]['end_site_tls_verified'] = False
    elif mutation == 'exit':
        android[3]['code'] = 1
    else:
        gateway.insert(0, {'event': 'CREATING'})
    with pytest.raises(RuntimeError):
        validator()(gateway, android)
