import base64
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import sqlite3
import uuid

import pytest

from test_fenced_rollback import rolled_back, RESULT
from test_activated_maintenance import Rejected, atomic, canonical, digest, parse
from device_identity.device import DeviceIdentity
from control.friends.access import Access
from grant_cutover import append_only_registry_overlay, restricted_projection
from node import dispatch


def device_row():
    identity = DeviceIdentity.generate()
    return dict(device=Access.binding(identity.public_identity,identity.wireguard_public_key),
                public=identity.public_identity,wg=identity.wireguard_public_key,tcp=str(uuid.uuid4()),revoked=0)


def additions(cluster, devices=2, invites=2):
    rows = [device_row() for _ in range(devices)]
    with cluster.nodes['RU'].database.connect(write=True) as database:
        for row in rows:
            database.execute('INSERT INTO devices VALUES (?,?,?,?,?)',tuple(row.values()))
        for index in range(invites):
            database.execute('INSERT INTO invites VALUES (?,?,0)',
                (hashlib.sha256(('synthetic-overlay-'+str(index)).encode()).hexdigest(),rows[index]['device'] if index < devices else None))
    return rows


@pytest.fixture
def overlay_cluster(rolled_back):
    rolled_back.now += 3000
    rolled_back.controller.save(rolled_back.record,'RECOVERY_REQUIRED')
    return rolled_back


def request(cluster):
    return dict(expected_database_sha256=cluster.record['before']['RU']['database_sha256'],controller_operation_sha256='a'*64)


def prove(cluster):
    return cluster.nodes['RU'].rollback_registry_overlay(cluster.record['operation_id'],request(cluster))


def recover(cluster):
    record = parse((cluster.controller.root/'transaction.json').read_bytes())
    return cluster.controller.recover(record,preserve_registry_overlay=True)


@pytest.mark.parametrize('devices,invites', [(0,0),(1,0),(0,1),(2,2)])
def test_append_only_valid_additions_and_zero_overlay(overlay_cluster, devices, invites):
    cluster = overlay_cluster
    additions(cluster,devices,invites)
    proof = prove(cluster)
    assert (proof['devices_added'],proof['invites_added']) == (devices,invites)
    assert all(proof[name] is True for name in ('schema_exact','foreign_keys_valid','restricted_state_exact','baseline_rows_preserved'))
    assert proof == prove(cluster)
    assert not {'devices','invites','public','wg','tcp','hash'} & set(proof)


@pytest.mark.parametrize('table,change', [('devices','update'),('invites','update'),('devices','delete'),
                                       ('invites','delete'),('devices','collision'),('invites','collision')])
def test_historical_rows_and_primary_keys_never_relaxed(overlay_cluster, table, change):
    before = overlay_cluster.nodes['RU'].database.snapshot()
    current = deepcopy(before)
    if change == 'update':
        current[table][0]['revoked'] = 1-current[table][0]['revoked']
    elif change == 'delete':
        current[table].pop()
    else:
        current[table].append(deepcopy(current[table][0]))
    with pytest.raises(Rejected):
        append_only_registry_overlay(before,current)


@pytest.mark.parametrize('table,change', [('restricted_grants','add'),('restricted_grants','change'),
    ('restricted_certificates','add'),('restricted_certificates','change'),('restricted_crl_sequence','change')])
def test_restricted_projection_must_remain_exact(overlay_cluster, table, change):
    before = overlay_cluster.nodes['RU'].database.snapshot()
    if not before[table]:
        before[table].append(dict(synthetic='baseline'))
    current = deepcopy(before)
    if change == 'add':
        current[table].append(dict(synthetic='addition'))
    else:
        current[table][0]['synthetic_change'] = True
    with pytest.raises(Rejected,match='ROLLBACK_RESTRICTED_STATE_CHANGED'):
        append_only_registry_overlay(before,current)


@pytest.mark.parametrize('field,value', [('public','bad'),('wg','bad'),('device','0'*32),('tcp','bad'),('revoked',2)])
def test_added_device_validation(overlay_cluster, field, value):
    before = overlay_cluster.nodes['RU'].database.snapshot()
    current = deepcopy(before)
    row = device_row()
    row[field] = value
    current['devices'].append(row)
    with pytest.raises(Rejected,match='ROLLBACK_REGISTRY_INVALID'):
        append_only_registry_overlay(before,current)


@pytest.mark.parametrize('field,value', [('hash','bad'),('device','f'*32),('revoked',2)])
def test_added_invite_validation(overlay_cluster, field, value):
    before = overlay_cluster.nodes['RU'].database.snapshot()
    current = deepcopy(before)
    row = dict(hash='e'*64,device=None,revoked=0)
    row[field] = value
    current['invites'].append(row)
    with pytest.raises(Rejected):
        append_only_registry_overlay(before,current)


def test_schema_change_rejected(overlay_cluster):
    node = overlay_cluster.nodes['RU']
    with sqlite3.connect(node.database.path) as database:
        database.execute('ALTER TABLE invites ADD COLUMN extra TEXT')
    with pytest.raises(Rejected,match='ROLLBACK_DATABASE_SCHEMA_CHANGED'):
        prove(overlay_cluster)


