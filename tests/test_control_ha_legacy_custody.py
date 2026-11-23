from dataclasses import replace
import json
import os
from pathlib import Path
import secrets
import shutil

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from scripts import control_ha_legacy_custody as custody
from scripts.control_ha_import import ImportRejected, digest, encoded
from scripts.control_ha_installed_inventory import Reader, collect, reconcile
from scripts.control_ha_recovery_bundle import Checkpoint, preflight_bundle

IDENTIFIER = '1234567890abcdef1234567890abcdef'
SECRET = b'PRIVATE-OPAQUE-CUSTODY\x00\xff\x80'


def write(path, raw):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o600)


def inventory(roots):
    return {slot: collect(roots[slot], roots['coordinator'] if slot == 'RU' else None)
            for slot in ('RU', 'NL1', 'NL2')}


@pytest.fixture
def source(tmp_path):
    roots = {slot: tmp_path / slot for slot in custody.SLOTS}
    for slot in ('RU', 'NL1', 'NL2'):
        operations = ('old-operation', 'current-operation') if slot != 'NL2' else ('current-operation',)
        ledger = {operation: dict(result='CLEANED', opaque='kept') for operation in operations}
        write(roots[slot] / 'completed.json', encoded(ledger))
        write(roots[slot] / 'operation.lock', b'')
        for operation in operations:
            archive = roots[slot] / 'archive' / operation
            for name in ('services-before.json', 'start-intent-0.json', 'unknown-legacy-file', 'plan.json'):
                write(archive / name, SECRET + name.encode())
    coordinator = roots['coordinator']
    write(coordinator / 'transaction.json', encoded(dict(operation_id='current-operation', state='COMMITTED',
        gate=dict(authorization='OPERATOR_APPROVED_LEAF_CRL_SCHEDULE'), private=SECRET.hex())))
    write(coordinator / 'operation.lock', b'')
    write(coordinator / 'plan.json', SECRET)
    write(coordinator / 'last-receipt.json', b'\r\nopaque-receipt\r\n')
    write(coordinator / 'supplement.json', encoded(dict(operation_id='old-operation', secret=SECRET.hex())))
    write(coordinator / 'recovery-requests' / 'nested' / 'opaque-envelope', SECRET)
    (coordinator / 'empty-directory').mkdir(mode=0o700)
    return roots, inventory(roots), secrets.token_bytes(32)


def seal(source):
    roots, census, key = source
    return custody.seal(roots, census, key, IDENTIFIER)


def rewrite(source, bundle, checkpoint, change, *, bind_manifest=False):
    key = source[2]
    offset = len(custody.MAGIC)
    nonce = bundle[offset:offset + 12]
    aad = custody.MAGIC + custody.PURPOSE.encode()
    document = json.loads(AESGCM(key).decrypt(nonce, bundle[offset + 12:], aad))
    change(document)
    if bind_manifest:
        _, fingerprint = custody.checked_trees(document['trees'])
        checkpoint = replace(checkpoint, manifest_sha256=fingerprint)
    changed = custody.MAGIC + nonce + AESGCM(key).encrypt(nonce, encoded(document), aad)
    return changed, replace(checkpoint, bundle_sha256=digest(changed))


def test_byte_exact_source_removed_readback_is_not_recovery(source):
    roots, _, key = source
    before = {slot: {str(path.relative_to(root)): (path.read_bytes(), custody.metadata(path.stat()))
        for path in root.rglob('*') if path.is_file()} for slot, root in roots.items()}
    bundle, checkpoint = seal(source)
    assert SECRET not in bundle and b'current-operation' not in bundle and key not in bundle
    for root in roots.values():
        shutil.rmtree(root)
    preserved = custody.inspect(bundle, key, checkpoint)
    for slot, files in before.items():
        restored = preserved.trees[slot]['entries']
        assert {name for name, entry in restored.items() if entry['kind'] == 'file'} == set(files)
        for name, (raw, information) in files.items():
            assert restored[name]['body'] == raw
            assert restored[name]['metadata'] == information
    assert preserved.trees['coordinator']['entries']['empty-directory']['kind'] == 'directory'
    assert len(json.loads(preserved.trees['RU']['entries']['completed.json']['body'])) == 2
    assert len(json.loads(preserved.trees['NL2']['entries']['completed.json']['body'])) == 1
    assert 'history' not in preserved.trees['coordinator']['entries']
    summary = preserved.summary()
    assert summary['result'] == 'OPAQUE_CUSTODY_VERIFIED'
    assert summary['history_validation'] == 'NOT_PERFORMED'
    assert summary['host_resume'] == summary['database_import'] == 'NOT_AUTHORIZED'
    assert summary['current_state_recovery'] == 'NOT_QUALIFIED'
    assert 'PRIVATE' not in repr(preserved) + repr(checkpoint) + json.dumps(summary)
    assert all(not root.exists() for root in roots.values())


