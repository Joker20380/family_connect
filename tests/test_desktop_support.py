import hashlib
import json
import os
from pathlib import Path
import threading
import time

import httpx
import pytest

from control.friends import diagnostics, support_ids
from control.friends.access import Access, Rejected
from control.friends.referrals import RateLimited
from provisioning.friends import FriendsClient, FriendsError
from provisioning.friends_owner import FriendsOwner
from provisioning.support import SupportConsent, SupportSnapshot, SupportUpload
from scripts.diagnostic106_vectors import baseline, support_cases


def snapshot():
    return dict(state='RESTORING', network_class='WIFI', restricted_readiness='READY',
                vpn_capture_open=False, restricted_session=baseline()['session'])


@pytest.mark.parametrize('name,ring', list(support_cases().items()))
def test_accepted106_projection_vectors(name, ring):
    contract = json.loads((Path(__file__).resolve().parents[1]/'clients/shared/android106-support.json').read_text())
    report = SupportSnapshot.project(ring, 2011, 1000000, report_id='a'*32)
    actual = hashlib.sha256(json.dumps(report,sort_keys=True,separators=(',', ':')).encode()).hexdigest()
    assert actual == contract['expected_sha256'][name]


@pytest.fixture
def endpoint(tmp_path):
    access = Access(tmp_path / 'registry.db')
    access.initialize()
    requests = []
    override = {}
    path = tmp_path / 'snapshots.db'
    def route(request):
        value = json.loads(request.content)
        requests.append((request.url.path, value))
        handler = override.get(request.url.path)
        if handler:
            return handler(value)
        try:
            if request.url.path == '/friends/challenge':
                return httpx.Response(200, json=access.challenge(**value))
            if request.url.path == '/friends/activate':
                return httpx.Response(200, json=dict(device=access.complete(value, 'activate')['device'], status='active'))
            if request.url.path == '/friends/device/diagnostics':
                return httpx.Response(200, json=diagnostics.request(access, path, value))
            raise AssertionError('Unexpected endpoint')
        except RateLimited:
            return httpx.Response(429)
        except Rejected:
            return httpx.Response(403)
    factory = lambda: httpx.Client(base_url='https://test.invalid', transport=httpx.MockTransport(route))
    owner = FriendsOwner(tmp_path / 'identity', tmp_path / 'anchor', http_factory=factory)
    owner.activate(access.invite())
    with access.db() as database:
        support_ids.create(database)
        support = support_ids.registered(database, owner._device().reference)
    requests.clear()
    return owner, access, requests, path, support, override


def test_authenticated_snapshot_bound_to_report_and_same_identity(endpoint):
    owner, access, requests, path, support, _ = endpoint
    original = {name: (owner.path / name).read_bytes() for name in ('reticulum.key', 'wireguard.key', 'friends.initialized')}
    report = SupportSnapshot.project(snapshot(), 2011, int(time.time()*1000))
    receipt = owner.support_diagnostics(report, cancelled=lambda: False, registration=owner._device().reference)
    assert receipt['report_id'] == report['report_id']
    assert [name for name, _ in requests] == ['/friends/challenge', '/friends/device/diagnostics']
    raw = requests[1][1]['report']
    assert requests[0][1]['purpose'] == 'diagnostics:' + hashlib.sha256(raw.encode()).hexdigest()
    saved = diagnostics.read(path, support, int(access.clock()))['report']
    assert saved == report and saved['platform'] == 'linux'
    assert saved['metrics']['effective_send_window'] == 32
    assert path.stat().st_mode & 0o777 == 0o600
    assert all((owner.path/name).read_bytes() == value for name, value in original.items())
    with pytest.raises(FriendsError, match='rate_limited'):
        owner.support_diagnostics(SupportSnapshot.project(snapshot(), 2011, 1), cancelled=lambda: False, registration=owner._device().reference)


@pytest.mark.parametrize('value', [True, -1, 2**53, 1.1, float('nan'), '1', None, [], {}])
def test_projection_drops_unsafe_numbers_and_private_content(value):
    ring = snapshot()
    ring.update(room_url='https://secret.invalid/', messages=['PRIVATE'], token='SECRET')
    ring['restricted_session'].update(protocol_errors=value, unknown_stream=value, private_key='SECRET')
    ring['restricted_session']['protocol_error_reasons'] = dict(unknown_stream=value, dns=['private.invalid'])
    projected = SupportSnapshot.project(ring, 2011, 123)
    metrics = projected['metrics']
    assert 'protocol_errors' not in metrics and 'unknown_stream' not in metrics
    raw = SupportSnapshot.encode(projected)
    assert len(raw.encode()) <= 4096 and all(secret not in raw for secret in ('PRIVATE', 'SECRET', 'secret.invalid', 'private.invalid'))
    assert diagnostics.validate(raw) == projected


