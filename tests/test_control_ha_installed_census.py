import json
from pathlib import Path
import runpy
import sqlite3
from types import SimpleNamespace

import pytest

from scripts import control_ha_installed_census as census


@pytest.fixture
def database(tmp_path):
    path = tmp_path / 'source.db'
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE devices(identity TEXT PRIMARY KEY, private_value TEXT DEFAULT 'secret-default')")
        connection.execute("INSERT INTO devices VALUES ('private-device', 'private-row')")
    return path


def test_schema_only_never_exports_rows_or_default_literals(database):
    before = database.read_bytes()
    result = census.database_schema(database)
    raw = json.dumps(result)
    assert 'private-device' not in raw and 'private-row' not in raw and 'secret-default' not in raw
    assert result['columns']['devices'][1]['default_sha256']
    assert result['row_values_read'] is False
    assert result['coherent_cross_store_snapshot'] == 'NOT_QUALIFIED'
    assert database.read_bytes() == before


def test_definition_digest_matches_existing_manifest_encoding(database):
    from scripts.control_ha_import import encoded, digest
    from scripts.control_ha_sqlite_import import definitions
    with sqlite3.connect(database) as connection:
        expected = digest(encoded(definitions(connection)))
    assert census.database_schema(database)['definitions_sha256'] == expected


def test_wal_schema_seen_without_checkpoint_or_immutable_mode(database):
    with sqlite3.connect(database) as writer:
        writer.execute('PRAGMA journal_mode=WAL')
        writer.execute('CREATE TABLE fresh(value TEXT)')
        writer.commit()
        assert 'fresh' in census.database_schema(database)['columns']


def test_wal_without_existing_sidecars_refuses_without_creating_them(database):
    with sqlite3.connect(database) as writer:
        writer.execute('PRAGMA journal_mode=WAL')
    writer.close()
    before = set(database.parent.iterdir())
    with pytest.raises(ValueError, match='DATABASE_WAL_SIDECARS_MISSING'):
        census.database_schema(database)
    assert set(database.parent.iterdir()) == before


def test_unsafe_sidecar_refuses(database, tmp_path):
    database.with_name(database.name + '-wal').symlink_to(database)
    with pytest.raises(ValueError, match='DATABASE_SIDECAR_UNSAFE'):
        census.database_schema(database)


@pytest.mark.parametrize('kind', ['symlink', 'parent-symlink', 'hardlink', 'directory', 'empty'])
def test_unsafe_file_refused(database, tmp_path, kind):
    path = tmp_path / 'target'
    if kind == 'symlink':
        path.symlink_to(database)
    elif kind == 'parent-symlink':
        path.symlink_to(tmp_path, target_is_directory=True)
        path = path / database.name
    elif kind == 'hardlink':
        path.hardlink_to(database)
    elif kind == 'directory':
        path.mkdir()
    else:
        path.touch()
    with pytest.raises(ValueError):
        census.database_schema(path)


def test_object_limit_refuses(database, monkeypatch):
    monkeypatch.setattr(census, 'MAX_OBJECTS', 1)
    with pytest.raises(ValueError, match='SCHEMA_BOUNDS'):
        census.database_schema(database)


def test_source_hash_cannot_escape_declared_root_with_parent_segments(database):
    traversed = database.parent / '..' / database.parent.name / database.name
    with pytest.raises(ValueError, match='UNSAFE_PATH'):
        census.file_hash(traversed)


def test_discovery_only_explicit_stores_not_backups_or_nested_databases(tmp_path, database):
    root = tmp_path / 'product'
    root.mkdir()
    (root / 'outside').symlink_to(tmp_path, target_is_directory=True)
    (root / 'backup').mkdir()
    (root / 'backup' / 'access.db').write_bytes(database.read_bytes())
    for number in range(40):
        (root / ('backup-' + str(number) + '.db')).write_bytes(database.read_bytes())
    target = root / 'access.db'
    target.write_bytes(database.read_bytes())
    assert census.database_candidates(root) == [target]


