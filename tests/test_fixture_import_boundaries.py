import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / 'tests/fixtures/mesh_perf3b'
spec = importlib.util.spec_from_file_location('fc_mesh_history_runner', HISTORY / 'run_history.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

IMPORT_CHECK = '''
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
paths = json.loads(sys.argv[2])
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

polluter = load('prepare', root / paths[0][1]).inputs
sys.modules['prepare'] = polluter
original_path = list(sys.path)
modules = {name: load('fc_regression_' + name, root / path) for name, path in paths}
assert sys.path == original_path
assert sys.modules['prepare'] is polluter
for name, path in paths:
    module = modules[name]
    assert Path(module.inputs.__file__) == (root / path).with_name('prepare.py')
    assert module.inputs.__name__ != 'prepare'
    assert module.WORK == module.inputs.WORK
assert modules['audit'].WORK.name == 'p1-lifecycle-101-20261021'
assert modules['queue'].WORK.name == 'queue-retry-20261019'
for name in ('results', 'scope'):
    module = modules[name]
    assert module.WORK.name == 'speed-candidate-20261021'
    assert module.digest(Path(module.__file__)) == hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
assert callable(modules['queue'].main)
assert not modules['audit'].classify(dict(protocol_errors=0))['clean']
result = modules['results'].body_accounting([dict(name='bulk-1-0', valid=False,
    intended_bytes=10, metrics=dict(BODY_BYTES='4', CURL_EXIT='18'))], [])
assert result['partial_response_bytes'] == 4 and result['complete_response_bytes'] == 0
messages, errors = modules['results'].capture_messages([dict(kind='journal', raw=json.dumps(
    dict(_SYSTEMD_INVOCATION_ID='epoch', _STREAM_ID='stream', _PID='1', MESSAGE='{}')))])
assert messages == [{}] and not errors
try:
    modules['scope'].validate_export(dict(ring={}), 'P0')
except KeyError:
    pass
else:
    raise AssertionError('invalid export accepted')
print('isolated imports PASS')
'''


@pytest.mark.parametrize('reverse', [False, True])
def test_fixture_import_order_uses_own_prepare(reverse, tmp_path):
    paths = [
        ('audit', 'tests/fixtures/p1_owner/lifecycle101/audit.py'),
        ('queue', 'tests/fixtures/queue_retry/local_test.py'),
        ('scope', 'tests/fixtures/speed_candidate/scope.py'),
        ('results', 'tests/fixtures/speed_candidate/phase_results.py'),
    ]
    if reverse:
        paths.reverse()
    result = subprocess.run([sys.executable, '-I', '-B', '-c', IMPORT_CHECK, str(ROOT), json.dumps(paths)],
                            cwd=tmp_path, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == 'isolated imports PASS'
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('reverse', [False, True])
def test_fixture_collection_cannot_shadow_product_control(reverse, tmp_path):
    paths = ['tests/fixtures/p1_owner/test_classify.py',
             'tests/fixtures/mux_profile/test_session_scope.py', 'tests/test_friends_access.py']
    if reverse:
        paths.reverse()
    result = subprocess.run([sys.executable, '-m', 'pytest', '--collect-only', '-q',
                            *(str(ROOT / path) for path in paths), '-o', 'cache_dir=' + str(tmp_path)],
                            cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'test_friends_access.py::' in result.stdout


def test_historical_boundary_is_exact_and_sources_are_unchanged():
    manifest = json.loads(runner.MANIFEST.read_text())
    assert set(manifest['tests']) == {
        'test_owner_handoff.py', 'test_cleaned_allocation.py', 'test_live_operator.py',
        'test_successor_lifecycle.py', 'test_successor_migration.py', 'test_successor_operator.py',
    }
    policy = importlib.util.spec_from_file_location('fc_mesh_history_policy', HISTORY / 'conftest.py')
    module = importlib.util.module_from_spec(policy)
    policy.loader.exec_module(module)
    assert set(module.collect_ignore) == set(manifest['tests'])
    for name in manifest['tests']:
        path = 'tests/fixtures/mesh_perf3b/' + name
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == manifest['files'][path], name


def test_historical_runner_missing_inputs_is_blocked(tmp_path):
    result = subprocess.run([sys.executable, str(HISTORY / 'run_history.py')], cwd=tmp_path,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert 'BLOCKED/NOT_RUN: MISSING_INPUTS' in result.stderr
    assert not list(tmp_path.iterdir())


def test_historical_runner_rejects_unverified_archive_without_execution(tmp_path):
    archive = tmp_path / 'unverified.pyz'
    archive.write_bytes(b'not the historical candidate')
    result = subprocess.run([sys.executable, str(HISTORY / 'run_history.py'), '--source-root', str(ROOT),
                             '--api-archive', str(archive)], cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert 'BLOCKED/NOT_RUN: HASH_MISMATCH: sealed owner API archive' in result.stderr
    assert list(tmp_path.iterdir()) == [archive]


def test_historical_direct_pytest_is_blocked(tmp_path):
    result = subprocess.run([sys.executable, '-m', 'pytest', '--collect-only', '-q',
                            str(HISTORY / 'test_owner_handoff.py'), '-o', 'cache_dir=' + str(tmp_path)],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode != 0
    assert 'BLOCKED: use tests/fixtures/mesh_perf3b/run_history.py' in result.stdout + result.stderr


@pytest.fixture
def synthetic_inputs(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'fixture.py').write_bytes(b'fixture')
    archive = tmp_path / 'api.zip'
    with zipfile.ZipFile(archive, 'w') as output:
        output.writestr('control/module.py', b'module')
    manifest = dict(files={'fixture.py': hashlib.sha256(b'fixture').hexdigest()},
                    api_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                    api_modules={'control/module.py': hashlib.sha256(b'module').hexdigest()})
    return manifest, source, archive


@pytest.mark.parametrize('change', ['missing-source', 'changed-source', 'missing-api', 'changed-api', 'changed-module'])
def test_historical_input_validation_fails_closed(synthetic_inputs, change):
    manifest, source, archive = synthetic_inputs
    if change == 'missing-source':
        (source / 'fixture.py').unlink()
    elif change == 'changed-source':
        (source / 'fixture.py').write_bytes(b'changed')
    elif change == 'missing-api':
        archive.unlink()
    elif change == 'changed-api':
        archive.write_bytes(b'changed')
    else:
        manifest['api_modules']['control/module.py'] = '0' * 64
    with pytest.raises((OSError, ValueError)):
        runner.verified_inputs(manifest, source, archive)


def test_historical_run_uses_snapshots_and_isolated_child(synthetic_inputs, monkeypatch):
    manifest, source, archive = synthetic_inputs
    sources, raw, retained = runner.verified_inputs(manifest, source, archive)
    (source / 'fixture.py').write_bytes(b'changed after verification')
    archive.write_bytes(b'changed after verification')
    manifest.update(source_commit='synthetic', tests={'test_fixture.py': []})
    calls = []

    def child(command, cwd, env, timeout):
        calls.append(command)
        assert command[:4] == [sys.executable, '-I', '-B', '-c']
        assert cwd != ROOT and (cwd / 'fixture.py').read_bytes() == b'fixture'
        assert (cwd / 'state-client-build/mesh-perf-3b/api/control/module.py').read_bytes() == b'module'
        assert 'PYTHONPATH' not in env and 'PYTEST_ADDOPTS' not in env
        assert not any(key.startswith(('FC_', 'SSH_')) for key in env)
        if command[-1] == runner.IMPORT_PREFLIGHT:
            return SimpleNamespace(returncode=0)
        assert command[-1] == str(cwd / runner.TEST_DIRECTORY / 'test_fixture.py')
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(runner.subprocess, 'run', child)
    assert runner.run(manifest, sources, raw, ['test_fixture.py']) == 7
    assert len(calls) == 2


@pytest.fixture
def complete_snapshot_inputs(tmp_path, synthetic_inputs):
    api_manifest, source, archive = synthetic_inputs
    manifest = json.loads(runner.MANIFEST.read_text())
    manifest.update(api_sha256=api_manifest['api_sha256'], api_modules=api_manifest['api_modules'])
    for name in manifest['files']:
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    paths = {}
    for name, entry in manifest['retained_inputs'].items():
        path = tmp_path / name
        paths[name] = path
        if entry['kind'] in ('tree', 'classes'):
            entry['files'] = {}
            for relative in entry['required_files']:
                target = path / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                raw = b'\xca\xfe\xba\xbe synthetic class' if entry['kind'] == 'classes' else b'synthetic runtime'
                if relative == 'bin/java':
                    raw = b'#!/bin/sh\ntest "$1" = --dry-run && test -f "${0%/bin/java}/lib/modules" && test -f "${0%/bin/java}/lib/server/libjvm.so"\n'
                target.write_bytes(raw)
                target.chmod(0o755 if relative in entry.get('executables', ()) else 0o644)
                entry['files'][relative] = hashlib.sha256(raw).hexdigest()
        else:
            if entry['kind'] == 'zip':
                with zipfile.ZipFile(path, 'w') as package:
                    for member in entry['members']:
                        package.writestr(member, b'synthetic member')
            else:
                path.write_bytes(b'#!/bin/sh\necho "delivery compatibility failed" >&2\nexit 1\n')
                path.chmod(0o755)
            entry['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    return manifest, source, archive, paths


@pytest.mark.parametrize('name', ['original-api', 'delivery-check', 'java-runtime', 'java-classes',
                                 'gson-jar', 'junit-jar', 'hamcrest-jar', 'bootstrap-vector'])
@pytest.mark.parametrize('change', ['missing', 'changed', 'unpinned'])
def test_complete_preflight_blocks_each_input_before_pytest(complete_snapshot_inputs, monkeypatch, tmp_path,
                                                          name, change, capsys):
    manifest, source, archive, paths = complete_snapshot_inputs
    if name == 'bootstrap-vector':
        relative = 'tests/vectors/bootstrap-timestamps.json'
        target = source / relative
        pins, key = manifest['files'], relative
    else:
        entry = manifest['retained_inputs'][name]
        target = paths[name]
        pins, key = entry, 'sha256'
        if entry['kind'] in ('tree', 'classes'):
            relative = entry['required_files'][0]
            target /= relative
            pins, key = entry['files'], relative
    if change == 'missing':
        target.unlink()
    elif change == 'changed':
        target.write_bytes(b'changed')
    else:
        pins[key] = None
    manifest_path = tmp_path / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest))
    monkeypatch.setattr(runner, 'MANIFEST', manifest_path)
    def forbidden(*args, **kwargs):
        pytest.fail('incomplete inputs reached subprocess/pytest')
    monkeypatch.setattr(runner.subprocess, 'run', forbidden)
    arguments = ['--source-root', str(source), '--api-archive', str(archive)]
    for label, path in paths.items():
        arguments.extend(['--' + label, str(path)])
    assert runner.main(arguments) == 2
    assert 'BLOCKED/NOT_RUN:' in capsys.readouterr().err


def test_snapshot_contains_real_public_sources_vector_and_retained_layout(complete_snapshot_inputs, tmp_path):
    manifest, source, archive, paths = complete_snapshot_inputs
    sources, raw, retained = runner.verified_inputs(manifest, source, archive, paths)
    root = tmp_path / 'snapshot'
    root.mkdir()
    vector = 'tests/vectors/bootstrap-timestamps.json'
    (source / vector).write_bytes(b'changed after validation')
    paths['delivery-check'].write_bytes(b'changed after validation')
    runner.write_snapshot(root, sources, raw, retained)
    for name, expected in manifest['files'].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected
    for name, (data, mode) in retained.items():
        assert (root / name).read_bytes() == data
        assert (root / name).stat().st_mode & 0o777 == mode
    check = '''
import ast, json
from pathlib import Path
__file__ = str(Path.cwd() / 'tests/test_friends_restricted.py')
tree = ast.parse(Path(__file__).read_text())
assignment, = [node for node in tree.body if isinstance(node, ast.Assign)
               and any(isinstance(target, ast.Name) and target.id == 'TIME_CONTRACT' for target in node.targets)]
exec(compile(ast.Module(body=[assignment], type_ignores=[]), __file__, 'exec'))
assert TIME_CONTRACT['valid'] and TIME_CONTRACT['invalid']
tools = Path('state-client-build/field65-export16/diag-source-freeze-1/resume-tools')
for library in ('com.google.code.gson/gson/2.13.2', 'junit/junit/4.13.2', 'org.hamcrest/hamcrest-core/1.3'):
    jar, = (tools / 'gradle-home/caches/modules-2/files-2.1' / library).glob('*/*.jar')
    assert jar.is_file()
'''
    result = subprocess.run([sys.executable, '-I', '-B', '-c', check], cwd=root, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    runner.retained_preflight(manifest, root, {'HOME': str(root)}, retained)


@pytest.mark.parametrize('name', ['delivery-check', 'java-runtime'])
def test_missing_execute_permission_blocks_preflight(complete_snapshot_inputs, name):
    manifest, source, archive, paths = complete_snapshot_inputs
    target = paths[name] / 'bin/java' if name == 'java-runtime' else paths[name]
    target.chmod(0o644)
    with pytest.raises(ValueError, match='NOT_EXECUTABLE'):
        runner.verified_inputs(manifest, source, archive, paths)


@pytest.mark.parametrize('change', ['extra', 'symlink', 'incomplete-pin'])
def test_java_tree_inventory_is_exact(complete_snapshot_inputs, change):
    manifest, source, archive, paths = complete_snapshot_inputs
    tree = paths['java-runtime']
    if change == 'extra':
        (tree / 'extra').write_bytes(b'unverified')
    elif change == 'symlink':
        (tree / 'extra').symlink_to(tree / 'bin/java')
    else:
        relative = 'lib/modules'
        (tree / relative).unlink()
        del manifest['retained_inputs']['java-runtime']['files'][relative]
    with pytest.raises(ValueError, match='INVENTORY|UNSAFE_TREE'):
        runner.verified_inputs(manifest, source, archive, paths)


@pytest.mark.parametrize('name', ['delivery-check', 'java-runtime'])
def test_unusable_executable_blocks_before_pytest(complete_snapshot_inputs, tmp_path, monkeypatch, name, capsys):
    manifest, source, archive, paths = complete_snapshot_inputs
    sources, raw, retained = runner.verified_inputs(manifest, source, archive, paths)
    entry = manifest['retained_inputs'][name]
    destination = entry['destination'] + ('/bin/java' if name == 'java-runtime' else '')
    retained[destination] = (b'#!/bin/sh\nexit 42\n', 0o755)
    monkeypatch.setattr(runner, 'IMPORT_PREFLIGHT', 'print("synthetic import probe")')
    monkeypatch.setattr(runner, 'CHILD', 'raise AssertionError("pytest must not start")')
    assert runner.run(manifest, sources, raw, list(manifest['tests']), retained) == 2
    assert 'BLOCKED/NOT_RUN:' in capsys.readouterr().err


def test_retained_requirements_follow_selected_files(complete_snapshot_inputs):
    manifest, source, archive, paths = complete_snapshot_inputs
    assert runner.verified_retained(manifest, {}, ['test_successor_operator.py']) == {}
    retained = runner.verified_retained(manifest, {'original-api': paths['original-api']},
                                      ['test_successor_migration.py'])
    assert set(retained) == {manifest['retained_inputs']['original-api']['destination']}
    with pytest.raises(ValueError, match='MISSING_INPUT: --delivery-check'):
        runner.verified_retained(manifest, {'original-api': paths['original-api']},
                                 ['test_successor_lifecycle.py'])


def test_real_unresolved_pins_cannot_be_replaced_by_found_bytes(complete_snapshot_inputs):
    manifest, _, _, paths = complete_snapshot_inputs
    real = json.loads(runner.MANIFEST.read_text())
    manifest['retained_inputs'] = real['retained_inputs']
    with pytest.raises(ValueError) as failure:
        runner.verified_retained(manifest, paths, list(manifest['tests']))
    for name in ('delivery-check', 'java-runtime', 'java-classes', 'gson-jar', 'junit-jar', 'hamcrest-jar'):
        assert 'UNPINNED_INPUT: ' + name in str(failure.value)


def test_import_preflight_failure_never_launches_pytest(synthetic_inputs, monkeypatch, capsys):
    manifest, source, archive = synthetic_inputs
    sources, raw, retained = runner.verified_inputs(manifest, source, archive)
    calls = []
    def child(command, **kwargs):
        calls.append(command)
        assert command[-1] == runner.IMPORT_PREFLIGHT
        return SimpleNamespace(returncode=1)
    monkeypatch.setattr(runner.subprocess, 'run', child)
    assert runner.run(manifest, sources, raw, ['test_owner_handoff.py'], retained) == 2
    assert len(calls) == 1
    assert 'BLOCKED/NOT_RUN: HISTORICAL_PYTHON_IMPORTS' in capsys.readouterr().err
