from contextlib import ExitStack
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import zipfile

import pytest

from control import capture_group as group, capture_launch as launch
from control.capture_gate import Busy, GateError, initialize
from scripts.package_capture_guardians import build


@pytest.fixture
def inputs(tmp_path):
    gates = [initialize(tmp_path / name) for name in ('first', 'second')]
    source = tmp_path / 'guardians.pyz'
    source_sha = build(source)
    with open('/proc/self/exe', 'rb') as runtime:
        runtime_sha = launch.runtime_sha(runtime.fileno())
    binding = dict(schema=1, source_sha256=source_sha, runtime_sha256=runtime_sha,
                   namespaces=launch.namespaces(), mappings=launch.mappings(),
                   coordinator=[os.getuid(), os.getgid()], guardians=[
                       dict(uid=os.getuid(), gid=os.getgid(), groups=sorted(os.getgroups()),
                            gate=str(gate.directory), pins=group.pins(gate.pins)) for gate in gates])
    return gates, source, binding, tmp_path / 'binding.json'


def save(inputs):
    gates, source, binding, path = inputs
    raw = json.dumps(binding, sort_keys=True).encode()
    path.write_bytes(raw)
    path.chmod(0o600)
    return str(path), launch.digest(raw), str(source)


def test_closed_launch_joint_and_cleanup(inputs, monkeypatch):
    gates, source, binding, path = inputs
    monkeypatch.setenv('PYTHONPATH', '/invalid')
    monkeypatch.setenv('PYTHONHOME', '/invalid')
    with launch.launch(*save(inputs)) as participants:
        owned = [item.identity[0] for item in participants]
        with group.joint(participants) as window:
            assert window.receipt is None
            for gate in gates:
                with pytest.raises(Busy), gate.operation():
                    pytest.fail('writer entered')
        assert window.receipt['status'] == 'LOCAL_INTERVAL_CONFIRMED'
        assert not window.receipt['capture_permitted']
    for pid in owned:
        with pytest.raises(ChildProcessError):
            os.waitpid(pid, os.WNOHANG)
    for gate in gates:
        with gate.operation():
            pass


def test_source_path_replacement_after_launch_cannot_change_children(inputs):
    with launch.launch(*save(inputs)) as participants:
        inputs[1].write_bytes(b'not executable')
        with group.joint(participants) as window:
            pass
        assert window.receipt is not None


def test_body_failure_reaps_children(inputs):
    with pytest.raises(RuntimeError, match='body'):
        with launch.launch(*save(inputs)) as participants:
            owned = [item.identity[0] for item in participants]
            raise RuntimeError('body')
    for pid in owned:
        with pytest.raises(ChildProcessError):
            os.waitpid(pid, os.WNOHANG)


@pytest.mark.parametrize('change', [
    lambda value: value.update(schema=True),
    lambda value: value.update(extra='command'),
    lambda value: value.update(source_sha256='x'),
    lambda value: value.update(runtime_sha256='A' * 64),
    lambda value: value['namespaces'].update(net=[1, 2]),
    lambda value: value['namespaces'].update(mnt=[1, True]),
    lambda value: value['mappings'].update(uid='bad'),
    lambda value: value.update(coordinator=[True, 1]),
    lambda value: value.update(guardians=value['guardians'][:1]),
    lambda value: value['guardians'][0].update(uid=0),
    lambda value: value['guardians'][0].update(gid=-1),
    lambda value: value['guardians'][0].update(uid=2**32 - 1),
    lambda value: value['guardians'][0].update(groups=[0]),
    lambda value: value['guardians'][0].update(groups=[1, 1]),
    lambda value: value['guardians'][0].update(groups=[2, 1]),
    lambda value: value['guardians'][0].update(command='sh'),
    lambda value: value['guardians'][0].update(gate='/tmp/../gate'),
    lambda value: value['guardians'][1].update(pins=value['guardians'][0]['pins']),
    lambda value: value['guardians'][1].update(gate=value['guardians'][0]['gate']),
])
def test_invalid_binding_never_spawns(inputs, monkeypatch, change):
    change(inputs[2])
    monkeypatch.setattr(subprocess, 'Popen', lambda *args, **kwargs: pytest.fail('spawned'))
    with pytest.raises(GateError), launch.launch(*save(inputs)):
        pytest.fail('accepted')


