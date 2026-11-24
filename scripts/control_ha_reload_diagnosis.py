"""Read-only systemd255 reload-cause witness; neither unit equivalence nor a capture permit."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

VERSION = '255.4-1ubuntu8.18'
UNIT = '-.slice'
MANAGER_FIELDS = {'Version': 's', 'UnitPath': 'as'}
UNIT_FIELDS = {'Id': 's', 'Names': 'as', 'LoadState': 's', 'NeedDaemonReload': 'b',
               'FragmentPath': 's', 'SourcePath': 's', 'DropInPaths': 'as'}
RELATIVES = ('-.slice', '-.slice.d', 'slice.d')


def require(condition):
    if not condition:
        raise ValueError('RELOAD_DIAGNOSIS_REFUSED')


def run(arguments):
    result = subprocess.run(['/usr/bin/busctl', '--system', '--json=short', '--timeout=2', '--', *arguments],
        capture_output=True, timeout=3, cwd='/', env={'PATH': '/usr/bin:/bin', 'LANG': 'C'})
    require(result.returncode == 0 and not result.stderr and len(result.stdout) <= 65536)
    return result.stdout


def properties(location, interface, fields):
    rows = run(['get-property', 'org.freedesktop.systemd1', location,
                'org.freedesktop.systemd1.' + interface, *fields]).splitlines()
    require(len(rows) == len(fields))
    result = {}
    for (name, signature), raw in zip(fields.items(), rows, strict=True):
        value = json.loads(raw)
        require(type(value) is dict and set(value) == {'type', 'data'} and value['type'] == signature)
        expected = str if signature == 's' else bool if signature == 'b' else list
        require(type(value['data']) is expected)
        if expected is list:
            require(len(value['data']) <= 64 and all(type(item) is str for item in value['data']))
        result[name] = value['data']
    return result


def absent(spelling):
    try:
        Path(spelling).lstat()
    except FileNotFoundError:
        return True
    return False


def manager_view():
    result = {}
    for name, observer, manager in (('mount', '/proc/self/ns/mnt', '/proc/1/ns/mnt'),
                                    ('root', '/', '/proc/1/root')):
        before, after = os.stat(observer), os.stat(manager)
        require((before.st_dev, before.st_ino) == (after.st_dev, after.st_ino))
        result[name] = [before.st_dev, before.st_ino]
    return result


def snapshot():
    view = manager_view()
    manager = properties('/org/freedesktop/systemd1', 'Manager', MANAGER_FIELDS)
    require(manager['Version'] == VERSION and 0 < len(manager['UnitPath']) <= 64 and
            len(set(manager['UnitPath'])) == len(manager['UnitPath']))
    unit = properties('/org/freedesktop/systemd1/unit/_2d_2eslice', 'Unit', UNIT_FIELDS)
    require(unit['Id'] == UNIT and unit['Names'] == [UNIT] and unit['LoadState'] == 'loaded' and
            unit['FragmentPath'] == unit['SourcePath'] == '' and unit['DropInPaths'] == [])
    checked = []
    for spelling in manager['UnitPath']:
        require(spelling.startswith('/') and spelling != '/' and not spelling.startswith('//') and
                spelling == os.path.normpath(spelling) and '\x00' not in spelling)
        for relative in RELATIVES:
            candidate = str(Path(spelling) / relative)
            require(absent(candidate))
            checked.append(candidate)
    require(view == manager_view())
    return dict(manager=manager, unit=unit, checked=checked, view=view)


def observe():
    started = time.time_ns()
    before = snapshot()
    after = snapshot()
    require(before == after)
    outdated = before['unit']['NeedDaemonReload']
    return dict(schema=1, classification='MANAGER_WIDE_OUTDATED_WITNESS' if outdated else 'NO_MANAGER_WIDE_OUTDATED_WITNESS',
        version=VERSION, sentinel=UNIT, need_daemon_reload=outdated,
        checked_absent_paths=len(before['checked']), search_paths_sha256=hashlib.sha256(
            json.dumps(before['manager']['UnitPath'], separators=(',', ':')).encode()).hexdigest(),
        started_at_ns=started, finished_at_ns=time.time_ns(), reload_performed=False, services_changed=False,
        full_unit_equivalence=False, originating_operation_identified=False, capture_permitted=False)


def main():
    try:
        require(os.geteuid() == 0)
        result = observe()
    except Exception:
        result = dict(classification='RELOAD_DIAGNOSIS_REFUSED', capture_permitted=False,
                      reload_performed=False, services_changed=False)
        print(json.dumps(result, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