@pytest.mark.parametrize('kind', ['key', 'bitflip', 'truncated', 'magic', 'checkpoint', 'identifier'])
def test_wrong_key_or_checkpoint_refuses(source, kind):
    bundle, checkpoint = seal(source)
    key = source[2]
    if kind == 'key':
        key = secrets.token_bytes(32)
    elif kind == 'bitflip':
        bundle = bundle[:-1] + bytes([bundle[-1] ^ 1])
        checkpoint = replace(checkpoint, bundle_sha256=digest(bundle))
    elif kind == 'truncated':
        bundle = bundle[:-20]
    elif kind == 'magic':
        bundle = b'X' + bundle[1:]
    elif kind == 'checkpoint':
        checkpoint = replace(checkpoint, manifest_sha256='0' * 64)
    else:
        checkpoint = replace(checkpoint, identifier='f' * 32)
    with pytest.raises(ImportRejected):
        custody.inspect(bundle, key, checkpoint)


@pytest.mark.parametrize('kind', ['purpose', 'version', 'missing_role', 'missing_file', 'private_bytes',
    'metadata', 'path', 'traversal', 'parent', 'inventory', 'missing_empty_directory'])
def test_authenticated_tampering_cannot_change_independent_manifest(source, kind):
    bundle, checkpoint = seal(source)

    def change(document):
        tree = document['trees']['RU']
        if kind == 'purpose':
            document['purpose'] = 'recovery'
        elif kind == 'version':
            document['version'] = True
        elif kind == 'missing_role':
            del document['trees']['NL2']
        elif kind == 'missing_file':
            del tree['entries']['archive/old-operation/unknown-legacy-file']
        elif kind == 'private_bytes':
            tree['entries']['archive/old-operation/unknown-legacy-file']['body'] = 'Zm9yZ2Vk'
        elif kind == 'metadata':
            tree['metadata']['uid'] += 1
        elif kind == 'path':
            tree['path'] += '-moved'
        elif kind == 'traversal':
            tree['entries']['../escaped'] = tree['entries'].pop('operation.lock')
        elif kind == 'parent':
            del tree['entries']['archive/old-operation']
        elif kind == 'inventory':
            document['inventory']['RU']['node']['ledger'].clear()
        else:
            del document['trees']['coordinator']['entries']['empty-directory']

    changed, receipt = rewrite(source, bundle, checkpoint, change)
    with pytest.raises(ImportRejected):
        custody.inspect(changed, source[2], receipt)


@pytest.mark.parametrize('kind', ['prune_archive', 'prune_ledger', 'equalize_cohort', 'change_current', 'drop_adjunct'])
def test_new_manifest_cannot_bypass_original_census(source, kind):
    roots, _, _ = source
    if kind == 'prune_archive':
        shutil.rmtree(roots['RU'] / 'archive' / 'old-operation')
    elif kind == 'prune_ledger':
        path = roots['RU'] / 'completed.json'
        document = json.loads(path.read_bytes())
        del document['old-operation']
        write(path, encoded(document))
    elif kind == 'equalize_cohort':
        shutil.copytree(roots['RU'] / 'archive' / 'old-operation', roots['NL2'] / 'archive' / 'old-operation')
    elif kind == 'change_current':
        path = roots['coordinator'] / 'transaction.json'
        document = json.loads(path.read_bytes())
        document['state'] = 'RECOVERY_REQUIRED'
        write(path, encoded(document))
    else:
        (roots['coordinator'] / 'supplement.json').unlink()
    with pytest.raises(ImportRejected, match='CUSTODY_'):
        seal(source)


@pytest.mark.parametrize('kind', ['leaf_symlink', 'ancestor_symlink', 'hardlink', 'fifo', 'overlap', 'relative'])
def test_unsafe_source_is_refused_without_leaking_path(source, tmp_path, kind):
    roots, census, key = source
    target = roots['RU'] / 'archive' / 'old-operation' / 'unknown-legacy-file'
    if kind == 'leaf_symlink':
        target.unlink()
        target.symlink_to(roots['RU'] / 'completed.json')
    elif kind == 'ancestor_symlink':
        alias = tmp_path / 'private-alias'
        alias.symlink_to(roots['RU'], target_is_directory=True)
        roots['RU'] = alias
    elif kind == 'hardlink':
        os.link(target, tmp_path / 'private-hardlink')
    elif kind == 'fifo':
        target.unlink()
        os.mkfifo(target)
    elif kind == 'overlap':
        roots['NL2'] = roots['RU'] / 'archive'
    else:
        roots['RU'] = Path('relative-secret')
    with pytest.raises(ImportRejected) as raised:
        custody.seal(roots, census, key, IDENTIFIER)
    assert str(raised.value).startswith('CUSTODY_') and str(tmp_path) not in str(raised.value)


