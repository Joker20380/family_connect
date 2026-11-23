import hashlib
import json
import os
from copy import deepcopy

import pytest

from scripts.control_ha_installed_inventory import Reader, Refused, collect, main, reconcile, token


@pytest.fixture
def journals(tmp_path):
    root, coordinator = tmp_path / 'node', tmp_path / 'coordinator'
    archive = root / 'archive' / 'private-operation-id'
    archive.mkdir(parents=True)
    coordinator.mkdir()
    (root / 'completed.json').write_text(json.dumps({'private-operation-id': {'result': 'CLEANED'}}))
    (archive / 'gateway.json.before').write_text('PRIVATE_PROFILE_DO_NOT_READ')
    (archive / 'services-before.json').write_text('PRIVATE_SERVICE_DATA')
    (archive / 'start-intent-0.json').write_text('PRIVATE_SERVICE_INTENT')
    (archive / 'private-user-filename').write_text('PRIVATE_OTHER')
    (coordinator / 'transaction.json').write_text(json.dumps(dict(operation_id='private-operation-id',
        state='COMMITTED', previous={'private_key': 'PRIVATE_KEY'}, arbitrary='PRIVATE_VALUE')))
    return root, coordinator, archive


def test_sanitized_read_only_shapes(journals, monkeypatch):
    root, coordinator, archive = journals
    original = {path: (path.read_bytes(), path.stat()) for path in root.parent.rglob('*') if path.is_file()}
    real_raw = Reader.raw

    def guarded(reader, path):
        assert path.parent != archive
        return real_raw(reader, path)

    monkeypatch.setattr(Reader, 'raw', guarded)
    result = collect(root, coordinator)
    serialized = json.dumps(result)
    for private in ('PRIVATE', 'private-user-filename', 'private-operation-id', str(root)):
        assert private not in serialized
    assert result['node']['result_counts'] == {'CLEANED': 1}
    assert result['node']['shapes'] == [dict(count=1, known=['gateway.json.before', 'services-before.json',
        'start-intent-0.json'], other_count=1)]
    assert result['node']['missing_archives'] == result['node']['unledgered_archives'] == 0
    assert result['coordinator']['history_present'] is False
    assert result['coordinator']['current']['operation'] == token('private-operation-id')
    assert result['activation'] == 'FORBIDDEN' and result['snapshot_barrier'] is False
    for path, (raw, information) in original.items():
        assert path.read_bytes() == raw
        assert path.stat().st_mtime_ns == information.st_mtime_ns


@pytest.mark.parametrize('kind', ['file_symlink', 'parent_symlink', 'hardlink', 'fifo', 'nested_directory'])
def test_unsafe_shapes_refuse(journals, tmp_path, kind):
    root, coordinator, archive = journals
    target = archive / 'gateway.json.before'
    if kind == 'parent_symlink':
        alias = tmp_path / 'alias'
        alias.symlink_to(root, target_is_directory=True)
        root = alias
    elif kind == 'hardlink':
        os.link(target, tmp_path / 'other-link')
    else:
        target.unlink()
        if kind == 'file_symlink':
            target.symlink_to(root / 'completed.json')
        elif kind == 'fifo':
            os.mkfifo(target)
        else:
            target.mkdir()
    with pytest.raises((Refused, OSError)):
        collect(root, coordinator)


@pytest.mark.parametrize('document', ['{"duplicate":1,"duplicate":2}', '[]', '{', '{"bad":2}'])
def test_invalid_ledger_refuses(journals, document):
    root, coordinator, _ = journals
    (root / 'completed.json').write_text(document)
    with pytest.raises((Refused, ValueError)):
        collect(root, coordinator)


def test_unknown_values_are_redacted(journals):
    root, coordinator, _ = journals
    (root / 'completed.json').write_text(json.dumps({'secret': {'result': ['SECRET_RESULT']}}))
    (coordinator / 'transaction.json').write_text(json.dumps(dict(operation_id='secret',
        state=['SECRET_STATE'], mode={'SECRET_MODE': 'value'})))
    result = collect(root, coordinator)
    assert 'SECRET' not in json.dumps(result)
    assert result['node']['result_counts'] == {'OTHER': 1}
    assert result['node']['missing_archives'] == result['node']['unledgered_archives'] == 1


@pytest.mark.parametrize('change', ['replace_file', 'add_archive', 'change_payload'])
def test_concurrent_change_refuses(journals, monkeypatch, change):
    root, coordinator, archive = journals
    verify = Reader.verify

    def changed(reader):
        if change == 'replace_file':
            target = root / 'completed.json'
            raw = target.read_bytes()
            target.unlink()
            target.write_bytes(raw)
        elif change == 'add_archive':
            (root / 'archive' / 'new').mkdir()
        else:
            (archive / 'gateway.json.before').write_text('changed')
        verify(reader)

    monkeypatch.setattr(Reader, 'verify', changed)
    with pytest.raises(Refused, match='OBSERVATION_CHANGED'):
        collect(root, coordinator)