@pytest.mark.parametrize('field,value', [('schema', True), ('platform', 'android'), ('consent', False),
    ('report_id', 'ROOM'), ('version_code', True), ('sampled_at_ms', 2**53), ('metrics', {'secret': 'SECRET'})])
def test_invalid_report_rejected_before_challenge(endpoint, field, value):
    owner, _, requests, _, _, _ = endpoint
    report = SupportSnapshot.project(snapshot(), 2011, 1)
    report[field] = value
    with pytest.raises(FriendsError, match='invalid_input'):
        owner.support_diagnostics(report, cancelled=lambda: False, registration=owner._device().reference)
    assert not requests


@pytest.mark.parametrize('status,code', [(302, 'service_unavailable'), (403, 'access_rejected'), (429, 'rate_limited'), (500, 'service_unavailable')])
def test_status_no_redirect_or_authorization_fallback(endpoint, status, code):
    owner, _, requests, _, _, override = endpoint
    override['/friends/device/diagnostics'] = lambda _: httpx.Response(status, headers={'Location': 'https://wrong.invalid/'})
    with pytest.raises(FriendsError, match=code):
        owner.support_diagnostics(SupportSnapshot.project(snapshot(), 2011, 1), cancelled=lambda: False, registration=owner._device().reference)
    assert len(requests) == 2


@pytest.mark.parametrize('response', [dict(schema=True, report_id='bad', stored_at=1),
    dict(schema=1, report_id='bad', stored_at=1), dict(schema=1, report_id='bad', stored_at=-1)])
def test_bad_receipt_rejected(endpoint, response):
    owner, _, _, _, _, override = endpoint
    override['/friends/device/diagnostics'] = lambda _: httpx.Response(200, json=response)
    with pytest.raises(FriendsError, match='invalid_response'):
        owner.support_diagnostics(SupportSnapshot.project(snapshot(), 2011, 1), cancelled=lambda: False, registration=owner._device().reference)


def test_cancel_between_challenge_and_submit_and_changed_identity(endpoint):
    owner, access, requests, _, _, override = endpoint
    cancelled = threading.Event()
    def challenge(value):
        result = access.challenge(**value)
        cancelled.set()
        return httpx.Response(200, json=result)
    override['/friends/challenge'] = challenge
    report = SupportSnapshot.project(snapshot(), 2011, 1)
    with pytest.raises(FriendsError, match='cancelled'):
        owner.support_diagnostics(report, cancelled=cancelled.is_set, registration=owner._device().reference)
    assert len(requests) == 1
    requests.clear()
    with pytest.raises(FriendsError, match='access_rejected'):
        owner.support_diagnostics(report, cancelled=lambda: False, registration='0'*32)
    assert not requests


def test_shared_deadline_and_socket_timeout(endpoint):
    owner, _, requests, _, _, override = endpoint
    report = SupportSnapshot.project(snapshot(), 2011, 1)
    with owner.http_factory() as http:
        client = FriendsClient(http, owner._device(), deadline=time.monotonic()-1)
        with pytest.raises(FriendsError, match='timeout'):
            client.support_diagnostics(report)
    assert not requests
    def timeout(_):
        raise httpx.ReadTimeout('Do not expose request URL or credentials')
    override['/friends/challenge'] = timeout
    with pytest.raises(FriendsError, match='^timeout$'):
        owner.support_diagnostics(report, cancelled=lambda: False, registration=owner._device().reference)


def test_default_off_identity_bound_expiry_clock_rollback_and_revoke(tmp_path):
    clock = [1000]
    path = tmp_path/'private'
    path.mkdir(mode=0o700)
    consent = SupportConsent(path, 'a'*32, clock=lambda: clock[0])
    assert not consent.enabled() and list(path.iterdir()) == []
    consent.grant()
    assert consent.enabled() and (path/consent.NAME).stat().st_mode & 0o777 == 0o600
    assert SupportConsent(path, 'a'*32, clock=lambda: clock[0]).enabled()
    assert not SupportConsent(path, 'b'*32, clock=lambda: clock[0]).enabled()
    clock[0] = 999
    assert not consent.enabled()
    clock[0] = 1000 + consent.DURATION
    assert not consent.enabled()
    clock[0] = 1001
    consent.revoke()
    assert not consent.enabled() and not (path/consent.NAME).exists()
    assert not SupportConsent(path, 'a'*32, clock=lambda: clock[0]).enabled()


