from concurrent.futures import Future
from contextlib import nullcontext
import json
from pathlib import Path
import threading
from types import SimpleNamespace

import pytest

import backend
import chat_daemon
from support_daemon import SupportCollector, SupportSession, version_info
from messenger.local import LocalError
from provisioning.support import SupportConsent, SupportUpload, SupportSnapshot
from provisioning.support_client import SupportClient
from scripts.diagnostic106_vectors import baseline
from test_chat_service import bare_service, request


def state(enabled=False, revision='a'*32):
    return dict(enabled=enabled, until=600000 if enabled else 0, state='STORED' if enabled else 'OFF',
                revision=revision, available=True, background=True, storage_error=False)


@pytest.fixture
def session(tmp_path):
    directory = tmp_path/'identity'
    directory.mkdir(mode=0o700)
    clock = [1000]
    sent = []
    def factory(snapshot, version):
        return SupportUpload(SupportConsent(directory, 'a'*32, clock=lambda: clock[0]),
            lambda report, **kwargs: sent.append(report), snapshot, version, monotonic=lambda: clock[0])
    result = SupportSession(SimpleNamespace(support_upload=factory), lambda: dict(state='CONNECTED'), 2011, clock=lambda: clock[0])
    result.poll()
    yield result, directory, clock, sent
    result.close()
    if result.upload is not None and result.upload.worker is not None:
        result.upload.worker.join(3)
        assert not result.upload.worker.is_alive()


def test_default_off_single_owner_replay_fence_and_no_renewal(session):
    owner, directory, clock, sent = session
    original = owner.status()
    assert original['available'] and not original['enabled'] and not list(directory.iterdir()) and not sent
    enabled = owner.change(True, original['revision'])
    owner.upload.worker.join(3)
    raw = (directory/SupportConsent.NAME).read_bytes()
    clock[0] += 10
    with pytest.raises(LocalError, match='support_conflict'):
        owner.change(True, original['revision'])
    second = owner.change(True, enabled['revision'])
    assert second['until'] == enabled['until'] and (directory/SupportConsent.NAME).read_bytes() == raw
    assert len(sent) == 1
    disabled = owner.change(False, second['revision'])
    assert not disabled['enabled'] and not (directory/SupportConsent.NAME).exists()
    with pytest.raises(LocalError, match='support_conflict'):
        owner.change(True, enabled['revision'])
    assert not owner.status()['enabled'] and len(sent) == 1


def test_crash_restart_retains_consent_but_invalidates_old_control_revision(session):
    first, directory, clock, sent = session
    enabled = first.change(True, first.status()['revision'])
    first.upload.worker.join(3)
    first.close()
    assert (directory/SupportConsent.NAME).exists()
    resumed = SupportSession(first.friends, first.snapshot, first.version_code, clock=lambda: clock[0])
    try:
        resumed.poll();resumed.upload.worker.join(3)
        assert resumed.status()['enabled'] and resumed.status()['until'] == enabled['until']
        with pytest.raises(LocalError, match='support_conflict'):
            resumed.change(False, enabled['revision'])
        assert resumed.status()['enabled']
        resumed.change(False, resumed.status()['revision'])
        assert not resumed.status()['enabled']
    finally:resumed.close()


def test_loading_missing_identity_is_bounded_and_never_opens_chat():
    calls = []
    def unavailable(*args):
        calls.append(True)
        raise OSError('missing')
    owner = SupportSession(SimpleNamespace(support_upload=unavailable), lambda: {}, 2011, clock=lambda: 0)
    for _ in range(10):owner.poll()
    assert len(calls) == 1 and not owner.status()['available']
    with pytest.raises(LocalError, match='support_unavailable'):
        owner.change(True, owner.status()['revision'])


def test_storage_error_stops_upload_and_is_visible(session, monkeypatch):
    owner, _, _, _ = session
    owner.change(True, owner.status()['revision']);owner.upload.worker.join(3)
    def unavailable():raise OSError('private path must not be exposed')
    monkeypatch.setattr(owner.upload.consent, 'revoke', unavailable)
    with pytest.raises(LocalError, match='^support_unavailable$'):
        owner.change(False, owner.status()['revision'])
    assert not owner.status()['enabled'] and owner.status()['storage_error']


