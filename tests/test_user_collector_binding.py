from contextvars import copy_context
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

from control.capture_gate import Busy, CURRENT, GateError, initialize
from control_plane import collect_inventory, collect_technical_metadata, monitor_inventory, probe_network
from control_plane import collector_binding as binding


ROOT = Path(__file__).resolve().parents[1]


def write_binding(path, document):
    path.write_text(json.dumps(document, sort_keys=True, separators=(',', ':')) + '\n')
    path.chmod(0o644)


@pytest.fixture
def installed(tmp_path, monkeypatch):
    application = tmp_path / 'application'
    for name in binding.SOURCE_NAMES:
        target = application / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    gates = {role: initialize(tmp_path / role) for role in binding.ROLES}
    document = dict(schema=1, baseline=binding.BASELINE, application=str(application), uid=os.geteuid(),
                    sources={name: hashlib.sha256((application / name).read_bytes()).hexdigest()
                             for name in binding.SOURCE_NAMES},
                    gates={role: dict(directory=str(gate.directory), pins=gate.pins) for role, gate in gates.items()})
    filename = tmp_path / 'binding.json'
    write_binding(filename, document)
    monkeypatch.setattr(binding, 'INSTALLED_APP', application)
    monkeypatch.setattr(binding, 'INSTALLED_BINDING', filename)
    monkeypatch.setattr(binding, 'BINDING_UID', os.geteuid())
    monkeypatch.setattr(binding, '__file__', str(application / 'control_plane/collector_binding.py'))
    monkeypatch.delenv('FC_CONTROL_CAPTURE_GATE', raising=False)
    return SimpleNamespace(application=application, filename=filename, gates=gates, document=document)


@pytest.mark.parametrize('role', binding.ROLES)
def test_no_environment_admission_and_closed_refusal(installed, role):
    gate = installed.gates[role]
    assert binding.configured_gate(role).pins == gate.pins
    with binding.operation(role) as admitted:
        assert admitted is CURRENT.get()
        assert len(list((gate.directory / 'pending').iterdir())) == 1
        with binding.operation(role) as nested:
            assert nested is admitted
    with gate.drain(.1):
        with pytest.raises(Busy):
            with binding.operation(role):
                pytest.fail('closed operation admitted')


@pytest.mark.parametrize('profile', ['inventory', 'probe', 'symlink'])
def test_actual_installed_source_scopes_and_symlink_alias(installed, monkeypatch, profile):
    if profile == 'symlink':
        alias = installed.application.with_name('application-alias')
        alias.symlink_to(installed.application, target_is_directory=True)
        monkeypatch.setattr(binding, '__file__', str(alias / 'control_plane/collector_binding.py'))
        role = 'inventory'
    else:
        monkeypatch.setattr(binding, 'INSTALLED_APP', installed.application.with_name('other-checkout'))
        monkeypatch.setattr(binding, 'INVENTORY_APP' if profile == 'inventory' else 'PROBE_APP', installed.application)
        filename = installed.filename.with_name('owner-user-' + profile + '.json')
        if profile == 'probe':
            installed.document['sources'] = {name: value for name, value in installed.document['sources'].items()
                                             if name in binding.PROBE_SOURCES}
        write_binding(filename, installed.document)
        role = profile
    with binding.operation(role):
        pass
    with installed.gates[role].drain(.1):
        with pytest.raises(Busy):
            with binding.operation(role):
                pytest.fail('installed scope lost mandatory admission')
    if profile != 'symlink':
        with pytest.raises(GateError, match='INSTALLED_ROLE'):
            binding.configured_gate('inventory' if role == 'probe' else 'probe')


def test_replaced_application_symlink_does_not_fall_back_to_opt_in(installed):
    retained = installed.application.with_name('retained-application')
    installed.application.rename(retained)
    installed.application.symlink_to(retained, target_is_directory=True)
    with pytest.raises(GateError, match='BINDING_PATH'):
        binding.configured_gate('inventory')


@pytest.mark.parametrize('entry', ['monitor', 'inventory', 'metadata', 'probe'])
def test_direct_entry_refuses_before_io(installed, monkeypatch, tmp_path, entry):
    def forbidden(*args, **kwargs):
        pytest.fail('I/O before admission')
    monkeypatch.setattr(collect_inventory, 'ssh_command', forbidden)
    calls = dict(
        monitor=lambda: monitor_inventory.cycle(tmp_path / 'absent', run=forbidden),
        inventory=lambda: collect_inventory.collect(SimpleNamespace(), SimpleNamespace()),
        metadata=lambda: collect_technical_metadata.collect(base=tmp_path / 'absent', run=forbidden),
        probe=lambda: probe_network.cycle(tmp_path / 'absent', probe=forbidden, run=forbidden),
    )
    role = 'probe' if entry == 'probe' else 'inventory'
    with installed.gates[role].drain(.1):
        with pytest.raises(Busy):
            calls[entry]()
    assert not (tmp_path / 'absent').exists()


@pytest.mark.parametrize('fault', ['missing-binding', 'invalid-json', 'incomplete', 'duplicate', 'binding-mode',
    'binding-symlink', 'unknown-source', 'changed-source', 'missing-source', 'source-symlink', 'source-hardlink',
    'wrong-uid', 'unknown-baseline', 'missing-gate', 'replacement-gate', 'gate-mode', 'role-alias', 'wrong-env'])