@pytest.mark.parametrize('kind', ['symlink', 'hardlink', 'fifo', 'mode', 'duplicate', 'oversize'])
def test_unsafe_consent_is_off_without_following_or_blocking(tmp_path, kind):
    path = tmp_path/'private'
    path.mkdir(mode=0o700)
    consent = SupportConsent(path, 'a'*32, clock=lambda: 1000)
    consent.grant()
    target = path/consent.NAME
    if kind in ('symlink', 'hardlink'):
        external = tmp_path/'external'
        target.rename(external)
        if kind == 'symlink':target.symlink_to(external)
        else:os.link(external, target)
    elif kind == 'fifo':
        target.unlink();os.mkfifo(target, 0o600)
    elif kind == 'mode':target.chmod(0o644)
    elif kind == 'duplicate':target.write_text('{"schema":1,"schema":1}')
    else:target.write_text(' '*1024)
    assert not SupportConsent(path, 'a'*32, clock=lambda: 1000).enabled()


def uploader(tmp_path, send):
    clock = [1000]
    path = tmp_path/'private'
    path.mkdir(mode=0o700)
    consent = SupportConsent(path, 'a'*32, clock=lambda: clock[0])
    return SupportUpload(consent, send, snapshot, 2011, monotonic=lambda: clock[0]), clock


@pytest.mark.parametrize('failure,delay,state', [(None, 60, 'STORED'), ('rate_limited', 300, 'RATE_LIMITED'),
    ('access_rejected', 300, 'AUTH_REJECTED'), ('timeout', 300, 'TIMEOUT'), ('invalid_response', 300, 'UNAVAILABLE')])
def test_completion_based_cooldown_and_single_inflight(tmp_path, failure, delay, state):
    entered, release = threading.Event(), threading.Event()
    def send(report, *, cancelled):
        entered.set();assert release.wait(3)
        if failure:raise FriendsError(failure)
    upload, clock = uploader(tmp_path, send)
    assert not upload.tick()
    upload.enable();assert upload.tick() and entered.wait(2)
    clock[0] += 14
    assert not upload.tick()
    release.set();upload.worker.join(3)
    assert not upload.worker.is_alive() and upload.status()['state'] == state
    clock[0] += delay-1
    assert not upload.tick()
    clock[0] += 1
    assert upload.tick()
    upload.worker.join(3);upload.close()


@pytest.mark.parametrize('ending', ['disable', 'close', 'expiry'])
def test_revoke_or_expiry_fences_inflight_success(tmp_path, ending):
    entered, release = threading.Event(), threading.Event()
    cancelled_result = []
    def send(report, *, cancelled):
        entered.set();assert release.wait(3)
        cancelled_result.append(cancelled())
    upload, clock = uploader(tmp_path, send)
    upload.enable();assert upload.tick() and entered.wait(2)
    if ending == 'expiry':clock[0] += SupportConsent.DURATION
    else:getattr(upload, ending)()
    assert not upload.status()['enabled'] and not upload.tick()
    release.set();upload.worker.join(3)
    assert cancelled_result == [True] and upload.status()['state'] == 'OFF'
    if ending == 'disable':assert not (upload.consent.path/SupportConsent.NAME).exists()


def test_failed_revocation_stops_current_process_and_reports_error(tmp_path, monkeypatch):
    upload, _ = uploader(tmp_path, lambda *args, **kwargs: None)
    upload.enable()
    def fail(*args, **kwargs):raise OSError('disk unavailable')
    monkeypatch.setattr(os, 'unlink', fail)
    with pytest.raises(OSError):upload.disable()
    assert not upload.tick() and upload.status()['state'] == 'OFF'


def test_missing_identity_never_created_by_support(tmp_path):
    owner = FriendsOwner(tmp_path/'missing', tmp_path/'anchor')
    with pytest.raises((OSError, ValueError)):
        owner.support_upload(snapshot, 2011)
    assert not owner.path.exists()


@pytest.mark.parametrize('platform', ['linux', 'windows'])
def test_platform_tag_does_not_substitute_an_identity(platform):
    report = SupportSnapshot.project(snapshot(), 2011, 1, platform=platform)
    assert diagnostics.validate(SupportSnapshot.encode(report))['platform'] == platform
    assert 'device' not in report and 'device_support_id' not in report
