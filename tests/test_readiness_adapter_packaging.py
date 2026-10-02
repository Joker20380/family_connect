import ast
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import zipfile

import pytest

from control.friends.readiness_fixture import listener
from control.friends.readiness_adapter import ExistingProcess
from scripts import friends_http_transition as transition
from scripts import friends_readiness_adapter as bootstrap
from scripts.package_friends_readiness import ARCHIVE, CONTRACT, ROOT, build

HTTP_SHA = '460e75205eb9baff313dc7dd963cdb7bceddf2d1e13405a71686f9ec6c976d71'
SYNC_SHA = '9d965b955cbd5375c82adadb3f25736d1cca3fe86ab477ea73269ef1499a5a2d'
MAPPING = json.loads((ROOT / CONTRACT / 'readiness-runtime-files.json').read_bytes())


@pytest.fixture(scope='module')
def packaged(tmp_path_factory):
    base = tmp_path_factory.mktemp('readiness-layout')
    assert not base.is_relative_to(ROOT)
    output = base / 'opt/apps/family_connect/http-operator'
    accepted = Path(os.environ['FC_TEST_HTTP_ARTIFACT']) / 'friends-http.pyz'
    assert hashlib.sha256(accepted.read_bytes()).hexdigest() == HTTP_SHA
    candidate = output.parent / 'http-candidate'
    candidate.mkdir(parents=True)
    shutil.copyfile(accepted, candidate / accepted.name)
    final = os.environ.get('FC_TEST_READINESS_ARTIFACT')
    if final:
        shutil.copytree(final, output)
    else:
        build(output, ROOT, 'test-worktree-not-release', Path(os.environ['FC_TEST_GO']))
    return output


def configuration(packaged):
    return dict(version=1, mode='fixture', http_artifact=str(packaged.parent / 'http-candidate/friends-http.pyz'),
                http_sha256=HTTP_SHA)


