import base64
import copy
import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest
from cryptography.hazmat.primitives.serialization import Encoding

from credential_renewal import DAY, Rejected, atomic, canonical, digest, parse, read_private
from expired_recovery import DOMAIN, historical, sign, verify
from maintenance_policy import MaintenanceAuthorization
from production_controller import ProductionController
from production_transport import UNITS
from test_production_controller import ControllerFixture
from test_production_adapter import NodesFixture
from test_production_controller import LocalRpc


class RecoveryFixture(ControllerFixture):
    operation = 'expired-recovery-fixture-0002'

    def __init__(self, root, now=None):
        if now is None:
            super().__init__(root)
        else:
            self.nodes = NodesFixture(root, now=now-2*DAY)
            self.root = root/'coordinator'
            self.root.mkdir(mode=0o700)
            self.rpc = {role:LocalRpc(node) for role,node in self.nodes.nodes.items()}
            self.controller = ProductionController(self.root, self.rpc, self.nodes.fixture.fixture.validator,
                                                   clock=lambda:self.nodes.now)
            self.approval = MaintenanceAuthorization(self.nodes.operation, digest(canonical(self.actual())),
                self.nodes.now, self.nodes.now+900)
        assert self.run()['result'] == 'COMMITTED'
        self.nodes.now += 2 * DAY
        self.validator = self.nodes.fixture.fixture.validator
        self.signer = self.nodes.fixture.fixture.root_key
        from control.friends.restricted import iso
        for node in self.nodes.nodes.values():
            path = node.state.parent/'next-directory.json'
            directory = parse(read_private(path))
            directory.update(issued_at=iso(self.nodes.now - 1), expires_at=iso(self.nodes.now + 3599))
            atomic(path, canonical(directory))

    def request(self, scope=None):
        return self.controller.recovery_request(self.operation,
            self.nodes.fixture.devices if scope is None else scope)

    def bundle(self, request=None):
        return sign(self.request() if request is None else request, self.validator, self.signer, self.nodes.now)

    def apply(self, bundle, resume=False):
        approval = MaintenanceAuthorization(self.operation, digest(canonical(self.actual())), self.nodes.now,
                                            self.nodes.now + 900)
        return self.controller.run_expired(self.operation, bundle, approval=approval, resume=resume)

    def strict(self):
        snapshot, _, _, _ = self.controller.read('strict-post-recovery-0003')
        self.validator.validate(canonical(snapshot), self.nodes.now)
        return snapshot

    def closed(self):
        return all(node.barrier.stopped() for node in self.nodes.nodes.values())

    def restart_controller(self):
        self.controller = ProductionController(self.root, self.rpc, self.validator, clock=lambda:self.nodes.now)


@pytest.fixture
def recovery(tmp_path):
    return RecoveryFixture(tmp_path)


def test_expired_full_chain_and_idempotence(recovery):
    before = recovery.actual()
    request = recovery.request()
    assert recovery.actual() == before
    bundle = recovery.bundle(request)
    assert recovery.apply(bundle)['result'] == 'COMMITTED'
    successor = recovery.strict()
    assert successor['authority'] != request['predecessor']['authority']
    after = recovery.actual()
    assert recovery.apply(bundle)['idempotent'] is True
    assert recovery.actual() == after
    assert recovery.controller.run('scheduled-after-recovery-0003', scheduled=True)['result'] == 'NOOP'
    with pytest.raises(Rejected, match='RECOVERY_REPLAY_MISMATCH'):
        recovery.apply(bundle + b' ')


def test_expired_normal_paths_remain_closed(recovery):
    before = recovery.actual()
    for action in (lambda: recovery.nodes.nodes['RU'].authority_request(recovery.operation),
                   lambda: recovery.controller.run(recovery.operation),
                   lambda: recovery.controller.run(recovery.operation, scheduled=True)):
        with pytest.raises(Exception):
            action()
        assert recovery.actual() == before


