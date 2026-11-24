"""Read-only installed-current observations, never recovery or historical approval."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import time

from scripts.control_ha_installed_inventory import (
    KNOWN_FILES, MAX_ENTRIES, Reader, Refused, installed_source, pairs, require, sha, token,
)


UNITS = {
    'RU': ('family-connect-friends-http-candidate.service', 'family-connect-restricted-sync.timer',
           'family-connect-restricted-sync.service', 'family-connect-restricted-directory-sync.timer',
           'family-connect-restricted-directory-sync.service'),
    'NL': ('family-connect-restricted-bootstrap.service',),
    'NL2': ('family-connect-restricted-bootstrap.service',),
}
RENEWAL_UNITS = ('family-connect-credential-renewal.service', 'family-connect-credential-renewal.timer')
COLUMNS = {
    'devices': ('device', 'public', 'wg', 'tcp', 'revoked'),
    'invites': ('hash', 'device', 'revoked'),
    'restricted_grants': ('device', 'family', 'revision', 'expires', 'revoked'),
    'restricted_certificates': ('device', 'revision', 'serial', 'expires', 'certificate'),
    'restricted_crl_sequence': ('singleton', 'sequence'),
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def parse(raw):
    value = json.loads(raw, object_pairs_hook=pairs)
    require(type(value) is dict, 'DOCUMENT_SHAPE')
    return value


def row_difference(current, expected):
    actual = Counter(canonical(row) for row in current)
    baseline = Counter(canonical(row) for row in expected)
    return dict(baseline_rows=len(expected), unchanged_rows=sum((actual & baseline).values()),
                added_rows=sum((actual - baseline).values()), removed_rows=sum((baseline - actual).values()))


def certificate_timing(current, expected, issued):
    from cryptography import x509
    try:
        certificates = [x509.load_pem_x509_certificate(row['certificate'].encode()) for row in current]
        return dict(parsed=True, current_issued_after_plan=sum(value.not_valid_before_utc.timestamp() > issued for value in certificates),
            baseline_expired_now=sum(type(row['expires']) is int and row['expires'] <= time.time() for row in expected))
    except (ValueError, TypeError, KeyError, AttributeError):
        return dict(parsed=False)


def systemd(unit):
    require(unit in {*RENEWAL_UNITS, *(unit for units in UNITS.values() for unit in units)}, 'UNIT_SCOPE')
    fields = ('LoadState', 'ActiveState', 'SubState', 'Result', 'MainPID', 'NRestarts')
    command = ['systemctl', 'show', unit, '--no-pager', '--property=' + ','.join(fields)]
    process = subprocess.run(command, capture_output=True, text=True, timeout=8, check=False)
    require(process.returncode == 0 and len(process.stdout) <= 4096, 'SYSTEMD_READ')
    values = dict(line.split('=', 1) for line in process.stdout.splitlines() if '=' in line)
    require(set(values) <= set(fields) and {'LoadState', 'ActiveState', 'SubState'} <= set(values), 'SYSTEMD_FIELDS')
    require(all(re.fullmatch('[a-z0-9-]{0,64}', value) is not None for value in values.values()), 'SYSTEMD_VALUE')
    return values


def database_projection(reader, path, plan):
    from cryptography import x509
    expected = dict(plan['grant_plan']['before'])
    require(set(expected) == set(COLUMNS), 'DATABASE_SCOPE')
    number = x509.load_pem_x509_crl(plan['candidate']['crl'].encode()).extensions.get_extension_for_class(
        x509.CRLNumber).value.crl_number
    expected.update(restricted_grants=plan['grant_plan']['after_grants'],
                    restricted_crl_sequence=[dict(singleton=1, sequence=number)])
    path = Path(path)
    siblings = reader.names(path.parent)
    require(path.name in siblings, 'DATABASE_MISSING')
    with reader.opened(path) as descriptor:
        header = os.read(descriptor, 20)
    require(header[:16] == b'SQLite format 3\x00', 'DATABASE_HEADER')
    require(header[18:20] != b'\x02\x02' or all(path.name + suffix in siblings for suffix in ('-wal', '-shm')),
            'DATABASE_WAL_SIDECARS_MISSING')
    for suffix in ('', '-wal', '-shm', '-journal'):
        if path.name + suffix in siblings:
            with reader.opened(path.with_name(path.name + suffix)):
                pass
    deadline = time.monotonic() + 5
    connection = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=2)
    try:
        connection.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 1024 * 1024)
        connection.execute('PRAGMA query_only=ON')
        connection.set_progress_handler(lambda: time.monotonic() > deadline, 1000)
        version = connection.execute('PRAGMA data_version').fetchone()[0]
        connection.execute('BEGIN')
        result, total = {}, 0
        for table, columns in COLUMNS.items():
            observed = tuple(row[1] for row in connection.execute('PRAGMA table_info("' + table + '")'))
            require(set(observed) == set(columns), 'DATABASE_COLUMNS')
            cursor = connection.execute('SELECT ' + ','.join('"' + column + '"' for column in columns)
                + ' FROM "' + table + '" LIMIT 4097')
            current = []
            for row in cursor:
                require(len(current) < MAX_ENTRIES, 'DATABASE_ROW_LIMIT')
                item = dict(zip(columns, row))
                total += len(canonical(item))
                require(total <= 16 * 1024 * 1024, 'DATABASE_READ_LIMIT')
                current.append(item)
            raw = canonical(sorted(current, key=canonical))
            result[table] = dict(rows=len(current), equals_current_plan=raw == canonical(sorted(expected[table], key=canonical)),
                                 **row_difference(current, expected[table]))
            if table == 'restricted_certificates':
                result[table]['timing_not_authorization'] = certificate_timing(current, expected[table], plan['grant_plan']['issued_at'])
        connection.rollback()
        require(connection.execute('PRAGMA data_version').fetchone()[0] == version, 'DATABASE_CHANGED')
    finally:
        connection.close()
    return result


def current_archive(reader, root, operation_hash):
    require(set(reader.names(root, 128)) <= {'operation.lock', 'completed.json', 'archive'}, 'NODE_PENDING_OR_UNKNOWN')
    require(reader.raw(root / 'operation.lock') == b'', 'LOCK_CONTENT')
    ledger = reader.document(root / 'completed.json')
    require(len(ledger) <= MAX_ENTRIES, 'LEDGER_LIMIT')
    matches = [operation for operation in ledger if token(operation) == operation_hash]
    require(len(matches) == 1, 'CURRENT_OPERATION_MISSING')
    operation = matches[0]
    require(re.fullmatch('[a-z0-9-]{16,96}', operation) is not None, 'OPERATION_PATH')
    entry = ledger[operation]
    require(set(entry) == {'result', 'manifest_sha256', 'timestamp'} and entry['result'] == 'CLEANED'
            and type(entry['timestamp']) is int, 'CURRENT_LEDGER')
    location = root / 'archive' / operation
    names = reader.names(location, 128)
    require(all(name in KNOWN_FILES or re.fullmatch(r'start-intent-[0-9]{1,3}\.json', name) for name in names),
            'CURRENT_ARCHIVE_SCOPE')
    files = {name: reader.raw(location / name) for name in names}
    manifest = parse(files['archive-manifest.json'])
    require(set(manifest) == set(files) - {'archive-manifest.json'}
            and all(sha(files[name]) == value for name, value in manifest.items())
            and sha(canonical(manifest)) == entry['manifest_sha256'], 'CURRENT_ARCHIVE_HASH')
    plan = parse(files['plan.json'])
    require(plan['operation_id'] == operation and files['plan.json'] == canonical(plan), 'CURRENT_PLAN')
    expected = dict(plan_sha256=sha(canonical(plan)), crl_sha256=sha(plan['candidate']['crl'].encode()), state='PROMOTED')
    require(parse(files['reconciliation.json']) == {slot: expected for slot in UNITS}, 'CURRENT_RECONCILIATION')
    return plan, files, dict(ledger_entries=len(ledger), archive_files=len(files),
        archive_manifest_sha256=entry['manifest_sha256'], completed_at=entry['timestamp'])


def material(reader, config, plan):
    live, slot = Path(config['live']), config['gateway_slot']
    if slot == 'RU':
        return dict(issuer=reader.document(live / 'issuer.json') == plan['candidate']['authority'],
            secondary_issuer=reader.document(live / 'gateways/nl-amsterdam-2/issuer.json') == plan['secondary']['candidate']['authority'],
            crl=reader.raw(live / 'revocations.pem') == plan['candidate']['crl'].encode())
    locator_raw = reader.raw(Path(config['profile_locator']))
    require(sha(locator_raw) == config['profile_locator_sha256'], 'PROFILE_LOCATOR_HASH')
    locator = parse(locator_raw)
    profile = reader.document(Path(locator['profile']))
    candidate = plan['candidate'] if slot == 'NL' else plan['secondary']['candidate']
    return dict(certificate=profile['certificate'] == candidate['certificate'],
        crl=profile['revocations'] == candidate['crl'])


def collect(config_path, runtime, *, operation_hash=None, controller_path=None):
    started = int(time.time())
    reader, config_path = Reader(), Path(config_path)
    config_raw = reader.raw(config_path)
    config = parse(config_raw)
    slot = config['gateway_slot']
    require(slot in UNITS and config['service_units'] == list(UNITS[slot]), 'INSTALLED_UNIT_ORDER')
    require(config['role'] == ('RU' if slot == 'RU' else 'NL'), 'INSTALLED_ROLE')
    source = installed_source(reader, config_path, Path(runtime))
    require(source['files_match'] and source['aggregate_matches'], 'INSTALLED_SOURCE')
    record, provenance = None, None
    if slot == 'RU':
        require(controller_path is not None and operation_hash is None, 'CONTROLLER_ARGUMENTS')
        controller_raw = reader.raw(Path(controller_path))
        controller = parse(controller_raw)
        require(controller['schema'] == 2 and controller['node_config'] == str(config_path), 'CONTROLLER_BINDING')
        coordinator = Path(controller['coordinator_state'])
        record = reader.document(coordinator / 'transaction.json')
        receipt = reader.document(coordinator / 'last-receipt.json')
        require(record['state'] == receipt['state'] == 'COMMITTED'
                and record['operation_id'] == receipt['operation_id'], 'COORDINATOR_UNSETTLED')
        require(type(receipt['timestamp']) is int and 0 < receipt['timestamp'] <= started, 'COORDINATOR_TIME')
        require(record['gate'] == dict(result='RENEWAL_READY', authorization='OPERATOR_APPROVED_LEAF_CRL_SCHEDULE',
            pre_stop_sessions='UNKNOWN', zero_downtime=False), 'CURRENT_GATE')
        operation_hash = token(record['operation_id'])
        provenance = dict(controller_sha256=sha(controller_raw), current_schedule_flag=controller.get('approved_leaf_crl_schedule') is True,
            original_schedule_approval='NOT_ESTABLISHED', original_controller_config='NOT_RETAINED_IN_TRANSACTION',
            node_config_sha256={node: record['before'][node]['policy']['node_config'] for node in UNITS},
            receipt_at=receipt['timestamp'])
        require(all(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) for value in provenance['node_config_sha256'].values()),
                'CONFIG_DIGEST_SHAPE')
    else:
        require(controller_path is None and type(operation_hash) is str
                and re.fullmatch('[0-9a-f]{64}', operation_hash), 'NODE_ARGUMENTS')
    plan, files, archive = current_archive(reader, Path(config['state']), operation_hash)
    require(type(plan['grant_plan']['issued_at']) is int
            and 0 < plan['grant_plan']['issued_at'] <= archive['completed_at'] <= started, 'CURRENT_TIME')
    if record is not None:
        require(reader.document(coordinator / 'plan.json') == plan
                and record['reconciliation'] == parse(files['reconciliation.json']), 'COORDINATOR_PLAN')
        require(archive['completed_at'] <= receipt['timestamp'], 'COORDINATOR_TIME')
    before = parse(files['services-before.json'])
    require(set(before) == set(UNITS[slot]), 'SERVICE_SNAPSHOT_SCOPE')
    starts = []
    for name, raw in files.items():
        if name.startswith('start-intent-'):
            index = int(name.removeprefix('start-intent-').removesuffix('.json'))
            require(index < len(UNITS[slot]) and parse(raw)['unit'] == UNITS[slot][index], 'START_UNIT_BINDING')
            starts.append(index)
    directories = {}
    if slot == 'RU':
        accepted = parse(files['directory-accepted.json'])
        require(accepted['operation_id'] == plan['operation_id'] and set(accepted['directories']) == {'NL', 'NL2'}, 'PUBLICATION_SCOPE')
        for node, relative in (('NL', 'directory.json'), ('NL2', 'gateways/nl-amsterdam-2/directory.json')):
            digest = sha(reader.raw(Path(config['live']) / relative))
            directories[node] = dict(sha256=digest, equals_committed_publication=digest == accepted['directories'][node])
    else:
        directories[slot] = dict(sha256=sha(reader.raw(Path(config['live']) / 'directory.json')))
    result = dict(schema=1, purpose='installed-current-observation/not-recovery-acceptance', slot=slot,
        operation_sha256=operation_hash, plan_sha256=sha(canonical(plan)), config_sha256=sha(config_raw),
        source=source, archive=archive, configured_units=list(UNITS[slot]), start_intent_indexes=sorted(starts),
        current_material=material(reader, config, plan), directories=directories,
        services={unit: systemd(unit) for unit in (*UNITS[slot], *(RENEWAL_UNITS if slot == 'RU' else ()))},
        original_approval='NOT_ESTABLISHED', signatures_verified=False, snapshot_barrier=False,
        activation='FORBIDDEN', recovery='BLOCKED', started_at=started)
    if provenance is not None:
        result['provenance'] = provenance
        result['database'] = database_projection(reader, config['database'], plan)
    reader.verify()
    result.update(observation='NO_OBSERVED_FILE_CHANGE', finished_at=int(time.time()), bytes_read=reader.bytes_read)
    return result


def reconcile(observations):
    require(set(observations) == set(UNITS), 'FLEET_SCOPE')
    for slot, value in observations.items():
        require(value['slot'] == slot and value['purpose'] == 'installed-current-observation/not-recovery-acceptance', 'FLEET_ROLE')
    coordinator = observations['RU']
    return dict(shared_operation=len({value['operation_sha256'] for value in observations.values()}) == 1,
        shared_plan=len({value['plan_sha256'] for value in observations.values()}) == 1,
        node_config_matches_record={slot: value['config_sha256'] == coordinator['provenance']['node_config_sha256'][slot]
                                   for slot, value in observations.items()},
        directory_matches_ru={slot: observations[slot]['directories'][slot]['sha256'] == coordinator['directories'][slot]['sha256']
                              for slot in ('NL', 'NL2')},
        recovery='BLOCKED', original_schedule_approval='NOT_ESTABLISHED', snapshot_barrier=False, activation='FORBIDDEN')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--controller', type=Path)
    parser.add_argument('--operation-sha256')
    arguments = parser.parse_args(argv)
    try:
        result = collect(arguments.config, arguments.runtime, controller_path=arguments.controller,
                         operation_hash=arguments.operation_sha256)
    except Refused as error:
        print(json.dumps(dict(result='OBSERVATION_REFUSED', reason=str(error), recovery='BLOCKED', activation='FORBIDDEN')))
        return 1
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError,
            RecursionError, sqlite3.Error, subprocess.SubprocessError):
        print(json.dumps(dict(result='OBSERVATION_REFUSED', recovery='BLOCKED', activation='FORBIDDEN')))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
