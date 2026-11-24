from dataclasses import asdict
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import sys

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts import control_ha_recovery_bundle as recovery
from scripts.control_ha_handoff_import import verify as verify_handoff
from scripts.control_ha_import import ImportRejected, import_snapshot
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.referral_postgres_rehearsal import NOW
from test_control_ha_current_audit import current, native_current_for
from test_control_ha_forward_checkpoint import authorize, candidate, candidate_for
from test_control_ha_forward_archive import packed, packed_for, verify
from test_control_ha_handoff_import import repository


@pytest.fixture(scope='module')
def native_current(tmp_path_factory):
    return native_current_for(tmp_path_factory.mktemp('handoff-current'), handoff=True)


def test_portable_forward_contract_keeps_handoff_and_external_permissions(candidate, packed, repository):
    qualified = verify(packed)
    state = qualified.current
    assert state.stores == candidate['current']['recovered'].stores
    assert tuple(map(len, state.snapshot.handoff)) == (1, 2, 1, 1, 1)
    assert import_snapshot(repository, state.snapshot)['result'] == 'IMPORTED'
    with repository.transaction() as transaction:
        verify_handoff(transaction.database, state.snapshot.handoff)
    summary = qualified.summary()
    assert summary['database_import'] == summary['host_resume'] == 'NOT_AUTHORIZED'
    assert summary['activation'] == 'FORBIDDEN' and summary['full_recovery'] == 'NOT_QUALIFIED'


@pytest.mark.parametrize('override', ['key', 'request', 'sequence', 'crl', 'expiry'])
def test_handoff_does_not_replace_independent_forward_authority(candidate, packed, override):
    external = packed['external']
    changes = {
        'key': dict(trusted_key=Ed25519PrivateKey.generate().public_key().public_bytes_raw()),
        'request': dict(expected_request_sha256='0' * 64),
        'sequence': dict(minimum_sequence=2),
        'crl': dict(minimum_crl=external['minimum_crl'] + 1),
        'expiry': dict(now=NOW + 300),
    }
    with pytest.raises(ImportRejected):
        verify(packed, **changes[override])


def test_v1_cannot_be_repackaged_to_silently_remove_handoff(candidate):
    state = candidate['current']['recovered']
    with pytest.raises(ImportRejected, match='SOURCE_SCHEMA_UNSUPPORTED'):
        recovery.seal(state.stores, state.references, state.artifacts, CHECKPOINT,
                      state.bootstrap, candidate['arguments']['anchor'], secrets.token_bytes(32), now=NOW)


def test_replaced_retention_snapshot_requires_new_independent_request_pin(candidate, packed):
    checkpoint = candidate['recovery_checkpoint']
    document = asdict(checkpoint)
    document['snapshot_sha256'] = '0' * 64
    authorize(candidate, lambda request: request.update(recovery=document))
    with pytest.raises(ImportRejected):
        verify(packed, expected_request_sha256=candidate['expected_request_sha256'])


def test_fresh_process_imports_all_49_tables_from_archive_without_source(repository, tmp_path):
    source_root = tmp_path / 'source'
    source_root.mkdir(mode=0o700)
    roots, recovered, publications, anchor = native_current_for(source_root, handoff=True)
    candidate = candidate_for(dict(roots=roots, recovered=recovered, publications=publications,
                                   anchor=anchor, key=secrets.token_bytes(32)))
    packed = packed_for(candidate)
    expected = verify(packed).current.snapshot.fingerprint
    shutil.rmtree(source_root)
    assert not source_root.exists()
    bundle_path = tmp_path / 'handoff-checkpoint.enc'
    bundle_path.write_bytes(packed.pop('bundle'))
    bundle_path.chmod(0o600)
    inputs = dict(external=packed['external'], key=packed['key'].hex(), checksum=packed['checksum'])
    for name in ('trusted_key', 'anchor', 'history_key', 'recovery_key'):
        inputs['external'][name] = inputs['external'][name].hex()
    candidate.clear()
    del roots, recovered, publications, anchor
    checkout = Path(__file__).resolve().parents[1]
    code = f'''import json,os,sys
from pathlib import Path
sys.path.insert(0,{str(checkout)!r})
from control.friends.enrollment_postgres import PostgresEnrollment
from scripts import control_ha_forward_archive as archive
from scripts.control_ha_handoff_import import verify
from scripts.control_ha_import import import_snapshot
inputs=json.load(sys.stdin)
external=inputs['external']
for name in ('trusted_key','anchor','history_key','recovery_key'):
    external[name]=bytes.fromhex(external[name])
qualified=archive.verify(Path(sys.argv[1]).read_bytes(),bytes.fromhex(inputs['key']),inputs['checksum'],**external)
snapshot=qualified.current.snapshot
repository=PostgresEnrollment(port=int(os.environ['FC_HA_PG_PORT']),schema=sys.argv[2],
    password=Path(os.environ['FC_HA_PG_PASSWORD_FILE']).read_text().strip())
result=import_snapshot(repository,snapshot)
with repository.transaction() as transaction:
    verify(transaction.database,snapshot.handoff)
    count=transaction.database.execute('SELECT count(*) AS count FROM pg_tables WHERE schemaname=current_schema()').fetchone()['count']
print(json.dumps(dict(result=result['result'],fingerprint=snapshot.fingerprint,tables=count,
    handoff_counts=list(map(len,snapshot.handoff)),summary=qualified.summary())))
'''
    completed = subprocess.run([sys.executable, '-I', '-B', '-c', code, str(bundle_path), repository.schema],
        input=json.dumps(inputs), text=True, capture_output=True, timeout=90, cwd=tmp_path)
    assert completed.returncode == 0, 'isolated child recovery failed'
    assert not completed.stderr
    received = json.loads(completed.stdout)
    assert received['result'] == 'IMPORTED' and received['tables'] == 49
    assert received['fingerprint'] == expected and received['handoff_counts'] == [1, 2, 1, 1, 1]
    assert received['summary']['activation'] == 'FORBIDDEN'
    assert received['summary']['database_import'] == 'NOT_AUTHORIZED'