@pytest.mark.parametrize('field', ['signature', 'anchor', 'scope', 'key', 'schema', 'interval'])
def test_untrusted_historical_predecessor(recovery, field):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    request = recovery.request()
    predecessor = copy.deepcopy(request['predecessor'])
    anchor = recovery.validator.anchor
    if field == 'signature':
        predecessor['authority']['signature'] = base64.b64encode(bytes(64)).decode()
    elif field == 'anchor':
        anchor = Ed25519PrivateKey.generate().public_key().public_bytes_raw()
    elif field == 'scope':
        predecessor['grants'][0]['family'] = 'b' * 32
    elif field == 'key':
        predecessor['certificate'] = recovery.nodes.fixture.old_certificates[recovery.nodes.fixture.devices[0]].public_bytes(Encoding.PEM).decode()
    elif field == 'schema':
        predecessor['unexpected'] = 1
    else:
        trust = parse(base64.b64decode(predecessor['authority']['payload']))
        trust['expires_at'] = trust['issued_at'] - 1
        payload = canonical(trust)
        predecessor['authority'] = dict(payload=base64.b64encode(payload).decode(), signature=base64.b64encode(
            recovery.signer.sign(b'family-connect/restricted-issuer/v1\0' + payload)).decode())
    before = recovery.actual()
    with pytest.raises(Rejected):
        historical(canonical(predecessor), anchor)
    assert recovery.actual() == before


@pytest.mark.parametrize('field', ['digest', 'scope', 'floor', 'successor', 'updates', 'expired', 'extra'])
def test_offline_verifier_rejects_request_mutation(recovery, field):
    request = copy.deepcopy(recovery.request())
    if field == 'digest':
        request['predecessor_sha256'] = '0' * 64
    elif field == 'scope':
        request['scope']['family'] = 'b' * 32
    elif field == 'floor':
        request['floors']['crl'] -= 1
    elif field == 'successor':
        request['successor_payload']['sequence'] -= 1
    elif field == 'updates':
        request['updates'].append('trust_anchor')
    elif field == 'expired':
        request['expires_at'] = recovery.nodes.now
    else:
        request['extra'] = True
    before = recovery.actual()
    with pytest.raises(Rejected):
        recovery.bundle(request)
    assert recovery.actual() == before


@pytest.mark.parametrize('field', ['signature', 'operation', 'successor', 'expired'])
def test_apply_rejects_bad_offline_approval(recovery, field):
    bundle = recovery.bundle()
    if field == 'expired':
        recovery.nodes.now += DAY
    else:
        envelope = parse(bundle)
        if field == 'signature':
            envelope['signature'] = base64.b64encode(bytes(64)).decode()
        else:
            payload = parse(base64.b64decode(envelope['payload']))
            if field == 'operation':
                payload['request']['operation_id'] = 'wrong-recovery-operation-0004'
            else:
                payload['authority'] = payload['request']['predecessor']['authority']
            raw = canonical(payload)
            envelope = dict(payload=base64.b64encode(raw).decode(),
                signature=base64.b64encode(recovery.signer.sign(DOMAIN + raw)).decode())
        bundle = canonical(envelope)
    before = recovery.actual()
    with pytest.raises(Rejected):
        recovery.apply(bundle)
    assert recovery.actual() == before
    assert all(not (node.state/'owner.json').exists() for node in recovery.nodes.nodes.values())


@pytest.mark.parametrize('change', ['device', 'invite', 'entitlement', 'floor', 'device_key', 'checkpoint'])
def test_authoritative_state_and_checkpoint_rejection(recovery, change):
    device = recovery.nodes.fixture.devices[0]
    with recovery.nodes.fixture.access.db() as database:
        if change in ('device', 'invite'):
            database.execute('UPDATE '+('devices' if change == 'device' else 'invites')+' SET revoked=1 WHERE device=?', (device,))
        elif change == 'floor':
            database.execute('UPDATE restricted_grants SET revision=0 WHERE device=?', (device,))
        elif change == 'device_key':
            database.execute('UPDATE devices SET public=? WHERE device=?', (base64.b64encode(bytes(64)).decode(), device))
    if change == 'entitlement':
        recovery.nodes.fixture.service.eligible_devices = set()
    if change == 'checkpoint':
        node = recovery.nodes.nodes['RU']
        atomic(node.state/'completed.json', canonical({}))
    before = recovery.actual()
    with pytest.raises(Rejected):
        recovery.request()
    assert recovery.actual() == before