def invoke(packaged, tmp_path, config=None, check=False):
    config_file = tmp_path / 'config.json'
    config_file.write_text(json.dumps(configuration(packaged) if config is None else config))
    config_file.chmod(0o600)
    evidence = tmp_path / 'evidence'
    command = [sys.executable, '-I', str(packaged / ARCHIVE), '--config', str(config_file), '--evidence', str(evidence)]
    if check:
        command.append('--check')
    environment = dict(PATH=os.defpath, HOME=str(tmp_path), PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run(command, cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=60)
    receipt = json.loads((evidence / 'result.json').read_bytes())
    assert not result.stderr
    assert receipt['isolated'] is True
    assert str(ROOT) not in receipt['search_roots']
    assert (evidence / 'result.json').stat().st_mode & 0o777 == 0o600
    return result, receipt, evidence


def records(evidence):
    return [json.loads(path.read_bytes()) for path in sorted((evidence / 'probes').glob('*.json'))]


def test_attempt13_import_boundary_reproduced_outside_checkout(packaged, tmp_path):
    archive = configuration(packaged)['http_artifact']
    code = '''import contextlib,io,json,runpy,sys
archive=sys.argv[1]
sys.argv=[archive,'--help']
with contextlib.redirect_stdout(io.StringIO()):
    try: runpy.run_path(archive,run_name='__main__')
    except SystemExit as error: assert error.code == 0
assert archive not in sys.path
from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,NoEncryption
from device_identity.device import DeviceIdentity
try:
    from control.friends.access import Access
    from control.friends.restricted import RestrictedReadiness,DOMAIN,migrate,iso,utc
except ModuleNotFoundError as error:
    trace=error.__traceback__
    while trace.tb_next: trace=trace.tb_next
    print(json.dumps(dict(missing=error.name,importer=trace.tb_frame.f_globals['__name__'],line=trace.tb_lineno)))
else: raise AssertionError('Expected original failure')
'''
    result = subprocess.run([sys.executable, '-I', '-c', code, archive], cwd=tmp_path,
                            capture_output=True, text=True, check=True, timeout=20)
    assert json.loads(result.stdout) == dict(missing='provisioning', importer='control.friends.restricted', line=21)
    with zipfile.ZipFile(archive) as original:
        assert 'provisioning/friends_catalog.py' in original.namelist()


def test_startup_and_config_from_closed_tree(packaged, tmp_path):
    result, receipt, _ = invoke(packaged, tmp_path, check=True)
    assert result.returncode == 0, receipt
    assert receipt['passed'] and receipt['step'] == 'complete'
    assert receipt['runtime_versions']['cryptography'] == '46.0.7'


@pytest.mark.parametrize('removed', list(MAPPING))
def test_each_manifest_dependency_missing_fails(packaged, tmp_path, removed):
    damaged = tmp_path / 'damaged'
    shutil.copytree(packaged, damaged)
    with zipfile.ZipFile(packaged / ARCHIVE) as original, zipfile.ZipFile(damaged / ARCHIVE, 'w') as archive:
        for entry in original.infolist():
            if entry.filename != removed:
                archive.writestr(entry, original.read(entry))
    if removed == '__main__.py':
        result = subprocess.run([sys.executable, '-I', str(damaged / ARCHIVE)], cwd=tmp_path,
                                capture_output=True, timeout=10)
        assert result.returncode != 0
    else:
        result, receipt, _ = invoke(damaged, tmp_path, config=configuration(packaged), check=True)
        assert result.returncode == 1 and not receipt['passed']
        assert receipt['exception_class'] in ('ModuleNotFoundError', 'ImportError', 'KeyError')


def test_proven_missing_package_receipt(packaged, tmp_path):
    damaged = tmp_path / 'missing-package'
    shutil.copytree(packaged, damaged)
    with zipfile.ZipFile(packaged / ARCHIVE) as original, zipfile.ZipFile(damaged / ARCHIVE, 'w') as archive:
        for entry in original.infolist():
            if not entry.filename.startswith('provisioning/'):
                archive.writestr(entry, original.read(entry))
    result, receipt, _ = invoke(damaged, tmp_path, config=configuration(packaged), check=True)
    assert result.returncode == 1
    assert receipt['step'] == 'runtime_import'
    assert receipt['exception_class'] == 'ModuleNotFoundError'
    assert receipt['missing_module'] == 'provisioning'
    assert receipt['importing_module'] == 'control.friends.restricted'
    assert receipt['frames'][-1]['file'] == 'artifact/control/friends/restricted.py'
    assert receipt['artifact_sha256'] == hashlib.sha256((damaged / ARCHIVE).read_bytes()).hexdigest()
    assert receipt['argv_shape'][4] == '<config>'


def test_controlled_bg_matrix(packaged, tmp_path):
    result, receipt, evidence = invoke(packaged, tmp_path)
    assert result.returncode == 0, receipt
    assert receipt['owner_product_ready'] is False
    probes = [record for record in records(evidence) if 'status' in record]
    assert [record['status'] for record in probes] == [400, 400, 400, 403, 200, 200]
    assert all(record['receipt_class'] == 'server_contract_fixture' for record in probes)
    assert records(evidence)[-1]['event'] == 'controlled_FG'
    assert records(evidence)[-1]['passed']


def test_exact_candidate_mode_with_local_fixture_only(packaged, tmp_path):
    config = configuration(packaged)
    sync = Path(os.environ['FC_TEST_SYNC_ARTIFACT']) / 'restricted-sync.pyz'
    assert hashlib.sha256(sync.read_bytes()).hexdigest() == SYNC_SHA
    with listener(config['http_artifact'], port=18086) as fixture:
        for name in ('sync.key', 'known_hosts'):
            (fixture['directory'] / name).write_text('offline-test-placeholder')
            (fixture['directory'] / name).chmod(0o600)
        config.update(mode='candidate', candidate=dict(port=18086, generation='local-fixture-only',
                      pid=fixture['process'].pid, start=transition.process_start(fixture['process'].pid),
                      non_canaries=fixture['identities']['non_canary']),
                      authority=dict(runtime=str(sync), sha256=SYNC_SHA,
                      database=str(fixture['directory'] / 'access.db'), material=str(fixture['directory']),
                      host='186.246.45.246', ssh_key=str(fixture['directory'] / 'sync.key'),
                      known_hosts=str(fixture['directory'] / 'known_hosts')))
        result, receipt, evidence = invoke(packaged, tmp_path, config=config)
        candidate = transition.Candidate(18086, 'local-fixture-only', config['http_artifact'], HTTP_SHA)
        candidate.capture(ExistingProcess(fixture['process'].pid))
        with_evidence = transition.Evidence(tmp_path / 'callback', 'local-only')
        try:
            assert candidate.ready_with_adapter(with_evidence, python=sys.executable, runtime=packaged / ARCHIVE,
                       sha256=hashlib.sha256((packaged / ARCHIVE).read_bytes()).hexdigest(),
                       config=tmp_path / 'config.json', directory=tmp_path / 'callback-adapter')
            assert candidate.direct_pass and candidate.upstream() == 'http://127.0.0.1:18086'
            assert not candidate.external_pass
        finally:
            with_evidence.close()
    assert result.returncode == 0, receipt
    assert receipt['state'] == 'SERVER_CANDIDATE_READY' and not receipt['owner_product_ready']
    probes = [record for record in records(evidence) if 'status' in record]
    assert [record['status'] for record in probes] == [400, 400, 400, 403, 200, 200, 400, 400, 400, 403]
    assert all(record.get('path') != '/status/server-load.json' for record in probes)
    assert any(record.get('event') == 'current_authority' and record['passed'] for record in records(evidence))


def test_invalid_config_is_durably_redacted(packaged, tmp_path):
    config = dict(configuration(packaged), credential='private-proof-sentinel')
    result, receipt, evidence = invoke(packaged, tmp_path, config=config, check=True)
    assert result.returncode == 1 and receipt['step'] == 'configuration'
    assert 'private-proof-sentinel' not in (evidence / 'result.json').read_text() + result.stdout


def test_existing_evidence_is_not_reused(packaged, tmp_path):
    invoke(packaged, tmp_path, check=True)
    original = (tmp_path / 'evidence/result.json').read_bytes()
    result = subprocess.run([sys.executable, '-I', str(packaged / ARCHIVE), '--config', str(tmp_path / 'config.json'),
                             '--evidence', str(tmp_path / 'evidence')], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 2
    assert (tmp_path / 'evidence/result.json').read_bytes() == original


def test_unknown_arguments_do_not_echo_secrets(packaged, tmp_path):
    evidence = tmp_path / 'safe'
    result = subprocess.run([sys.executable, '-I', str(packaged / ARCHIVE), '--config', str(tmp_path / 'config'),
                             '--evidence', str(evidence), '--private-proof', 'secret-sentinel'],
                            cwd=tmp_path, capture_output=True, text=True)
    receipt = (evidence / 'result.json').read_text()
    assert result.returncode == 1 and json.loads(receipt)['step'] == 'arguments'
    assert 'secret-sentinel' not in result.stdout + result.stderr + receipt


def test_receipt_storage_failure_cannot_report_success(packaged, tmp_path):
    invalid = tmp_path / 'not-a-directory'
    invalid.write_bytes(b'preserved')
    result = subprocess.run([sys.executable, '-I', str(packaged / ARCHIVE), '--config', str(tmp_path / 'config'),
                             '--evidence', str(invalid)], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 2
    assert json.loads(result.stdout) == dict(passed=False, classification='receipt_storage_failed')
    assert invalid.read_bytes() == b'preserved'


@pytest.mark.parametrize('failure', ['timeout', 'generation', 'nonzero', 'missing_receipt'])
def test_callback_failure_never_sets_direct_pass(tmp_path, monkeypatch, failure):
    archive = tmp_path / 'adapter.pyz'
    archive.write_bytes(b'fixture')
    candidate = transition.Candidate(18086, 'local-only', archive, hashlib.sha256(b'fixture').hexdigest())
    candidate.process, candidate.start = ExistingProcess(os.getpid()), 'test-start'
    monkeypatch.setattr(candidate, 'verify', lambda: None)
    directory = tmp_path / 'adapter-result'
    def run(*args, **kwargs):
        if failure == 'timeout':
            raise subprocess.TimeoutExpired('redacted', 90)
        directory.mkdir(mode=0o700)
        receipt = dict(passed=True, isolated=True, step='complete', state='SERVER_CANDIDATE_READY',
                       owner_product_ready=False, artifact_sha256=candidate.sha256,
                       candidate=dict(port=18086, generation='wrong' if failure == 'generation' else 'local-only',
                                      pid=os.getpid(), start='test-start', http_sha256=candidate.sha256))
        if failure != 'missing_receipt':
            (directory / 'result.json').write_text(json.dumps(receipt))
        return subprocess.CompletedProcess([], 1 if failure == 'nonzero' else 0, b'', b'')
    monkeypatch.setattr(subprocess, 'run', run)
    evidence = transition.Evidence(tmp_path / 'callback', 'local-only')
    try:
        with pytest.raises((transition.ProbeFailed, subprocess.TimeoutExpired, FileNotFoundError)):
            candidate.ready_with_adapter(evidence, python=sys.executable, runtime=archive, sha256=candidate.sha256,
                                         config=tmp_path / 'config.json', directory=directory)
        assert not candidate.direct_pass
        assert not json.loads(next((tmp_path / 'callback').glob('*.json')).read_bytes())['passed']
    finally:
        evidence.close()


def test_exception_redaction_and_durable_persistence(tmp_path, monkeypatch):
    directory = tmp_path / 'receipts'
    directory.mkdir(mode=0o700)
    try:
        raise ModuleNotFoundError('secret-proof-and-response', name='private_secret_identity')
    except ModuleNotFoundError as error:
        receipt = bootstrap.failure_details(error, tmp_path / ARCHIVE)
    assert receipt['missing_module'] == 'unknown'
    assert 'secret' not in json.dumps(receipt)
    calls = []
    real = os.fsync
    def sync(descriptor):
        calls.append(descriptor)
        real(descriptor)
    monkeypatch.setattr(os, 'fsync', sync)
    bootstrap.persist(directory, receipt)
    assert len(calls) == 2
    with pytest.raises(FileExistsError):
        bootstrap.persist(directory, receipt)


def test_runtime_source_and_secret_guards(packaged):
    with zipfile.ZipFile(packaged / ARCHIVE) as archive:
        manifest = json.loads(archive.read('adapter-inventory.json'))
        assert len(manifest['sources']) == len(MAPPING)
        for name, digest in manifest['files'].items():
            raw = archive.read(name)
            assert hashlib.sha256(raw).hexdigest() == digest
            assert b'-----BEGIN PRIVATE KEY-----' not in raw
            assert b'provider.env' not in raw and b'ya29.' not in raw
            if name.endswith('.py'):
                tree = ast.parse(raw)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        assert not (node.module or '').startswith(('test_', 'tests.'))
                assert b'sys.path.insert' not in raw and b'sys.path.append' not in raw
        assert not any(name.endswith(('.key', '.env', '.db', '.pem')) for name in archive.namelist())


def test_repeat_build_is_deterministic(tmp_path):
    first = build(tmp_path / 'first', ROOT, 'test-determinism', Path(os.environ['FC_TEST_GO']))
    second = build(tmp_path / 'second', ROOT, 'test-determinism', Path(os.environ['FC_TEST_GO']))
    assert first == second
    for name in (ARCHIVE, 'readiness-delivery-check', 'readiness.lock', 'provenance.json'):
        assert (tmp_path / 'first' / name).read_bytes() == (tmp_path / 'second' / name).read_bytes()


def test_clean_committed_export_build(tmp_path):
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    raw = subprocess.check_output(['git', 'archive', head], cwd=ROOT)
    source = tmp_path / 'clean-export'
    source.mkdir()
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        archive.extractall(source, filter='data')
    report = build(tmp_path / 'bundle', source, head, Path(os.environ['FC_TEST_GO']))
    assert report['source_head'] == head
    assert len(report['sources']) == 13