def test_limits(journals, monkeypatch):
    root, coordinator, _ = journals
    with pytest.raises(Refused, match='ENTRY_LIMIT'):
        Reader().names(root, 1)
    monkeypatch.setattr('scripts.control_ha_installed_inventory.MAX_DOCUMENT', 2)
    with pytest.raises(Refused, match='DOCUMENT_LIMIT'):
        collect(root, coordinator)


@pytest.mark.parametrize('limit', ['MAX_READ', 'MAX_OBSERVED'])
def test_global_budgets(journals, monkeypatch, limit):
    root, coordinator, _ = journals
    monkeypatch.setattr('scripts.control_ha_installed_inventory.' + limit, 1)
    with pytest.raises(Refused, match='(READ|METADATA)_LIMIT'):
        collect(root, coordinator)


def test_source_pin_and_history_presence(journals, tmp_path):
    root, coordinator, _ = journals
    runtime = tmp_path / 'runtime'
    runtime.mkdir()
    (runtime / 'node.py').write_text('raise AssertionError("MUST_NOT_EXECUTE")')
    hashes = {'node.py': hashlib.sha256((runtime / 'node.py').read_bytes()).hexdigest()}
    aggregate = hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    config = tmp_path / 'config.json'
    config.write_text(json.dumps(dict(source_files=hashes, source_sha256=aggregate)))
    result = collect(root, coordinator, config, runtime)['source']
    assert result['files_match'] and result['aggregate_matches']
    assert result['history_module_present'] is False
    (runtime / 'node.py').write_text('different')
    (runtime / 'online_history.py').write_text('not declared')
    result = collect(root, coordinator, config, runtime)['source']
    assert not result['files_match'] and not result['aggregate_matches']
    assert result['history_module_present'] and not result['history_module_declared']


def test_history_is_names_only_not_validated_custody(journals):
    root, coordinator, _ = journals
    history = coordinator / 'history'
    history.mkdir()
    (history / 'private-operation-id.json').write_text('not a valid history document')
    result = collect(root, coordinator)
    assert result['coordinator']['history_count'] == 1
    assert result['approval_custody'] == 'NOT_ESTABLISHED'
    assert result['signatures_verified'] is False


def test_adjuncts_are_not_invented_history(journals):
    root, coordinator, _ = journals
    (coordinator / 'private-backup-name.json').write_text(json.dumps(dict(operation_id='private-old-id',
        state='SECRET_STATE', files={'private': 'secret'}, arbitrary='secret')))
    result = collect(root, coordinator)
    assert result['coordinator']['adjunct_json'] == [dict(operation=token('private-old-id'),
        record_fields=['files', 'operation_id', 'state'])]
    assert result['coordinator']['history_count'] == 0
    assert 'SECRET' not in json.dumps(result) and 'private-backup-name' not in json.dumps(result)


def test_native_scheduled_gate(journals):
    root, coordinator, _ = journals
    path = coordinator / 'transaction.json'
    record = json.loads(path.read_bytes())
    record['gate'] = dict(authorization='OPERATOR_APPROVED_LEAF_CRL_SCHEDULE')
    path.write_text(json.dumps(record))
    result = collect(root, coordinator)
    assert result['coordinator']['current']['gate_authorization'] == 'OPERATOR_APPROVED_LEAF_CRL_SCHEDULE'


def test_cli_error_does_not_disclose_path(monkeypatch, capsys):
    monkeypatch.setattr('sys.argv', ['inventory', '--root', '/nonexistent/private-secret-path'])
    assert main() == 1
    assert json.loads(capsys.readouterr().out) == dict(observation='REFUSED', activation='FORBIDDEN')


def test_reconcile_different_cohorts_without_inventing_history(journals):
    root, coordinator, _ = journals
    document = collect(root, coordinator)
    documents = {slot: deepcopy(document) for slot in ('RU', 'NL1', 'NL2')}
    for slot in ('RU', 'NL1'):
        documents[slot]['node']['ledger'][token('older')] = 'CLEANED'
    result = reconcile(documents)
    assert result['common_operations'] == 1 and result['union_operations'] == 2
    assert result['hosts']['NL2']['outside_common'] == 0
    assert result['current_in_all_ledgers'] is True
    assert result['ru_ledger_without_current_or_history_name'] == 1
    assert result['common_result_disagreements'] == 0
    assert result['recovery_ready'] is False
    documents['NL2']['node']['ledger'][token('private-operation-id')] = 'CLEANED_FENCED_ROLLBACK'
    assert reconcile(documents)['common_result_disagreements'] == 1
    del documents['NL2']['node']['ledger'][token('private-operation-id')]
    assert reconcile(documents)['current_in_all_ledgers'] is False


@pytest.mark.parametrize('invalid', ['missing_node', 'failed_node', 'wrong_purpose'])
def test_reconcile_incomplete_refuses(journals, invalid):
    root, coordinator, _ = journals
    documents = {slot: collect(root, coordinator) for slot in ('RU', 'NL1', 'NL2')}
    if invalid == 'missing_node':
        del documents['NL2']
    elif invalid == 'failed_node':
        documents['NL2']['observation'] = 'REFUSED'
    else:
        documents['NL2']['purpose'] = 'something-else'
    with pytest.raises(Refused):
        reconcile(documents)
