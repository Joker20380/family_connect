from pathlib import Path
import stat
from types import SimpleNamespace

import pytest

pytest.importorskip('psycopg')

from scripts.control_ha_replication_rehearsal import configuration, ReplicationRehearsal, TTL

IMAGE = 'sha256:' + 'a' * 64


@pytest.fixture
def rehearsal(tmp_path):
    return ReplicationRehearsal(tmp_path / 'new', tmp_path / 'etcd', IMAGE)


@pytest.mark.parametrize('image', ['latest', 'postgres:17', '', 'sha256:' + '0' * 63, None])
def test_mutable_or_invalid_image_refused_before_directory_creation(tmp_path, image):
    with pytest.raises(ValueError, match='LOCAL_IMAGE_ID_REQUIRED'):
        ReplicationRehearsal(tmp_path / 'new', tmp_path / 'etcd', image)
    assert not (tmp_path / 'new').exists()


def test_only_fresh_non_symlink_temporary_directory(tmp_path):
    with pytest.raises(FileExistsError):
        ReplicationRehearsal(tmp_path, tmp_path / 'etcd', IMAGE)
    linked = tmp_path / 'link'
    linked.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='REHEARSAL_SYMLINK'):
        ReplicationRehearsal(linked / 'new', tmp_path / 'etcd', IMAGE)
    with pytest.raises(ValueError, match='TEMPORARY_REHEARSAL_ONLY'):
        ReplicationRehearsal(Path('/not-temporary'), tmp_path / 'etcd', IMAGE)


def test_configuration_has_strict_durable_majority_and_no_failsafe():
    ports = [[12000 + index * 2, 12001 + index * 2] for index in range(3)]
    for index in range(3):
        config = configuration('token', index, ports, ['https://127.0.0.1:12345'], 'test-secret', 'test-replication')
        dcs = config['bootstrap']['dcs']
        assert dcs['synchronous_mode'] == 'quorum'
        assert dcs['synchronous_node_count'] == 1
        assert dcs['synchronous_mode_strict'] is True
        assert dcs['failsafe_mode'] is False
        assert dcs['maximum_lag_on_failover'] == 0 and dcs['check_timeline'] is True
        assert dcs['ttl'] == TTL >= dcs['loop_wait'] + 2 * dcs['retry_timeout']
        for setting in ('fsync', 'full_page_writes', 'synchronous_commit'):
            assert dcs['postgresql']['parameters'][setting] == 'on'
        assert config['postgresql']['listen'].startswith('127.0.0.1:')
        assert config['restapi']['listen'].startswith('127.0.0.1:')
        assert config['restapi']['authentication']['password'] == 'test-secret'
        assert config['etcd3']['protocol'] == 'https' and config['etcd3']['key'] == '/tmp/lab/client.key'
        assert config['postgresql']['data_dir'] == '/tmp/lab/data'
        assert all('0.0.0.0' not in rule for rule in config['bootstrap']['pg_hba'])


@pytest.mark.parametrize('action', [('kill', '--signal', 'KILL'), ('start',), ('rm', '--force', '--volumes')])
def test_node_actions_require_exact_ownership(rehearsal, monkeypatch, action):
    rehearsal.nodes[1] = 'b' * 64
    calls = []
    def docker(*arguments, **kwargs):
        calls.append(arguments)
        return 'different-owner'
    monkeypatch.setattr(rehearsal, 'docker', docker)
    with pytest.raises(ValueError, match='REHEARSAL_CONTAINER_OWNERSHIP'):
        rehearsal.node_action(1, *action)
    assert len(calls) == 1 and calls[0][0] == 'inspect'


def test_cleanup_recovers_lost_response_and_preserves_private_logs(rehearsal, monkeypatch):
    (rehearsal.root / 'node2.id').write_text('c' * 64)
    calls = []
    def docker(*arguments, **kwargs):
        calls.append(arguments)
        if arguments[0] == 'inspect':
            return rehearsal.token + ':2'
        return b'private logs' if kwargs.get('binary') else ''
    monkeypatch.setattr(rehearsal, 'docker', docker)
    rehearsal.__exit__()
    assert calls[-1] == ('rm', '--force', '--volumes', 'c' * 64)
    assert stat.S_IMODE((rehearsal.root / 'patroni2.log').stat().st_mode) == 0o600


def test_cleanup_wrong_owner_never_removes_container_but_stops_owned_etcd(rehearsal, monkeypatch):
    rehearsal.nodes[0] = 'a' * 64
    calls = []
    monkeypatch.setattr(rehearsal, 'docker', lambda *args, **kwargs: calls.append(args) or 'wrong-owner')
    stopped = []
    rehearsal.etcd = SimpleNamespace(__exit__=lambda *args: stopped.append(True))
    with pytest.raises(ValueError, match='OWNED_CLEANUP_FAILED'):
        rehearsal.__exit__()
    assert stopped == [True]
    assert len(calls) == 1 and calls[0][0] == 'inspect'


def test_unlabelled_image_refused_without_starting_children(rehearsal, monkeypatch):
    calls = []
    monkeypatch.setattr(rehearsal, 'docker', lambda *args, **kwargs: calls.append(args) or 'wrong-image')
    with pytest.raises(ValueError, match='REHEARSAL_IMAGE_REQUIRED'):
        rehearsal.__enter__()
    assert len(calls) == 1 and calls[0][:2] == ('image', 'inspect')
    assert rehearsal.etcd is None


def test_log_failure_still_removes_only_owned_container(rehearsal, monkeypatch):
    rehearsal.nodes[1] = 'd' * 64
    calls = []
    def docker(*arguments, **kwargs):
        calls.append(arguments)
        if arguments[0] == 'inspect':
            return rehearsal.token + ':1'
        if arguments[0] == 'logs':
            raise RuntimeError('synthetic log failure')
        return ''
    monkeypatch.setattr(rehearsal, 'docker', docker)
    with pytest.raises(ValueError, match='OWNED_CLEANUP_FAILED'):
        rehearsal.__exit__()
    assert calls[-1] == ('rm', '--force', '--volumes', 'd' * 64)


def test_unknown_rest_route_refused_without_network(rehearsal):
    with pytest.raises(ValueError, match='REHEARSAL_STATUS_ROUTE'):
        rehearsal.status(0, '/restart')
