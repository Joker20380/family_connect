import json
from pathlib import Path
import shutil
import sqlite3
import subprocess

from cryptography import x509
import pytest

from scripts import control_ha_installed_current as probe
from scripts.control_ha_installed_inventory import Refused, token
from test_control_ha_current_audit import native_current, UNITS as FIXTURE_UNITS


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if type(value) is bytes else probe.canonical(value))


def remanifest(root, operation):
    archive = root / 'archive' / operation
    manifest = {path.name: probe.sha(path.read_bytes()) for path in archive.iterdir() if path.name != 'archive-manifest.json'}
    write(archive / 'archive-manifest.json', manifest)
    ledger = json.loads((root / 'completed.json').read_bytes())
    ledger[operation]['manifest_sha256'] = probe.sha(probe.canonical(manifest))
    write(root / 'completed.json', ledger)


@pytest.fixture
def installed(native_current, tmp_path, monkeypatch):
    original, recovered, publications, anchor = native_current
    roots = {('NL' if slot == 'NL1' else slot): Path(shutil.copytree(path, tmp_path / slot)) for slot, path in original.items()}
    record = json.loads((roots['coordinator'] / 'transaction.json').read_bytes())
    receipt = json.loads((roots['coordinator'] / 'last-receipt.json').read_bytes())
    monkeypatch.setattr(probe.time, 'time', lambda: receipt['timestamp'] + 1)
    operation = record['operation_id']
    plan = json.loads((roots['coordinator'] / 'plan.json').read_bytes())
    runtime = tmp_path / 'runtime'
    write(runtime / 'node.py', b'NOT_EXECUTABLE_RUNTIME_SENTINEL')
    sources = {'node.py': probe.sha((runtime / 'node.py').read_bytes())}
    configurations = {}
    for slot in probe.UNITS:
        live = tmp_path / ('live-' + slot)
        config = dict(role='RU' if slot == 'RU' else 'NL', gateway_slot=slot, live=str(live), state=str(roots[slot]),
            service_units=list(probe.UNITS[slot]), source_files=sources, source_sha256=probe.sha(probe.canonical(sources)))
        if slot == 'RU':
            write(live / 'issuer.json', plan['candidate']['authority'])
            write(live / 'gateways/nl-amsterdam-2/issuer.json', plan['secondary']['candidate']['authority'])
            write(live / 'revocations.pem', plan['candidate']['crl'].encode())
            write(live / 'directory.json', publications['NL'])
            write(live / 'gateways/nl-amsterdam-2/directory.json', publications['NL2'])
            database = tmp_path / 'access.db'
            target = dict(plan['grant_plan']['before'], restricted_grants=plan['grant_plan']['after_grants'])
            crl = x509.load_pem_x509_crl(plan['candidate']['crl'].encode())
            target['restricted_crl_sequence'] = [dict(singleton=1, sequence=crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number)]
            with sqlite3.connect(database) as connection:
                for table, columns in probe.COLUMNS.items():
                    connection.execute('CREATE TABLE "' + table + '" (' + ','.join('"' + column + '"' for column in columns) + ')')
                    connection.executemany('INSERT INTO "' + table + '" VALUES (' + ','.join('?' for column in columns) + ')',
                        [tuple(row[column] for column in columns) for row in target[table]])
            config['database'] = str(database)
        else:
            candidate = plan['candidate'] if slot == 'NL' else plan['secondary']['candidate']
            write(live / 'private-profile.json', dict(certificate=candidate['certificate'], revocations=candidate['crl'],
                private_key='PRIVATE_KEY_MUST_NOT_LEAVE_HOST'))
            locator = live / 'locator.json'
            write(locator, dict(profile=str(live / 'private-profile.json')))
            config.update(profile_locator=str(locator), profile_locator_sha256=probe.sha(locator.read_bytes()))
            write(live / 'directory.json', publications[slot])
        config_path = tmp_path / ('config-' + slot + '.json')
        write(config_path, config)
        configurations[slot] = config_path
        record['before'][slot]['policy'] = dict(node_config=probe.sha(config_path.read_bytes()))
        archive = roots[slot] / 'archive' / operation
        before = json.loads((archive / 'services-before.json').read_bytes())
        write(archive / 'services-before.json', {new: before[old] for old, new in zip(FIXTURE_UNITS[slot], probe.UNITS[slot])})
        for intent in archive.glob('start-intent-*.json'):
            value = json.loads(intent.read_bytes())
            value['unit'] = probe.UNITS[slot][int(intent.stem.removeprefix('start-intent-'))]
            write(intent, value)
        remanifest(roots[slot], operation)
    write(roots['coordinator'] / 'transaction.json', record)
    controller = tmp_path / 'controller.json'
    write(controller, dict(schema=2, node_config=str(configurations['RU']), coordinator_state=str(roots['coordinator']),
        approved_leaf_crl_schedule=True, ssh=dict(key='PRIVATE_SSH_PATH', target='PRIVATE_TARGET')))
    monkeypatch.setattr(probe, 'systemd', lambda unit: dict(LoadState='loaded', ActiveState='active', SubState='running'))
    return dict(configs=configurations, runtime=runtime, controller=controller, roots=roots, operation=operation)


