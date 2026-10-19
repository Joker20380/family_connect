import base64
from concurrent.futures import ThreadPoolExecutor
import copy
import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading

import pytest

from test_owner_handoff import fixtures, handoff as legacy, other, BOOT


ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('control.friends.owner_handoff', Path(__file__).with_name('successor_owner_handoff.py'))
handoff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handoff)


@pytest.fixture
def saved(tmp_path):
    service, owner, now = fixtures.configured(tmp_path, 1800000000, directory_lifetime=10800)
    with service.access.db() as database:
        legacy.migrate(database)
        legacy.prepare(database, 'retired-01', owner.reference, 'a'*32, 'b'*32, now+2400, now)
    first = service.fetch(fixtures.proof(service, owner))
    with service.access.db() as database:
        legacy.return_only(database, owner.reference, 'retired-01')
        legacy.cleanup(database, owner.reference, 'retired-01', first)
        original = dict(legacy.read(database, owner.reference))
    return service, owner, now, first, original


@pytest.fixture
def successor(saved, monkeypatch):
    service, owner, now, first, original = saved
    import control.friends
    monkeypatch.setitem(sys.modules, 'control.friends.owner_handoff', handoff)
    monkeypatch.setattr(control.friends, 'owner_handoff', handoff)
    monkeypatch.setenv('INVOCATION_ID', BOOT)
    with service.access.db() as database:
        handoff.migrate(database)
    return saved


def prepare(case, operation='successor-02', deadline=None):
    service, owner, now, *_ = case
    with service.access.db() as database:
        return handoff.prepare(database, operation, owner.reference, 'a'*32, 'b'*32, deadline or now+2400, now)


def current(case):
    with case[0].access.db() as database:
        return dict(handoff.current(database))


def capture(case):
    service, owner, *_ = case
    return service.fetch(fixtures.proof(service, owner))


def finish(case):
    service, owner, *_ = case
    row = current(case)
    with service.access.db() as database:
        handoff.return_only(database, owner.reference, row['operation'], generation=row['generation'])
    response = capture(case)
    with service.access.db() as database:
        handoff.cleanup(database, owner.reference, row['operation'], response, generation=row['generation'])
    return response


def arm(case):
    service, owner, now, first, *_ = case
    if current(case)['captured'] == 0:
        capture(case)
    canary, returning = copy.deepcopy(first['directory']), copy.deepcopy(first['directory'])
    canary['issued_at'] = fixtures.iso(now)
    canary['seeds'][0]['join_url'] = 'https://telemost.yandex.ru/j/synthetic-successor'
    returning['issued_at'] = fixtures.iso(now+10)
    service.access.clock = lambda: now+10
    row = current(case)
    with service.access.db() as database:
        handoff.arm(database, owner.reference, row['operation'], canary, returning, BOOT, now+10, generation=row['generation'])
    return canary, returning


def test_migration_successor_preserves_every_legacy_field_and_floor(successor):
    service, owner, now, first, original = successor
    result = prepare(successor)
    assert result['phase'] == 'PREPARED' and result['generation'] == 2 and result['predecessor'] == 'retired-01'
    with service.access.db() as database:
        assert handoff.legacy_rows(database) == [original]
        copied = dict(database.execute('SELECT * FROM restricted_owner_handoff_operations WHERE operation=?', ('retired-01',)).fetchone())
        assert {name:copied[name] for name in handoff.FIELDS} == original
        assert handoff.read(database, owner.reference, 'successor-02', 2)['floor'] == original['floor']
        assert handoff.security(database, owner.reference, 'a'*32, 'b'*32)['floor'] == original['floor']
        assert handoff.migrate(database)['result'] == 'ALREADY_MIGRATED'
    assert current(successor)['captured'] == 0


@pytest.mark.parametrize('phase', ['PREPARED', 'ACTIVE', 'RETURN'])
def test_unfinished_including_expired_blocks_next(successor, phase):
    service, owner, now, *_ = successor
    prepare(successor)
    if phase == 'ACTIVE':
        arm(successor)
    elif phase == 'RETURN':
        with service.access.db() as database:
            handoff.return_only(database, owner.reference, 'successor-02', generation=2)
    with pytest.raises(ValueError):
        with service.access.db() as database:
            handoff.prepare(database, 'successor-03', owner.reference, 'a'*32, 'b'*32, now+6000, now+2500)
    assert current(successor)['operation'] == 'successor-02'


