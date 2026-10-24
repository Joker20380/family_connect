import base64
import copy
from dataclasses import replace
import json
import os
from pathlib import Path
import stat
import sys
import threading
import time
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'clients/linux'))
import auto_platform
import auto_policy
from auto_policy import Context, Failure
from auto_platform import Capabilities, HintStore, Platform, Underlying
from auto_runtime import Coordinator
from auto_guard import candidate, policy
from auto_configuration import verified
from test_auto_configuration import response, PRIVATE


class Guard:
    def __init__(self, directory, events):
        self.directory, self.events, self.record = directory, events, None
        self.uid, self.generation = 1000, 'a'*32

    def _owned(self):
        assert self.record is not None

    def acquire(self):
        assert self.record is None
        self.record = dict(current=policy())
        self.events.append('guard-acquire')

    def block(self):
        self._owned()
        self.record['current'] = policy(selected=self.record['current']['selected'])
        self.events.append('guard-block')

    def prepare(self, selected):
        assert self.record['current']['mode'] == 'blocked'
        self.record['current'] = policy('probe', selected)
        self.events.append('guard-probe-'+selected['kind'])

    def ready(self, index, ipv6):
        assert self.record['current']['mode'] == 'probe' and index == 7 and ipv6 is False
        self.record['current'] = policy('ready', self.record['current']['selected'], index)
        self.events.append('guard-ready')

    def release(self):
        assert self.record['current']['mode'] == 'blocked'
        self.record = None
        self.events.append('guard-release')


@pytest.fixture
def platform(tmp_path):
    events = []
    guard = Guard(tmp_path, events)
    class Underlay:
        value = dict(index=2, name='eth0', gateway='10.0.0.1', addresses=['10.0.0.2'])
        def read(self, context):
            context.check()
            if self.value is None:
                raise Failure('NETWORK')
            return copy.deepcopy(self.value)
    class Owner:
        error, validation_error = None, None
        def validate(self, material, context):
            events.append('validate')
            if self.validation_error:
                raise Failure(self.validation_error)
        def resolve(self, material, country, private, seeds, underlying, context):
            events.append('configure')
            assert guard.record['current']['mode'] == 'blocked' and len(private) == 32 and underlying == 2
            if self.error:
                raise Failure(self.error)
            return SimpleNamespace(awg='synthetic', tcp='synthetic')
    class Attempt:
        kind, error, selected = 'mesh', None, ''
        journal = tmp_path / 'mesh.json'
        owns_journal = False
        def restore(self):
            events.append('mesh-restore')
            self.owns_journal = True
        def cleanup(self):
            events.append('mesh-cleanup')
            self.owns_journal = False
            self.journal.unlink()
        def prepare(self, *args):
            self.selected = 'mesh' if len(args) == 1 else args[1]
            events.append('prepare-'+self.selected)
            return candidate('mesh', 'fcmesh0') if self.selected == 'mesh' else candidate(self.selected, 'fc'+self.selected+'12345678', '8.8.8.8', 443)
        def open(self, context):
            events.append('open-'+self.selected)
            if self.error:
                raise Failure(self.error)
            return 7, False
        def close(self, context):
            events.append('close-'+self.kind)
            self.selected = ''
        def release(self, context):
            events.append('release-'+self.kind)
        def health(self, context):
            context.check()
            events.append('health-'+self.kind)
            return True
        def snapshot(self):
            return dict(native={}, readiness={})
    normal, mesh, owner, underlay = Attempt(), Attempt(), Owner(), Underlay()
    normal.kind = 'normal'
    mesh.network = mesh
    material = dict(identity=base64.b64encode(b'a'*64).decode(), wireguard_public=base64.b64encode(b'b'*32).decode(),
        wireguard_private=base64.b64encode(b'c'*32).decode(), anchor=base64.b64encode(b'd'*32).decode(),
        country='nl', profile='P1', normal_floors=[])
    host = Platform(guard, owner, mesh, material, normal=normal, underlying=underlay,
                    capabilities=lambda configuration, context: ['awg', 'tcp'])
    return host, guard, owner, normal, mesh, underlay, events, material


def test_platform_orders_guard_validation_configuration_and_real_attempt_boundary(platform):
    host, guard, owner, normal, mesh, underlay, events, material = platform
    boundary = auto_policy.GuardedHost(guard, host, 7)
    assert boundary.call(dict(generation=7, operation='configure'), Context(30000)) == ['awg', 'tcp']
    boundary.call(dict(generation=7, operation='close'), Context(20000))
    boundary.call(dict(generation=7, operation='open', candidate='awg'), Context(20000))
    assert events.index('guard-acquire') < events.index('validate') < events.index('configure')
    assert events.index('guard-probe-awg') < events.index('open-awg') < events.index('guard-ready')
    assert host.health(Context(20000)) and host.snapshot()['selected'] == 'awg'
    boundary.call(dict(generation=7, operation='close'), Context(20000))
    boundary.call(dict(generation=7, operation='release'), Context(20000))
    assert host.material == {} and material['identity'] and guard.record is None
    host.close(Context(20000))
    host.release(Context(20000))
    assert events.count('release-normal') == 1 and events.count('release-mesh') == 1