def observe(installed, slot='RU'):
    return probe.collect(installed['configs'][slot], installed['runtime'],
        controller_path=installed['controller'] if slot == 'RU' else None,
        operation_hash=token(installed['operation']) if slot != 'RU' else None)


def test_current_observations_never_authorize_recovery(installed):
    root = installed['runtime'].parent
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in root.rglob('*') if path.is_file()}
    fleet = {slot: observe(installed, slot) for slot in probe.UNITS}
    result = probe.reconcile(fleet)
    assert result['shared_operation'] and result['shared_plan']
    assert all(result['node_config_matches_record'].values()) and all(result['directory_matches_ru'].values())
    assert all(value['equals_current_plan'] for value in fleet['RU']['database'].values())
    assert all(value['added_rows'] == value['removed_rows'] == 0 for value in fleet['RU']['database'].values())
    assert all(all(value['current_material'].values()) for value in fleet.values())
    assert all(value['equals_committed_publication'] for value in fleet['RU']['directories'].values())
    assert result['recovery'] == 'BLOCKED' and result['activation'] == 'FORBIDDEN' and not result['snapshot_barrier']
    assert fleet['RU']['provenance']['original_schedule_approval'] == 'NOT_ESTABLISHED'
    assert all(not value['signatures_verified'] for value in fleet.values())
    serialized = json.dumps(fleet)
    for private in ('PRIVATE', str(root), installed['operation'], 'legacy-fenced-operation', 'PRIVATE_KEY_MUST_NOT_LEAVE_HOST'):
        assert private not in serialized
    assert set(before) == {path for path in root.rglob('*') if path.is_file()}
    for path, expected in before.items():
        assert (path.read_bytes(), path.stat().st_mtime_ns) == expected


@pytest.mark.parametrize('table', list(probe.COLUMNS))
def test_later_database_state_is_reported_not_repaired(installed, table):
    config = json.loads(installed['configs']['RU'].read_bytes())
    with sqlite3.connect(config['database']) as connection:
        connection.execute('DELETE FROM "' + table + '"')
        if connection.total_changes == 0:
            columns = probe.COLUMNS[table]
            connection.execute('INSERT INTO "' + table + '" VALUES (' + ','.join('?' for column in columns) + ')',
                tuple('PRIVATE_NEW_ROW' for column in columns))
    before = Path(config['database']).read_bytes()
    result = observe(installed)
    assert not result['database'][table]['equals_current_plan']
    assert result['recovery'] == 'BLOCKED' and Path(config['database']).read_bytes() == before
    assert 'PRIVATE_NEW_ROW' not in json.dumps(result)


@pytest.mark.parametrize('kind', ['pending', 'archive_hash', 'fenced', 'unknown_file', 'source', 'units', 'symlink',
    'duplicate_json', 'coordinator_pending', 'wrong_operation', 'wrong_intent', 'locator_hash'])
def test_unqualified_or_unsafe_inputs_refuse(installed, kind):
    root = installed['roots']['RU']
    archive = root / 'archive' / installed['operation']
    slot = 'RU'
    if kind == 'pending':
        write(root / 'owner.json', {})
    elif kind == 'archive_hash':
        write(archive / 'services-before.json', {})
    elif kind == 'fenced':
        ledger = json.loads((root / 'completed.json').read_bytes())
        ledger[installed['operation']]['result'] = 'CLEANED_FENCED_ROLLBACK'
        write(root / 'completed.json', ledger)
    elif kind == 'unknown_file':
        write(archive / 'PRIVATE_NAME', b'PRIVATE_DATA')
    elif kind == 'source':
        write(installed['runtime'] / 'node.py', b'CHANGED')
    elif kind == 'units':
        config = json.loads(installed['configs']['RU'].read_bytes())
        config['service_units'].reverse()
        write(installed['configs']['RU'], config)
    elif kind == 'symlink':
        target = archive / 'plan.json'
        moved = target.with_name('other')
        target.rename(moved)
        target.symlink_to(moved)
    elif kind == 'duplicate_json':
        write(installed['controller'], b'{"schema":2,"schema":2}')
    elif kind == 'coordinator_pending':
        path = installed['roots']['coordinator'] / 'transaction.json'
        record = json.loads(path.read_bytes())
        record['state'] = 'PREPARED'
        write(path, record)
    elif kind == 'wrong_operation':
        installed['operation'] = 'another-operation-identifier'
        slot = 'NL'
    elif kind == 'wrong_intent':
        write(archive / 'start-intent-0.json', dict(unit='other.service'))
        remanifest(root, installed['operation'])
    else:
        slot = 'NL'
        config = json.loads(installed['configs'][slot].read_bytes())
        write(Path(config['profile_locator']), dict(profile='PRIVATE_WRONG_PATH'))
    with pytest.raises((Refused, OSError)):
        observe(installed, slot)