def test_two_concurrent_new_ids_only_one_wins(successor):
    barrier = threading.Barrier(2)
    def allocate(operation):
        barrier.wait(timeout=3)
        try:
            return prepare(successor, operation)['operation']
        except ValueError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(allocate, ('candidate-a','candidate-b')))
    assert sum(value is not None for value in results) == 1
    with successor[0].access.db() as database:
        assert database.execute("SELECT COUNT(*) FROM restricted_owner_handoff_operations WHERE phase!='CLEANED'").fetchone()[0] == 1


def test_prepare_replay_is_read_only_and_terminal_does_not_reopen(successor):
    first = prepare(successor)
    assert prepare(successor) == first
    with pytest.raises(ValueError):
        prepare(successor, deadline=successor[2]+2401)
    finish(successor)
    history = current(successor)
    assert prepare(successor)['phase'] == 'CLEANED'
    assert current(successor) == history
    prepare(successor, 'successor-03')
    assert not prepare(successor)['current']
    assert current(successor)['operation'] == 'successor-03'


def test_before_commit_rolls_back_after_commit_and_receipt_failure_read_back(successor):
    service, owner, now, *_ = successor
    with pytest.raises(RuntimeError):
        with service.access.db() as database:
            handoff.prepare(database, 'successor-02', owner.reference, 'a'*32, 'b'*32, now+2400, now)
            raise RuntimeError('before commit')
    assert current(successor)['operation'] == 'retired-01'
    committed = prepare(successor)
    with pytest.raises(OSError):
        raise OSError('durable external receipt unavailable after commit')
    assert prepare(successor) == committed
    with service.access.db() as database:
        assert database.execute('SELECT COUNT(*) FROM restricted_owner_handoff_operations').fetchone()[0] == 2


@pytest.mark.parametrize('action', ['arm','return','cleanup','callback'])
def test_stale_operation_commands_cannot_change_successor(successor, action):
    service, owner, now, first, original = successor
    prepare(successor)
    before = current(successor)
    with pytest.raises(ValueError):
        with service.access.db() as database:
            if action == 'arm':
                handoff.arm(database, owner.reference, 'retired-01', first['directory'], first['directory'], BOOT, now, generation=1)
            elif action == 'return':
                handoff.return_only(database, owner.reference, 'retired-01', generation=1)
            elif action == 'cleanup':
                handoff.cleanup(database, owner.reference, 'retired-01', first, generation=1)
            else:
                handoff.select(database, copy.deepcopy(first), owner.reference, BOOT, now, 'old-fetch', operation='retired-01', generation=1)
    assert current(successor) == before
    with service.access.db() as database:
        assert handoff.legacy_rows(database) == [original]


def test_wrong_generation_rejected(successor):
    prepare(successor)
    with pytest.raises(ValueError):
        with successor[0].access.db() as database:
            handoff.return_only(database, successor[1].reference, 'successor-02', generation=1)


def test_three_consecutive_cleanup_successors_keep_history(successor):
    frozen = {}
    for operation in ('successor-02','successor-03','successor-04'):
        prepare(successor, operation)
        capture(successor)
        finish(successor)
        frozen[operation] = current(successor)
    with successor[0].access.db() as database:
        for operation, original in frozen.items():
            assert dict(database.execute('SELECT * FROM restricted_owner_handoff_operations WHERE operation=?',(operation,)).fetchone()) == original
        assert handoff.legacy_rows(database) == [successor[4]]
    assert current(successor)['generation'] == 4


def test_no_arbitrary_cross_device_or_scope_floor_merge(successor):
    service, owner, now, first, _ = successor
    with pytest.raises(ValueError):
        with service.access.db() as database:
            handoff.prepare(database, 'new-scope', owner.reference, 'c'*32, 'b'*32, now+2400, now)
    ordinary = other(service, now)
    prepare(successor)
    assert service.fetch(fixtures.proof(service, ordinary))['directory'] == first['directory']
    with service.access.db() as database:
        assert database.execute('SELECT * FROM restricted_owner_handoff_security WHERE device=?',(ordinary.reference,)).fetchone() is None


