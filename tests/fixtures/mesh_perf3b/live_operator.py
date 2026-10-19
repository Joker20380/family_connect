import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys
import time


API_UNIT = 'family-connect-friends-http-candidate.service'
BASE_API = '12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed'
CANDIDATE_API = '78a69db8f4e48ee89cf132ea279287dbfc71bdf8d9ae69c205bcaa0e19932a46'
OPERATION = 'mesh-perf-3b-20261018-01'


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def require_root():
    require(os.geteuid() == 0, 'ROOT_REQUIRED')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def private(path):
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
            and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1, 'PRIVATE_FILE_REQUIRED')
    return path.read_bytes()


def exclusive(path, raw, mode=0o600):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    with os.fdopen(descriptor, 'wb') as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


@contextlib.contextmanager
def lock(path):
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(descriptor)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.geteuid()
                and stat.S_IMODE(info.st_mode) == 0o600, 'LOCK_PERMISSIONS')
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(descriptor)


def run(arguments, timeout=15):
    reply = subprocess.run(arguments, capture_output=True, text=True, timeout=timeout)
    require(reply.returncode == 0, 'COMMAND_FAILED_' + Path(arguments[0]).name)
    return reply.stdout


def state(unit):
    return dict(line.split('=', 1) for line in run(['systemctl', 'show', unit,
                '--property=MainPID,InvocationID,ActiveState,SubState,NRestarts']).splitlines())


def process_inputs(pid):
    process = Path('/proc') / pid
    arguments = [value.decode() for value in (process / 'cmdline').read_bytes().split(b'\0') if value]
    environment = dict(item.decode().split('=', 1) for item in (process / 'environ').read_bytes().split(b'\0') if item)
    return arguments, environment


def dropin_path():
    return Path('/etc/systemd/system') / (API_UNIT + '.d/97-mesh-perf-3b.conf')


def wait_archive(archive, timeout=15):
    deadline = time.monotonic() + timeout
    while True:
        current = state(API_UNIT)
        require(current['NRestarts'] == '0' and current['ActiveState'] not in ('failed', 'inactive'), 'API_START_FAILED')
        if current['MainPID'] != '0':
            try:
                arguments, _ = process_inputs(current['MainPID'])
            except FileNotFoundError:
                arguments = []
            if str(archive) in arguments and current['ActiveState'] == 'active' and current['SubState'] == 'running':
                return current
        require(time.monotonic() < deadline, 'API_ARCHIVE_READBACK_TIMEOUT')
        time.sleep(.1)


def replacement_unit(arguments, original, candidate):
    require(arguments.count(str(original)) == 1, 'EXACT_EXECSTART_REQUIRED')
    selected = [str(candidate) if item == str(original) else item for item in arguments]
    require(all(item and not any(char in item for char in ('"', '\\', '%', '\n', '\r', '\0'))
                for item in selected), 'UNSUPPORTED_SYSTEMD_ARGUMENT')
    return ('[Service]\nExecStart=\nExecStart=' + ' '.join('"' + item + '"' for item in selected) + '\n').encode()