def test_drift_and_directory_refresh_are_not_historical_approval(installed):
    observed = {slot: observe(installed, slot) for slot in probe.UNITS}
    observed['NL']['config_sha256'] = '0' * 64
    observed['NL2']['directories']['NL2']['sha256'] = '1' * 64
    result = probe.reconcile(observed)
    assert result['node_config_matches_record']['NL'] is False
    assert result['directory_matches_ru']['NL2'] is False
    assert result['recovery'] == 'BLOCKED'
    with pytest.raises(Refused, match='FLEET_SCOPE'):
        probe.reconcile({'RU': observed['RU']})


def test_replacement_during_observation_refuses(installed, monkeypatch):
    def changed(unit):
        write(installed['controller'], b'PRIVATE_CHANGED')
        return dict(ActiveState='active')
    monkeypatch.setattr(probe, 'systemd', changed)
    with pytest.raises(Refused, match='OBSERVATION_CHANGED'):
        observe(installed)


def test_only_fixed_product_systemctl_show_is_allowed(monkeypatch):
    calls = []
    def run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, 'LoadState=loaded\nActiveState=inactive\nSubState=dead\nResult=success\n', '')
    monkeypatch.setattr(subprocess, 'run', run)
    value = probe.systemd(probe.RENEWAL_UNITS[0])
    assert value['ActiveState'] == 'inactive' and value['Result'] == 'success'
    assert calls[0][0][:3] == ['systemctl', 'show', probe.RENEWAL_UNITS[0]]
    with pytest.raises(Refused, match='UNIT_SCOPE'):
        probe.systemd('unrelated.service')
    assert len(calls) == 1


def test_cli_refusal_does_not_leak_private_exception(installed, monkeypatch, capsys):
    def failure(*args, **kwargs):
        raise ValueError('PRIVATE_KEY_AND_PATH')
    monkeypatch.setattr(probe, 'collect', failure)
    assert probe.main(['--config', str(installed['configs']['RU']), '--runtime', str(installed['runtime'])]) == 1
    output = capsys.readouterr().out
    assert json.loads(output)['recovery'] == 'BLOCKED' and 'PRIVATE' not in output


@pytest.mark.parametrize('timestamp', ['PRIVATE_TIMESTAMP', True, 2**63])
def test_untrusted_receipt_time_refuses_without_export(installed, timestamp):
    path = installed['roots']['coordinator'] / 'last-receipt.json'
    receipt = json.loads(path.read_bytes())
    receipt['timestamp'] = timestamp
    write(path, receipt)
    with pytest.raises(Refused, match='COORDINATOR_TIME'):
        observe(installed)


def test_row_difference_preserves_duplicates_without_revealing_rows():
    assert probe.row_difference([dict(private='secret')] * 2, [dict(private='secret')]) == dict(
        baseline_rows=1, unchanged_rows=1, added_rows=1, removed_rows=0)


def test_bad_certificate_timing_is_not_acceptance():
    assert probe.certificate_timing([dict(certificate='PRIVATE_BAD_PEM')], [], 100) == dict(parsed=False)


def test_database_row_limit(installed):
    config = json.loads(installed['configs']['RU'].read_bytes())
    with sqlite3.connect(config['database']) as connection:
        connection.execute('DELETE FROM invites')
        connection.executemany('INSERT INTO invites VALUES (?, ?, ?)', [('PRIVATE', None, 0)] * 4097)
    with pytest.raises(Refused, match='DATABASE_ROW_LIMIT'):
        observe(installed)


def test_wal_without_sidecars_refuses_before_sqlite_open(installed, monkeypatch):
    config = json.loads(installed['configs']['RU'].read_bytes())
    with sqlite3.connect(config['database']) as connection:
        connection.execute('PRAGMA journal_mode=WAL')
    connection.close()
    def forbidden(*args, **kwargs):
        raise AssertionError('SQLite must not initialize sidecars')
    monkeypatch.setattr(sqlite3, 'connect', forbidden)
    with pytest.raises(Refused, match='DATABASE_WAL_SIDECARS_MISSING'):
        observe(installed)


def test_existing_wal_includes_uncheckpointed_rows(installed):
    config = json.loads(installed['configs']['RU'].read_bytes())
    writer = sqlite3.connect(config['database'])
    try:
        writer.execute('PRAGMA journal_mode=WAL')
        writer.execute('PRAGMA wal_autocheckpoint=0')
        writer.execute('INSERT INTO invites VALUES (?, ?, ?)', ('PRIVATE_WAL', None, 0))
        writer.commit()
        result = observe(installed)
        assert result['database']['invites']['added_rows'] == 1
        assert not result['database']['invites']['equals_current_plan']
        assert 'PRIVATE_WAL' not in json.dumps(result)
    finally:
        writer.close()
