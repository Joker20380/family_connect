from copy import deepcopy
import os
from pathlib import Path
import secrets
import sqlite3
import uuid

import pytest

from control.friends.enrollment_postgres import PostgresEnrollment
from scripts.control_ha_external_v1 import preflight_external
from scripts.control_ha_import import ImportRejected, encoded, import_snapshot
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_receiver_fixture import artifacts_for_receivers, exercise_receiver_files
from scripts.control_ha_receiver_v1 import PARTS, preflight_receivers
from scripts.control_ha_recovery_bundle import parse, seal
from scripts.control_ha_sqlite_fixture import joint_fixture
from scripts.referral_postgres_rehearsal import NOW


@pytest.fixture
def source(tmp_path):
    root = tmp_path / 'source'
    root.mkdir(mode=0o700)
    fixture = joint_fixture(root)
    return fixture, artifacts_for_receivers(fixture), secrets.token_bytes(32)


def capture(source):
    fixture, artifacts, key = source
    return seal(fixture.stores, fixture.external, artifacts, CHECKPOINT, fixture.bootstrap,
                fixture.service.anchor, key, now=NOW)


def recover(source, bundle, checkpoint, *, now=NOW):
    return preflight_receivers(bundle, source[2], checkpoint, source[0].service.anchor, now=now)


def checked(source):
    return recover(source, *capture(source))


def test_safety_profile_and_native_recovered_consumers(source, tmp_path):
    recovered = checked(source)
    summary = recovered.summary()
    assert summary['artifacts'] == 35 and summary['receiver_nodes'] == 3
    assert summary['activation'] == 'FORBIDDEN' and summary['exact_bytes_only'] == ['maintenance_state']
    behavior = exercise_receiver_files(recovered, tmp_path / 'restored')
    assert all(behavior.values()) and behavior['partial_preparation_nodes'] == 2
    assert (tmp_path / 'restored/mailbox/node.identity').stat().st_mode & 0o777 == 0o600
    assert (tmp_path / 'restored').stat().st_mode & 0o777 == 0o700


def test_expired_receivers_are_not_refreshed_or_discarded(source):
    raw, checkpoint = capture(source)
    recovered = recover(source, raw, checkpoint, now=NOW + 121)
    assert recovered.artifacts['receiver_state'] == source[1]['receiver_state']
    assert parse(recovered.artifacts['receiver_state']['members.json'])['sequence'] == 2


def test_preflight_has_no_writable_db_or_pg_access(source, monkeypatch):
    raw, checkpoint = capture(source)
    connect = sqlite3.connect
    def memory_only(path, *args, **kwargs):
        assert path == ':memory:'
        return connect(path, *args, **kwargs)
    monkeypatch.setattr(sqlite3, 'connect', memory_only)
    monkeypatch.setattr(PostgresEnrollment, 'connect', lambda *args: pytest.fail('No PG in receiver dry run'))
    assert recover(source, raw, checkpoint).summary()['receiver_nodes'] == 3


@pytest.mark.parametrize('name', sorted(PARTS))
def test_every_receiver_part_is_mandatory(source, name):
    del source[1]['receiver_state'][name]
    with pytest.raises(ImportRejected, match='RECEIVER_PARTS'):
        checked(source)


@pytest.mark.parametrize('kind', ['opaque', 'extra', 'schema', 'purpose', 'future', 'nodes', 'boot', 'negative', 'infinite'])
def test_capture_and_format_are_explicit(source, kind):
    parts = source[1]['receiver_state']
    value = parse(parts['capture.json'])
    if kind == 'opaque':
        source[1]['receiver_state'] = {'opaque-probe': b'not-runtime'}
    elif kind == 'extra':
        parts['unexpected'] = b'private-canary'
    elif kind == 'schema':
        value['schema'] = True
    elif kind == 'purpose':
        value['purpose'] = 'live-attested'
    elif kind == 'future':
        value['captured_at'] = NOW + 6
    elif kind == 'nodes':
        value['nodes'].pop('nl-amsterdam-2')
    elif kind == 'boot':
        value['nodes']['gateway-ru']['boot'] = 'not-uuid'
    elif kind == 'negative':
        value['nodes']['gateway-ru']['monotonic'] = -1
    else:
        parts['capture.json'] = encoded(value).replace(b'1000.0', b'1e999')
    if kind != 'infinite':
        parts['capture.json'] = encoded(value)
    with pytest.raises(ImportRejected) as failure:
        checked(source)
    assert 'private-canary' not in str(failure.value)


@pytest.mark.parametrize('kind', ['node', 'schema', 'missing-device', 'future', 'extra-cache', 'boot',
    'negative-deadline', 'extended-deadline', 'prepared', 'identity', 'binding', 'revision', 'device',
    'receipt-extra', 'receipt-revision', 'receipt-registered', 'receipt-allow', 'receipt-time', 'duplicate-json'])