@pytest.mark.parametrize('change', ['revoked', 'deleted'])
def test_removed_grants_are_not_restored(recovery, change):
    device = recovery.nodes.fixture.devices[0]
    with recovery.nodes.fixture.access.db() as database:
        if change == 'revoked':
            database.execute('UPDATE restricted_grants SET revoked=1 WHERE device=?', (device,))
        else:
            database.execute('DELETE FROM restricted_grants WHERE device=?', (device,))
    with pytest.raises(Rejected, match='RECOVERY_GRANT_SCOPE'):
        recovery.request()
    scope = recovery.nodes.fixture.devices[1:]
    request = recovery.request(scope)
    assert recovery.apply(recovery.bundle(request))['result'] == 'COMMITTED'
    rows = recovery.strict()['grants']
    assert all(row['device'] != device or row['revoked'] == 1 for row in rows)


@pytest.mark.parametrize('when', ['before_sign', 'after_sign', 'after_acquire'])
def test_stale_authorization_cas(recovery, when):
    request = recovery.request()
    def revoke():
        with recovery.nodes.fixture.access.db() as database:
            database.execute('UPDATE invites SET revoked=1 WHERE device=?', (recovery.nodes.fixture.devices[0],))
    if when == 'before_sign':
        revoke()
    bundle = recovery.bundle(request)
    if when == 'after_sign':
        revoke()
    if when == 'after_acquire':
        def fault(stage):
            if stage == 'RECOVERY_STEP_2':
                revoke()
        recovery.controller.fault = fault
        result = recovery.apply(bundle)
        assert result['result'] == 'PUBLICATION_INCOMPLETE'
        assert result['first_cause'] == 'STALE_NODE_STATE'
        assert recovery.closed()
    else:
        before = recovery.actual()
        with pytest.raises(Rejected, match='RECOVERY_STALE_APPROVAL'):
            recovery.apply(bundle)
        assert recovery.actual() == before


def test_short_locks_and_competing_owners(recovery):
    bundle = recovery.bundle()
    with recovery.controller.operation.lock():
        with pytest.raises(Rejected, match='OPERATION_BUSY'):
            recovery.apply(bundle)
    node = recovery.nodes.nodes['RU']
    node.acquire('competing-operation-owner-0004', node.inspect())
    with pytest.raises(Rejected, match='OTHER_OPERATION_RECOVERY_REQUIRED'):
        recovery.apply(bundle)
    assert node.owner('competing-operation-owner-0004')['state'] == 'ACQUIRED'


CRASH_STAGES = ['ACQUIRING'] + ['RECOVERY_STEP_'+str(index) for index in range(1, 10)] + [
    'COMMIT_DECIDED', 'DECISION_REPLICATED', 'NL_RESUMED', 'RU_RESUMED', 'CLEANING', 'COMMITTED']


@pytest.mark.parametrize('stage', CRASH_STAGES)
def test_controller_process_crash_forward_only(recovery, stage):
    bundle = recovery.bundle()
    def child():
        recovery.controller.fault = lambda current: os._exit(73) if current == stage else None
        recovery.apply(bundle)
        os._exit(99)
    process = multiprocessing.get_context('fork').Process(target=child)
    process.start()
    process.join(30)
    assert process.exitcode == 73
    record = parse(read_private(recovery.root/'transaction.json'))
    if not record['commit_decided'] and record['cursor'] >= 4:
        assert recovery.closed()
    before = recovery.actual()
    if record['state'] != 'COMMITTED':
        with pytest.raises(Rejected, match='OPERATOR_RECOVERY_REQUIRED'):
            recovery.controller.run('scheduled-competing-0004', scheduled=True)
        assert recovery.actual() == before
    recovery.restart_controller()
    assert recovery.apply(bundle, resume=True)['result'] == 'COMMITTED'
    recovery.strict()
    for node in recovery.nodes.nodes.values():
        assert not (node.state/'owner.json').exists()
    counts = json.loads((recovery.nodes.nodes['NL'].state.parent/'counts.json').read_bytes())
    assert counts['start '+UNITS['NL'][0]] == 2