@pytest.mark.parametrize('limit', ['MAX_FILE', 'MAX_TOTAL', 'MAX_PLAINTEXT', 'MAX_ENTRIES'])
def test_budgets_refuse_instead_of_truncating(source, monkeypatch, limit):
    monkeypatch.setattr(custody, limit, 1)
    with pytest.raises(ImportRejected, match='CUSTODY_'):
        seal(source)


@pytest.mark.parametrize('kind', ['changed_file', 'added_file', 'removed_empty_directory'])
def test_concurrent_source_changes_refuse(source, monkeypatch, kind):
    roots, _, _ = source
    verify = Reader.verify

    def changed(reader):
        if kind == 'changed_file':
            write(roots['RU'] / 'archive' / 'old-operation' / 'plan.json', b'changed')
        elif kind == 'added_file':
            write(roots['coordinator'] / 'unknown-new-envelope', b'changed')
        else:
            (roots['coordinator'] / 'empty-directory').rmdir()
        verify(reader)

    monkeypatch.setattr(Reader, 'verify', changed)
    with pytest.raises(ImportRejected, match='CUSTODY_SOURCE_REFUSED'):
        seal(source)


def test_stale_custody_is_not_a_current_checkpoint(source):
    roots, census, key = source
    old, previous = seal(source)
    write(roots['RU'] / 'archive' / 'old-operation' / 'unknown-legacy-file', b'new opaque bytes')
    current, expected = custody.seal(roots, census, key, 'f' * 32)
    with pytest.raises(ImportRejected, match='CUSTODY_CHECKPOINT_MISMATCH'):
        custody.inspect(old, key, expected)
    assert custody.inspect(current, key, expected).summary()['activation'] == 'FORBIDDEN'
    assert custody.inspect(old, key, previous).summary()['current_state_recovery'] == 'NOT_QUALIFIED'