def test_foreign_key_failure_rejected(overlay_cluster):
    node = overlay_cluster.nodes['RU']
    with sqlite3.connect(node.database.path) as database:
        database.execute('INSERT INTO restricted_grants VALUES (?,?,1,NULL,0)',('f'*32,'a'*32))
    with pytest.raises(Rejected,match='ROLLBACK_FOREIGN_KEY_FAILURE'):
        prove(overlay_cluster)


def test_quick_check_failure_rejected(overlay_cluster, monkeypatch):
    original = sqlite3.connect
    class InvalidConnection(sqlite3.Connection):
        def execute(self, sql, *arguments):
            if sql == 'PRAGMA quick_check':
                return super().execute("SELECT 'synthetic integrity failure'")
            return super().execute(sql,*arguments)
    monkeypatch.setattr(sqlite3,'connect',lambda *args,**kwargs: original(*args,**kwargs,factory=InvalidConnection))
    with pytest.raises(Rejected,match='DATABASE_INVALID'):
        prove(overlay_cluster)


@pytest.mark.parametrize('obstacle', ['non-database','active','expected-hash','operator-snapshot','controller-hash','future'])
def test_narrow_proof_gates(overlay_cluster, obstacle, monkeypatch):
    cluster = overlay_cluster
    node = cluster.nodes['RU']
    payload = request(cluster)
    if obstacle == 'non-database':
        original = node.inspect
        monkeypatch.setattr(node,'inspect',lambda: dict(original(),extra='changed'))
    elif obstacle == 'active':
        node.barrier.quiet = False
    elif obstacle == 'expected-hash':
        plan = parse((node.state/'plan.json').read_bytes())
        plan['grant_plan']['before_sha256'] = '0'*64
        atomic(node.state/'plan.json',canonical(plan))
    elif obstacle == 'operator-snapshot':
        payload['expected'] = node.database.snapshot()
    elif obstacle == 'controller-hash':
        payload['expected_database_sha256'] = '0'*64
    else:
        cluster.now -= 16000
    with pytest.raises(Rejected):
        node.rollback_registry_overlay(cluster.record['operation_id'],payload)
    assert not (node.state/'rollback-registry-overlay.json').exists()


def test_proof_stale_after_later_addition_no_new_receipt(overlay_cluster):
    node = overlay_cluster.nodes['RU']
    prove(overlay_cluster)
    raw = (node.state/'rollback-registry-overlay.json').read_bytes()
    additions(overlay_cluster,1,1)
    with pytest.raises(Rejected,match='ROLLBACK_REGISTRY_OVERLAY_STALE'):
        prove(overlay_cluster)
    assert (node.state/'rollback-registry-overlay.json').read_bytes() == raw


def test_proof_no_database_write_or_owner_change(overlay_cluster, monkeypatch):
    cluster = overlay_cluster
    additions(cluster)
    node = cluster.nodes['RU']
    owner = (node.state/'owner.json').read_bytes()
    raw = node.database.path.read_bytes()
    statements = []
    original = node.database.connect
    @contextmanager
    def readonly(write=False):
        assert not write
        with original() as database:
            database.set_trace_callback(statements.append)
            yield database
    monkeypatch.setattr(node.database,'connect',readonly)
    prove(cluster)
    assert node.database.path.read_bytes() == raw and (node.state/'owner.json').read_bytes() == owner
    assert all(not sql.lstrip().upper().startswith(('INSERT','UPDATE','DELETE','CREATE','ALTER','REPLACE')) for sql in statements)


def test_normal_paths_still_exact_and_nl_cannot_use_overlay(overlay_cluster):
    cluster = overlay_cluster
    additions(cluster)
    node = cluster.nodes['RU']
    prove(cluster)
    with pytest.raises(Rejected,match='ROLLBACK_READBACK_MISMATCH'):
        node.previous_readback(cluster.record['operation_id'])
    with pytest.raises(Rejected,match='NODE_ROLE'):
        cluster.nodes['NL'].rollback_registry_overlay(cluster.record['operation_id'],request(cluster))
    with pytest.raises(Rejected,match='ROLLBACK_DATABASE_UNEXPECTED'):
        node.rollback(cluster.record['operation_id'])
    plan = parse((node.state/'plan.json').read_bytes())
    _,_,issuer,_,_ = node.validator.validate(canonical(plan['candidate']),cluster.now)
    with pytest.raises(Rejected,match='STALE_DATABASE'):
        node.database.apply(plan['grant_plan'],plan['candidate']['crl'].encode(),issuer,plan['grant_plan']['issued_at'],
                            readers_quiesced=node.barrier.stopped)