@pytest.mark.parametrize('reason', ['NETWORK', 'AUTH', 'CONFIGURATION', 'INTERNAL', 'CANCELLED'])
def test_only_transient_normal_refresh_allows_restricted_candidate(platform, reason):
    host, guard, owner, normal, mesh, underlay, events, material = platform
    guard.acquire()
    owner.error = reason
    if reason == 'NETWORK':
        assert host.configure(Context(30000)) == []
        assert host.prepare(Context(20000), 'restricted')['kind'] == 'mesh'
    else:
        with pytest.raises(Failure, match=reason):
            host.configure(Context(30000))
    assert not any(event.startswith('open-') for event in events)
    assert host.snapshot()['first_reason'] == reason


def test_offline_cannot_hide_invalid_identity_or_catalog_floor(platform):
    host, guard, owner, normal, mesh, underlay, events, material = platform
    guard.acquire()
    underlay.value = None
    owner.validation_error = 'CONFIGURATION'
    with pytest.raises(Failure, match='CONFIGURATION'):
        host.configure(Context(30000))
    assert 'configure' not in events
    assert host.snapshot()['first_reason'] == 'CONFIGURATION'


def test_recovery_reconciles_own_mesh_journal_before_fresh_configuration(platform):
    host, guard, owner, normal, mesh, underlay, events, material = platform
    guard.acquire()
    mesh.journal.write_text('synthetic old owner')
    assert host.configure(Context(30000)) == ['awg', 'tcp']
    assert events.index('mesh-restore') < events.index('mesh-cleanup') < events.index('configure')
    assert not mesh.journal.exists()


def test_address_change_is_loss_even_if_underlying_index_is_unchanged(platform):
    host, guard, owner, normal, mesh, underlay, events, material = platform
    boundary = auto_policy.GuardedHost(guard, host, 7)
    boundary.call(dict(generation=7, operation='configure'), Context(30000))
    boundary.call(dict(generation=7, operation='open', candidate='tcp'), Context(20000))
    underlay.value['addresses'] = ['10.0.0.3']
    with pytest.raises(Failure, match='NETWORK'):
        host.health(Context(20000))
    assert host.network_matches(underlay.value) is False


def test_close_cancels_health_before_waiting_for_attempt_lock(platform):
    host, guard, owner, normal, mesh, underlay, events, material = platform
    guard.acquire()
    host.configure(Context(30000))
    plan = host.prepare(Context(20000), 'tcp')
    guard.prepare(plan)
    host.open(Context(20000), 'tcp')
    entered, stopped = threading.Event(), threading.Event()
    def health(context):
        entered.set()
        context.cancel.wait(5)
        context.check()
    normal.health = health
    def run():
        try:
            host.health(Context(10000))
        except Failure as failure:
            assert failure.category == 'CANCELLED'
            stopped.set()
    thread = threading.Thread(target=run)
    thread.start()
    assert entered.wait(2)
    guard.block()
    host.close(Context(20000))
    thread.join(2)
    assert stopped.is_set() and not thread.is_alive() and host.selected == ''


def test_underlying_reads_main_table_not_its_own_policy_tun():
    class System:
        def run(self, arguments):
            if arguments[-1] == 'default':
                assert 'main' in arguments and 'get' not in arguments
                return [dict(dst='default', dev='eth0', gateway='10.0.0.1', metric=100)]
            if 'link' in arguments:
                return [dict(ifname='eth0', ifindex=2, flags=['UP','LOWER_UP']),
                        dict(ifname='fctcp12345678', ifindex=7, flags=['UP','LOWER_UP'], linkinfo=dict(info_kind='tun'))]
            return [dict(ifname='eth0', ifindex=2, addr_info=[dict(family='inet', scope='global', local='10.0.0.2')])]
    assert Underlying(System()).read(Context(5000)) == dict(index=2, name='eth0', gateway='10.0.0.1', addresses=['10.0.0.2'])


