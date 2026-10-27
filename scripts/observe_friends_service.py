"""Read-only, typed systemd D-Bus observation of the Friends HTTP service."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

UNIT = 'family-connect-friends-http-candidate.service'
DESTINATION = 'org.freedesktop.systemd1'
MANAGER_PATH = '/org/freedesktop/systemd1'
MAX_RESPONSE = 1024 * 1024


class ObservationError(Exception):
    def __init__(self, stage, code):
        self.stage = stage
        self.code = code
        super().__init__(stage + ':' + code)


def require(condition, stage, code='INVALID_TYPED_RESPONSE'):
    if not condition:
        raise ObservationError(stage, code)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('nonfinite JSON')


def decode_response(raw, signature, stage):
    require(isinstance(raw, bytes) and len(raw) <= MAX_RESPONSE, stage, 'RESPONSE_SIZE')
    try:
        result = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object,
            parse_constant=reject_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise ObservationError(stage, 'INVALID_JSON') from None
    require(type(result) is dict and set(result) == {'type', 'data'}, stage)
    require(result['type'] == signature and type(result['data']) is list
        and len(result['data']) == 1, stage)
    return result['data'][0]


def valid(value, signature):
    if signature in ('s', 'o'):
        return (type(value) is str and len(value) <= 16384 and '\x00' not in value
            and (signature != 'o' or re.fullmatch(r'/(?:[A-Za-z0-9_]+/?)*', value) is not None))
    if signature == 'b':
        return type(value) is bool
    if signature in ('u', 't', 'i'):
        bounds = {'u': (0, 2**32), 't': (0, 2**64), 'i': (-2**31, 2**31)}
        lower, upper = bounds[signature]
        return type(value) is int and lower <= value < upper
    if signature == 'as':
        return type(value) is list and len(value) <= 4096 and all(valid(item, 's') for item in value)
    if signature == '(uo)':
        return type(value) is list and len(value) == 2 and valid(value[0], 'u') and valid(value[1], 'o')
    return False


class Bus:
    def __init__(self, runner=subprocess.run):
        self.runner = runner

    def call(self, path, interface, method, signature, *arguments):
        stage = method + (':' + arguments[-1].rsplit('.', 1)[-1] if method == 'GetAll' else '')
        allowed = (path == MANAGER_PATH and interface == DESTINATION + '.Manager'
            and ((method == 'GetUnit' and arguments == ('s', UNIT) and signature == 'o')
                or (method == 'ListJobs' and not arguments and signature == 'a(usssoo)')))
        allowed = allowed or (path.startswith(MANAGER_PATH + '/unit/')
            and valid(path, 'o') and interface == 'org.freedesktop.DBus.Properties'
            and method == 'GetAll' and signature == 'a{sv}'
            and arguments in (('s', DESTINATION + '.Unit'), ('s', DESTINATION + '.Service')))
        require(allowed, stage, 'UNSUPPORTED_READ')
        command = ['/usr/bin/busctl', '--system', '--json=short', 'call', DESTINATION,
            path, interface, method, *arguments]
        try:
            result = self.runner(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                timeout=10, check=False)
        except subprocess.TimeoutExpired:
            raise ObservationError(stage, 'BUS_TIMEOUT') from None
        except OSError:
            raise ObservationError(stage, 'BUS_UNAVAILABLE') from None
        require(result.returncode == 0, stage, 'BUS_CALL_FAILED')
        return decode_response(result.stdout, signature, stage)


def property_value(properties, name, signature):
    stage = 'property:' + name
    require(type(properties) is dict and name in properties, stage, 'MISSING_PROPERTY')
    variant = properties[name]
    require(type(variant) is dict and set(variant) == {'type', 'data'}
        and variant['type'] == signature, stage)
    value = variant['data']
    require(valid(value, signature), stage)
    return value


def execstart(properties):
    stage = 'property:ExecStart'
    require(type(properties) is dict and 'ExecStart' in properties, stage, 'MISSING_PROPERTY')
    variant = properties['ExecStart']
    require(type(variant) is dict and set(variant) == {'type', 'data'}
        and variant['type'] == 'a(sasbttttuii)', stage)
    rows = variant['data']
    require(type(rows) is list and len(rows) == 1, stage, 'EXECSTART_CARDINALITY')
    row = rows[0]
    signatures = ('s', 'as', 'b', 't', 't', 't', 't', 'u', 'i', 'i')
    require(type(row) is list and len(row) == len(signatures)
        and all(valid(value, kind) for value, kind in zip(row, signatures)), stage)
    require(row[1] and row[0] == row[1][0] and row[2] is False, stage, 'EXECSTART_POLICY')
    return row[:3]


def jobs(bus):
    rows = bus.call(MANAGER_PATH, DESTINATION + '.Manager', 'ListJobs', 'a(usssoo)')
    require(type(rows) is list and len(rows) <= 4096, 'ListJobs')
    identifiers = set()
    target_count = 0
    for row in rows:
        require(type(row) is list and len(row) == 6
            and all(valid(value, kind) for value, kind in zip(row, ('u', 's', 's', 's', 'o', 'o'))), 'ListJobs')
        require(row[0] not in identifiers, 'ListJobs', 'DUPLICATE_JOB')
        identifiers.add(row[0])
        target_count += row[1] == UNIT
    return {'count': len(rows), 'target_count': target_count,
        'sha256': digest(sorted(rows, key=lambda row: row[0]))}


def snapshot(bus, path):
    unit = bus.call(path, 'org.freedesktop.DBus.Properties', 'GetAll', 'a{sv}', 's', DESTINATION + '.Unit')
    service = bus.call(path, 'org.freedesktop.DBus.Properties', 'GetAll', 'a{sv}', 's', DESTINATION + '.Service')
    unit_fields = {'Id': 's', 'ActiveState': 's', 'SubState': 's', 'FragmentPath': 's',
        'DropInPaths': 'as', 'NeedDaemonReload': 'b', 'Job': '(uo)'}
    service_fields = {'MainPID': 'u', 'Result': 's', 'NRestarts': 'u',
        'ExecMainStartTimestamp': 't', 'ExecMainStartTimestampMonotonic': 't',
        'User': 's', 'Group': 's', 'WorkingDirectory': 's'}
    result = {name: property_value(unit, name, kind) for name, kind in unit_fields.items()}
    result.update({name: property_value(service, name, kind) for name, kind in service_fields.items()})
    require(result['Id'] == UNIT, 'snapshot', 'WRONG_UNIT')
    environment = property_value(service, 'Environment', 'as')
    names = [entry.partition('=')[0] for entry in environment]
    require(all('=' in entry for entry in environment) and len(set(names)) == len(names)
        and all(re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', name) for name in names), 'environment')
    result['environment_names'] = sorted(names)
    result['environment_sha256'] = digest(environment)
    result['execstart'] = execstart(service)
    return result


def process(pid, proc_root=Path('/proc')):
    require(valid(pid, 'u') and pid > 0, 'process', 'NO_MAIN_PID')
    try:
        with (proc_root / str(pid) / 'stat').open('rb') as source:
            raw_stat = source.read(65537)
        with (proc_root / str(pid) / 'cmdline').open('rb') as source:
            raw_args = source.read(65537)
        require(len(raw_stat) <= 65536 and len(raw_args) <= 65536 and raw_args.endswith(b'\0'),
            'process', 'INVALID_PROC')
        fields = raw_stat.decode().rsplit(')', 1)[1].split()
        require(int(raw_stat.split(b' ', 1)[0]) == pid and len(fields) >= 20, 'process', 'INVALID_PROC')
        start_ticks = int(fields[19])
        require(start_ticks > 0, 'process', 'INVALID_PROC')
        arguments = raw_args[:-1].decode().split('\0')
        require(valid(arguments, 'as'), 'process', 'INVALID_PROC')
        return {'pid': pid, 'start_ticks': start_ticks, 'argv_sha256': digest(arguments)}
    except (OSError, ValueError, IndexError):
        raise ObservationError('process', 'PROC_UNAVAILABLE') from None


def observe(expected_exec, expected_running=None, *, bus=None, read_process=process):
    require(valid(expected_exec, 'as') and bool(expected_exec), 'expected', 'INVALID_ARGUMENTS')
    if expected_running is None:
        expected_running = expected_exec
    require(valid(expected_running, 'as') and bool(expected_running), 'expected', 'INVALID_ARGUMENTS')
    bus = bus or Bus()
    path = bus.call(MANAGER_PATH, DESTINATION + '.Manager', 'GetUnit', 'o', 's', UNIT)
    require(valid(path, 'o') and path.startswith(MANAGER_PATH + '/unit/'), 'GetUnit')
    initial_jobs = jobs(bus)
    first = snapshot(bus, path)
    first_process = read_process(first['MainPID'])
    second = snapshot(bus, path)
    second_process = read_process(second['MainPID'])
    final_jobs = jobs(bus)
    require(first == second and first_process == second_process, 'consistency', 'SERVICE_CHANGED_DURING_READ')
    require(initial_jobs == final_jobs, 'consistency', 'JOBS_CHANGED_DURING_READ')
    executable, arguments, ignored = second.pop('execstart')
    second['effective_execstart_matches'] = executable == expected_exec[0] and arguments == expected_exec
    second['execstart_sha256'] = digest([executable, arguments, ignored])
    second['running_argv_matches'] = second_process['argv_sha256'] == digest(expected_running)
    second['process'] = second_process
    return {'schema': 1, 'result': 'OBSERVED', 'unit': UNIT, 'service': second,
        'jobs': final_jobs, 'restarts': 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', required=True)
    parser.add_argument('--archive', required=True)
    parser.add_argument('--running-archive')
    parser.add_argument('--port', type=int, default=18086)
    args = parser.parse_args(argv)
    expected = [args.python, '-I', args.archive, '--port', str(args.port)]
    running = [args.python, '-I', args.running_archive or args.archive, '--port', str(args.port)]
    try:
        receipt = observe(expected, running)
    except ObservationError as error:
        print(json.dumps({'schema': 1, 'result': 'OBSERVATION_BLOCKED', 'stage': error.stage,
            'code': error.code, 'restarts': 0}, allow_nan=False))
        return 1
    print(json.dumps(receipt, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
