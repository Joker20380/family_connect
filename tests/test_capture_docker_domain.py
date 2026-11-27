import json
import os
from pathlib import Path

import pytest

from control.capture_docker_domain import DomainAdmission
from test_capture_docker import FakeEngine, request


class EnrolledEngine(FakeEngine):
    def __init__(self, root):
        super().__init__(root)
        self.host = dict(CgroupParent='fcfixture.slice', RestartPolicy=dict(Name='no'), CgroupnsMode='private')

    def get(self, route):
        if route == '/containers/json?all=1':
            return [dict(Id='protected')]
        result = super().get(route)
        if route.startswith('/containers/'):
            result['HostConfig'] = self.host.copy()
        return result


@pytest.fixture
def policy(tmp_path):
    (tmp_path / 'protected').mkdir()
    (tmp_path / 'neighbor').mkdir()
    pidfile = tmp_path / 'pid'
    pidfile.write_text(str(os.getpid()))
    config = tmp_path / 'daemon.json'
    config.write_text('{"authorization-plugins":["domain"]}')
    config.chmod(0o600)
    return DomainAdmission(EnrolledEngine(tmp_path), [tmp_path / 'protected'], pidfile, tmp_path / 'journal',
        config=config, plugin='domain', parent='fcfixture.slice')


@pytest.mark.parametrize('field,value', [('CgroupParent', ''), ('RestartPolicy', dict(Name='always')),
    ('CgroupnsMode', 'host'), ('PidMode', 'host')])
def test_unenrolled_resource_refuses_before_launch(policy, field, value):
    host = {**policy.scope.engine.host, field: value, 'Binds': [str(policy.scope.paths[0]) + ':/data']}
    assert not policy.request(request('/containers/create', dict(HostConfig=host)))['Allow']


def test_correct_enrollment_and_late_restart_policy(policy):
    host = {**policy.scope.engine.host, 'Binds': [str(policy.scope.paths[0]) + ':/data']}
    assert policy.request(request('/containers/create', dict(HostConfig=host)))['Allow']
    assert not policy.request(request('/containers/protected/update',
        dict(RestartPolicy=dict(Name='unless-stopped'))))['Allow']
    assert not policy.request(request('/containers/protected/exec', dict(Privileged=True)))['Allow']


def test_prior_unenrolled_container_terminalizes_close(policy):
    policy.scope.engine.host['CgroupParent'] = ''
    with pytest.raises(ValueError, match='DOCKER_DOMAIN_NOT_ENROLLED'):
        policy.control('CLOSE')
    assert policy.phase == 'FAILED'
    assert json.loads((policy.journal / 'failed').read_bytes())['reason'] == 'DOCKER_DOMAIN_NOT_ENROLLED'


@pytest.mark.parametrize('path', ['/sys/fs/cgroup', '/proc', '/dev', 'config', 'journal'])
def test_indirect_control_mount_is_not_an_unprotected_neighbor(policy, path):
    source = policy.config if path == 'config' else policy.journal if path == 'journal' else Path(path)
    host = {**policy.scope.engine.host, 'Binds': [str(policy.scope.paths[0]) + ':/data', str(source) + ':/escape']}
    assert not policy.request(request('/containers/create', dict(HostConfig=host)))['Allow']


def test_old_exec_without_privilege_proof_refuses(policy):
    assert not policy.request(request('/exec/old/start', dict(Detach=True)))['Allow']


def test_lab_empty_readback_is_retained_and_never_ready(monkeypatch):
    from fixtures.docker_authz_checks import API
    reader = API('/not-contacted')
    monkeypatch.setattr(reader, 'call', lambda *args: (200, b''))
    with pytest.raises(AssertionError, match='LAB_EMPTY_JSON_RESPONSE'):
        reader.json('GET', '/version')
    assert reader.observations[0]['category'] == 'EMPTY_JSON_RESPONSE'


def test_failed_release_record_cannot_become_cached_success(tmp_path, monkeypatch):
    from control import capture_docker_domain as module
    from types import SimpleNamespace
    boundary = object.__new__(module.ExecutorBoundary)
    boundary.journal, boundary.lease, boundary.failed, boundary.released = tmp_path, 'lease', False, None
    boundary.check = lambda: 'lease'
    boundary.domain = SimpleNamespace(__exit__=lambda *args: None)
    boundary.client = SimpleNamespace(command=lambda command: dict(phase='RELEASED'))
    original = module.record
    def failing(root, name, value):
        if name == 'released.json':
            raise OSError('DISPOSABLE_RECEIPT_FAILURE')
        return original(root, name, value)
    monkeypatch.setattr(module, 'record', failing)
    with pytest.raises(OSError, match='DISPOSABLE_RECEIPT_FAILURE'):
        boundary.release()
    assert boundary.failed and boundary.released is None
    assert json.loads((tmp_path / 'failed.json').read_bytes())['reason'] == 'DISPOSABLE_RECEIPT_FAILURE'
