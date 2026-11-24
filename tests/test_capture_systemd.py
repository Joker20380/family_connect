import copy
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

import pytest

from control import capture_group as group, capture_launch as launch, capture_systemd as lifecycle
from control.capture_gate import GateError, initialize
from scripts.package_capture_guardians import build

NAME = 'family-connect-friends-awg.service'


def values():
    return dict(Id=NAME, LoadState='loaded', ActiveState='active', SubState='running', Job=[0, '/'],
                NeedDaemonReload=False, InvocationID=[1] * 16, StateChangeTimestampMonotonic=100,
                MainPID=123, ControlPID=0, ControlGroup='/system.slice/' + NAME, Result='success',
                ReloadResult='success', NRestarts=0, ExecMainStartTimestampMonotonic=90)


def bus(monkeypatch, fields=None):
    selected = values() if fields is None else fields
    def query(scope, arguments, deadline):
        assert scope == 'system'
        if arguments[0] == 'call':
            return json.dumps(dict(type='o', data=['/org/freedesktop/systemd1/unit/fixture'])).encode()
        interface = arguments[3].rsplit('.', 1)[1]
        return b'\n'.join(json.dumps(dict(type=signature, data=selected[name])).encode()
                          for name, signature in lifecycle.FIELDS[interface].items())
    monkeypatch.setattr(lifecycle, 'command', query)


def test_settled_properties(monkeypatch):
    bus(monkeypatch)
    assert lifecycle.properties('system', NAME, 10) == values()


@pytest.mark.parametrize('change', [
    {'Job': [42, '/org/freedesktop/systemd1/job/42']}, {'Job': [False, '/']},
    {'ControlPID': 12}, {'MainPID': 0}, {'ActiveState': 'deactivating'},
    {'SubState': 'stop-post'}, {'Result': 'timeout'}, {'ReloadResult': 'exit-code'},
    {'NeedDaemonReload': True}, {'LoadState': 'not-found'}, {'Id': 'other.service'},
    {'InvocationID': [0] * 16}, {'InvocationID': [True] * 16}, {'InvocationID': [1]},
    {'StateChangeTimestampMonotonic': 0}, {'NRestarts': -1}, {'MainPID': True},
])
def test_unsettled_unit_is_not_an_ack(monkeypatch, change):
    selected = values()
    selected.update(change)
    bus(monkeypatch, selected)
    with pytest.raises(GateError):
        lifecycle.properties('system', NAME, 10)


@pytest.mark.parametrize('binding', [
    {}, {'scope': 'remote', 'units': {NAME: 'a' * 64}},
    {'scope': 'system', 'units': {}}, {'scope': 'system', 'units': {NAME: 'A' * 64}},
    {'scope': 'system', 'units': {'ssh.service': 'a' * 64}},
    {'scope': 'user', 'units': {NAME: 'a' * 64}},
    {'scope': 'system', 'units': {NAME: 'a' * 64}, 'wait': True},
])
def test_invalid_binding(binding):
    with pytest.raises(GateError):
        lifecycle.validate(binding)


def test_veto_requires_same_approved_snapshot_and_resets_after_error(monkeypatch):
    binding = dict(scope='system', units={NAME: 'a' * 64})
    state = lifecycle.SystemdState(binding)
    binding['units'][NAME] = 'b' * 64
    monkeypatch.setattr(lifecycle, 'observe', lambda *args: 'a' * 64)
    with pytest.raises(GateError, match='NOT_HELD'):
        state.verify()
    with state.hold():
        with pytest.raises(GateError, match='ALREADY_HELD'), state.hold():
            pytest.fail('reentered')
        monkeypatch.setattr(lifecycle, 'observe', lambda *args: 'b' * 64)
        with pytest.raises(GateError, match='BINDING_CHANGED'):
            state.verify()
    with pytest.raises(GateError, match='BINDING_CHANGED'), state.hold():
        pytest.fail('changed binding accepted')
    assert not state.held


@pytest.fixture
def cgroup(tmp_path):
    root = tmp_path / 'groups'
    directory = root / 'system.slice' / NAME
    directory.mkdir(parents=True)
    (directory / 'cgroup.events').write_text('populated 1\nfrozen 0\n')
    (directory / 'cgroup.procs').write_text(str(os.getpid()) + '\n')
    return root, directory


def test_native_self_identity_and_recursive_cgroup(cgroup):
    root, directory = cgroup
    child = directory / 'worker'
    child.mkdir()
    (child / 'cgroup.events').write_text('populated 0\nfrozen 0\n')
    (child / 'cgroup.procs').write_text('')
    groups, members = lifecycle.processes('/system.slice/' + NAME, NAME, root=root)
    assert set(groups) == {'.', 'worker'} and members == {os.getpid()}
    assert groups['.'][2][0][1] > 0