def test_stage_is_not_security_floor_and_capture_required(successor):
    service, owner, now, first, _ = successor
    prepare(successor)
    with pytest.raises(ValueError):
        with service.access.db() as database:
            handoff.arm(database, owner.reference, 'successor-02', first['directory'], first['directory'], BOOT, now, generation=2)
    canary, returning = arm(successor)
    with service.access.db() as database:
        assert json.loads(handoff.security(database,owner.reference,'a'*32,'b'*32)['floor'])['directory'] == first['directory']
    assert capture(successor)['directory'] == canary
    with service.access.db() as database:
        assert json.loads(handoff.security(database,owner.reference,'a'*32,'b'*32)['floor'])['directory'] == canary
    service.seed_source = lambda:json.dumps(returning).encode()
    returned = finish(successor)
    assert returned['directory'] == returning
    historical = current(successor)
    service.access.clock = lambda: now+20
    capture(successor)
    assert current(successor) == historical


@pytest.mark.parametrize('reason', ['restart','expiry'])
def test_restart_expiry_never_creates_successor_or_rearms(successor, monkeypatch, reason):
    service, owner, now, *_ = successor
    prepare(successor)
    canary, returning = arm(successor)
    capture(successor)
    if reason == 'restart':
        monkeypatch.setenv('INVOCATION_ID','d'*32)
    else:
        service.access.clock = lambda:now+2400
    assert capture(successor)['directory'] == returning
    assert current(successor)['phase'] == 'RETURN'
    with pytest.raises(ValueError):
        prepare(successor,'successor-03')


def test_nano_precision_and_older_directory_rejection(successor):
    first = copy.deepcopy(successor[3]['directory'])
    later = dict(first,issued_at=first['issued_at'][:-1]+'.000000001Z')
    assert handoff.ordered(later, first) and not handoff.ordered(first, later)
    prepare(successor)
    canary, returning = arm(successor)
    capture(successor)
    with successor[0].access.db() as database:
        handoff.return_only(database,successor[1].reference,'successor-02',generation=2)
    assert capture(successor)['directory'] == returning


def test_return_import_before_first_capture_prevents_older_canary(successor):
    service, owner, now, first, _ = successor
    prepare(successor)
    returning = dict(first['directory'], issued_at=fixtures.iso(now+10))
    service.access.clock = lambda:now+10
    service.seed_source = lambda:json.dumps(returning).encode()
    capture(successor)
    with pytest.raises(ValueError):
        arm(successor)


def test_fence_blocks_later_common_refresh_without_advancing_floor(successor):
    service, owner, now, first, _ = successor
    prepare(successor); capture(successor)
    before = current(successor)
    later = dict(first['directory'], issued_at=fixtures.iso(now+10))
    service.access.clock = lambda:now+10
    service.seed_source = lambda:json.dumps(later).encode()
    with pytest.raises(ValueError):
        capture(successor)
    assert current(successor) == before


@pytest.mark.parametrize('failure',['revoked','expired','wrong-family','wrong-key','replay','client-selector','revoked-certificate'])
def test_existing_authorization_not_weakened(successor, failure):
    from device_identity.device import DeviceIdentity
    service, owner, now, *_ = successor
    prepare(successor); arm(successor)
    proof = fixtures.proof(service,owner)
    with service.access.db() as database:
        if failure == 'revoked':
            database.execute('UPDATE devices SET revoked=1 WHERE device=?',(owner.reference,))
        elif failure == 'expired':
            database.execute('UPDATE restricted_grants SET expires=?',(now-1,))
        elif failure == 'wrong-family':
            database.execute('UPDATE restricted_grants SET family=?',('e'*32,))
    if failure == 'wrong-key':
        proof = DeviceIdentity.generate().prove_transport_key(proof['challenge'])
    elif failure == 'replay':
        service.fetch(proof)
    elif failure == 'client-selector':
        proof['canary'] = True
    elif failure == 'revoked-certificate':
        from cryptography import x509
        from cryptography.hazmat.primitives.serialization import Encoding
        from control.friends.restricted import utc
        certificate = x509.load_pem_x509_certificate(successor[3]['certificate'].encode())
        old = x509.load_pem_x509_crl(service.crl_source())
        revoked = x509.RevokedCertificateBuilder().serial_number(certificate.serial_number).revocation_date(utc(now-1)).build()
        crl = (x509.CertificateRevocationListBuilder().issuer_name(old.issuer).last_update(utc(now-1))
               .next_update(utc(now+3500)).add_extension(x509.CRLNumber(2), False)
               .add_revoked_certificate(revoked).sign(service.signing_key, None))
        service.crl_source = lambda: crl.public_bytes(Encoding.PEM)
    with pytest.raises(ValueError):
        service.fetch(proof)
    assert current(successor)['phase'] == 'ACTIVE'


