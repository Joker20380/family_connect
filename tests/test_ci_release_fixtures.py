import hashlib
import json
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
    head = fixtures.git('rev-parse', 'HEAD').decode().strip()
    monkeypatch.setattr(fixtures, 'HISTORICAL', head)
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
    fixtures.restore_git(output / 'current.commit', output / 'tracked.paths')
    assert fixtures.git('rev-parse', 'HEAD').decode().strip() == head
    assert fixtures.git('archive', 'HEAD') == (output / 'current.tar').read_bytes()
    assert b'private-marker' not in (restored / '.git/config').read_bytes()
    with pytest.raises(ValueError, match='replace Git'):
        fixtures.restore_git(output / 'current.commit', output / 'tracked.paths')


def test_fixture_environment_rejects_modified_artifact_or_commit(tmp_path, monkeypatch):
    files = {}
    for name in ('http/friends-http.pyz', 'sync/restricted-sync.pyz', 'historical-http/friends-http.pyz', 'readiness/candidate-readiness.pyz'):
        path = tmp_path / name
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(name.encode())
        files[name] = fixtures.digest(path)
    monkeypatch.setattr(fixtures, 'HISTORICAL_SHA', files['historical-http/friends-http.pyz'])
    monkeypatch.setattr(fixtures, 'git', lambda *args: b'fixture-head\n')
    (tmp_path / 'inventory.json').write_text(json.dumps(dict(source_commit='fixture-head', files=files)))
    environment = fixtures.environment(tmp_path, tmp_path / 'go', tmp_path / 'nginx')
    assert environment['FC_TEST_HTTP_SHA256'] == files['http/friends-http.pyz']
    assert environment['FC_TEST_HISTORICAL_HTTP_ARTIFACT'] != environment['FC_TEST_HTTP_ARTIFACT']
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
