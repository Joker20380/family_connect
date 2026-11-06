import hashlib
import json
import shutil
import tarfile
import zipfile

import pytest

from scripts import ci_release_fixtures as fixtures


def test_public_export_restores_exact_commit_without_host_git_or_untracked_files(tmp_path, monkeypatch):
    source = tmp_path / 'source'
    source.mkdir()
    monkeypatch.setattr(fixtures, 'ROOT', source)
    fixtures.git('init', '--quiet')
    (source / 'public.txt').write_text('public source\n')
    fixtures.git('add', 'public.txt')
    fixtures.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')
    historical = fixtures.git('rev-parse', 'HEAD').decode().strip()
    (source / 'public.txt').write_text('current public source\n')
    fixtures.git('add', 'public.txt')
    fixtures.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'current')
    head = fixtures.git('rev-parse', 'HEAD').decode().strip()
    monkeypatch.setattr(fixtures, 'HISTORICAL', historical)
    monkeypatch.setattr(fixtures, 'REQUIRED_COMMITS', (historical,))
    private = source / 'state-private'
    private.mkdir()
    (private / 'token.key').write_text('not-for-export')
    fixtures.git('config', 'http.extraHeader', 'private-marker')
    output = tmp_path / 'export'
    fixtures.export(output)
    with tarfile.open(output / 'current.tar') as archive:
        assert archive.getnames() == ['public.txt']
    restored = tmp_path / 'restored'
    fixtures.extract((output / 'current.tar').read_bytes(), restored)
    monkeypatch.setattr(fixtures, 'ROOT', restored)
    fixtures.restore_git(output / 'current.commit', output / 'tracked.paths', output / 'fixture-objects.pack')
    assert fixtures.git('rev-parse', 'HEAD').decode().strip() == head
    assert fixtures.git('archive', 'HEAD') == (output / 'current.tar').read_bytes()
    assert fixtures.git('show', historical + ':public.txt') == b'public source\n'
    assert fixtures.git('archive', historical) == (output / 'historical.tar').read_bytes()
    assert b'private-marker' not in (restored / '.git/config').read_bytes()
    with pytest.raises(ValueError, match='replace Git'):
        fixtures.restore_git(output / 'current.commit', output / 'tracked.paths')


def test_required_git_objects_cover_the_real_native_and_renewal_inputs():
    from scripts.package_credential_renewal import ACCEPTED_API_SOURCE
    from scripts.stage_linux_native import reference
    assert set(fixtures.REQUIRED_COMMITS) == {fixtures.HISTORICAL, ACCEPTED_API_SOURCE, reference()['commit']}


def test_fixture_environment_rejects_modified_artifact_or_commit(tmp_path, monkeypatch):
    files = {}
    for name in ('http/friends-http.pyz', 'sync/restricted-sync.pyz', 'historical-http/friends-http.pyz', 'readiness/candidate-readiness.pyz', 'accepted-snapshot.pyz', 'credential-renewal.tar.gz'):
        path = tmp_path / name
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(name.encode())
        files[name] = fixtures.digest(path)
    monkeypatch.setattr(fixtures, 'HISTORICAL_SHA', files['historical-http/friends-http.pyz'])
    monkeypatch.setattr(fixtures, 'SNAPSHOT_SHA', files['accepted-snapshot.pyz'])
    monkeypatch.setattr(fixtures, 'git', lambda *args: b'fixture-head\n')
    (tmp_path / 'inventory.json').write_text(json.dumps(dict(source_commit='fixture-head', files=files)))
    environment = fixtures.environment(tmp_path, tmp_path / 'go', tmp_path / 'nginx')
    assert environment['FC_TEST_HTTP_SHA256'] == files['http/friends-http.pyz']
    assert environment['FC_TEST_HISTORICAL_HTTP_ARTIFACT'] != environment['FC_TEST_HTTP_ARTIFACT']
    assert environment['FC_TEST_SNAPSHOT_ARCHIVE'] == str(tmp_path / 'accepted-snapshot.pyz')
    assert environment['FC_TEST_RENEWAL_PACKAGE'] == str(tmp_path / 'credential-renewal.tar.gz')
    (tmp_path / 'http/friends-http.pyz').write_bytes(b'changed')
    with pytest.raises(ValueError, match='inventory mismatch'):
        fixtures.environment(tmp_path, tmp_path / 'go', tmp_path / 'nginx')
    monkeypatch.setattr(fixtures, 'git', lambda *args: b'other-head\n')
    with pytest.raises(ValueError, match='commit mismatch'):
        fixtures.environment(tmp_path, tmp_path / 'go', tmp_path / 'nginx')


def test_sync_fixture_normalization_is_deterministic(tmp_path):
    results = []
    for year in (2000, 2026):
        path = tmp_path / (str(year) + '.pyz')
        with zipfile.ZipFile(path, 'w') as archive:
            entry = zipfile.ZipInfo('module.py', (year, 1, 1, 0, 0, 0))
            archive.writestr(entry, b'VALUE = 1\n')
        fixtures.normalize_zip(path)
        results.append(hashlib.sha256(path.read_bytes()).hexdigest())
    assert results[0] == results[1]


def test_historical_http_uses_pinned_builder_not_current_ingress_inputs(tmp_path):
    source = tmp_path / 'historical'
    fixtures.extract(fixtures.git('archive', fixtures.HISTORICAL), source)
    assert not (source / 'deploy/friends/subscription-location.conf').exists()
    assert not (source / 'deploy/friends/gateway-selection-location.conf').exists()
    output = tmp_path / 'bundle'
    fixtures.historical_http(output, source)
    assert fixtures.digest(output / 'friends-http.pyz') == fixtures.HISTORICAL_SHA
    with zipfile.ZipFile(output / 'friends-http.pyz') as archive:
        assert 'control/friends/subscription.py' not in archive.namelist()


def test_retained_snapshot_reproduces_original_archive_and_rejects_tampering(tmp_path, monkeypatch):
    output = tmp_path / 'accepted.pyz'
    fixtures.historical_snapshot(output)
    assert fixtures.digest(output) == '0120dad028ead353b8b83a600538f3e578b2b46ddf871bf16e97529f9449f450'
    assert output.stat().st_size == 26854
    with zipfile.ZipFile(output) as archive:
        assert len(archive.namelist()) == 18
    source = fixtures.ROOT
    target = tmp_path / 'source'
    shutil.copytree(source / 'tests/fixtures/accepted_snapshot', target / 'tests/fixtures/accepted_snapshot')
    monkeypatch.setattr(fixtures, 'ROOT', target)
    original_git = fixtures.git
    monkeypatch.setattr(fixtures, 'git', lambda *args: original_git(*args, source=source))
    member = target / 'tests/fixtures/accepted_snapshot/restricted_sync.py.txt'
    member.write_bytes(member.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='Snapshot member mismatch'):
        fixtures.historical_snapshot(tmp_path / 'tampered.pyz')


def test_ci_renewal_package_uses_real_unbound_builder_and_accepted_api(tmp_path):
    from scripts.package_credential_renewal import build, ACCEPTED_API_SOURCE
    package = tmp_path / 'renewal.tar.gz'
    result = build(package, 'HEAD')
    assert result['binding'] == 'unbound'
    with tarfile.open(package) as archive:
        manifest = json.load(archive.extractfile('source-manifest.json'))
        assert manifest['accepted_api_source_commit'] == ACCEPTED_API_SOURCE
        assert manifest['production_configuration'] == 'absent'
        assert manifest['operation_permit'] is None
        assert hashlib.sha256(archive.extractfile('api.pyz').read()).hexdigest() == manifest['api_sha256']