def test_controller_terminalization_preserves_overlay_history_and_fresh_state(overlay_cluster):
    cluster = overlay_cluster
    additions(cluster)
    node = cluster.nodes['RU']
    before = node.database.path.read_bytes()
    expected_record = deepcopy(cluster.record['before'])
    plan_raw = (node.state/'plan.json').read_bytes()
    owner = parse((node.state/'owner.json').read_bytes())
    assert recover(cluster)['result'] == RESULT
    record = parse((cluster.controller.root/'transaction.json').read_bytes())
    assert record['state'] == 'ABORTED' and record['first_cause'] == 'DIRECTORY_INVALID' and not record['commit_decided']
    assert record['before'] == expected_record and record['historical_expected_state_unchanged'] is True
    assert record['registry_overlay_preserved'] is True and record['registry_devices_added'] == record['registry_invites_added'] == 2
    assert node.database.path.read_bytes() == before
    archive = node.state/'archive'/record['operation_id']
    assert (archive/'plan.json').read_bytes() == plan_raw
    assert parse((archive/'owner-before-cleanup.json').read_bytes())['expected_state'] == owner['expected_state']
    proof = parse((archive/'rollback-registry-overlay.json').read_bytes())
    terminal = parse((archive/'rollback-terminal.json').read_bytes())
    assert terminal['registry_overlay_receipt_sha256'] == digest(canonical(proof))
    assert record['fenced_rollback']['registry_overlay_receipt_sha256'] == digest(canonical(proof))
    assert 'registry_overlay_receipt_sha256' not in parse((cluster.nodes['NL'].state/'archive'/record['operation_id']/'rollback-terminal.json').read_bytes())
    assert all(member.barrier.starts == 0 and member.barrier.stopped() for member in cluster.nodes.values())
    assert node.cleanup(record['operation_id'])['result'] == 'CLEANED_FENCED_ROLLBACK'
    assert cluster.scheduled('fresh-overlay')['result'] == 'COMMITTED'
    fresh = parse((cluster.controller.root/'plan.json').read_bytes())
    assert fresh['grant_plan']['before']['devices'] == node.database.snapshot()['devices']


@pytest.mark.parametrize('stage', ['registry-overlay-receipt','rollback-terminal-receipt','aborted-fenced',
    'archive-rollback-registry-overlay.json','archive-plan.json','completed-ledger'])
def test_overlay_fault_replay_preserves_additions(overlay_cluster, stage):
    cluster = overlay_cluster
    additions(cluster)
    node = cluster.nodes['RU']
    before = node.database.path.read_bytes()
    def fail(current):
        if current == stage:
            raise OSError('synthetic overlay failure')
    node.fault = fail
    assert recover(cluster)['result'] in ('RECOVERY_REQUIRED','CLEANUP_REQUIRED')
    assert node.database.path.read_bytes() == before
    node.fault = lambda current: None
    assert recover(cluster)['result'] == RESULT
    assert node.database.path.read_bytes() == before


@pytest.mark.parametrize('action', ['acquire','rollback','stage','restore','resume','publish-directory','commit-decision'])
def test_source_bridge_only_allows_fenced_recovery_actions(overlay_cluster, action):
    node = overlay_cluster.nodes['RU']
    node.fenced_recovery = True
    with pytest.raises(Rejected,match='FENCED_RECOVERY_ACTION_FORBIDDEN'):
        dispatch(node,dict(schema=1,role='RU',action=action,operation_id=overlay_cluster.record['operation_id'],
            expected_source_sha256='a'*64,payload=None))


@pytest.mark.parametrize('table', ['paid_beta_subscriptions','paid_beta_events'])
def test_paid_ledger_change_rejected(overlay_cluster, table):
    node = overlay_cluster.nodes['RU']
    with node.database.connect(write=True) as database:
        database.execute('DROP TABLE IF EXISTS '+table)
        database.execute('CREATE TABLE '+table+' (value INTEGER)')
        database.execute('INSERT INTO '+table+' VALUES (1)')
    with pytest.raises(Rejected,match='ROLLBACK_PAID_LEDGER_CHANGED'):
        prove(overlay_cluster)


@pytest.mark.parametrize('column', ['public','wg','tcp'])
def test_new_device_cannot_replace_unique_identity(overlay_cluster, column):
    before = overlay_cluster.nodes['RU'].database.snapshot()
    current = deepcopy(before)
    row = device_row()
    row[column] = before['devices'][0][column]
    current['devices'].append(row)
    with pytest.raises(Rejected,match='ROLLBACK_REGISTRY_UNIQUE_CONFLICT'):
        append_only_registry_overlay(before,current)


def test_database_change_during_proof_rejected(overlay_cluster, monkeypatch):
    node = overlay_cluster.nodes['RU']
    original = node.database.snapshot
    def changed(connection=None):
        value = original(connection)
        if connection is None:
            value['devices'].append(device_row())
        return value
    monkeypatch.setattr(node.database,'snapshot',changed)
    with pytest.raises(Rejected,match='ROLLBACK_REGISTRY_OVERLAY_STALE'):
        node.database.registry_overlay(original())


def test_recovery_without_explicit_overlay_keeps_exact_guard(overlay_cluster):
    additions(overlay_cluster)
    before = overlay_cluster.nodes['RU'].database.path.read_bytes()
    assert overlay_cluster.controller.recover(overlay_cluster.record)['result'] == 'RECOVERY_REQUIRED'
    assert overlay_cluster.nodes['RU'].database.path.read_bytes() == before
    assert not (overlay_cluster.nodes['RU'].state/'rollback-registry-overlay.json').exists()
