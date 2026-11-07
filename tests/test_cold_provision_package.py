import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import threading
import zipfile
from http.server import ThreadingHTTPServer

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_packager_rejects_uncommitted_source(tmp_path, monkeypatch):
    from scripts import package_cold_provision as builder
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    (tmp_path/'untracked').write_text('not an accepted checkpoint')
    monkeypatch.setattr(builder, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='clean committed source'):
        builder.build(tmp_path/'output', tmp_path/'not-a-compiler')
    assert not (tmp_path/'output').exists()


@pytest.fixture
def packaged_authority(tmp_path):
    package = os.environ.get('FC_ENTRY_PACKAGE')
    binary = os.environ.get('FC_ENTRY_TEST_BINARY')
    if not package or not binary:
        pytest.skip('requires built entry package and bounded Go lifecycle test binary')
    spec = importlib.util.spec_from_file_location('entry_fixture', ROOT/'tests/fixtures/mobile_bootstrap/provision_backend.py')
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    fixture.prepare(tmp_path)
    (tmp_path/'gateway.pem').write_text(json.loads((tmp_path/'gateway.json').read_text())['certificate'])
    return tmp_path, Path(package), Path(binary)


def test_closed_package_custody_configuration_and_lifecycle(packaged_authority, monkeypatch):
    root, package, binary = packaged_authority
    manifest = json.loads((package/'manifest.json').read_text())
    for name, expected in manifest['artifacts'].items():
        assert hashlib.sha256((package/name).read_bytes()).hexdigest() == expected
    with zipfile.ZipFile(package/'cold-provision-locator.pyz') as archive:
        assert not any('fixture' in name or name.endswith(('.key', '.db', '.private')) for name in archive.namelist())
    before = {name: (root/name).read_bytes() for name in ('access.db', 'issuer.key', 'admission.json')}
    command = [str(package/'cold-provision-entry'), '--check', '--profile', str(root/'gateway.json'),
               '--anchor', str(root/'anchor.pub'), '--state', str(root/'not-created'), '--node', 'nl-amsterdam-1']
    result = subprocess.run(command, cwd=root, capture_output=True, timeout=5)
    assert result.returncode == 0 and b'CONFIGURATION_VALID_NO_PROVIDER_CALL' in result.stdout
    assert not (root/'not-created').exists()
    for extra in (['--backend', '8.8.8.8:53'], ['--duration', '8m'], ['--node', 'unknown']):
        result = subprocess.run(command+extra, cwd=root, capture_output=True, timeout=5)
        assert result.returncode != 0 and result.stderr == b'ENTRY_CONFIGURATION_REJECTED\n'
    (root/'gateway.json').chmod(0o666)
    assert subprocess.run(command, cwd=root, capture_output=True, timeout=5).returncode != 0
    (root/'gateway.json').chmod(0o600)
    env = dict(os.environ, FC_ENTRY_TEST_FIXTURE=str(root), FC_ENTRY_PACKAGE=str(package))
    result = subprocess.run([str(binary), '-test.v', '-test.run=^TestPackagedIssuerLifecycle$', '-test.timeout=50s'],
                            cwd=root, env=env, capture_output=True, timeout=55)
    assert result.returncode == 0, result.stdout.decode()+result.stderr.decode()
    assert b'PASS: TestPackagedIssuerLifecycle/ready' in result.stdout
    locator = root/'ready/locator.json'
    digest = hashlib.sha256(locator.read_bytes()).hexdigest()
    assert json.loads((root/'ready/ready.json').read_text())['locator_sha256'] == digest
    issue = ['python3', str(package/'cold-provision-locator.pyz'), '--database', str(root/'access.db'),
             '--material', str(root), '--certificate', str(root/'gateway.pem'), '--state', str(root/'ready'),
             '--node', 'nl-amsterdam-1', '--sequence', '2']
    result = subprocess.run(issue, cwd=root, capture_output=True, timeout=10)
    assert result.returncode != 0 and b'LOCATOR_ISSUANCE_REJECTED' in result.stderr
    assert hashlib.sha256(locator.read_bytes()).hexdigest() == digest
    for name, raw in before.items():
        assert (root/name).read_bytes() == raw, name
    (root/'directory.json').write_bytes((root/'ready/seed.json').read_bytes())
    spec = importlib.util.spec_from_file_location('entry_http', ROOT/'deploy/friends/access-api.py')
    handler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(handler)
    from control.friends.access import Access
    handler.ROOT, handler.access = root, Access(root/'access.db')
    monkeypatch.setenv('FC_FRIENDS_RESTRICTED_DIR', str(root))
    with ThreadingHTTPServer(('127.0.0.1', 0), handler.Handler) as server:
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            env['FC_ENTRY_TEST_BACKEND'] = '127.0.0.1:'+str(server.server_port)
            result = subprocess.run([str(binary), '-test.v', '-test.run=^TestExistingAuthorityHandlers$', '-test.timeout=15s'],
                                    cwd=root, env=env, capture_output=True, timeout=20)
            assert result.returncode == 0, result.stdout.decode()+result.stderr.decode()
        finally:
            server.shutdown()
            thread.join(2)
        assert not thread.is_alive()


def test_entry_reuses_existing_rpc_and_has_no_issuer_custody():
    source = (ROOT/'carrier/cmd/cold-provision-entry/main.go').read_text()
    assert 'coldprovision.Run(' in source
    backend = (ROOT/'carrier/cmd/cold-provision-entry/backend.go').read_text()
    assert 'coldprovision.LoopbackBackend(' in backend and 'Proxy: nil' in backend
    assert 'issuer.key' not in source and 'ListenAndServe' not in source
    unit = (ROOT/'deploy/friends/restricted/cold-provision-entry@.service').read_text()
    assert 'Restart=no' in unit and 'RuntimeMaxSec=440' in unit and 'TimeoutStopSec=20' in unit
    assert '[Install]' not in unit