@pytest.mark.parametrize('failure', ['frozen', 'duplicate', 'symlink', 'missing', 'invalid'])
def test_bad_cgroup_refuses(cgroup, failure):
    root, directory = cgroup
    if failure == 'frozen':
        (directory / 'cgroup.events').write_text('populated 1\nfrozen 1\n')
    elif failure == 'duplicate':
        (directory / 'cgroup.procs').write_text((str(os.getpid()) + '\n') * 2)
    elif failure == 'symlink':
        (directory / 'bad').symlink_to(directory)
    elif failure == 'missing':
        (directory / 'cgroup.procs').unlink()
    else:
        (directory / 'cgroup.procs').write_text('bad')
    with pytest.raises((GateError, OSError)):
        lifecycle.processes('/system.slice/' + NAME, NAME, root=root)


@pytest.mark.parametrize('mutation', ['lifecycle', 'main_outside'])
def test_mid_observation_change_refuses(monkeypatch, mutation):
    first, second = values(), values()
    if mutation == 'lifecycle':
        second['InvocationID'] = [2] * 16
    snapshots = iter((first, second))
    monkeypatch.setattr(lifecycle, 'properties', lambda *args: next(snapshots))
    monkeypatch.setattr(lifecycle, 'processes', lambda *args: ({}, {123} if mutation == 'lifecycle' else {456}))
    with pytest.raises(GateError):
        lifecycle.observe('system', NAME, time.monotonic() + 1)


def test_command_is_read_only_bounded_and_drops_bus_environment(monkeypatch):
    observed = []
    monkeypatch.setenv('DBUS_SYSTEM_BUS_ADDRESS', 'untrusted')
    def run(arguments, **kwargs):
        observed.append((arguments, kwargs))
        return subprocess.CompletedProcess(arguments, 0, b'{}', b'')
    monkeypatch.setattr(subprocess, 'run', run)
    assert lifecycle.command('system', ['get-property'], time.monotonic() + .75) == b'{}'
    arguments, options = observed[0]
    assert arguments[:3] == ['/usr/bin/busctl', '--system', '--json=short']
    assert options['env'] == {'PATH': '/usr/bin:/bin', 'LANG': 'C'}
    assert 0 < options['timeout'] <= .75
    with pytest.raises(GateError, match='DEADLINE'):
        lifecycle.command('system', [], 0)
    assert len(observed) == 1


def binding(tmp_path, unit, expected):
    gates = [initialize(tmp_path / name) for name in ('first', 'second')]
    source = tmp_path / 'guardians.pyz'
    source_sha = build(source)
    with open('/proc/self/exe', 'rb') as runtime:
        runtime_sha = launch.runtime_sha(runtime.fileno())
    value = dict(schema=3, source_sha256=source_sha, runtime_sha256=runtime_sha,
                 namespaces=launch.namespaces(), mappings=launch.mappings(),
                 coordinator=[os.getuid(), os.getgid()], guardians=[
                     dict(uid=os.getuid(), gid=os.getgid(), groups=sorted(os.getgroups()), renewal=None,
                          systemd=None, gate=str(gate.directory), pins=group.pins(gate.pins)) for gate in gates])
    value['guardians'][0]['systemd'] = dict(scope='user', units={unit: expected})
    path = tmp_path / 'binding.json'
    raw = json.dumps(value).encode()
    path.write_bytes(raw)
    path.chmod(0o600)
    return (str(path), launch.digest(raw), str(source)), gates, value


def test_schema3_closed_package_and_alias_refusal(tmp_path):
    arguments, gates, value = binding(tmp_path, 'fc-ha-lifecycle-' + 'a' * 16 + '.service', 'a' * 64)
    launch.validate(value)
    launch.archive(Path(arguments[2]).read_bytes())
    value['guardians'][1]['systemd'] = copy.deepcopy(value['guardians'][0]['systemd'])
    with pytest.raises(GateError, match='SYSTEMD_ALIAS'):
        launch.validate(value)


@pytest.fixture
def native_unit(tmp_path):
    if os.environ.get('FC_HA_SYSTEMD_NATIVE') != '1':
        pytest.skip('explicit owned user-systemd qualification only')
    name = 'fc-ha-lifecycle-' + secrets.token_hex(8) + '.service'
    ready = tmp_path / 'ready.json'
    child = 'import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(120)'
    script = ('import json,pathlib,signal,subprocess,sys,time;'
              'child=subprocess.Popen([sys.executable,"-c",sys.argv[2]]);'
              'signal.signal(signal.SIGTERM,lambda *args:sys.exit(0));time.sleep(.15);'
              'pathlib.Path(sys.argv[1]).write_text(json.dumps([child.pid]));time.sleep(120)')
    command = ['systemd-run', '--user', '--quiet', '--unit=' + name, '--property=KillMode=control-group',
               '--property=TimeoutStopSec=2', '--property=ExecStopPost=/usr/bin/sleep 1',
               sys.executable, '-I', '-B', '-c', script, str(ready), child]
    children = []
    try:
        subprocess.run(command, check=True, capture_output=True, timeout=5)
        deadline = time.monotonic() + 5
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(.02)
        assert ready.exists()
        children = json.loads(ready.read_bytes())
        expected = lifecycle.observe('user', name, time.monotonic() + .75)
        yield name, expected, children
    finally:
        subprocess.run(['systemctl', '--user', 'stop', name], capture_output=True, timeout=8, check=True)
        subprocess.run(['systemctl', '--user', 'reset-failed', name], capture_output=True, timeout=3)
        assert all(not Path('/proc', str(pid)).exists() for pid in children)