@pytest.mark.parametrize('role,stage', [('RU', 'stage-issuer.json'), ('RU', 'stage-revocations.pem'),
    ('NL', 'stage-gateway.json'), ('RU', 'after-rename-issuer.json'), ('RU', 'after-rename-revocations.pem'),
    ('RU', 'after-sqlite-commit'), ('NL', 'after-rename-gateway.json')])
def test_partial_node_writes_resume(recovery, role, stage):
    bundle = recovery.bundle()
    node = recovery.nodes.nodes[role]
    def fault(current):
        if current == stage:
            node.fault = lambda value: None
            raise OSError('disposable fault')
    node.fault = fault
    result = recovery.apply(bundle)
    assert result['result'] == 'PUBLICATION_INCOMPLETE'
    assert result['first_cause'] == 'IO_OR_TRANSPORT_FAILURE'
    assert recovery.closed()
    sequence = recovery.nodes.fixture.database.snapshot()['restricted_crl_sequence'][0]['sequence']
    with pytest.raises(Rejected, match='RECOVERY_ROLLFORWARD_ONLY'):
        recovery.nodes.nodes['RU'].rollback(recovery.operation)
    recovery.restart_controller()
    result = recovery.apply(bundle, resume=True)
    assert result['result'] == 'COMMITTED' and result['first_cause'] == 'IO_OR_TRANSPORT_FAILURE'
    assert recovery.nodes.fixture.database.snapshot()['restricted_crl_sequence'][0]['sequence'] >= sequence
    recovery.strict()


@pytest.mark.parametrize('role,action', [('RU','commit-decision'), ('NL','commit-decision'),
    ('NL','resume'), ('RU','publish-directory'), ('RU','resume'), ('RU','cleanup'), ('NL','cleanup')])
def test_lost_response_after_publication_or_cleanup(recovery, role, action):
    bundle = recovery.bundle()
    def child():
        rpc = recovery.rpc[role]
        original = rpc.call
        def call(actual_action, operation, payload=None):
            result = original(actual_action, operation, payload)
            if actual_action == action:
                os._exit(74)
            return result
        rpc.call = call
        recovery.apply(bundle)
        os._exit(99)
    process = multiprocessing.get_context('fork').Process(target=child)
    process.start()
    process.join(30)
    assert process.exitcode == 74
    recovery.restart_controller()
    assert recovery.apply(bundle, resume=True)['result'] == 'COMMITTED'
    recovery.strict()


def test_expired_successor_during_partial_commit_stays_closed(recovery):
    bundle = recovery.bundle()
    recovery.rpc['NL'].fail = 'promote'
    assert recovery.apply(bundle)['result'] == 'PUBLICATION_INCOMPLETE'
    before = recovery.actual()
    recovery.nodes.now += DAY
    result = recovery.apply(bundle, resume=True)
    assert result['result'] == 'PUBLICATION_INCOMPLETE' and recovery.closed()
    assert recovery.actual() == before


def test_strict_successor_tamper_never_opens_readers(recovery):
    bundle = recovery.bundle()
    recovery.rpc['RU'].fail = 'stage'
    assert recovery.apply(bundle)['result'] == 'PUBLICATION_INCOMPLETE'
    path = recovery.root/'plan.json'
    plan = parse(read_private(path))
    plan['candidate']['certificate'] = plan['previous']['certificate']
    atomic(path, canonical(plan))
    before = recovery.actual()
    assert recovery.apply(bundle, resume=True)['result'] == 'PUBLICATION_INCOMPLETE'
    assert recovery.closed() and recovery.actual() == before


def test_stale_database_after_stage_rejected_before_first_publication(recovery):
    bundle = recovery.bundle()
    recovery.rpc['RU'].fail = 'promote'
    assert recovery.apply(bundle)['result'] == 'PUBLICATION_INCOMPLETE'
    with recovery.nodes.fixture.access.db() as database:
        database.execute('UPDATE invites SET revoked=1 WHERE device=?', (recovery.nodes.fixture.devices[0],))
    before = recovery.actual()
    result = recovery.apply(bundle, resume=True)
    assert result['result'] == 'PUBLICATION_INCOMPLETE'
    assert recovery.closed() and recovery.actual() == before