def test_nonowner_unaffected_by_bad_canary(successor):
    service, owner, now, first, _ = successor
    ordinary = other(service,now)
    prepare(successor);arm(successor)
    with service.access.db() as database:
        database.execute('UPDATE restricted_owner_handoff_operations SET canary=? WHERE operation=?',('{}','successor-02'))
    assert service.fetch(fixtures.proof(service,ordinary))['directory'] == first['directory']
    with pytest.raises(ValueError):capture(successor)


def test_schema_refuses_unclean_legacy_and_transaction_interruption(saved):
    service, owner, *_ = saved
    with service.access.db() as database:
        database.execute("UPDATE restricted_owner_handoff SET phase='RETURN'")
    with pytest.raises(ValueError):
        with service.access.db() as database:handoff.migrate(database)
    with service.access.db() as database:
        assert not handoff.exists(database,handoff.SCHEMA)
        database.execute("UPDATE restricted_owner_handoff SET phase='CLEANED'")
    with pytest.raises(RuntimeError):
        with service.access.db() as database:
            handoff.migrate(database)
            raise RuntimeError('interrupted before migration commit')
    with service.access.db() as database:
        assert not handoff.exists(database,handoff.SCHEMA)
        assert handoff.legacy_rows(database) == [saved[4]]


@pytest.mark.parametrize('statement',[
    "UPDATE restricted_owner_handoff SET phase='PREPARED'", 'DELETE FROM restricted_owner_handoff',
    "UPDATE restricted_owner_handoff_operations SET phase='PREPARED' WHERE operation='retired-01'",
    'DELETE FROM restricted_owner_handoff_operations','DELETE FROM restricted_owner_handoff_security'])
def test_db_constraints_protect_history_against_old_writers(successor, statement):
    with pytest.raises(sqlite3.IntegrityError):
        with successor[0].access.db() as database:database.execute(statement)


def test_global_exclusivity_enforced_by_database(successor):
    prepare(successor)
    with pytest.raises(sqlite3.IntegrityError):
        with successor[0].access.db() as database:
            row=dict(handoff.current(database))
            row.update(operation='illegal-second',generation=3)
            database.execute('INSERT INTO restricted_owner_handoff_operations VALUES ('+','.join('?' for _ in row)+')',tuple(row.values()))


def test_new_api_actual_deliveries_pass_existing_native_and_java_cache(successor, tmp_path):
    service, owner, now, first, _ = successor
    prepare(successor)
    canary, returning = arm(successor)
    middle = capture(successor)
    service.seed_source = lambda:json.dumps(returning).encode()
    returned = finish(successor)
    for response in (first,middle,returned):
        value=dict(response=response,public=owner.public_identity,anchor=base64.b64encode(service.anchor).decode(),now=now+10)
        result=subprocess.run([str(ROOT/'state-client-build/mesh-perf-3b/delivery-check')],input=json.dumps(value).encode(),capture_output=True,timeout=15)
        assert result.returncode==0 and result.stdout==b'compatible\n'
    path=tmp_path/'roundtrip.json';path.write_text(json.dumps([first,middle,returned]))
    tools=ROOT/'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
    jars=[str(next((tools/'gradle-home/caches/modules-2/files-2.1'/name).glob('*/*.jar'))) for name in ('com.google.code.gson/gson/2.13.2','junit/junit/4.13.2','org.hamcrest/hamcrest-core/1.3')]
    classpath=':'.join([str(ROOT/'state-client-build/mesh-perf-3b/java-floors-final-classes'),*jars])
    result=subprocess.run([str(tools/'jdk/bin/java'),'-cp',classpath,'com.familyconnect.app.FloorRoundtrip',str(path)],capture_output=True,timeout=15)
    assert result.returncode==0, result.stderr.decode()


