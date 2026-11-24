"""Bounded read-only Family Connect schema/unit census; never a coherent capture permit."""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import subprocess
import time

PRODUCT = Path('/opt/apps/family_connect')
DATABASE_NAMES = ('access.db', 'diagnostics.sqlite', 'notices.sqlite', 'technical-metadata.sqlite')
MAX_OBJECTS = 256
MAX_BYTES = 96 * 1024 * 1024
PROPERTIES = ('Id', 'LoadState', 'ActiveState', 'SubState', 'MainPID', 'ControlPID', 'Type',
              'Result', 'ExecMainStatus', 'NRestarts', 'Restart', 'Environment',
              'FragmentPath', 'DropInPaths', 'ExecStart', 'EnvironmentFiles', 'ControlGroup', 'Triggers', 'TriggeredBy')
UNIT = re.compile(r'family-connect-[A-Za-z0-9_.@-]{1,120}\.(?:service|timer)\Z')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def identity(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and
            all(not parent.is_symlink() for parent in (path, *path.parents)), 'UNSAFE_PATH')
    record = path.stat()
    require(stat.S_ISREG(record.st_mode) and record.st_nlink == 1 and 0 < record.st_size <= MAX_BYTES,
            'UNSAFE_FILE')
    return (record.st_dev, record.st_ino, record.st_size, record.st_mtime_ns, record.st_ctime_ns)


def file_bytes(path, maximum=2 * 1024 * 1024):
    before = identity(path)
    require(before[2] <= maximum, 'FILE_BOUNDS')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as source:
        opened = os.fstat(source.fileno())
        require((opened.st_dev, opened.st_ino) == before[:2], 'FILE_REPLACED')
        raw = source.read(maximum + 1)
    require(len(raw) == before[2] and identity(path) == before, 'FILE_CHANGED')
    return raw


def file_hash(path, maximum=2 * 1024 * 1024):
    return digest(file_bytes(path, maximum))


def database_schema(path):
    path = Path(path)
    before = identity(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as source:
        header = source.read(20)
    require(header[:16] == b'SQLite format 3\x00', 'DATABASE_HEADER')
    for suffix in ('-wal', '-shm', '-journal'):
        sidecar = path.with_name(path.name + suffix)
        require(not sidecar.is_symlink(), 'DATABASE_SIDECAR_UNSAFE')
        if sidecar.exists():
            record = sidecar.stat()
            require(stat.S_ISREG(record.st_mode) and record.st_nlink == 1, 'DATABASE_SIDECAR_UNSAFE')
    require(header[18:20] != b'\x02\x02' or all(path.with_name(path.name + suffix).exists()
            for suffix in ('-wal', '-shm')), 'DATABASE_WAL_SIDECARS_MISSING')
    deadline = time.monotonic() + 5
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=2)) as database:
        database.enable_load_extension(False)
        database.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 1024 * 1024)
        database.execute('PRAGMA trusted_schema=OFF')
        database.execute('PRAGMA query_only=ON')
        database.set_progress_handler(lambda: time.monotonic() > deadline, 1000)
        database.execute('BEGIN')
        rows = [list(row) for row in database.execute(
            'SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY name').fetchmany(MAX_OBJECTS + 1)]
        require(0 < len(rows) <= MAX_OBJECTS and len(canonical(rows)) <= 1024 * 1024, 'SCHEMA_BOUNDS')
        columns = {}
        for kind, name, table, declaration in rows:
            require(kind in ('table', 'index', 'view', 'trigger') and type(name) is str and len(name) <= 256 and
                    type(table) is str and len(table) <= 256, 'SCHEMA_OBJECT')
            if kind == 'table' and not name.startswith('sqlite_'):
                values = database.execute('SELECT name,type,"notnull",dflt_value,pk,hidden FROM pragma_table_xinfo(?)',
                                          (name,)).fetchmany(129)
                require(len(values) <= 128, 'COLUMN_BOUNDS')
                columns[name] = [dict(name=row[0], type=row[1], notnull=row[2],
                    default_sha256=digest(canonical(row[3])) if row[3] is not None else None,
                    primary_key=row[4], hidden=row[5]) for row in values]
        properties = {name: database.execute('PRAGMA ' + name).fetchone()[0]
                      for name in ('user_version', 'application_id', 'encoding', 'journal_mode', 'schema_version')}
        database.rollback()
    require(identity(path)[:2] == before[:2], 'DATABASE_REPLACED')
    return dict(path=str(path), definitions_sha256=digest(canonical(rows)), columns=columns,
        objects=[dict(type=row[0], name=row[1], table=row[2], sql_sha256=digest(canonical(row[3]))) for row in rows],
        properties=properties, file_changed=identity(path) != before,
        coherent_cross_store_snapshot='NOT_QUALIFIED', row_values_read=False)