def test_explicit_store_symlink_is_refused(tmp_path, database):
    (tmp_path / 'access.db').symlink_to(database)
    with pytest.raises(ValueError, match='DATABASE_SYMLINK'):
        census.database_candidates(tmp_path)


def test_absent_defaults_do_not_discover_unrelated_databases(tmp_path, database):
    assert census.database_candidates(tmp_path) == []


def test_systemctl_command_is_read_only_fixed_and_private(monkeypatch):
    calls = []
    def run(command, **options):
        calls.append((command, options))
        return SimpleNamespace(returncode=1, stdout=b'', stderr=b'private credentials')
    monkeypatch.setattr(census.subprocess, 'run', run)
    with pytest.raises(ValueError, match='SYSTEMD_OBSERVATION_FAILED') as failure:
        census.systemctl('show', 'family-connect-test.service')
    assert 'private credentials' not in str(failure.value)
    assert calls[0][0] == ['systemctl', 'show', 'family-connect-test.service', '--no-pager']
    assert calls[0][1]['env'] == {'PATH': census.os.defpath, 'LC_ALL': 'C'}
    with pytest.raises(ValueError, match='READ_ONLY_SYSTEMD_ONLY'):
        census.systemctl('stop', 'family-connect-test.service')
    assert len(calls) == 1


def test_unit_census_combines_installed_and_loaded_without_neighbors(monkeypatch):
    def command(mode, *args):
        return 'family-connect-file.service enabled\n' if mode == 'list-unit-files' else 'family-connect-transient.service loaded active running\n'
    monkeypatch.setattr(census, 'systemctl', command)
    assert census.unit_names() == ['family-connect-file.service', 'family-connect-transient.service']
    monkeypatch.setattr(census, 'systemctl', lambda *args: 'other-project.service enabled\n')
    with pytest.raises(ValueError, match='UNEXPECTED_UNIT'):
        census.unit_names()


def test_unit_arguments_and_environment_never_exported(monkeypatch):
    monkeypatch.setattr(census, 'systemctl', lambda *args: 'Id=family-connect-test.service\nActiveState=active\n'
        'ExecStart={ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 --password secret-token ; }\n'
        'EnvironmentFiles=/private/config\n')
    result = census.observe_unit('family-connect-test.service')
    assert 'secret-token' not in json.dumps(result) and '/private/config' not in json.dumps(result)
    assert result['all_writers_qualified'] is False
    with pytest.raises(ValueError, match='UNEXPECTED_UNIT'):
        census.observe_unit('other-project.service')


def test_missing_source_retains_unit_state_but_never_qualifies_writer(monkeypatch):
    monkeypatch.setattr(census, 'systemctl', lambda *args: 'Id=family-connect-test.service\nActiveState=failed\n'
        'ExecStart={ path=/opt/apps/family_connect/missing.py ; }\n')
    monkeypatch.setattr(census, 'file_hash', lambda *args: (_ for _ in ()).throw(FileNotFoundError()))
    result = census.observe_unit('family-connect-test.service')
    assert result['state']['ActiveState'] == 'failed'
    assert result['entrypoint_source_sha256']['/opt/apps/family_connect/missing.py']['status'] == 'REFUSED'
    assert result['all_writers_qualified'] is False


@pytest.fixture
def observed_schemas():
    root = Path(__file__).resolve().parents[1]
    application = json.loads((root / 'deploy/control-ha/sqlite-source-v1.json').read_bytes())
    handoff = json.loads((root / 'deploy/control-ha/sqlite-handoff-v2.json').read_bytes())
    observation = dict(version=1, node='RU', databases=[])
    for name, store in [('access.db', 'registry'), ('diagnostics.sqlite', 'diagnostics'),
                        ('notices.sqlite', 'notices'), ('technical-metadata.sqlite', 'metadata')]:
        definitions = application['stores'][store] + (handoff['definitions'] if store == 'registry' else [])
        definitions.sort(key=lambda row: row[1])
        observation['databases'].append(dict(path='/synthetic/' + name,
            definitions_sha256=census.digest(census.canonical(definitions)),
            properties=dict(user_version=0, application_id=0, encoding='UTF-8')))
    return observation, application, handoff