@pytest.mark.parametrize('field', ['source_sha256', 'runtime_sha256', 'namespaces', 'mappings', 'coordinator', 'groups'])
def test_mismatched_binding_never_spawns(inputs, monkeypatch, field):
    binding = inputs[2]
    if field.endswith('sha256'):
        binding[field] = '0' * 64
    elif field == 'namespaces':
        binding[field]['mnt'][1] += 1
    elif field == 'mappings':
        binding[field]['uid'] = '0' * 64
    elif field == 'coordinator':
        binding[field][0] += 1
    else:
        binding['guardians'][0]['groups'] = []
    monkeypatch.setattr(subprocess, 'Popen', lambda *args, **kwargs: pytest.fail('spawned'))
    with pytest.raises(GateError), launch.launch(*save(inputs)):
        pytest.fail('accepted')


@pytest.mark.parametrize('failure', ['sha', 'permissions', 'symlink', 'hardlink', 'duplicate', 'fifo', 'oversize', 'parent_symlink'])
def test_input_fail_closed(inputs, monkeypatch, failure):
    arguments = list(save(inputs))
    path = inputs[3]
    if failure == 'sha':
        arguments[1] = '0' * 64
    elif failure == 'permissions':
        path.chmod(0o644)
    elif failure == 'symlink':
        path.rename(path.with_suffix('.real'))
        path.symlink_to(path.with_suffix('.real'))
    elif failure == 'hardlink':
        os.link(path, path.with_suffix('.link'))
    elif failure == 'fifo':
        path.unlink()
        os.mkfifo(path)
    elif failure == 'oversize':
        path.write_bytes(b'x' * (launch.LIMIT + 1))
    elif failure == 'parent_symlink':
        link = path.parent / 'linked'
        link.symlink_to(path.parent, target_is_directory=True)
        arguments[0] = str(link / path.name)
    else:
        raw = b'{"schema":1,"schema":1}'
        path.write_bytes(raw)
        arguments[1] = launch.digest(raw)
    monkeypatch.setattr(subprocess, 'Popen', lambda *args, **kwargs: pytest.fail('spawned'))
    with pytest.raises(OSError), launch.launch(*arguments):
        pytest.fail('accepted')


@pytest.mark.parametrize('mutation', ['extra', 'entry', 'missing', 'compressed', 'duplicate', 'corrupt'])
def test_archive_closure(inputs, mutation):
    with zipfile.ZipFile(inputs[1]) as original:
        members = {name: original.read(name) for name in original.namelist()}
    if mutation == 'extra':
        members['control/__init__.py'] = b'raise RuntimeError()'
    elif mutation == 'entry':
        members['__main__.py'] = b'print("wrong")'
    elif mutation == 'missing':
        del members['control/capture_gate.py']
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED if mutation == 'compressed' else zipfile.ZIP_STORED) as archive:
        for name, raw in members.items():
            archive.writestr(name, raw)
        if mutation == 'duplicate':
            with pytest.warns(UserWarning):
                archive.writestr('__main__.py', launch.MAIN)
    with pytest.raises(GateError):
        launch.archive(b'invalid' if mutation == 'corrupt' else output.getvalue())


def test_deterministic_package_and_no_overwrite(inputs, tmp_path):
    target = tmp_path / 'second.pyz'
    assert build(target) == inputs[2]['source_sha256']
    assert target.read_bytes() == inputs[1].read_bytes()
    launch.archive(target.read_bytes())
    with pytest.raises(FileExistsError):
        build(target)


def test_sealed_bytes_are_readable_not_mutable():
    with ExitStack() as stack:
        descriptor = launch.sealed(stack, b'source')
        assert launch.read_sealed(descriptor) == b'source'
        with pytest.raises(OSError):
            os.pwrite(descriptor, b'bad', 0)
        with pytest.raises(OSError):
            os.ftruncate(descriptor, 0)


def test_unsealed_input_refused():
    descriptor = os.memfd_create('test', os.MFD_ALLOW_SEALING)
    try:
        os.write(descriptor, b'source')
        with pytest.raises(GateError, match='UNSEALED'):
            launch.read_sealed(descriptor)
    finally:
        os.close(descriptor)