def test_transport_state_binding_and_safety(source, kind):
    parts = source[1]['receiver_state']
    name = 'gateway-ru.state.json'
    state = parse(parts[name])
    cached = next(value for value in state['records'].values() if value['prepared'])
    if kind == 'node':
        state['node'] = 'nl-amsterdam-2'
    elif kind == 'schema':
        state['schema'] = True
    elif kind == 'missing-device':
        state['records'].pop(next(iter(state['records'])))
    elif kind == 'future':
        state['observed_at'] = NOW + 6
    elif kind == 'extra-cache':
        cached['unexpected'] = True
    elif kind == 'boot':
        cached['boot'] = 'bad'
    elif kind == 'negative-deadline':
        cached['deadline'] = -1
    elif kind == 'extended-deadline':
        cached['deadline'] = 1121
    elif kind == 'prepared':
        cached['prepared'] = False
    elif kind == 'identity':
        cached['decision']['identity_allowed'] = False
    elif kind == 'binding':
        cached['decision']['tcp_id'] = str(uuid.uuid4())
    elif kind == 'revision':
        cached['decision']['revision'] += 1
    elif kind == 'device':
        cached['decision']['device'] = 'f' * 32
    elif kind == 'receipt-extra':
        cached['applied']['unexpected'] = True
    elif kind == 'receipt-revision':
        cached['applied']['applied_revision'] += 1
    elif kind == 'receipt-registered':
        cached['applied']['registered'] = False
    elif kind == 'receipt-allow':
        cached['applied']['allowed'] = True
    elif kind == 'receipt-time':
        cached['applied']['observed_at'] = NOW + 1
    parts[name] = encoded(state)
    if kind == 'duplicate-json':
        parts[name] = parts[name].replace(b'"schema":1', b'"schema":1,"schema":1')
    with pytest.raises(ImportRejected):
        checked(source)


@pytest.mark.parametrize('field,value', [('schema', True), ('enabled', 1), ('enabled', False),
                                       ('profile', 'unknown'), ('node', 'nl-amsterdam-1')])
def test_node_configuration_is_not_interchangeable(source, field, value):
    parts = source[1]['receiver_state']
    config = parse(parts['gateway-ru.config.json'])
    config[field] = value
    parts['gateway-ru.config.json'] = encoded(config)
    with pytest.raises(ImportRejected, match='RECEIVER_CONFIG'):
        checked(source)


@pytest.mark.parametrize('kind', ['sequence-behind', 'sequence-ahead', 'members', 'expiry', 'duplicate',
    'key', 'key-length', 'volume', 'static-unknown', 'static-duplicate', 'static-empty', 'host',
    'port', 'destination', 'bootstrap-key', 'controller', 'controller-extra'])
def test_mailbox_identity_membership_floor_and_bindings(source, kind):
    parts = source[1]['receiver_state']
    documents = {name: parse(parts[name]) for name in ('members.json', 'settings.json', 'bootstrap.json', 'chat-node.json')}
    members, settings, bootstrap, controller = documents.values()
    if kind == 'sequence-behind': members['sequence'] -= 1
    elif kind == 'sequence-ahead': members['sequence'] += 1
    elif kind == 'members': members['public_keys'].pop()
    elif kind == 'expiry': members['expires_at'] = NOW + 121
    elif kind == 'duplicate': members['public_keys'].append(members['public_keys'][0])
    elif kind == 'key': parts['node.identity'] = secrets.token_bytes(64)
    elif kind == 'key-length': parts['node.identity'] = b'x'
    elif kind == 'volume': parts['volume-id'] = b'unknown\n'
    elif kind == 'static-unknown': settings['allowed_public'] = ['f' * 128]
    elif kind == 'static-duplicate': settings['allowed_public'] *= 2
    elif kind == 'static-empty': settings['allowed_public'] = []
    elif kind == 'host': bootstrap['server'] = '192.0.2.99'
    elif kind == 'port': bootstrap['port'] = True
    elif kind == 'destination': bootstrap['destination'] = 'f' * 32
    elif kind == 'bootstrap-key': bootstrap['public_key'] = 'f' * 128
    elif kind == 'controller': controller['host'] = '192.0.2.99'
    else: controller['unexpected'] = True
    parts.update({name: encoded(value) for name, value in documents.items()})
    with pytest.raises(ImportRejected):
        checked(source)


@pytest.fixture
def repository():
    if not os.environ.get('FC_HA_PG_PORT'):
        pytest.skip('Run scripts.control_ha_receiver_rehearsal for real PostgreSQL qualification')
    return PostgresEnrollment(port=int(os.environ['FC_HA_PG_PORT']), schema='ha_enrollment_' + uuid.uuid4().hex,
        password=Path(os.environ['FC_HA_PG_PASSWORD_FILE']).read_text().strip())


def test_strict_receiver_import_and_retry(source, repository):
    recovered = checked(source)
    assert import_snapshot(repository, recovered.snapshot)['result'] == 'IMPORTED'
    assert import_snapshot(repository, recovered.snapshot)['result'] == 'EXACT_RETRY'


def test_external_role_receipt_cannot_claim_receiver_acceptance(source, repository):
    raw, checkpoint = capture(source)
    prior = preflight_external(raw, source[2], checkpoint, source[0].service.anchor, now=NOW)
    import_snapshot(repository, prior.snapshot)
    with pytest.raises(ImportRejected, match='TARGET_NOT_SAME_IMPORT'):
        import_snapshot(repository, recover(source, raw, checkpoint).snapshot)


def test_lost_preparation_cannot_replace_trusted_checkpoint_or_import(source, repository):
    raw, checkpoint = capture(source)
    accepted = recover(source, raw, checkpoint)
    import_snapshot(repository, accepted.snapshot)
    parts = source[1]['receiver_state']
    state = parse(parts['gateway-ru.state.json'])
    cached = next(value for value in state['records'].values() if value['prepared'])
    cached['prepared'] = None
    cached['applied'] = None
    parts['gateway-ru.state.json'] = encoded(state)
    changed_raw, changed_checkpoint = capture(source)
    with pytest.raises(ImportRejected):
        recover(source, changed_raw, checkpoint)
    changed = recover(source, changed_raw, changed_checkpoint)
    with pytest.raises(ImportRejected, match='TARGET_NOT_SAME_IMPORT'):
        import_snapshot(repository, changed.snapshot)
    assert import_snapshot(repository, accepted.snapshot)['result'] == 'EXACT_RETRY'