def test_pinned_handoff_definitions_match_existing_migration_source(observed_schemas):
    _, _, handoff = observed_schemas
    root = Path(__file__).resolve().parents[1]
    source = root / handoff['source']
    assert census.file_hash(source) == handoff['source_sha256']
    namespace = runpy.run_path(str(source))
    with sqlite3.connect(':memory:') as connection:
        connection.row_factory = sqlite3.Row
        connection.execute('BEGIN')
        namespace['migrate'](connection)
        actual = [list(row) for row in connection.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY name')]
    assert actual == handoff['definitions']


def test_recognized_schema_is_not_implemented_import_or_writer_acceptance(observed_schemas):
    result = census.compare_schemas(*observed_schemas)
    assert result['schema_coverage'] is True
    assert result['stores']['registry']['adapter'] == 'NOT_IMPLEMENTED_HANDOFF_OVERLAY'
    assert result['import_ready'] is False and result['all_writers_qualified'] is False
    assert result['activation'] == 'FORBIDDEN'


@pytest.mark.parametrize('change', ['definitions', 'user_version', 'application_id', 'encoding'])
def test_changed_schema_or_format_cannot_match(observed_schemas, change):
    observation, application, handoff = observed_schemas
    if change == 'definitions':
        observation['databases'][0]['definitions_sha256'] = '0' * 64
    else:
        observation['databases'][0]['properties'][change] = 'changed'
    result = census.compare_schemas(observation, application, handoff)
    assert result['schema_coverage'] is False
    assert result['stores']['registry']['schema'] == 'UNSUPPORTED'


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'unknown', 'failed'])
def test_partial_or_failed_observation_refuses(observed_schemas, change):
    observation, application, handoff = observed_schemas
    if change == 'missing':
        observation['databases'].pop()
    elif change == 'duplicate':
        observation['databases'][1] = observation['databases'][0]
    elif change == 'unknown':
        observation['databases'][1]['path'] = '/synthetic/backup.db'
    else:
        observation['databases'][1]['status'] = 'REFUSED'
    with pytest.raises(ValueError):
        census.compare_schemas(observation, application, handoff)


def test_exact_family_transient_fragment_is_observed_without_expanding_scope(monkeypatch):
    monkeypatch.setattr(census, 'systemctl', lambda *args: 'Id=family-connect-test.service\nActiveState=active\n'
        'MainPID=0\nControlPID=0\nFragmentPath=/run/systemd/transient/family-connect-test.service\n')
    monkeypatch.setattr(census, 'file_hash', lambda *args: '0' * 64)
    result = census.observe_unit('family-connect-test.service')
    assert result['fragment_sha256'] == '0' * 64
    assert result['state']['MainPID'] == '0' and result['all_writers_qualified'] is False
    monkeypatch.setattr(census, 'systemctl', lambda *args: 'Id=family-connect-test.service\n'
        'FragmentPath=/run/systemd/transient/neighbour.service\n')
    with pytest.raises(ValueError, match='UNIT_FRAGMENT_SCOPE'):
        census.observe_unit('family-connect-test.service')


@pytest.fixture
def containers():
    return [dict(Name='/fc-control-plane-0-' + name + '-1', Image='sha256:' + 'a' * 64,
        State=dict(Running=True, Restarting=False, ExitCode=0, Pid=123), RestartCount=0,
        Config=dict(Labels={'com.docker.compose.project': 'fc-control-plane-0'},
                    Env=['PASSWORD=private-password'], Cmd=['--token=private-token']),
        Mounts=[dict(Type='bind', RW=True, Source='/private/customer-state', Destination='/private/mount')])
        for name in ('console', 'postgres', 'system_publisher')]