def load_service(config, candidate):
    sys.path.insert(0, str(candidate))
    from control.friends.access import Access
    from control.friends.restricted import from_env
    from control.friends import owner_handoff
    require(Path(owner_handoff.__file__).as_posix().startswith(str(candidate) + '/'), 'WRONG_API_IMPORT')
    os.environ['FC_FRIENDS_RESTRICTED_DIR'] = config['material']
    os.environ['FC_FRIENDS_RESTRICTED_DELIVERY_LIFETIME'] = '14400'
    service = from_env(Access(config['database']))
    now = int(time.time())
    trust, _, _, _, _ = service._trust(now)
    connection = sqlite3.connect('file:' + config['database'] + '?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    try:
        grant = service._grant(connection, config['owner_guard_identity']['device'], now)
        import base64
        identity = base64.b64decode(grant['public'], validate=True)
        require(hashlib.sha256(identity).hexdigest()[:32] == config['owner_guard_identity']['device']
                and identity[32:].hex() == config['owner_guard_identity']['public_key']
                and grant['family'] == trust['family'] == config['owner_guard_identity']['family'], 'OWNER_BINDING_CHANGED')
    finally:
        connection.close()
    return service, owner_handoff, trust


def prepare_api(stage, config):
    require_root()
    require(config['operation'] == OPERATION, 'OPERATION_MISMATCH')
    original = Path(config['archive'])
    candidate = stage / 'friends-http-owner-candidate.pyz'
    require(sha(original) == BASE_API and sha(candidate) == CANDIDATE_API, 'API_HASH_MISMATCH')
    material = Path(config['material'])
    renewal = json.loads(private(material / 'renewal/controller.json'))
    with lock(Path(renewal['coordinator_state']) / 'operation.lock'), lock(stage / 'operator.lock'):
        require(not (stage / 'prepare-intent.json').exists(), 'READBACK_REQUIRED_NOT_BLIND_RETRY')
        before = state(API_UNIT)
        require(before == config['state'], 'API_PROCESS_CHANGED')
        arguments, environment = process_inputs(before['MainPID'])
        require(arguments == config['args'], 'API_ARGUMENTS_CHANGED')
        require(environment['FC_FRIENDS_RESTRICTED_DIR'] == config['material']
                and environment['FC_FRIENDS_RESTRICTED_DELIVERY_LIFETIME'] == '14400', 'API_ENVIRONMENT_CHANGED')
        require(sha(material / 'directory.json') == config['directory_sha256'], 'PREPARE_DIRECTORY_CHANGED')
        service, handoff, trust = load_service(config, candidate)
        dropin = dropin_path()
        require(dropin.parent.is_dir() and not dropin.exists(), 'DROPIN_CONFLICT')
        replacement = replacement_unit(arguments, original, candidate)
        ordinary = {unit: state(unit) for unit in ('family-connect-friends-awg.service', 'family-connect-friends-tcp.service')}
        exclusive(stage / 'api-unit.before', run(['systemctl', 'cat', API_UNIT]).encode())
        exclusive(stage / 'prepare-intent.json', encode(dict(operation=OPERATION, before=before,
                  ordinary=ordinary, api_before=BASE_API, api_after=CANDIDATE_API,
                  dropin=str(dropin), dropin_sha256=hashlib.sha256(replacement).hexdigest(),
                  database=config['database'], deadline=config['deadline'], utc_epoch=time.time())))
        with service.access.db() as database:
            handoff.migrate(database)
            handoff.prepare(database, OPERATION, config['owner_guard_identity']['device'], trust['family'],
                            trust['gateway'], config['deadline'], int(time.time()))
        exclusive(dropin, replacement, 0o644)
        run(['systemctl', 'daemon-reload'])
        run(['systemctl', 'restart', API_UNIT], timeout=40)
        after = wait_archive(candidate)
        require(sha(original) == BASE_API, 'RENEWAL_PIN_CHANGED')
        require({unit: state(unit) for unit in ordinary} == ordinary, 'ORDINARY_SERVICE_CHANGED')
        require(sha(material / 'directory.json') == config['directory_sha256'], 'PREPARE_DIRECTORY_CHANGED_AFTER_RESTART')
        result = dict(operation=OPERATION, result='PREPARED_NOT_ARMED', state=after,
                      candidate_sha256=CANDIDATE_API, original_sha256=BASE_API,
                      ordinary_services_unchanged=True, directory_unchanged=True,
                      deadline=config['deadline'], owner_identity_pin='VERIFIED', owner_handoff=False)
        exclusive(stage / 'prepare-receipt.json', encode(result))
        return result


def reconcile_prepare(stage, config):
    renewal = json.loads(private(Path(config['material']) / 'renewal/controller.json'))
    with lock(Path(renewal['coordinator_state']) / 'operation.lock'), lock(stage / 'operator.lock'):
        intent = json.loads(private(stage / 'prepare-intent.json'))
        candidate = stage / 'friends-http-owner-candidate.pyz'
        require(intent['operation'] == OPERATION and not (stage/'prepare-receipt.json').exists(), 'OUTCOME_ALREADY_RECORDED')
        require(sha(candidate) == CANDIDATE_API and sha(Path(config['archive'])) == BASE_API, 'API_HASH_MISMATCH')
        require(str(dropin_path()) == intent['dropin'] and sha(dropin_path()) == intent['dropin_sha256'], 'DROPIN_CHANGED')
        service, handoff, _ = load_service(config, candidate)
        with service.access.db() as database:
            row = handoff.read(database, config['owner_guard_identity']['device'])
            require(row['operation'] == OPERATION and row['phase'] == 'PREPARED' and row['canary'] is None
                    and row['deadline'] == config['deadline'], 'PREPARED_STATE_CHANGED')
        after = wait_archive(candidate)
        require({unit: state(unit) for unit in intent['ordinary']} == intent['ordinary'], 'ORDINARY_SERVICE_CHANGED')
        require(sha(Path(config['material'])/'directory.json') == config['directory_sha256'], 'COMMON_DIRECTORY_CHANGED')
        result = dict(operation=OPERATION, result='PREPARED_NOT_ARMED_RECONCILED', state=after,
                      candidate_sha256=CANDIDATE_API, original_sha256=BASE_API, additional_restarts=0,
                      ordinary_services_unchanged=True, directory_unchanged=True, owner_handoff=False)
        exclusive(stage/'prepare-receipt.json', encode(result))
        return result


def abort_unarmed(stage, config):
    candidate = stage / 'friends-http-owner-candidate.pyz'
    require(sha(candidate) == CANDIDATE_API and sha(Path(config['archive'])) == BASE_API, 'API_HASH_MISMATCH')
    renewal = json.loads(private(Path(config['material']) / 'renewal/controller.json'))
    with lock(Path(renewal['coordinator_state']) / 'operation.lock'), lock(stage / 'operator.lock'):
        service, handoff, _ = load_service(config, candidate)
        intent = json.loads(private(stage / 'prepare-intent.json'))
        require(intent['operation'] == OPERATION and not (stage / 'abort-intent.json').exists(), 'READBACK_REQUIRED_NOT_BLIND_RETRY')
        with service.access.db() as database:
            row = handoff.read(database, config['owner_guard_identity']['device'])
            require(row['operation'] == OPERATION and row['phase'] in ('PREPARED', 'RETURN')
                    and row['canary'] is None and row['return_view'] is None, 'CANARY_MAY_HAVE_ESCAPED_FORWARD_RETURN_REQUIRED')
            exclusive(stage / 'unarmed-row-before-cleanup.json', encode(dict(row)))
            exclusive(stage / 'abort-intent.json', encode(dict(operation=OPERATION, never_armed=True,
                      utc_epoch=time.time(), phase=row['phase'])))
            database.execute('UPDATE restricted_owner_handoff SET phase=? WHERE slot=1', ('CLEANED',))
        dropin = dropin_path()
        require(str(dropin) == intent['dropin'] and sha(dropin) == intent['dropin_sha256'], 'DROPIN_CHANGED')
        dropin.unlink()
        descriptor = os.open(dropin.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        run(['systemctl', 'daemon-reload'])
        run(['systemctl', 'restart', API_UNIT], timeout=40)
        after = wait_archive(Path(config['archive']))
        loaded, _ = process_inputs(after['MainPID'])
        require(after['ActiveState'] == 'active' and after['NRestarts'] == '0'
                and config['archive'] in loaded, 'BASE_API_NOT_RESTORED')
        require(run(['systemctl', 'cat', API_UNIT]).encode() == private(stage / 'api-unit.before'), 'API_UNIT_NOT_RESTORED')
        result = dict(operation=OPERATION, result='UNARMED_ABORTED', state=after,
                      original_sha256=BASE_API, canary_issued=False, owner_security_state_reset=False,
                      operation_tombstone_retained=True, only_api_restarted=True)
        exclusive(stage / 'abort-receipt.json', encode(result))
        return result


def transition(stage, config, action):
    candidate = stage / 'friends-http-owner-candidate.pyz'
    require(sha(candidate) == CANDIDATE_API and sha(Path(config['archive'])) == BASE_API, 'API_HASH_MISMATCH')
    renewal = json.loads(private(Path(config['material']) / 'renewal/controller.json'))
    with lock(Path(renewal['coordinator_state']) / 'operation.lock'), lock(stage / 'operator.lock'):
        service, handoff, trust = load_service(config, candidate)
        current = state(API_UNIT)
        arguments, _ = process_inputs(current['MainPID'])
        require(current['ActiveState'] == 'active' and current['NRestarts'] == '0'
                and str(candidate) in arguments, 'CANDIDATE_API_NOT_RUNNING')
        require(not (stage / (action + '-intent.json')).exists(), 'READBACK_REQUIRED_NOT_BLIND_RETRY')
        now = int(time.time())
        common_raw = (Path(config['material']) / 'directory.json').read_bytes()
        common = json.loads(common_raw)
        with service.access.db() as database:
            row = handoff.read(database, config['owner_guard_identity']['device'])
            require(row['operation'] == OPERATION, 'OPERATION_MISMATCH')
            if action == 'arm':
                verified = json.loads(private(stage / 'live-material-verified.json'))
                canary_raw = private(stage / 'canary-directory.json')
                require(verified['operation'] == OPERATION and 0 <= time.time() - verified['verified_epoch'] <= 30
                        and verified['runtime_binding'] == 'PASS' and verified['native_floor_roundtrip'] == 'PASS'
                        and verified['production_sha256'] == hashlib.sha256(common_raw).hexdigest()
                        and verified['canary_sha256'] == hashlib.sha256(canary_raw).hexdigest(), 'LIVE_RETURN_GATE_REQUIRED')
                require(verified['chain_valid_until'] >= config['deadline'] + 600, 'CHAIN_HEADROOM_REQUIRED')
                exclusive(stage / 'arm-intent.json', encode(dict(operation=OPERATION, phase=row['phase'],
                          current=current, material_receipt_sha256=sha(stage/'live-material-verified.json'), epoch=time.time())))
                handoff.arm(database, row['device'], OPERATION, json.loads(canary_raw), common, current['InvocationID'], now)
            elif action == 'return':
                exclusive(stage / 'return-intent.json', encode(dict(operation=OPERATION, phase=row['phase'], epoch=time.time())))
                handoff.return_only(database, row['device'], OPERATION)
            else:
                require(action == 'cleanup' and row['phase'] == 'RETURN' and row['floor'], 'RETURN_REQUIRED')
                verified = json.loads(private(stage / 'owner-return-verified.json'))
                require(verified['operation'] == OPERATION and 0 <= time.time() - verified['verified_epoch'] <= 30
                        and verified['production_process_dns_https'] == 'PASS'
                        and verified['production_sha256'] == hashlib.sha256(common_raw).hexdigest(), 'PHYSICAL_RETURN_REQUIRED')
                observed = json.loads(row['floor'])
                require(observed['directory'] == common, 'COMMON_DIRECTORY_NOT_YET_ACKNOWLEDGED')
                ack_row = database.execute('SELECT ack,ack_at FROM restricted_readiness_results WHERE fetch_id=? AND device=?', (row['fetch_id'], row['device'])).fetchone()
                require(ack_row is not None and ack_row['ack'] is not None, 'IMPORT_ACK_REQUIRED')
                ack = json.loads(ack_row['ack'])
                require(ack['result'] == 'READY' and ack['version_code'] == 84 and ack['minimum_crl'] == observed['minimum_crl']
                        and ack['revision'] == observed['revision'] and ack['expires_at'] > now, 'CURRENT_OWNER_IMPORT_REQUIRED')
                floor_view = dict(issued_at=observed['issued_at'], revision=observed['revision'], minimum_crl=observed['minimum_crl'],
                                  issuer=service.manifest, directory=common)
                require(trust == observed['issuer'], 'ISSUER_CHANGED_SINCE_IMPORT')
                exclusive(stage / 'cleanup-intent.json', encode(dict(operation=OPERATION, phase=row['phase'],
                          owner_return_sha256=sha(stage/'owner-return-verified.json'), ack_at=ack_row['ack_at'], epoch=time.time())))
                handoff.cleanup(database, row['device'], OPERATION, floor_view)
        result = inspect(stage, config)
        result.update(operation=OPERATION, action=action, result='COMMITTED')
        exclusive(stage / (action + '-receipt.json'), encode(result))
        return result


def inspect(stage, config):
    connection = sqlite3.connect('file:' + config['database'] + '?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    try:
        present = connection.execute("SELECT 1 FROM sqlite_master WHERE name='restricted_owner_handoff' AND type='table'").fetchone()
        row = connection.execute('SELECT * FROM restricted_owner_handoff WHERE slot=1').fetchone() if present else None
        result = dict(state=state(API_UNIT), operation_present=row is not None,
                      original_sha256=sha(Path(config['archive'])), utc_epoch=time.time())
        if row:
            require(row['operation'] == OPERATION and row['device'] == config['owner_guard_identity']['device'], 'OTHER_OPERATION_PRESENT')
            result.update(phase=row['phase'], deadline=row['deadline'], floor_captured=row['floor'] is not None)
            if row['floor']:
                floor = json.loads(row['floor'])
                result['directory_issued_at'] = floor['directory']['issued_at']
                result['minimum_crl'] = floor['minimum_crl']
                ack = connection.execute('SELECT ack,ack_at FROM restricted_readiness_results WHERE fetch_id=? AND device=?', (row['fetch_id'], row['device'])).fetchone()
                result['last_fetch_ack'] = json.loads(ack['ack'])['result'] if ack and ack['ack'] else 'NOT_OBSERVED'
        return result
    finally:
        connection.close()


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare-api', 'inspect', 'abort-unarmed', 'reconcile-prepare', 'arm', 'return', 'cleanup'))
    parser.add_argument('--stage', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(private(args.stage / 'operation.json'))
    actions = {'prepare-api': prepare_api, 'inspect': inspect, 'abort-unarmed': abort_unarmed, 'reconcile-prepare': reconcile_prepare}
    result = actions[args.action](args.stage, config) if args.action in actions else transition(args.stage, config, args.action)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
