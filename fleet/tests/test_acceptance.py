import copy

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from fleet.acceptance import sign
from fleet.contracts import FleetError
from fleet.tests.test_permit import authority
from fleet.tests.test_rehearsal_state import complete, external, request, state


def awaiting(state):
    state.execute(request(state,'stage'))
    receipt = state.execute(request(state,'start-verification'))
    assert receipt['result']=='AWAITING_EXTERNAL_ACCEPTANCE'
    return state.status()['verification']


def test_absent_receipt_does_not_rollback(state):
    challenge = awaiting(state)
    result = state.execute(request(state,'complete-verification'))
    assert result['result']=='AWAITING_EXTERNAL_ACCEPTANCE'
    assert result['rollback'] is None
    assert state.status()['verification']==challenge
    assert state.runtime.stopped is False


@pytest.mark.parametrize('field,value', [('verification_nonce','f'*64), ('bundle_id','gw-'+'f'*32),
    ('instance_id','fleet-rehearsal-other'), ('operation_id','other'), ('ipv4','1.1.1.1'),
    ('local_health_sha256','f'*64), ('issued_at',900)])
def test_wrong_signed_receipt(state, field, value):
    awaiting(state)
    receipt = external(state)
    receipt['body'][field] = value
    receipt = sign(receipt['body'],state.runtime.test_signer,now=1001)
    operation = request(state,'complete-verification')
    operation['parameters']={'receipt':receipt}
    assert state.execute(operation)['result']=='FAIL'
    assert state.status()['state']=='AWAITING_EXTERNAL_ACCEPTANCE'


def test_forged_expired_and_local_drift(state):
    awaiting(state)
    operation = request(state,'complete-verification','-forged')
    receipt = external(state)
    receipt['signature']='A'*88
    operation['parameters']={'receipt':receipt}
    assert state.execute(operation)['result']=='FAIL'
    operation = request(state,'complete-verification','-expired')
    receipt = external(state)
    state.clock = lambda:1200
    operation['parameters']={'receipt':receipt}
    assert state.execute(operation)['result']=='FAIL'
    state.clock=lambda:1001
    operation = request(state,'complete-verification','-drift')
    operation['parameters']={'receipt':external(state)}
    state.runtime.accept=lambda target,fresh:dict(changed=True)
    assert state.execute(operation)['result']=='FAIL'


def test_verified_and_replay(state):
    awaiting(state)
    operation=request(state,'complete-verification')
    operation['parameters']={'receipt':external(state)}
    receipt=state.execute(operation)
    assert receipt['result']=='PASS' and state.status()['state']=='VERIFIED'
    assert state.execute(operation)==receipt
    changed=copy.deepcopy(operation)
    changed['parameters']['receipt']['body']['verification_nonce']='f'*64
    with pytest.raises(FleetError,match='replay_changed'):
        state.execute(changed)


def test_nonce_is_generated_after_start(state):
    challenge=awaiting(state)
    assert len(challenge['verification_nonce'])==64
    assert state.runtime.current==challenge['bundle_id'] and not state.runtime.stopped
    assert state.execute(request(state,'complete-verification'))['result']=='AWAITING_EXTERNAL_ACCEPTANCE'
    assert state.execute(request(state,'activate-local'))['result']=='FAIL'
    assert state.status()['state']=='AWAITING_EXTERNAL_ACCEPTANCE'