def test_panel_observation_is_exact_project_and_never_exports_secrets(containers, monkeypatch):
    calls = []
    def run(command, **options):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout=json.dumps(containers).encode())
    monkeypatch.setattr(census.subprocess, 'run', run)
    result = census.panel_containers()
    assert calls == [['docker', 'inspect', 'fc-control-plane-0-console-1', 'fc-control-plane-0-postgres-1',
                      'fc-control-plane-0-system_publisher-1']]
    raw = json.dumps(result)
    assert all(value not in raw for value in ('private-password', 'private-token', '/private/customer-state', '/private/mount'))
    assert all(item['all_writers_qualified'] is False for item in result)


@pytest.mark.parametrize('changed', ['name', 'project', 'image', 'count'])
def test_other_or_unidentified_containers_refuse(containers, monkeypatch, changed):
    if changed == 'name':
        containers[0]['Name'] = '/neighbour'
    elif changed == 'project':
        containers[0]['Config']['Labels']['com.docker.compose.project'] = 'neighbour'
    elif changed == 'image':
        containers[0]['Image'] = 'mutable-tag'
    else:
        containers.pop()
    monkeypatch.setattr(census.subprocess, 'run', lambda *args, **kwargs:
        SimpleNamespace(returncode=0, stdout=json.dumps(containers).encode()))
    with pytest.raises(ValueError):
        census.panel_containers()


@pytest.mark.parametrize('kind', ['cron', 'authorized_keys'])
def test_dispatch_scan_is_private_literal_evidence_not_complete_coverage(kind):
    raw = (b'# ignored\ncommand="/opt/apps/family_connect/helper --secret private-token",restrict '
           b'ssh-ed25519 public-material user@example.test\ncommand="/other/project/helper" other-material\n')
    result = census.scoped_dispatch_lines(raw, kind)
    assert len(result['scoped_lines']) == 1 and result['other_line_count'] == 1
    assert result['coverage'] == 'LITERAL_ROOT_MATCH_ONLY' and result['all_writers_qualified'] is False
    assert all(value not in json.dumps(result) for value in ('private-token', 'public-material', 'user@example.test', '/other/project'))
    assert result['scoped_lines'][0]['forced_command_candidate'] == (kind == 'authorized_keys')


def test_dispatch_bounds_and_kind_refuse():
    with pytest.raises(ValueError, match='DISPATCH_BOUNDS'):
        census.scoped_dispatch_lines(b'x' * (128 * 1024 + 1), 'cron')
    with pytest.raises(ValueError, match='DISPATCH_LINE_BOUNDS'):
        census.scoped_dispatch_lines(b'x\n' * 257, 'cron')
    with pytest.raises(ValueError, match='DISPATCH_KIND'):
        census.scoped_dispatch_lines(b'value', 'execute')


def test_missing_root_crontab_is_distinguished_from_failed_observation(tmp_path, monkeypatch):
    keys = tmp_path / 'authorized_keys'
    calls = []
    def run(command, **options):
        calls.append(command)
        return SimpleNamespace(returncode=1, stdout=b'', stderr=b'no crontab for root\n')
    monkeypatch.setattr(census.subprocess, 'run', run)
    result = census.root_dispatchers(keys)
    assert calls == [['crontab', '-l', '-u', 'root']]
    assert result['authorized_keys']['status'] == result['crontab']['status'] == 'ABSENT'
    monkeypatch.setattr(census.subprocess, 'run', lambda *args, **kwargs:
        SimpleNamespace(returncode=1, stdout=b'', stderr=b'permission denied private detail'))
    with pytest.raises(ValueError, match='CRON_OBSERVATION_FAILED'):
        census.root_dispatchers(keys)