@pytest.mark.parametrize('broken', ['no-route', 'vpn', 'link-down', 'no-address', 'ambiguous'])
def test_underlying_never_substitutes_a_vpn_or_missing_physical_path(broken):
    class System:
        def run(self, arguments):
            if arguments[-1] == 'default':
                if broken == 'no-route':
                    return []
                values = [dict(dst='default', dev='eth0', gateway='10.0.0.1')]
                return values + [dict(dst='default', dev='eth0', gateway='10.0.0.254')] if broken == 'ambiguous' else values
            if 'link' in arguments:
                return [dict(ifname='eth0', ifindex=2, flags=['UP'] if broken == 'link-down' else ['UP','LOWER_UP'],
                             linkinfo=dict(info_kind='tun' if broken == 'vpn' else 'ether'))]
            return [] if broken == 'no-address' else [dict(ifname='eth0', ifindex=2, addr_info=[dict(family='inet', scope='global', local='10.0.0.2')])]
    with pytest.raises(Failure, match='NETWORK'):
        Underlying(System()).read(Context(5000))


def test_capabilities_filter_missing_engines_and_old_awg31_without_running_them(tmp_path, monkeypatch):
    configuration = verified(response(), 1, 'nl', PRIVATE)
    configuration = replace(configuration, awg=configuration.awg.replace('[Peer]', 'RandomTrailers = true\n[Peer]'))
    library, config, units = tmp_path/'lib', tmp_path/'config', tmp_path/'units'
    for directory in (library, config, units):
        directory.mkdir()
    monkeypatch.setattr(auto_platform, 'trusted', lambda path, directory=False: path.lstat())
    capabilities = Capabilities(library, config, units, SimpleNamespace(stat=lambda: SimpleNamespace(st_mode=stat.S_IFCHR)))
    assert capabilities(configuration, Context(5000)) == []
    for kind, engines in [('awg', ['amneziawg-go','awg','awg-quick']), ('tcp', ['xray'])]:
        root = library/('family-connect-'+kind)
        root.mkdir()
        (config/kind).mkdir()
        for name in ['helper','backend.py','profile_config.py','authorization-session-v1','awg_lifecycle.py',*engines]:
            (root/name).write_text('not executed')
            (root/name).chmod(0o755)
    (units/'family-connect-tcp@.service').write_text('synthetic fixture')
    assert capabilities(configuration, Context(5000)) == ['tcp']
    marker = library/'family-connect-awg/awg31.json'
    marker.write_text(json.dumps(dict(schema=1,engine='old',tools='old')))
    assert capabilities(configuration, Context(5000)) == ['tcp']
    marker.write_text(json.dumps(dict(schema=1,engine='b5928efb6ca19f0153958460c3d141f04abc5c2e',tools='ee0f0a9aa34ff0a0da4b3433b9512781cfe02843')))
    assert capabilities(configuration, Context(5000)) == ['awg','tcp']


def test_hint_is_bounded_country_selection_not_a_stored_credential(tmp_path, monkeypatch):
    original = auto_platform.private_read
    monkeypatch.setattr(auto_platform, 'private_read', lambda path: original(path, expected_owner=os.getuid()))
    store = HintStore(tmp_path/'hint.json', 1000)
    assert store.last('nl') == ''
    store.remember('nl','awg')
    store.remember('ru','tcp')
    assert store.last('nl') == 'awg' and set(store.read()['countries']) == {'nl','ru'}
    with pytest.raises(ValueError):
        store.remember('nl','restricted')
    with pytest.raises(ValueError):
        HintStore(store.path,1001).last('nl')


@pytest.fixture
def native(platform, monkeypatch):
    artifact = os.environ.get('FC_TEST_MESH_WORKER')
    if not artifact:
        pytest.skip('Requires actual Auto worker; platform/network remain synthetic')
    monkeypatch.setattr(auto_policy.os, 'geteuid', lambda: 0)
    host, guard, *rest = platform
    runtime = Coordinator(guard, host, 77, worker=str(Path(artifact).resolve(strict=True)))
    yield runtime
    if runtime.thread is not None:
        runtime.close()


def until(runtime, expected):
    deadline = time.monotonic()+10
    while time.monotonic() < deadline:
        value = runtime.status()['policy']
        if value['state'] == expected:
            return value
        runtime.wake.set()
        time.sleep(.02)
    pytest.fail('native coordinator did not reach '+expected)


def test_actual_native_controller_connects_and_explicit_stop_releases_once(native, platform):
    host, guard, owner, normal, mesh, underlay, events, material = platform
    native.start()
    assert until(native,'CONNECTED')['selected'] == 'awg'
    native.request_disconnect()
    assert native.status()['policy']['state'] in ('DISCONNECTING', 'DISCONNECTED')
    native.request_disconnect()
    assert until(native,'DISCONNECTED')['desired_connected'] is False
    assert events.count('guard-release') == 1