def database_candidates(root=PRODUCT / 'friends-access'):
    require(root.is_absolute() and not root.is_symlink(), 'UNSAFE_ROOT')
    found = []
    for name in DATABASE_NAMES:
        path = root / name
        require(not path.is_symlink(), 'DATABASE_SYMLINK')
        if path.exists():
            found.append(path)
    return sorted(found)


def systemctl(*arguments):
    require(arguments and arguments[0] in ('show', 'list-unit-files', 'list-units'), 'READ_ONLY_SYSTEMD_ONLY')
    result = subprocess.run(['systemctl', *arguments, '--no-pager'], capture_output=True, timeout=10,
                            env={'PATH': os.defpath, 'LC_ALL': 'C'})
    require(result.returncode == 0 and len(result.stdout) <= 256 * 1024, 'SYSTEMD_OBSERVATION_FAILED')
    return result.stdout.decode('utf-8')


def unit_names():
    names = set()
    for mode in ('list-unit-files', 'list-units'):
        raw = systemctl(mode, 'family-connect*', '--all', '--plain', '--no-legend')
        for line in raw.splitlines():
            name = line.split()[0] if line.split() else ''
            require(UNIT.fullmatch(name), 'UNEXPECTED_UNIT')
            names.add(name)
    require(0 < len(names) <= 128, 'UNIT_COUNT')
    return sorted(names)


def observe_unit(name):
    require(UNIT.fullmatch(name), 'UNEXPECTED_UNIT')
    raw = systemctl('show', name, '--property=' + ','.join(PROPERTIES))
    values = dict(line.split('=', 1) for line in raw.splitlines() if '=' in line)
    require(set(values) <= set(PROPERTIES) and values.get('Id') == name, 'UNIT_PROPERTIES')
    retained = {key: values.get(key, '') for key in
                ('Id', 'LoadState', 'ActiveState', 'SubState', 'MainPID', 'ControlPID', 'Type',
                 'Result', 'ExecMainStatus', 'NRestarts', 'Restart', 'Triggers', 'TriggeredBy')}
    private_fields = {key: digest(values.get(key, '').encode()) for key in
                      ('ExecStart', 'Environment', 'EnvironmentFiles', 'ControlGroup', 'DropInPaths')}
    sources = {}
    for candidate in sorted(set(re.findall(r'/(?:opt/apps/family_connect|var/lib/fc-profile-control)/[A-Za-z0-9_./-]+',
                                          values.get('ExecStart', '')))):
        if candidate.endswith(('.py', '.sh', '.pyz')):
            try:
                sources[candidate] = dict(sha256=file_hash(candidate, 32 * 1024 * 1024))
            except (OSError, ValueError):
                sources[candidate] = dict(status='REFUSED', reason='SOURCE_OBSERVATION_FAILED')
    fragment = values.get('FragmentPath')
    if fragment:
        path = Path(fragment)
        require(path.is_relative_to('/etc/systemd/system') or path.is_relative_to('/run/systemd/system') or
                path == Path('/run/systemd/transient') / name or
                path.is_relative_to('/usr/lib/systemd/system') or path.is_relative_to('/lib/systemd/system'),
                'UNIT_FRAGMENT_SCOPE')
        try:
            fragment_hash = file_hash(path, 128 * 1024)
        except (OSError, ValueError):
            fragment_hash = 'REFUSED'
    else:
        fragment_hash = None
    return dict(state=retained, private_field_sha256=private_fields, entrypoint_source_sha256=sources,
                fragment_sha256=fragment_hash, all_writers_qualified=False)


