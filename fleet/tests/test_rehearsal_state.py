from types import SimpleNamespace

import pytest

from fleet.contracts import FleetError, canonical, digest
from fleet.acceptance import SCOPE, STEPS, sign
from fleet.materials import public_hex
from fleet.rehearsal_state import RehearsalState
from fleet.tests.test_permit import authority


@pytest.fixture
def state(authority, tmp_path):
    key, permit, arguments = authority
    runtime = SimpleNamespace(current=None, calls=[], broken=set(), stopped=True)
    runtime.authority = key.public_key()
    runtime.test_signer = key
    def switch(target):
        runtime.current = target
        runtime.calls.append(('switch', target))
    def accept(target, fresh):
        if target in runtime.broken:
            raise RuntimeError('sensitive-key-not-for-receipts')
        return dict(scope='fixture-not-physical-data-plane', result=True)
    def stop():
        runtime.stopped = True
    def start(target):
        runtime.stopped = False
    runtime.switch = switch
    runtime.accept = accept
    runtime.stop = stop
    runtime.start = start
    runtime.stage = lambda target: runtime.calls.append(('stage', target))
    runtime.configure = lambda target: runtime.calls.append(('configure', target))
    runtime.enrolled_identity = lambda: 'a'*64
    runtime.reboot_check = lambda target, identity: runtime.calls.append(('reboot', target))
    runtime.drain = stop
    runtime.retire = lambda: runtime.calls.append(('retire', None))
    return RehearsalState(tmp_path/'state', permit, runtime, clock=lambda: 1001)


def request(state, action, suffix='', bundle='a'):
    return dict(operation_id=action+suffix, action=action, bundle_id=state.permit['body']['bundle_'+bundle], parameters={})


def active(state):
    assert state.execute(request(state,'stage'))['result']=='PASS'
    assert state.execute(request(state,'start-verification'))['result']=='AWAITING_EXTERNAL_ACCEPTANCE'
    complete(state)
    assert state.execute(request(state,'activate-local'))['result']=='PASS'
    assert state.status()['state'] == 'ACTIVE'


def external(state):
    challenge = state.status()['verification']
    body = {name:challenge[name] for name in ('instance_id','bundle_id','operation_id','verification_nonce','ipv4','local_health_sha256')}
    body.update(schema=1,scope=SCOPE,roles={role:{step:'PASS' for step in steps} for role,steps in STEPS.items()},
                issued_at=1001,expires_at=1200,external_evidence_sha256='e'*64,cleanup='PASS',
                signer=digest(bytes.fromhex(public_hex(state.runtime.test_signer.public_key()))))
    return sign(body,state.runtime.test_signer,now=1001)


def complete(state, suffix='', bundle='a'):
    operation = request(state,'complete-verification',suffix,bundle=bundle)
    operation['parameters'] = {'receipt':external(state)}
    assert state.execute(operation)['result']=='PASS'


def test_stage_replay_and_active_boundary(state):
    receipt = state.execute(request(state,'stage'))
    assert state.execute(request(state,'stage')) == receipt
    assert len(state.runtime.calls) == 1
    rejected = state.execute(request(state,'activate-local'))
    assert rejected['result'] == 'FAIL'
    assert state.status()['state'] != 'ACTIVE'


def test_upgrade_failure_rollback_reboot_and_retirement(state):
    active(state)
    original = state.status()['actual_bundle']
    target = state.permit['body']['bundle_b']
    assert state.execute(request(state,'stage','-b',bundle='b'))['result'] == 'PASS'
    state.runtime.broken.add(target)
    failure = state.execute(request(state,'upgrade','-injected',bundle='b'))
    assert failure['result'] == 'FAIL' and failure['rollback'] == 'PASS'
    assert state.runtime.current == original
    assert b'sensitive' not in canonical(failure)
    state.runtime.broken.clear()
    assert state.execute(request(state,'upgrade','-success',bundle='b'))['result'] == 'AWAITING_EXTERNAL_ACCEPTANCE'
    complete(state,'-b',bundle='b')
    assert state.execute(request(state,'activate-local','-b',bundle='b'))['result']=='PASS'
    assert state.runtime.current == target
    assert state.execute(request(state,'rollback'))['result'] == 'AWAITING_EXTERNAL_ACCEPTANCE'
    complete(state,'-rollback')
    assert state.execute(request(state,'activate-local','-rollback'))['result']=='PASS'
    assert state.runtime.current == original
    assert state.execute(request(state,'reboot-verify'))['result'] == 'PASS'
    assert state.execute(request(state,'drain'))['result'] == 'PASS'
    assert state.runtime.stopped
    assert state.execute(request(state,'retire'))['result'] == 'PASS'
    assert state.status()['state'] == 'RETIRED'
    with pytest.raises(FleetError):
        state.execute(request(state,'stage','-after-retire'))


def test_rollback_failure_fences_mutations(state):
    active(state)
    state.execute(request(state,'stage','-b',bundle='b'))
    state.runtime.broken.update((state.permit['body']['bundle_a'], state.permit['body']['bundle_b']))
    failure = state.execute(request(state,'upgrade',bundle='b'))
    assert failure['rollback'] == 'FAIL'
    assert state.status()['fenced']
    assert state.status()['state'] == 'QUARANTINED'
    with pytest.raises(FleetError, match='fenced'):
        state.execute(request(state,'drain'))


def test_changed_replay_and_no_untrusted_parameters(state):
    original = request(state,'stage')
    state.execute(original)
    original['parameters'] = {'shell':'untrusted'}
    with pytest.raises(FleetError, match='replay_changed'):
        state.execute(original)
    new = request(state,'stage','-bad')
    new['parameters'] = {'argv':['untrusted']}
    assert state.execute(new)['result'] == 'FAIL'


def test_identity_cannot_change(state):
    state.execute(request(state,'stage'))
    state.runtime.enrolled_identity = lambda: 'b'*64
    assert state.execute(request(state,'stage','-other'))['result'] == 'FAIL'