def test_actual_native_service_abort_retains_guard_and_closes_candidate(platform, monkeypatch):
    artifact = os.environ.get('FC_TEST_MESH_WORKER')
    if not artifact:
        pytest.skip('Requires actual Auto worker; platform/network remain synthetic')
    monkeypatch.setattr(auto_policy.os, 'geteuid', lambda: 0)
    host, guard, owner, normal, mesh, underlay, events, material = platform
    guard.acquire()
    runtime = Coordinator(guard, host, 91, worker=str(Path(artifact).resolve(strict=True)), guard_prepared=True)
    try:
        runtime.start()
        until(runtime, 'CONNECTED')
    finally:
        runtime.abort()
    assert runtime.thread is not None and not runtime.thread.is_alive()
    assert not runtime.failed and events.count('guard-acquire') == 1
    assert guard.record['current']['mode'] == 'blocked' and 'guard-release' not in events
    assert host.selected == ''


def test_actual_native_auth_failure_never_falls_through_to_mesh(native, platform):
    host, guard, owner, normal, mesh, underlay, events, material = platform
    owner.error = 'AUTH'
    terminal = []
    native.terminal = lambda: terminal.append('revoke-intent')
    native.start()
    assert until(native,'FAILED')['first_reason'] == 'AUTH'
    deadline = time.monotonic()+3
    while not terminal and time.monotonic()<deadline:
        native.wake.set()
        time.sleep(.02)
    assert terminal == ['revoke-intent'] and not any(event.startswith('open-') for event in events)


def test_actual_native_transient_normal_failure_selects_only_mesh(native, platform):
    host, guard, owner, normal, mesh, underlay, events, material = platform
    owner.error = 'NETWORK'
    native.start()
    assert until(native,'CONNECTED')['selected'] == 'restricted'
    assert 'open-mesh' in events and 'open-awg' not in events


def test_actual_native_address_change_recovers_without_releasing_guard(native, platform):
    host, guard, owner, normal, mesh, underlay, events, material = platform
    native.start()
    until(native, 'CONNECTED')
    underlay.value['addresses'] = ['10.0.0.9']
    deadline = time.monotonic()+10
    while time.monotonic() < deadline:
        native.wake.set()
        if events.count('open-awg') == 2 and native.status()['policy']['state'] == 'CONNECTED':
            break
        time.sleep(.02)
    else:
        pytest.fail('address change did not drive the shared native restoration path')
    assert events.count('guard-acquire') == 1 and 'guard-release' not in events
    assert native.status()['policy']['generation'] == 77


def test_actual_native_offline_wait_is_cancelled_without_starting_a_transport(native, platform):
    host, guard, owner, normal, mesh, underlay, events, material = platform
    underlay.value = None
    native.start()
    view = until(native, 'RESTORING')
    assert view['desired_connected'] and view['retry_at_ms'] > 0
    native.request_disconnect()
    until(native, 'DISCONNECTED')
    assert not any(event.startswith('open-') for event in events)


def test_health_cancel_before_health_enters_does_not_start_another_probe(platform):
    host, guard, owner, normal, mesh, underlay, events, material = platform
    boundary = auto_policy.GuardedHost(guard, host, 7)
    boundary.call(dict(generation=7, operation='configure'), Context(30000))
    boundary.call(dict(generation=7, operation='open', candidate='awg'), Context(20000))
    host.cancel_health()
    with pytest.raises(Failure, match='CANCELLED'):
        host.health(Context(20000))
    assert 'health-normal' not in events


def test_late_connected_reply_cannot_restore_intent_after_explicit_disconnect(platform):
    host, guard, *rest = platform
    runtime = Coordinator(guard, host, 7)
    runtime.stopping = True
    value = dict(generation=7, state='CONNECTED', desired_connected=True, retry_at_ms=0, events=[], events_dropped=0)
    ticket = SimpleNamespace(wait=lambda timeout: dict(ok=True, snapshot=value))
    runtime.accept(ticket)
    assert runtime.status()['policy']['state'] == 'DISCONNECTING'
    assert runtime.status()['policy']['desired_connected'] is False


@pytest.mark.parametrize('error', ['BUSY', 'STALE', 'INVALID', 'INTERNAL'])
def test_rejected_controller_command_is_not_reported_as_progress(platform, error):
    host, guard, *rest = platform
    runtime = Coordinator(guard, host, 7)
    before = runtime.status()
    ticket = SimpleNamespace(wait=lambda timeout: dict(ok=False, error=error, snapshot=runtime.view))
    with pytest.raises(ValueError):
        runtime.accept(ticket)
    assert runtime.status() == before
