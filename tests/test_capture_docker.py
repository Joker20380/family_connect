import base64
import http.client
import json
import os
from pathlib import Path
import socket
import threading

import pytest

from control.capture_docker import Admission, Handler, Server


class FakeEngine:
    def __init__(self, root):
        self.root = root

    def get(self, route):
        if route.startswith('/containers/'):
            name = route.split('/')[2]
            assert name in ('protected', 'neighbor', 'renamed')
            return dict(HostConfig={}, Mounts=[dict(Type='bind', Source=str(
                self.root / ('neighbor' if name == 'neighbor' else 'protected')))])
        if route == '/exec/old/json':
            return dict(ContainerID='protected')
        if route == '/volumes/store':
            return dict(Driver='local', Mountpoint=str(self.root / 'protected'), Options={})
        raise ValueError('UNKNOWN_FIXTURE_ROUTE')


def request(route, body=None, method='POST'):
    return dict(RequestMethod=method, RequestURI='/v1.52' + route, RequestHeaders={},
                RequestBody=base64.b64encode(json.dumps(body or {}).encode()).decode())


@pytest.fixture
def admission(tmp_path):
    (tmp_path / 'protected').mkdir()
    (tmp_path / 'neighbor').mkdir()
    pidfile = tmp_path / 'pid'
    pidfile.write_text(str(os.getpid()))
    config = tmp_path / 'daemon.json'
    config.write_text('{"authorization-plugins":["test-plugin"]}')
    config.chmod(0o600)
    return Admission(FakeEngine(tmp_path), [tmp_path / 'protected'], pidfile, tmp_path / 'journal',
                     config=config, plugin='test-plugin')


@pytest.mark.parametrize('route,method', [('/containers/protected/exec', 'POST'),
    ('/exec/old/start', 'POST'), ('/containers/protected/start', 'POST'),
    ('/containers/protected/restart', 'POST'), ('/containers/protected/unpause', 'POST'),
    ('/containers/protected/update', 'POST'), ('/containers/protected/archive?path=/data', 'PUT'),
    ('/containers/renamed/exec', 'POST'), ('/containers/protected/attach/ws', 'GET')])
def test_direct_calls_refuse_by_resource(admission, route, method):
    closed = admission.control('CLOSE')
    assert closed['process_containment'] is False
    assert admission.request(request(route, method=method))['Allow'] is False
    assert admission.request(request('/containers/neighbor/exec'))['Allow'] is True


@pytest.mark.parametrize('kind', ['bind', 'mount-bind', 'volume', 'mount-volume', 'from', 'ancestor', 'symlink'])
def test_new_container_resources_not_just_names(admission, kind):
    root = admission.scope.paths[0]
    alias = root.parent / 'alias'
    alias.symlink_to(root)
    hosts = {
        'bind': dict(Binds=[str(root) + ':/data']),
        'mount-bind': dict(Mounts=[dict(Type='bind', Source=str(root), Target='/data')]),
        'volume': dict(Binds=['store:/data']),
        'mount-volume': dict(Mounts=[dict(Type='volume', Source='store', Target='/data')]),
        'from': dict(VolumesFrom=['renamed:rw']),
        'ancestor': dict(Binds=[str(root.parent) + ':/parent']),
        'symlink': dict(Binds=[str(alias) + ':/data']),
    }
    admission.control('CLOSE')
    assert not admission.request(request('/containers/create', dict(HostConfig=hosts[kind])))['Allow']


def test_allowed_before_close_remains_pending_until_response(admission):
    call = request('/containers/protected/exec')
    assert admission.request(call)['Allow']
    assert admission.control('CLOSE')['pending'] == 1
    assert not admission.request(call)['Allow']
    assert admission.control('CHECK')['pending'] == 1
    admission.response(call)
    assert admission.control('CHECK')['pending'] == 0
    receipt = admission.control('RELEASE')
    assert admission.control('RELEASE') == receipt
    assert admission.request(call)['Allow']
    assert admission.control('RELEASE') == receipt


def test_inline_volume_options_cannot_hide_a_resource(admission):
    admission.control('CLOSE')
    mount = dict(Type='volume', Target='/data', VolumeOptions=dict(DriverConfig=dict(Name='local',
        Options=dict(type='none', o='bind', device=str(admission.scope.paths[0])))))
    assert not admission.request(request('/containers/create', dict(HostConfig=dict(Mounts=[mount]))))['Allow']


def test_hook_loss_and_restore_is_not_the_same_admission(admission):
    admission.control('CLOSE')
    before = admission.config.read_bytes()
    admission.config.write_text('{"authorization-plugins":[]}')
    admission.config.write_bytes(before)
    assert not admission.request(request('/containers/protected/exec'))['Allow']
    with pytest.raises(ValueError, match='DOCKER_ADMISSION_FAILED'):
        admission.control('CHECK')
    assert json.loads((admission.journal / 'failed').read_bytes())['reason'] == 'DOCKER_HOOK_CONFIGURATION_CHANGED'


def test_unknown_effect_is_not_replayed_or_released(admission):
    call = request('/containers/protected/start')
    admission.request(call)
    admission.control('CLOSE')
    with pytest.raises(ValueError, match='DOCKER_RELEASE_UNCERTAIN'):
        admission.control('RELEASE')
    assert admission.phase == 'FAILED'
    assert not admission.request(call)['Allow']


def test_daemon_replacement_refuses(admission, monkeypatch):
    admission.control('CLOSE')
    monkeypatch.setattr(admission, 'daemon', lambda: dict(pid=-1))
    with pytest.raises(ValueError, match='DOCKER_DAEMON_GENERATION_CHANGED'):
        admission.control('CHECK')
    assert admission.phase == 'FAILED'


def test_real_plugin_chunked_envelope_and_empty_activation(admission, tmp_path):
    path = str(tmp_path / 'plugin.sock')
    with Server(path, Handler) as server:
        server.admission = admission
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        def call(route, payload, chunked=False):
            channel = socket.socket(socket.AF_UNIX)
            channel.settimeout(3)
            channel.connect(path)
            connection = http.client.HTTPConnection('localhost')
            connection.sock = channel
            try:
                body = iter([payload]) if chunked else payload
                connection.request('POST', route, body=body, encode_chunked=chunked)
                response = connection.getresponse()
                assert response.status == 200
                return json.loads(response.read())
            finally:
                connection.close()
        try:
            assert call('/Plugin.Activate', b'')['Implements'] == ['authz']
            data = request('/containers/protected/exec')
            data['RequestUri'] = data.pop('RequestURI')
            assert call('/AuthZPlugin.AuthZReq', json.dumps(data).encode(), True)['Allow']
            assert admission.control('CHECK')['pending'] == 1
            assert call('/AuthZPlugin.AuthZRes', json.dumps(data).encode(), True)['Allow']
            assert admission.control('CHECK')['pending'] == 0
        finally:
            server.shutdown()
            thread.join(3)