def test_native_closed_guardian_accepts_unchanged_running_service(tmp_path, native_unit):
    name, expected, children = native_unit
    arguments, gates, value = binding(tmp_path, name, expected)
    with launch.launch(*arguments) as participants:
        with group.joint(participants) as window:
            assert all(Path('/proc', str(pid)).exists() for pid in children)
        assert window.receipt['status'] == 'LOCAL_INTERVAL_CONFIRMED'
        assert window.receipt['capture_permitted'] is False


def test_native_async_stop_cannot_confirm_interval(tmp_path, native_unit):
    name, expected, children = native_unit
    arguments, gates, value = binding(tmp_path, name, expected)
    with launch.launch(*arguments) as participants:
        with pytest.raises((GateError, OSError)), group.joint(participants) as window:
            result = subprocess.run(['systemctl', '--user', '--no-block', 'stop', name],
                                    capture_output=True, timeout=1)
            assert result.returncode == 0
            assert any(Path('/proc', str(pid)).exists() for pid in children)
            with pytest.raises(GateError, match='UNSETTLED'):
                lifecycle.observe('user', name, time.monotonic() + .75)
        assert window.receipt is None
    for gate in gates:
        with gate.operation():
            pass


def test_native_stop_post_with_no_main_pid_is_still_unsettled(native_unit):
    name, expected, children = native_unit
    subprocess.run(['systemctl', '--user', '--no-block', 'stop', name],
                   capture_output=True, timeout=1, check=True)
    deadline = time.monotonic() + 5
    selected = {}
    while time.monotonic() < deadline:
        result = subprocess.run(['systemctl', '--user', 'show', name,
            '--property=MainPID,ControlPID,SubState,Job'], capture_output=True, timeout=1, check=True)
        selected = dict(line.split('=', 1) for line in result.stdout.decode().splitlines())
        if selected['SubState'] == 'stop-post':
            break
        time.sleep(.02)
    assert selected['SubState'] == 'stop-post' and selected['MainPID'] == '0'
    assert int(selected['ControlPID']) > 0 and selected['Job']
    with pytest.raises(GateError, match='UNSETTLED'):
        lifecycle.observe('user', name, time.monotonic() + .75)


@pytest.mark.parametrize('failure', ['pid_reuse', 'zombie', 'executable_change'])
def test_process_identity_refuses_ambiguous_completion(tmp_path, monkeypatch, failure):
    directory = tmp_path / '123'
    directory.mkdir()
    (directory / 'exe').write_bytes(b'first')
    (directory / 'cmdline').write_bytes(b'fixture\x00')
    status = b'123 (fixture ) process) S ' + b'0 ' * 18 + b'100 0'
    (directory / 'stat').write_bytes(status)
    original = lifecycle.bounded
    reads = 0
    def read(path, limit=8192):
        nonlocal reads
        raw = original(path, limit)
        if path.name == 'stat':
            reads += 1
            if failure == 'zombie':
                return raw.replace(b') S ', b') Z ')
            if reads == 2 and failure == 'pid_reuse':
                return raw.replace(b'100 0', b'101 0')
        if path.name == 'cmdline' and failure == 'executable_change':
            (directory / 'other').write_bytes(b'changed')
            (directory / 'other').replace(directory / 'exe')
        return raw
    monkeypatch.setattr(lifecycle, 'bounded', read)
    with pytest.raises(GateError):
        lifecycle.process(123, tmp_path)


def test_schema3_system_scope_requires_root_and_rejects_extra_fields(tmp_path):
    arguments, gates, value = binding(tmp_path, 'fc-ha-lifecycle-' + 'a' * 16 + '.service', 'a' * 64)
    value['guardians'][0]['systemd'] = dict(scope='system', units={NAME: 'a' * 64})
    with pytest.raises(GateError, match='SYSTEMD_IDENTITY'):
        launch.validate(value)
    value['guardians'][0]['uid'] = value['guardians'][0]['gid'] = 0
    value['guardians'][0]['groups'] = []
    value['coordinator'] = [0, 0]
    launch.validate(value)
    value['guardians'][0]['systemd']['activate'] = True
    with pytest.raises(GateError, match='SYSTEMD_BINDING'):
        launch.validate(value)
