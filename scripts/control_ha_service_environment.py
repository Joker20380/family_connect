"""Read-only scoped systemd environment comparison; no values, activation or capture permit."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time


UNIT = 'family-connect-restricted-bootstrap.service'
NAME = re.compile(r'[A-Za-z_][A-Za-z0-9_]*\Z')
FIELDS = {
    'Service': {'MainPID': 'u', 'ControlPID': 'u', 'EnvironmentFiles': 'a(sb)',
        'Environment': 'as', 'UnsetEnvironment': 'as', 'ExecStopPost': 'a(sasbttttuii)'},
    'Unit': {'ActiveState': 's', 'SubState': 's', 'InvocationID': 'ay', 'NeedDaemonReload': 'b'},
}


def require(condition):
    if not condition:
        raise ValueError('SERVICE_ENVIRONMENT_REFUSED')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def assignment(value):
    require(type(value) is str and len(value) <= 65536 and '\x00' not in value)
    name, separator, content = value.partition('=')
    require(separator and NAME.fullmatch(name) is not None)
    return name, content


def environment_file(raw):
    require(type(raw) is bytes and len(raw) <= 65536 and b'\x00' not in raw and b'\r' not in raw)
    result = {}
    for line in raw.decode('utf-8').split('\n'):
        line = line.strip(' \t')
        if not line or line.startswith(('#', ';')):
            continue
        name, value = assignment(line)
        value = value.strip(' \t')
        require('\\' not in value)
        if value.startswith(('"', "'")):
            require(len(value) >= 2 and value[-1] == value[0] and value[0] not in value[1:-1])
            value = value[1:-1]
        else:
            require('"' not in value and "'" not in value)
        result[name] = value
        require(len(result) <= 1024)
    return result


def process_environment(raw):
    require(type(raw) is bytes and len(raw) <= 262144 and (not raw or raw.endswith(b'\x00')))
    result = {}
    for entry in raw[:-1].split(b'\x00') if raw else ():
        name, value = assignment(entry.decode('utf-8'))
        require(name not in result and len(result) < 4096)
        result[name] = value
    return result


def compare(environment, files, unset, process):
    require(type(environment) is list and len(environment) <= 1024 and
            type(files) is list and len(files) <= 8 and type(unset) is list and len(unset) <= 1024)
    expected = dict(assignment(item) for item in environment)
    for raw in files:
        expected.update(environment_file(raw))
    require(bool(expected))
    selected = set(expected)
    for entry in unset:
        require(type(entry) is str)
        if '=' in entry:
            name, value = assignment(entry)
            require(name in selected)
            if name in expected and expected[name] == value:
                del expected[name]
        else:
            require(NAME.fullmatch(entry) is not None)
            selected.add(entry)
            expected.pop(entry, None)
    actual = process_environment(process)
    missing = sorted(name for name in expected if name not in actual)
    mismatched = sorted(name for name in expected if name in actual and actual[name] != expected[name])
    unexpectedly_present = sorted(name for name in selected - expected.keys() if name in actual)
    return dict(classification='SELECTED_ENVIRONMENT_MATCH' if not (missing or mismatched or unexpectedly_present)
        else 'SELECTED_ENVIRONMENT_DIFFER', compared_names=sorted(selected), missing_names=missing,
        mismatched_names=mismatched, unexpectedly_present_names=unexpectedly_present,
        unqualified_process_names=len(actual.keys() - selected), values_disclosed=False)


def identity(info):
    return [info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
            info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns]


def literal_path(spelling):
    require(type(spelling) is str and 0 < len(spelling) <= 4096 and
            not any(character in spelling for character in '\x00\n\r%*?[]'))
    path = Path(spelling)
    require(path.is_absolute() and str(path) == spelling and '..' not in path.parts and
            not spelling.startswith('//'))
    return path


def read_file(path, limit=65536, *, owner=0):
    path = literal_path(str(path))
    require(all(not part.is_symlink() for part in (path, *path.parents)))
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_uid == owner and before.st_nlink == 1 and
                not before.st_mode & 0o022 and 0 <= before.st_size <= limit)
        raw = stream.read(limit + 1)
        require(len(raw) == before.st_size and identity(before) == identity(os.fstat(stream.fileno())) and
                identity(before) == identity(path.stat(follow_symlinks=False)))
    return raw, dict(metadata=identity(before), sha256=digest(raw))


def run(arguments):
    result = subprocess.run(arguments, capture_output=True, timeout=10, cwd='/',
        env={'PATH': '/usr/bin:/bin', 'LANG': 'C'})
    require(result.returncode == 0 and not result.stderr and len(result.stdout) <= 262144)
    return result.stdout


def properties():
    lookup = json.loads(run(['/usr/bin/busctl', '--json=short', 'call', 'org.freedesktop.systemd1',
        '/org/freedesktop/systemd1', 'org.freedesktop.systemd1.Manager', 'GetUnit', 's', UNIT]))
    require(lookup.get('type') == 'o' and type(lookup.get('data')) is list and len(lookup['data']) == 1)
    location = lookup['data'][0]
    require(type(location) is str and re.fullmatch(r'/org/freedesktop/systemd1/unit/[A-Za-z0-9_]+', location))
    result = {}
    for interface, fields in FIELDS.items():
        rows = run(['/usr/bin/busctl', '--json=short', 'get-property', 'org.freedesktop.systemd1',
            location, 'org.freedesktop.systemd1.' + interface, *fields]).splitlines()
        require(len(rows) == len(fields))
        for (name, signature), row in zip(fields.items(), rows, strict=True):
            value = json.loads(row)
            require(type(value) is dict and set(value) == {'type', 'data'} and value['type'] == signature)
            expected = int if signature == 'u' else bool if signature == 'b' else str if signature == 's' else list
            require(type(value['data']) is expected)
            result[name] = value['data']
    return result


def process_snapshot(pid):
    require(type(pid) is int and 1 < pid < 4194304)
    root = Path('/proc') / str(pid)
    status = (root / 'stat').read_bytes()
    fields = status.rsplit(b')', 1)[1].split()
    require(len(fields) >= 20 and fields[19].isdigit())
    with (root / 'environ').open('rb') as stream:
        environment = stream.read(262145)
    require(len(environment) <= 262144 and status.split(b' ', 1)[0] == str(pid).encode())
    return fields[19].decode(), environment


def observe():
    require(os.geteuid() == 0)
    started = time.time_ns()
    before = properties()
    require(before['ActiveState'] == 'active' and before['SubState'] == 'running' and before['ControlPID'] == 0)
    require(type(before['InvocationID']) is list and len(before['InvocationID']) == 16 and
            all(type(value) is int and 0 <= value <= 255 for value in before['InvocationID']))
    start_ticks, environment = process_snapshot(before['MainPID'])
    require(type(before['EnvironmentFiles']) is list and 0 < len(before['EnvironmentFiles']) <= 8)
    files, pins, missing_optional = [], {}, []
    for entry in before['EnvironmentFiles']:
        require(type(entry) is list and len(entry) == 2 and type(entry[0]) is str and type(entry[1]) is bool)
        spelling, optional = entry
        literal_path(spelling)
        try:
            raw, pin = read_file(spelling)
        except FileNotFoundError:
            require(optional)
            missing_optional.append(spelling)
            continue
        files.append(raw)
        pins[spelling] = pin
    hooks = []
    require(type(before['ExecStopPost']) is list and len(before['ExecStopPost']) <= 8)
    for entry in before['ExecStopPost']:
        require(type(entry) is list and len(entry) == 10 and type(entry[1]) is list)
        arguments = entry[1]
        require(2 <= len(arguments) <= 32 and all(type(value) is str for value in arguments) and
                entry[0] == arguments[0] == '/usr/bin/python3')
        script_index = 1
        while script_index < len(arguments) and arguments[script_index] in ('-B', '-E', '-I', '-s', '-u'):
            script_index += 1
        require(script_index < len(arguments))
        script = arguments[script_index]
        literal_path(script)
        require(script.endswith('.py'))
        raw, pin = read_file(script)
        tree = ast.parse(raw)
        pins[script] = pin
        imports = sorted({item.module for item in ast.walk(tree) if isinstance(item, ast.ImportFrom) and item.module} |
            {alias.name for item in ast.walk(tree) if isinstance(item, ast.Import) for alias in item.names})
        hooks.append(dict(source_path=script, source=pin, imports=imports,
            argv_sha256=digest(json.dumps(arguments, separators=(',', ':')).encode()), executed=False))
    result = compare(before['Environment'], files, before['UnsetEnvironment'], environment)
    require(properties() == before)
    require(process_snapshot(before['MainPID']) == (start_ticks, environment))
    for spelling, pin in pins.items():
        require(read_file(spelling)[1] == pin)
    require(all(not Path(spelling).exists() and not Path(spelling).is_symlink() for spelling in missing_optional))
    return dict(result, observed_at_ns=started, finished_at_ns=time.time_ns(), unit=UNIT, pid=before['MainPID'],
        process_start_ticks=start_ticks, invocation=bytes(before['InvocationID']).hex(), files=pins,
        absent_optional_files=missing_optional, stop_post=hooks, need_daemon_reload=before['NeedDaemonReload'],
        services_changed=False, helper_executed=False, full_runtime_qualified=False,
        capture_permitted=False, independent_approval=False)


def main():
    try:
        result = observe()
        print(json.dumps(result, sort_keys=True))
        return 0 if result['classification'] == 'SELECTED_ENVIRONMENT_MATCH' else 1
    except Exception:
        print(json.dumps(dict(classification='SERVICE_ENVIRONMENT_REFUSED', values_disclosed=False,
            services_changed=False, helper_executed=False, capture_permitted=False)))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