def test_scheduled_leaf_crl_after_recovery_no_authority_power(recovery):
    assert recovery.apply(recovery.bundle())['result'] == 'COMMITTED'
    before = recovery.strict()
    recovery.nodes.now += 10000
    from control.friends.restricted import iso
    for node in recovery.nodes.nodes.values():
        path = node.state.parent/'next-directory.json'
        directory = parse(read_private(path))
        directory.update(issued_at=iso(recovery.nodes.now-1), expires_at=iso(recovery.nodes.now+3599))
        atomic(path, canonical(directory))
    result = recovery.controller.run('scheduled-leaf-crl-after-0004', scheduled=True, approved_leaf_crl_schedule=True)
    assert result['result'] == 'COMMITTED'
    after = recovery.strict()
    assert after['authority'] == before['authority'] and after['grants'] == before['grants']
    assert after['crl'] != before['crl'] and after['certificate'] != before['certificate']


def test_cli_request_offline_fd_sign_apply(tmp_path, monkeypatch, capsys):
    import runtime_controller
    recovery = RecoveryFixture(tmp_path, now=int(time.time()))
    for node in recovery.nodes.nodes.values():
        node.clock = lambda: int(time.time())
    config = recovery.root/'config.json'
    atomic(config, canonical(dict(schema=1, node_config=str(recovery.root/'unused-node.json'),
        coordinator_state=str(recovery.root), nl_source_sha256='a'*64,
        ssh=dict(key='/unused', known_hosts='/unused'), approved_leaf_crl_schedule=True)))
    scope = recovery.root/'scope.json'
    request_path, bundle_path = recovery.root/'request.json', recovery.root/'bundle.json'
    atomic(scope, canonical(recovery.nodes.fixture.devices))
    monkeypatch.setattr(runtime_controller, 'construct', lambda path: (recovery.nodes.nodes['RU'], 'a'*64))
    monkeypatch.setattr(runtime_controller, 'SshNode', lambda *args, **kwargs: recovery.rpc['NL'])
    common = ['runtime_controller.py', '--config', str(config), '--operation', recovery.operation]
    monkeypatch.setattr(sys, 'argv', common+['--mode', 'expired-request', '--grant-scope', str(scope),
                                           '--request-output', str(request_path)])
    runtime_controller.main()
    assert json.loads(capsys.readouterr().out)['result'] == 'RECOVERY_REQUESTED'
    anchor = recovery.root/'anchor.pub'
    atomic(anchor, base64.b64encode(recovery.validator.anchor))
    read_fd, write_fd = os.pipe()
    try:
        os.write(write_fd, recovery.signer.private_bytes_raw())
        os.close(write_fd)
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('sign_authority_offline.py')),
            '--request', str(request_path), '--anchor', str(anchor), '--root-key-fd', str(read_fd),
            '--output', str(bundle_path), '--expired-recovery', '--confirm-authority-renewal'],
            pass_fds=(read_fd,), capture_output=True, timeout=20, check=False)
    finally:
        os.close(read_fd)
    assert result.returncode == 0, result.stdout
    assert json.loads(result.stdout)['result'] == 'SIGNED_OFFLINE'
    monkeypatch.setattr(sys, 'argv', common+['--mode', 'expired-apply', '--authority-bundle', str(bundle_path),
                                           '--approve-maintenance-outage'])
    runtime_controller.main()
    assert json.loads(capsys.readouterr().out)['result'] == 'COMMITTED'
    recovery.nodes.now = int(time.time())
    recovery.strict()


def test_failed_gateway_start_is_not_retried(recovery):
    bundle = recovery.bundle()
    node = recovery.nodes.nodes['NL']
    (node.state.parent/'reject-start').write_bytes(b'fixture')
    result = recovery.apply(bundle)
    assert result['result'] == 'PUBLICATION_INCOMPLETE' and recovery.closed()
    counts = json.loads((node.state.parent/'counts.json').read_bytes())
    assert counts['start '+UNITS['NL'][0]] == 2
    assert recovery.apply(bundle, resume=True)['result'] == 'PUBLICATION_INCOMPLETE'
    assert json.loads((node.state.parent/'counts.json').read_bytes())['start '+UNITS['NL'][0]] == 2
    assert recovery.closed()