def test_wrong_gate_refuses_before_drain_reaps_all(inputs, monkeypatch):
    inputs[2]['guardians'][1]['pins']['admission.lock'][1] += 999999
    children = []
    original = subprocess.Popen

    def tracked(*args, **kwargs):
        child = original(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(subprocess, 'Popen', tracked)
    with pytest.raises(OSError), launch.launch(*save(inputs)):
        pytest.fail('accepted')
    assert len(children) == 2 and all(child.poll() is not None for child in children)
    for gate in inputs[0]:
        with gate.operation():
            pass


def test_partial_spawn_failure_does_not_leak_children(inputs, monkeypatch):
    children = []
    original = subprocess.Popen

    def tracked(*args, **kwargs):
        if children:
            raise OSError('spawn failed')
        child = original(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(subprocess, 'Popen', tracked)
    with pytest.raises(OSError, match='spawn failed'), launch.launch(*save(inputs)):
        pytest.fail('accepted')
    assert children[0].poll() is not None


def test_terminated_guardian_cannot_get_receipt(inputs):
    with launch.launch(*save(inputs)) as participants:
        os.kill(participants[0].identity[0], signal.SIGKILL)
        with pytest.raises(OSError), group.joint(participants):
            pytest.fail('accepted')


def test_argv_refuses_unsealed_direct_entry(inputs):
    process = subprocess.run([sys.executable, '-I', '-S', '-B', str(inputs[1]), '3', '4', '5'],
                             capture_output=True, timeout=3)
    assert process.returncode == 1 and not process.stdout and not process.stderr


def test_mutable_checkout_is_not_a_trusted_root_entrypoint(inputs):
    with pytest.raises(GateError, match='TRUSTED_ENTRYPOINT'):
        launch.trusted_entrypoint(inputs[2]['source_sha256'])


@pytest.mark.parametrize('failure', ['ready', 'timeout', 'identity'])
def test_failed_startup_reaps_children(inputs, monkeypatch, failure):
    children = []
    original = subprocess.Popen

    def tracked(*args, **kwargs):
        assert kwargs['cwd'] == '/' and kwargs['env'] == {'LANG': 'C.UTF-8'}
        assert kwargs['close_fds'] and len(kwargs['pass_fds']) == 4
        assert args[0][1:4] == ['-I', '-S', '-B']
        child = original(*args, **kwargs)
        children.append(child)
        return child

    def refuse(*args):
        raise GateError('INJECTED_STARTUP')

    monkeypatch.setattr(subprocess, 'Popen', tracked)
    if failure == 'ready':
        monkeypatch.setattr(group, 'receive', lambda *args: dict(status='READY', binding_sha256='0' * 64))
    else:
        monkeypatch.setattr(group, 'wait' if failure == 'timeout' else 'receive', refuse)
    with pytest.raises(OSError), launch.launch(*save(inputs)):
        pytest.fail('accepted')
    assert len(children) == 2 and all(child.poll() is not None for child in children)


def test_symlink_packaging_input_refused(inputs, tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'control').symlink_to(Path(__file__).resolve().parents[1] / 'control', target_is_directory=True)
    with pytest.raises(ValueError, match='UNSAFE_GUARDIAN_SOURCE'):
        build(tmp_path / 'unsafe.pyz', source)


@pytest.mark.parametrize('failure', [None, 'source', 'binding', 'flags'])
def test_standalone_trusted_probe(inputs, failure):
    binding_path, binding_sha, source_path = save(inputs)
    script = Path(__file__).resolve().parents[1] / 'scripts/control_ha_guardian_probe.py'
    command = [sys.executable, *(['-I', '-S', '-B'] if failure != 'flags' else []), str(script),
               '--source', source_path, '--source-sha256', '0' * 64 if failure == 'source' else inputs[2]['source_sha256'],
               '--binding', binding_path, '--binding-sha256', '0' * 64 if failure == 'binding' else binding_sha]
    process = subprocess.run(command, capture_output=True, timeout=5)
    assert not process.stderr
    result = json.loads(process.stdout)
    assert process.returncode == (0 if failure is None else 1)
    assert result['status'] == ('LOCAL_LAUNCH_PROBE_CONFIRMED' if failure is None else 'LOCAL_LAUNCH_PROBE_REFUSED')
    assert not result['capture_permitted']


def test_bootstrap_does_not_execute_unverified_source(inputs):
    marker = inputs[3].with_suffix('.executed')
    with zipfile.ZipFile(inputs[1], 'w') as archive:
        archive.writestr('__main__.py', f'open({str(marker)!r}, "w").close()')
    from scripts.control_ha_guardian_probe import verified_source
    with pytest.raises(ValueError, match='SOURCE_SHA'):
        verified_source(str(inputs[1]), inputs[2]['source_sha256'])
    assert not marker.exists()