def panel_containers():
    names = ('fc-control-plane-0-console-1', 'fc-control-plane-0-postgres-1', 'fc-control-plane-0-system_publisher-1')
    result = subprocess.run(['docker', 'inspect', *names], capture_output=True, timeout=10,
                            env={'PATH': os.defpath, 'LC_ALL': 'C'})
    require(result.returncode == 0 and len(result.stdout) <= 1024 * 1024, 'PANEL_OBSERVATION_FAILED')
    values = json.loads(result.stdout)
    require(type(values) is list and len(values) == len(names) and {item['Name'] for item in values} == {'/' + name for name in names},
            'PANEL_CONTAINER_SCOPE')
    observed = []
    for item in values:
        require(item['Config']['Labels'].get('com.docker.compose.project') == 'fc-control-plane-0', 'PANEL_PROJECT_SCOPE')
        require(re.fullmatch(r'sha256:[0-9a-f]{64}', item['Image']), 'PANEL_IMAGE_ID')
        observed.append(dict(name=item['Name'], image=item['Image'], running=item['State']['Running'],
            restarting=item['State']['Restarting'], exit_code=item['State']['ExitCode'],
            pid=item['State']['Pid'], restart_count=item['RestartCount'],
            health=item['State'].get('Health', {}).get('Status', 'not-configured'),
            environment_sha256=digest(canonical(item['Config'].get('Env'))),
            command_sha256=digest(canonical([item['Config'].get('Entrypoint'), item['Config'].get('Cmd')])),
            mounts=[dict(type=mount['Type'], read_write=mount['RW'], source_sha256=digest(mount['Source'].encode()),
                         destination=mount['Destination'] if mount['Destination'] in ('/var/lib/postgresql/data',
                             '/app/control_plane/.local') else 'OTHER_PRIVATE_MOUNT') for mount in item['Mounts']],
            queue_contents_observed=False, all_writers_qualified=False))
    return observed


def scoped_dispatch_lines(raw, kind):
    require(type(raw) is bytes and len(raw) <= 128 * 1024, 'DISPATCH_BOUNDS')
    require(kind in ('cron', 'authorized_keys'), 'DISPATCH_KIND')
    lines = [line.strip() for line in raw.decode('utf-8').splitlines() if line.strip() and not line.lstrip().startswith('#')]
    require(len(lines) <= 256, 'DISPATCH_LINE_BOUNDS')
    scoped = []
    for line in lines:
        if '/opt/apps/family_connect/' not in line and '/var/lib/fc-profile-control/' not in line:
            continue
        command = re.search(r'(?:^|,)command="((?:[^"\\]|\\.)*)"', line) if kind == 'authorized_keys' else None
        scoped.append(dict(line_sha256=digest(line.encode()), forced_command_candidate=command is not None,
                           command_sha256=digest(command.group(1).encode()) if command else None))
    return dict(kind=kind, scoped_lines=scoped, other_line_count=len(lines) - len(scoped),
                coverage='LITERAL_ROOT_MATCH_ONLY', all_writers_qualified=False)


def root_dispatchers(keys=Path('/root/.ssh/authorized_keys')):
    records = {}
    if keys.exists():
        records['authorized_keys'] = scoped_dispatch_lines(file_bytes(keys, 128 * 1024), 'authorized_keys')
    else:
        records['authorized_keys'] = dict(status='ABSENT')
    result = subprocess.run(['crontab', '-l', '-u', 'root'], capture_output=True, timeout=10,
                            env={'PATH': os.defpath, 'LC_ALL': 'C'})
    if result.returncode == 1 and result.stderr.strip() == b'no crontab for root':
        records['crontab'] = dict(status='ABSENT')
    else:
        require(result.returncode == 0, 'CRON_OBSERVATION_FAILED')
        records['crontab'] = scoped_dispatch_lines(result.stdout, 'cron')
    records['system_cron_and_other_accounts'] = 'NOT_OBSERVED'
    records['all_writers_qualified'] = False
    return records