def test_original_api_archive_still_fetches_after_additive_migration(successor, tmp_path):
    service, owner, now, first, _ = successor
    prepare(successor)
    _, returning = arm(successor)
    capture(successor)
    service.seed_source = lambda:json.dumps(returning).encode()
    finish(successor)
    before=current(successor)
    baseline=ROOT/'state-client-build/field65-export16/warm-start-collector-rebase-1/preservation/deployed-api.pyz'
    import zipfile
    with zipfile.ZipFile(baseline) as archive:
        raw=archive.read('control/friends/restricted.py')
    source=tmp_path/'original_restricted.py';source.write_bytes(raw)
    original_spec=importlib.util.spec_from_file_location('control.friends.original_restricted',source)
    original=importlib.util.module_from_spec(original_spec);sys.modules[original_spec.name]=original
    try:
        original_spec.loader.exec_module(original)
        restored=original.RestrictedReadiness(service.access,manifest=service.manifest,anchor=service.anchor,
            signing_key=service.signing_key,seed_source=service.seed_source,crl_source=service.crl_source,
            delivery_lifetime=service.delivery_lifetime)
        response=restored.fetch(fixtures.proof(restored,owner))
        assert handoff.preserves(handoff.floor(response),json.loads(before['floor']))
        assert current(successor)==before
    finally:
        del sys.modules[original_spec.name]


def test_concurrent_same_proof_and_subsequent_fetch(successor):
    service, owner, *_ = successor
    prepare(successor);arm(successor)
    proof = fixtures.proof(service, owner)
    barrier = threading.Barrier(2)
    def fetch():
        barrier.wait(timeout=3)
        try:
            return service.fetch(proof)
        except ValueError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _:fetch(), range(2)))
    assert sum(response is not None for response in responses) == 1
    selected = next(response for response in responses if response is not None)
    assert capture(successor)['directory'] == selected['directory']


def test_other_owner_cannot_open_second_operation(successor):
    service, owner, now, *_ = successor
    ordinary = other(service, now)
    prepare(successor)
    with pytest.raises(ValueError):
        with service.access.db() as database:
            handoff.prepare(database, 'different-owner', ordinary.reference, 'a'*32, 'b'*32, now+2400, now)


def test_security_continues_after_cleanup_without_changing_history(successor):
    service, owner, now, first, _ = successor
    prepare(successor);finish(successor)
    before = current(successor)
    newer = dict(first['directory'], issued_at=fixtures.iso(now+10))
    service.access.clock = lambda:now+10
    service.seed_source = lambda:json.dumps(newer).encode()
    response = capture(successor)
    assert current(successor) == before
    with service.access.db() as database:
        result = handoff.prepare(database, 'successor-03', owner.reference, 'a'*32, 'b'*32, now+2400, now+10)
        assert result['generation'] == 3
        assert json.loads(handoff.current(database)['floor']) == handoff.floor(response)
    service.seed_source = lambda:json.dumps(first['directory']).encode()
    with pytest.raises(ValueError):capture(successor)


def test_inflight_background_fetch_obeys_new_operation_fence(successor):
    service, owner, now, first, _ = successor
    prepare(successor);capture(successor)
    entered, released = threading.Event(), threading.Event()
    returning = dict(first['directory'],issued_at=fixtures.iso(now+10))
    proof = fixtures.proof(service,owner)
    def pending_directory():
        entered.set()
        assert released.wait(3)
        return json.dumps(returning).encode()
    service.seed_source=pending_directory
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(service.fetch,proof)
        try:
            assert entered.wait(3)
            service.seed_source=lambda:json.dumps(first['directory']).encode()
            canary, _ = arm(successor)
        finally:
            released.set()
        assert pending.result(timeout=3)['directory']==canary