class Driver:
    def __init__(self, *, automatic=None, mesh=None, normal=('DISCONNECTED', 'none')):
        self.automatic = automatic or dict(state='DISCONNECTED', desired_connected=False)
        self.mesh = mesh or dict(state='DISCONNECTED', desired_connected=False)
        self.normal = normal
        self.calls = []

    def auto_status(self):
        self.calls.append('auto_status')
        return self.automatic

    def mesh_status(self):
        self.calls.append('mesh_status')
        return self.mesh

    def support_normal_state(self):
        self.calls.append('support_normal_state')
        return self.normal


def test_fresh_readonly_mesh_snapshot_not_gui_cache():
    value = dict(state='CONNECTED', desired_connected=True, requested_profile='P1', native=dict(native=dict(
        tun_ready=True, packet=dict(diagnostic=baseline()['session']), startup=baseline()['startup'])))
    driver = Driver(mesh=value)
    collect = SupportCollector('0.2.11', driver=driver, environment=lambda: dict(network_class='WIFI'))
    report = SupportSnapshot.project(collect(), 2011, 1)['metrics']
    assert report['state'] == 'CONNECTED' and report['speed_profile'] == 'P1' and report['effective_send_window'] == 32
    assert driver.calls == ['auto_status', 'mesh_status']
    value.update(state='RESTORING')
    assert SupportSnapshot.project(collect(), 2011, 2)['metrics']['vpn_capture_open'] is False
    driver.mesh = dict(state='DISCONNECTED', desired_connected=False)
    last = SupportSnapshot.project(collect(), 2011, 3)['metrics']
    assert last['state'] == 'DISCONNECTED' and last['vpn_capture_open'] is False and last['speed_profile'] == 'P1'
    driver.mesh = dict(state='CONNECTING', desired_connected=True)
    fresh = SupportSnapshot.project(collect(), 2011, 4)['metrics']
    assert fresh['speed_profile'] == 'UNKNOWN' and 'session_tag' not in fresh


def test_auto_observation_does_not_fall_back_to_manual_or_stale_gui():
    driver = Driver(automatic=dict(state='RESTORING', desired_connected=True, requested_profile='P1', controller=None))
    collect = SupportCollector('0.2.11', driver=driver, environment=lambda: dict(network_class='ETHERNET'))
    assert collect()['state'] == 'RESTORING' and driver.calls == ['auto_status']
    def denied():raise RuntimeError('sensitive endpoint detail')
    driver.auto_status = denied
    result = collect()
    assert result == dict(state='UNKNOWN', network_class='ETHERNET', restricted_readiness='UNKNOWN', vpn_capture_open=False, restricted_session={})


@pytest.mark.parametrize('normal', [('CONNECTED','tcp'),('CONNECTED','awg'),('DISCONNECTED','none')])
def test_normal_snapshot_does_not_invent_mesh_receipt(normal):
    driver = Driver(normal=normal)
    report = SupportSnapshot.project(SupportCollector('0.2.11', driver=driver, environment=lambda: {})(),2011,1)['metrics']
    assert report['state'] == normal[0] and report['speed_profile'] == 'UNKNOWN'
    assert 'session_tag' not in report and 'effective_send_window' not in report


def test_normal_observer_never_invokes_mutating_helper(monkeypatch):
    driver = backend.LinuxAuto()
    calls = []
    monkeypatch.setattr(backend, 'connection_operation', lambda: nullcontext())
    monkeypatch.setattr(driver, '_awg_records', lambda: {})
    monkeypatch.setattr(driver, '_tcp_records', lambda: {})
    def run(*args,**kwargs):
        calls.append((args,kwargs));return 'uuid:wireguard:'+backend.PREFIX+'test: label\nuuid:ethernet:ETH\n'
    monkeypatch.setattr(backend,'run',run)
    assert driver.support_normal_state() == ('CONNECTED','awg')
    assert len(calls) == 1 and calls[0][0][-3:] == ('connection','show','--active') and calls[0][1]['timeout'] == 3
    monkeypatch.setattr(backend,'run',lambda *args,**kwargs:'uuid:wireguard:Other VPN')
    assert driver.support_normal_state() == ('DISCONNECTED','none')
    monkeypatch.setattr(driver, '_awg_records', lambda: {str(index):{} for index in range(65)})
    with pytest.raises(backend.BackendError,match='limit'):driver.support_normal_state()


@pytest.mark.parametrize('raw', [b'0.2.11\n', b'1.2.3'])
def test_packaged_version_does_not_import_gtk(tmp_path, raw):
    (tmp_path/'VERSION').write_bytes(raw)
    version, code = version_info(tmp_path)
    assert version == raw.decode().strip() and code in (2011,1002003)