def test_no_executor_and_no_recovery_bundle_substitution(source, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('NO_EXECUTOR_ALLOWED')

    monkeypatch.setattr('subprocess.run', forbidden)
    monkeypatch.setattr('subprocess.Popen', forbidden)
    monkeypatch.setattr('os.system', forbidden)
    bundle, checkpoint = seal(source)
    assert custody.inspect(bundle, source[2], checkpoint).summary()['database_import'] == 'NOT_AUTHORIZED'
    with pytest.raises(ImportRejected, match='BUNDLE_CHECKPOINT_REQUIRED'):
        preflight_bundle(bundle, source[2], checkpoint, b'0' * 32, now=1)
    normal = Checkpoint(IDENTIFIER, digest(bundle), digest(b'0' * 32), checkpoint.manifest_sha256)
    with pytest.raises(ImportRejected, match='BUNDLE_FORMAT'):
        preflight_bundle(bundle, source[2], normal, b'0' * 32, now=1)


def test_fresh_nonce_preserves_same_input_identity(source):
    first, before = seal(source)
    second, after = seal(source)
    assert first != second and before.bundle_sha256 != after.bundle_sha256
    assert before.manifest_sha256 == after.manifest_sha256
    assert before.inventory_sha256 == after.inventory_sha256


def test_pending_and_unknown_state_is_preserved_not_executed(source):
    roots, _, key = source
    write(roots['RU'] / 'owner.json', SECRET + b'PENDING')
    path = roots['RU'] / 'completed.json'
    ledger = json.loads(path.read_bytes())
    ledger['old-operation']['result'] = 'UNKNOWN_LEGACY_RESULT'
    write(path, encoded(ledger))
    path = roots['coordinator'] / 'transaction.json'
    current = json.loads(path.read_bytes())
    current['state'] = 'RECOVERY_REQUIRED'
    write(path, encoded(current))
    bundle, checkpoint = custody.seal(roots, inventory(roots), key, IDENTIFIER)
    preserved = custody.inspect(bundle, key, checkpoint)
    assert preserved.trees['RU']['entries']['owner.json']['body'] == SECRET + b'PENDING'
    assert json.loads(preserved.trees['RU']['entries']['completed.json']['body']) == ledger
    assert preserved.summary()['host_resume'] == 'NOT_AUTHORIZED'


@pytest.mark.parametrize('kind', ['malformed_parent', 'alias', 'body_encoding', 'wrong_metadata_type'])
def test_structural_documents_fail_safely(source, kind):
    bundle, checkpoint = seal(source)

    def change(document):
        tree = document['trees']['RU']
        if kind == 'malformed_parent':
            tree['entries']['archive'] = []
        elif kind == 'alias':
            tree['entries']['operation.lock']['metadata']['inode'] = tree['metadata']['inode']
        elif kind == 'body_encoding':
            tree['entries']['operation.lock']['body'] = '*not-base64*'
        else:
            tree['metadata']['mode'] = True

    changed, expected = rewrite(source, bundle, checkpoint, change)
    with pytest.raises(ImportRejected, match='CUSTODY_'):
        custody.inspect(changed, source[2], expected)


def test_full_observed_shapes_survive_source_removal(tmp_path, record_testsuite_property):
    specification = json.loads((Path(__file__).parent / 'fixtures/control_ha_installed_shapes.json').read_text())
    roots = {slot: tmp_path / slot for slot in custody.SLOTS}
    operations = [f'legacy-operation-{index:04d}' for index in range(366)]
    fenced = {operations[0], operations[-2], operations[-1]}
    for slot in ('RU', 'NL1', 'NL2'):
        chosen = operations if slot != 'NL2' else operations[-172:]
        ledger = {operation: dict(result='CLEANED_FENCED_ROLLBACK' if operation in fenced else 'CLEANED')
                  for operation in chosen}
        queues = {True: [operation for operation in chosen if operation in fenced],
                  False: [operation for operation in chosen if operation not in fenced]}
        write(roots[slot] / 'completed.json', encoded(ledger))
        write(roots[slot] / 'operation.lock', b'')
        for item in specification['hosts'][slot]['shapes']:
            for _ in range(item['count']):
                operation = queues['rollback-terminal.json' in item['known']].pop()
                for name in item['known']:
                    write(roots[slot] / 'archive' / operation / name, SECRET + slot.encode() + operation.encode() + name.encode())
        assert not any(queues.values())
    coordinator = roots['coordinator']
    write(coordinator / 'transaction.json', encoded(dict(operation_id=operations[-3], state='COMMITTED',
        gate=dict(authorization='OPERATOR_APPROVED_LEAF_CRL_SCHEDULE'))))
    for name in ('operation.lock', 'plan.json', 'last-receipt.json'):
        write(coordinator / name, SECRET if name != 'operation.lock' else b'')
    for index in range(5):
        write(coordinator / f'adjunct-{index}.json', encoded(dict(operation_id=operations[index], opaque=SECRET.hex())))
    for name in ('recovery-prep', 'recovery-requests', 'recovery-results'):
        write(coordinator / name / 'opaque-artifact', SECRET)
        (coordinator / name / 'empty-directory').mkdir(mode=0o700)
    census = inventory(roots)
    comparison = reconcile(census)
    assert comparison['common_operations'] == 172 and comparison['common_result_disagreements'] == 0
    assert comparison['ru_ledger_without_current_or_history_name'] == 365
    for slot in ('RU', 'NL1', 'NL2'):
        assert census[slot]['node']['shapes'] == specification['hosts'][slot]['shapes']
        assert census[slot]['node']['result_counts'] == specification['hosts'][slot]['result_counts']
    key = secrets.token_bytes(32)
    bundle, checkpoint = custody.seal(roots, census, key, IDENTIFIER)
    before = {slot: {str(path.relative_to(root)): digest(path.read_bytes())
                    for path in root.rglob('*') if path.is_file()} for slot, root in roots.items()}
    for root in roots.values():
        shutil.rmtree(root)
    preserved = custody.inspect(bundle, key, checkpoint)
    for slot, tree in preserved.trees.items():
        assert {name: digest(entry['body']) for name, entry in tree['entries'].items()
                if entry['kind'] == 'file'} == before[slot]
    assert preserved.summary()['files'] > 8000
    assert preserved.summary()['activation'] == 'FORBIDDEN'
    for name, value in preserved.summary().items():
        record_testsuite_property('legacy_custody_' + name, value)
    record_testsuite_property('legacy_custody_bundle_bytes', len(bundle))
    record_testsuite_property('legacy_custody_bundle_sha256', checkpoint.bundle_sha256)
    record_testsuite_property('legacy_custody_manifest_sha256', checkpoint.manifest_sha256)
    record_testsuite_property('legacy_custody_source_removed', all(not root.exists() for root in roots.values()))
