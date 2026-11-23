from pathlib import Path
import stat
from types import SimpleNamespace

import pytest

from scripts.enrollment_postgres_rehearsal import Rehearsal


def test_rehearsal_refuses_reuse_and_symlink(tmp_path):
    with pytest.raises(FileExistsError):
        Rehearsal(tmp_path)
    linked = tmp_path / 'linked'
    linked.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='REHEARSAL_SYMLINK'):
        Rehearsal(linked / 'new')
    with pytest.raises(ValueError, match='TEMPORARY_REHEARSAL_ONLY'):
        Rehearsal(Path('/not-a-temporary-rehearsal'))


def test_docker_is_local_and_does_not_inherit_database_configuration(tmp_path, monkeypatch):
    monkeypatch.setenv('PGSERVICE', 'not-for-tests')
    monkeypatch.setenv('DOCKER_HOST', 'tcp://not-for-tests:2375')
    monkeypatch.setenv('FC_HA_PG_PORT', '5432')
    rehearsal = Rehearsal(tmp_path / 'rehearsal')
    calls = []

    def command(arguments, **settings):
        calls.append((arguments, settings))
        return SimpleNamespace(returncode=0, stdout=b'output', stderr=b'logs')

    monkeypatch.setattr('subprocess.run', command)
    assert rehearsal.docker('version') == 'output'
    assert rehearsal.docker('logs', 'synthetic', include_stderr=True) == 'outputlogs'
    assert calls[0][0][:3] == ['docker', '--host', 'unix:///var/run/docker.sock']
    assert not any(key.startswith(('PG', 'FC_HA_', 'DOCKER_')) for key in calls[0][1]['env'])
    assert stat.S_IMODE(rehearsal.root.stat().st_mode) == 0o700


def test_cleanup_refuses_any_container_with_wrong_ownership(tmp_path, monkeypatch):
    rehearsal = Rehearsal(tmp_path / 'rehearsal')
    rehearsal.container = 'a' * 64
    calls = []

    def command(*arguments, **settings):
        calls.append(arguments)
        return 'different-owner'

    monkeypatch.setattr(rehearsal, 'docker', command)
    with pytest.raises(ValueError, match='REHEARSAL_CONTAINER_OWNERSHIP'):
        rehearsal.__exit__(None, None, None)
    assert len(calls) == 1 and calls[0][0] == 'inspect'


def test_cleanup_can_recover_id_after_lost_run_response(tmp_path, monkeypatch):
    rehearsal = Rehearsal(tmp_path / 'rehearsal')
    (rehearsal.root / 'container.id').write_text('a' * 64)
    calls = []

    def command(*arguments, **settings):
        calls.append(arguments)
        return rehearsal.token if arguments[0] == 'inspect' else 'synthetic logs'

    monkeypatch.setattr(rehearsal, 'docker', command)
    rehearsal.__exit__(None, None, None)
    assert calls[-1] == ('rm', '--force', '--volumes', 'a' * 64)
    assert stat.S_IMODE((rehearsal.root / 'postgres.log').stat().st_mode) == 0o600


def test_docker_error_is_retained_privately_not_reprinted(tmp_path, monkeypatch):
    rehearsal = Rehearsal(tmp_path / 'rehearsal')
    monkeypatch.setattr('subprocess.run', lambda *args, **kwargs:
        SimpleNamespace(returncode=1, stdout=b'', stderr=b'synthetic diagnostic detail'))
    with pytest.raises(RuntimeError, match='private evidence retained') as failure:
        rehearsal.docker('version')
    assert 'synthetic diagnostic' not in str(failure.value)
    logs = list(rehearsal.root.glob('docker-error-*.log'))
    assert len(logs) == 1 and stat.S_IMODE(logs[0].stat().st_mode) == 0o600


def test_driver_pin_is_checked_before_starting_a_container(tmp_path, monkeypatch):
    rehearsal = Rehearsal(tmp_path / 'rehearsal')
    monkeypatch.setattr('importlib.metadata.version', lambda package: '0.0.0')
    with pytest.raises(ValueError, match='POSTGRES_DRIVER_PIN_MISMATCH'):
        with rehearsal:
            pytest.fail('Unpinned driver must not start a container')
    assert not list(rehearsal.root.iterdir())