@pytest.mark.parametrize('raw', [b'0.2',b'1000.2.1',b'0.2.11\nPRIVATE',b'0.2.11'+b' '*64,b'\xff'])
def test_invalid_version_rejected(tmp_path, raw):
    (tmp_path/'VERSION').write_bytes(raw)
    with pytest.raises(ValueError):version_info(tmp_path)


def test_support_lane_authenticated_bounded_and_independent_of_chat_queue(session, monkeypatch):
    owner, _, _, _ = session
    service = bare_service()
    service.support = owner
    service.pending = 8
    monkeypatch.setattr(chat_daemon.GLib,'idle_add',lambda callback,*args:callback(*args))
    def submit(call,*args):
        future = Future()
        try:future.set_result(call(*args))
        except Exception as error:future.set_exception(error)
        return future
    service.support_pool = SimpleNamespace(submit=submit)
    assert request(service,'support_status',{})['ok']
    status = request(service,'support_status',{})['value']
    changed = request(service,'support_consent',dict(enabled=True,revision=status['revision']))
    assert changed['ok'] and changed['value']['enabled'] and service.owner.local is None
    owner.upload.worker.join(3)
    assert request(service,'support_consent',dict(enabled=False,revision=status['revision']))['error'] == 'support_conflict'
    assert request(service,'support_status',{},uid=999999)['error'] == 'invalid_input'
    for arguments in ({'command':'rm'}, {'enabled':'yes','revision':'a'*32}, {'enabled':False,'revision':'unsafe'}):
        assert request(service,'support_consent',arguments)['error'] == 'invalid_input'
    service.support_pending = True
    assert request(service,'support_status',{})['ok']
    assert request(service,'support_consent',dict(enabled=False,revision=owner.status()['revision']))['error'] == 'busy'


def test_consent_keeps_locked_chat_owner_alive_until_withdrawn(session, monkeypatch):
    owner, _, _, _ = session
    owner.change(True,owner.status()['revision']);owner.upload.worker.join(3)
    service = bare_service();service.support=owner;service.loop=SimpleNamespace(quit=lambda:None)
    monkeypatch.setattr(chat_daemon.time,'monotonic',lambda:61)
    assert service.poll() is True and service.idle_since == 61
    owner.change(False,owner.status()['revision'])
    monkeypatch.setattr(chat_daemon.time,'monotonic',lambda:122)
    assert service.poll() is False and service.stopping


@pytest.mark.parametrize('field,value',[('enabled','yes'),('until',True),('revision','private'),('background',False),('state','private')])
def test_proxy_rejects_unsafe_service_state(field,value):
    response=state();response[field]=value
    with pytest.raises(LocalError):SupportClient.validate(response)


def test_proxy_stale_poll_cannot_restore_revoked_state():
    entered, release = threading.Event(),threading.Event()
    calls=[]
    def rpc(operation,arguments):
        calls.append(operation)
        if operation=='support_status':
            entered.set();assert release.wait(3);return state(True)
        assert arguments == dict(enabled=False,revision='a'*32)
        return state(False,'b'*32)
    proxy=SupportClient(client=SimpleNamespace(request=rpc,connection=None,closed=False))
    proxy.current=state(True)
    assert proxy.tick() and entered.wait(2)
    proxy.disable();release.set();proxy.worker.join(3)
    assert not proxy.status()['enabled'] and proxy.status()['revision']=='b'*32
    proxy.close();assert calls == ['support_status','support_consent']


def test_proxy_unknown_write_reads_back_without_retrying_mutation():
    calls=[]
    def rpc(operation,arguments):
        calls.append(operation)
        if operation=='support_consent':raise LocalError('operation_outcome_unknown')
        return state(True,'c'*32)
    proxy=SupportClient(client=SimpleNamespace(request=rpc,connection=None,closed=False))
    proxy.current=state()
    with pytest.raises(LocalError,match='operation_outcome_unknown'):proxy.enable()
    assert proxy.tick();proxy.worker.join(3)
    assert proxy.status()['enabled'] and calls == ['support_consent','support_status']
    proxy.close();assert calls == ['support_consent','support_status']


def test_proxy_close_detaches_without_revoking_consent():
    calls=[]
    connection=SimpleNamespace(close=lambda *args:calls.append('close'))
    proxy=SupportClient(client=SimpleNamespace(request=lambda *args:pytest.fail('Unexpected RPC'),connection=connection,closed=False))
    proxy.current=state(True);proxy.close()
    assert proxy.client.closed and calls == ['close'] and not proxy.tick()