def collect(node):
    require(node in ('RU', 'NL1', 'NL2'), 'NODE')
    started = int(time.time())
    databases = []
    for path in database_candidates():
        try:
            databases.append(database_schema(path))
        except (ValueError, OSError, sqlite3.Error):
            databases.append(dict(path=str(path), status='REFUSED', reason='SCHEMA_OBSERVATION_FAILED'))
    units = []
    for name in unit_names():
        try:
            units.append(observe_unit(name))
        except (ValueError, OSError, subprocess.SubprocessError):
            units.append(dict(unit=name, status='REFUSED', reason='UNIT_OBSERVATION_FAILED'))
    dispatchers = {}
    for name, observer in [('root', root_dispatchers)]:
        try:
            dispatchers[name] = observer()
        except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError):
            dispatchers[name] = dict(status='REFUSED', reason='DISPATCH_OBSERVATION_FAILED')
    return dict(version=1, node=node, started_at=started, finished_at=int(time.time()),
        dispatchers=dispatchers,
        databases=databases, units=units, discovery='EXPLICIT_FRIENDS_DEFAULTS_NOT_COMPLETE_COVERAGE',
        configured_store_binding='NOT_ATTESTED',
        missing_default_stores=sorted(set(DATABASE_NAMES) - {Path(item['path']).name for item in databases}),
        user_rows_exported=False, services_changed=False, coherent_snapshot='NOT_QUALIFIED',
        writer_barrier='NOT_IMPLEMENTED', runtime_loaded_bytes='NOT_ATTESTED')


def compare_schemas(observation, application_manifest, handoff_manifest):
    require(observation['node'] == 'RU' and observation['version'] == 1, 'SCHEMA_SOURCE')
    require(application_manifest['version'] == 1 and
            application_manifest['adapter'] == 'family-connect/application-sqlite/v1/not-for-activation', 'APPLICATION_MANIFEST')
    require(handoff_manifest['version'] == 2 and handoff_manifest['purpose'] ==
            'family-connect/installed-handoff-schema/v2/observation-only', 'HANDOFF_MANIFEST')
    names = {'access.db': 'registry', 'diagnostics.sqlite': 'diagnostics',
             'notices.sqlite': 'notices', 'technical-metadata.sqlite': 'metadata'}
    observed = observation['databases']
    require(len(observed) == 4 and {Path(item['path']).name for item in observed} == set(names), 'STORE_COVERAGE')
    result = {}
    for item in observed:
        name = names[Path(item['path']).name]
        require(item.get('status') != 'REFUSED', 'SCHEMA_UNAVAILABLE')
        expected = list(application_manifest['stores'][name])
        if name == 'registry':
            expected += handoff_manifest['definitions']
        expected.sort(key=lambda row: row[1])
        matches = digest(canonical(expected)) == item['definitions_sha256']
        properties = item['properties']
        supported = properties['user_version'] == 0 and properties['application_id'] == 0 and properties['encoding'] == 'UTF-8'
        result[name] = dict(schema='EXACT_RECOGNIZED' if matches and supported else 'UNSUPPORTED',
            adapter='NOT_IMPLEMENTED_HANDOFF_OVERLAY' if name == 'registry' else 'APPLICATION_V1',
            definitions_sha256=item['definitions_sha256'])
    return dict(version=1, stores=result, schema_coverage=all(item['schema'] == 'EXACT_RECOGNIZED' for item in result.values()),
                import_ready=False, all_writers_qualified=False, coherent_snapshot='NOT_QUALIFIED', activation='FORBIDDEN')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--node', choices=('RU', 'NL1', 'NL2'))
    selection.add_argument('--panel-only', action='store_true')
    args = parser.parse_args()
    value = dict(version=1, node='OWNER', panel=panel_containers(), all_writers_qualified=False) if args.panel_only else collect(args.node)
    print(canonical(value).decode())


if __name__ == '__main__':
    main()
