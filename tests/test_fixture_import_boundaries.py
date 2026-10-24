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
    sources, raw = runner.verified_inputs(manifest, source, archive)
    (source / 'fixture.py').write_bytes(b'changed after verification')
    archive.write_bytes(b'changed after verification')
    manifest.update(source_commit='synthetic', tests={'test_fixture.py': []})
    calls = []

    def child(command, cwd, env, timeout):
        calls.append(command)
        assert command[:4] == [sys.executable, '-I', '-B', '-c']
        assert cwd != ROOT and (cwd / 'fixture.py').read_bytes() == b'fixture'
        assert (cwd / 'state-client-build/mesh-perf-3b/api/control/module.py').read_bytes() == b'module'
        assert command[-1] == str(cwd / runner.TEST_DIRECTORY / 'test_fixture.py')
        assert 'PYTHONPATH' not in env and 'PYTEST_ADDOPTS' not in env
        assert not any(key.startswith(('FC_', 'SSH_')) for key in env)
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(runner.subprocess, 'run', child)
    assert runner.run(manifest, sources, raw, ['test_fixture.py']) == 7
    assert len(calls) == 1