@pytest.mark.parametrize('role', binding.ROLES)
def test_invalid_installed_state_refuses_before_operation(installed, monkeypatch, fault, role):
    target = installed.application / binding.SOURCE_NAMES[0]
    gate = installed.gates[role]
    if fault == 'missing-binding':
        installed.filename.unlink()
    elif fault == 'invalid-json':
        installed.filename.write_text('{')
    elif fault == 'duplicate':
        installed.filename.write_text(installed.filename.read_text().replace('{', '{"schema":1,', 1))
    elif fault == 'binding-mode':
        installed.filename.chmod(0o666)
    elif fault == 'binding-symlink':
        moved = installed.filename.with_suffix('.retained')
        installed.filename.rename(moved)
        installed.filename.symlink_to(moved)
    elif fault in ('incomplete', 'unknown-source', 'wrong-uid', 'unknown-baseline', 'role-alias'):
        if fault == 'incomplete':
            installed.document['sources'].pop(binding.SOURCE_NAMES[0])
        elif fault == 'unknown-source':
            installed.document['sources']['unknown.py'] = '1' * 64
        elif fault == 'wrong-uid':
            installed.document['uid'] += 1
        elif fault == 'unknown-baseline':
            installed.document['baseline'] = 'unreviewed'
        else:
            installed.document['gates']['probe'] = installed.document['gates']['inventory']
        write_binding(installed.filename, installed.document)
    elif fault == 'changed-source':
        target.write_bytes(target.read_bytes() + b'\n')
    elif fault == 'missing-source':
        target.unlink()
    elif fault in ('source-symlink', 'source-hardlink'):
        retained = target.with_suffix('.retained')
        target.rename(retained)
        if fault == 'source-symlink':
            target.symlink_to(retained)
        else:
            os.link(retained, target)
    elif fault in ('missing-gate', 'replacement-gate'):
        gate.directory.rename(gate.directory.with_name(role + '-retained'))
        if fault == 'replacement-gate':
            initialize(gate.directory)
    elif fault == 'gate-mode':
        gate.directory.chmod(0o755)
    else:
        monkeypatch.setenv('FC_CONTROL_CAPTURE_GATE', str(installed.gates['probe' if role == 'inventory' else 'inventory'].directory))
    with pytest.raises(GateError):
        with binding.operation(role):
            pytest.fail('invalid installed state admitted')


def test_expired_and_foreign_contexts_cannot_bypass_closed_gate(installed):
    with binding.operation('inventory'):
        stale = copy_context()
    with pytest.raises(GateError, match='STALE_CONTEXT'):
        stale.run(lambda: binding.operation('inventory').__enter__())
    with installed.gates['inventory'].operation():
        with pytest.raises(GateError, match='FOREIGN_CONTEXT'):
            with binding.operation('inventory'):
                pytest.fail('unverified context accepted')


def test_historical_markers_survive_normal_work_and_strict_drain(installed):
    gate = installed.gates['inventory']
    with gate.operation() as operation:
        operation.uncertain()
    original = {path: (path.read_bytes(), path.stat()) for path in (gate.directory / 'pending').iterdir()}
    with binding.operation('inventory'):
        pass
    for path, (raw, info) in original.items():
        assert path.read_bytes() == raw and path.stat().st_ino == info.st_ino and path.stat().st_mtime_ns == info.st_mtime_ns
    assert set((gate.directory / 'pending').iterdir()) == set(original)
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('historical uncertainty discarded')


def test_metadata_swallowed_remote_timeout_retains_dispatch_uncertainty(installed, tmp_path):
    base = tmp_path / 'metadata-runtime'
    local = base / '.local'
    local.mkdir(parents=True)
    config = dict(python='/isolated/python', archive='/isolated/source.pyz', archive_sha256='a' * 64)
    for name, raw in [('technical-metadata-source.json', json.dumps(config).encode()),
                      ('inventory-hmac.key', b'x' * 32),
                      ('transport-source.json', json.dumps(dict(archive_sha256='b' * 64)).encode())]:
        target = local / name
        target.write_bytes(raw)
        target.chmod(0o600)
    script = base / 'apps/console/technical_metadata_collector.py'
    script.parent.mkdir(parents=True)
    script.write_text('')
    calls = []

    def remote(command, **options):
        calls.append(command)
        if len(calls) == 2:
            raise subprocess.TimeoutExpired(command, options['timeout'])
        data = dict(source='gateway-ru', status='ok', devices=[])
        if len(calls) == 1:
            data['_targets'] = [dict(source='nl-amsterdam-1')]
        return SimpleNamespace(stdout=json.dumps(data).encode())

    collect_technical_metadata.collect(base=base, run=remote)
    assert len(calls) == 3
    gate = installed.gates['inventory']
    assert len(list((gate.directory / 'pending').iterdir())) == 1
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(.1):
            pytest.fail('remote timeout erased by later export success')


@pytest.mark.parametrize('role', binding.ROLES)
def test_fresh_process_no_environment_does_not_repin_replaced_gate(installed, role):
    gate = installed.gates[role]
    gate.directory.rename(gate.directory.with_name(role + '-retained'))
    initialize(gate.directory)
    code = '''
import os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from control_plane import collector_binding as binding
binding.INSTALLED_APP = Path(sys.argv[1])
binding.INSTALLED_BINDING = Path(sys.argv[2])
binding.BINDING_UID = os.geteuid()
try:
    with binding.operation(sys.argv[3]):
        raise AssertionError('replaced gate admitted')
except binding.GateError:
    print('REFUSED_BEFORE_IO')
'''
    environment = {key: value for key, value in os.environ.items() if key != 'FC_CONTROL_CAPTURE_GATE'}
    result = subprocess.run([sys.executable, '-I', '-B', '-c', code, str(installed.application),
        str(installed.filename), role], env=environment, capture_output=True, text=True, timeout=5)
    assert result.returncode == 0 and result.stdout.strip() == 'REFUSED_BEFORE_IO', result.stderr
    assert not list((gate.directory / 'pending').iterdir())
