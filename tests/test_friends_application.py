from pathlib import Path
from types import SimpleNamespace

import pytest

from device_identity.friends import load_friends_identity
from provisioning.friends_application import FriendsApplication
from provisioning.friends_store import FriendsConfigurationStore
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'clients/desktop'))
import backend as desktop

OLD = '11111111-1111-4111-8111-111111111111'
NEW = 'fctcp12345678'


class Crash(BaseException):pass


class Driver(desktop.LinuxTCP):
    def __init__(self):
        self.known = [OLD];self.live = {OLD};self.failure = None;self.crash = None
        self.bad_health = False;self.broken_rollback = False;self.imports = 0
    def step(self, name):
        if self.crash == name:raise Crash()
        if self.failure == name:raise RuntimeError('synthetic failure')
    def profiles(self):return [(ident, ident) for ident in self.known]
    def active(self, ident):return ident in self.live
    def import_profile(self, path):
        assert Path(path).stat().st_mode & 0o777 == 0o600
        assert 'test-credential' in Path(path).read_text()
        self.imports += 1;self.known.append(NEW);self.step('import');return NEW
    def disconnect(self, ident):
        if self.broken_rollback and ident == NEW:raise RuntimeError('rollback blocked')
        self.live.discard(ident)
        if ident == OLD:self.step('disconnect')
    def connect(self, ident):
        self.live.add(ident)
        if ident == NEW:self.step('connect')
    def healthy(self, ident):
        if ident == NEW:self.step('health')
        return ident in self.live and not (ident == NEW and self.bad_health)
    def discard_inactive(self, ident):
        assert ident not in self.live
        self.known.remove(ident)

    def rollback_imported(self, ident):
        self.disconnect(ident)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(desktop, 'operation_directory', lambda:tmp_path/'operations')
    device = load_friends_identity(tmp_path/'identity', create=True)
    store = FriendsConfigurationStore(tmp_path/'identity', device, bytes(32))
    driver = Driver()
    app = FriendsApplication(store, driver)
    config = SimpleNamespace(tcp='test-credential', awg='test-credential', country='nl', sequence=2)
    return app, driver, lambda:config, tmp_path


def assert_idle(app, root):
    with app.store._locked() as fd:assert app._read(fd)['phase'] == 'IDLE'
    with desktop.connection_operation() as lease:assert lease.record['pending'] is None
    raw=(root/'identity'/'friends.application.json').read_text()
    assert 'test-credential' not in raw
    assert (root/'identity'/'friends.application.json').stat().st_mode & 0o777 == 0o600


def test_apply_commits_only_after_health(setup):
    app, driver, fetch, root = setup
    assert app.connect(fetch) == dict(profile=NEW, country='nl', transport='tcp', sequence=2)
    assert driver.live == {NEW};assert_idle(app,root)
    FriendsApplication(app.store, driver).recover()
    assert driver.live == {NEW}  # A committed tunnel is not rolled back on restart.


@pytest.mark.parametrize('transport', ['awg', 'tcp'])
def test_terminal_prestart_refusal_has_one_request_and_finishes(setup, monkeypatch, transport):
    app, driver, fetch, root = setup
    driver.known = ['fcmesh0'];driver.live.clear()
    attempts, fetches = [], []
    def reject(ident):
        attempts.append(ident)
        raise desktop.PreStartRejected('TRANSPORT_BUSY')
    monkeypatch.setattr(driver, 'connect', reject)
    def configuration():
        fetches.append(True)
        return fetch()
    with pytest.raises(desktop.PreStartRejected) as caught:
        app.connect(configuration, transport=transport)
    assert attempts == [NEW] and fetches == [True] and driver.known == ['fcmesh0']
    assert_idle(app, root)
    observed = driver.poll_state(None)
    assert observed.generation == 2 and not observed.active_ids
    assert caught.value.operation_diagnostic == dict(category='TRANSPORT_BUSY', phase='IDLE',
        outcome='PRE_START_REJECTED', cleanup_confirmed=True, generation=2, pending=False)
    assert caught.value.cleanup_error is None


@pytest.mark.parametrize('reason', ['CHANNEL_LOST', 'HELPER_TIMEOUT', 'HELPER_FAILED'])
def test_unknown_dispatch_preserves_journal_until_same_owner_recovery(setup, monkeypatch, reason):
    app, driver, fetch, root = setup
    driver.known = ['fcmesh0'];driver.live.clear()
    attempts = []
    primary = desktop.RecoveryRequired(reason)
    def uncertain(ident):
        attempts.append(ident);driver.live.add(ident)
        raise primary
    monkeypatch.setattr(driver, 'connect', uncertain)
    with pytest.raises(desktop.RecoveryRequired) as caught:
        app.connect(fetch)
    assert caught.value.primary_error is primary and caught.value.cleanup_error is None
    assert attempts == [NEW] and driver.live == {NEW}
    with app.store._locked() as directory:assert app._read(directory)['phase'] == 'APPLYING'
    with desktop.connection_operation(owner=app.owner) as lease:
        assert lease.record == dict(generation=1, pending=app.owner)
    with pytest.raises(desktop.ConnectionBusy):
        with desktop.connection_operation(owner='f'*64) as lease:lease.finish()
    driver.broken_rollback = True
    with pytest.raises(RuntimeError):FriendsApplication(app.store, driver).recover()
    with desktop.connection_operation(owner=app.owner) as lease:assert lease.record['pending'] == app.owner
    driver.broken_rollback = False
    FriendsApplication(app.store, driver).recover()
    assert_idle(app, root)
    assert not driver.live and driver.known == ['fcmesh0'] and attempts == [NEW]
    FriendsApplication(app.store, driver).recover()
    assert driver.poll_state(None).generation == 2


def test_cleanup_failure_preserves_primary_and_does_not_write_idle(setup, monkeypatch):
    app, driver, fetch, root = setup
    driver.live.clear();driver.known = ['fcmesh0']
    primary = desktop.PreStartRejected('TRANSPORT_BUSY')
    cleanup = RuntimeError('synthetic inactive-profile cleanup refused')
    def reject(_):raise primary
    def refuse(_):raise cleanup
    monkeypatch.setattr(driver, 'connect', reject)
    monkeypatch.setattr(driver, 'discard_inactive', refuse)
    with pytest.raises(desktop.RecoveryRequired) as caught:app.connect(fetch)
    assert caught.value.primary_error is primary and caught.value.__cause__ is primary
    assert caught.value.cleanup_error is cleanup
    assert caught.value.operation_diagnostic['cleanup_confirmed'] is False
    with app.store._locked() as directory:assert app._read(directory)['phase'] == 'APPLYING'
    with desktop.connection_operation(owner=app.owner) as lease:assert lease.record['generation'] == 1


def test_old_virtual_inventory_is_normalized_only_when_inactive(setup):
    app, driver, fetch, root = setup
    baseline = dict(known=['fcmesh0', NEW], active=[])
    assert app.adapter._snapshot(baseline) == dict(known=[NEW], active=[])
    with pytest.raises(ValueError):app.adapter._snapshot(dict(known=['fcmesh0'], active=['fcmesh0']))


def test_expired_lease_cannot_finish_a_later_generation(setup):
    app, driver, fetch, root = setup
    with desktop.connection_operation(owner=app.owner) as old:
        old.reserve();old.finish()
    with desktop.connection_operation(owner=app.owner) as current:
        current.reserve()
        with pytest.raises(desktop.StaleConnection):old.finish()
        assert current.record == dict(generation=3,pending=app.owner)
        current.finish()
    assert driver.poll_state(None).generation == 4


@pytest.mark.parametrize('failure', ['import','disconnect','connect','health','unhealthy'])
def test_apply_failure_restores_old_tunnel(setup, failure):
    app, driver, fetch, root = setup
    driver.failure = failure;driver.bad_health = failure == 'unhealthy'
    with pytest.raises(RuntimeError):app.connect(fetch)
    assert driver.live == {OLD};assert_idle(app,root)


@pytest.mark.parametrize('crash', ['import','disconnect','connect','health'])
def test_crash_blocks_gui_until_restart_rollback(setup, crash):
    app, driver, fetch, root = setup
    driver.crash = crash
    with pytest.raises(Crash):app.connect(fetch)
    with pytest.raises(desktop.ConnectionBusy):
        with desktop.connection_operation(mutate=True):pass
    driver.crash = None
    FriendsApplication(app.store, driver).recover()
    assert driver.live == {OLD};assert_idle(app,root)


def test_failed_rollback_keeps_pending_owner(setup):
    app, driver, fetch, root = setup
    driver.failure = 'health';driver.broken_rollback = True
    with pytest.raises(RuntimeError):app.connect(fetch)
    with pytest.raises(desktop.ConnectionBusy):
        with desktop.connection_operation(mutate=True):pass
    driver.failure = None;driver.broken_rollback = False
    app.recover();assert driver.live == {OLD};assert_idle(app,root)


def test_denied_refresh_never_imports_cache_or_changes_routes(setup):
    app, driver, fetch, root = setup
    def denied():raise ValueError('access rejected')
    with pytest.raises(ValueError):app.connect(denied)
    assert driver.live == {OLD} and driver.imports == 0
    with desktop.connection_operation() as lease:assert lease.record['pending'] is None


def test_corrupt_journal_never_fetches_or_mutates(setup):
    app, driver, fetch, root = setup
    app.connect(fetch)
    (root/'identity'/'friends.application.json').write_text('invalid')
    count = driver.imports
    with pytest.raises(ValueError):app.connect(lambda:pytest.fail('fetch after corruption'))
    assert driver.live == {NEW} and driver.imports == count


def test_commit_write_failure_rolls_back(setup, monkeypatch):
    app, driver, fetch, root = setup
    write = app._write;failed = False
    def interrupted(fd, record):
        nonlocal failed
        if record['phase'] == 'IDLE' and not failed:
            failed = True;raise OSError('disk full')
        write(fd,record)
    monkeypatch.setattr(app,'_write',interrupted)
    with pytest.raises(OSError):app.connect(fetch)
    assert driver.live == {OLD};assert_idle(app,root)


def test_second_owner_cannot_mutate_during_apply(setup):
    app, driver, fetch, root = setup
    from concurrent.futures import ThreadPoolExecutor
    def collide():
        with pytest.raises(desktop.ConnectionBusy):
            with desktop.connection_operation(mutate=True):pass
    def checked_fetch():
        with ThreadPoolExecutor(1) as pool:pool.submit(collide).result()
        return fetch()
    app.connect(checked_fetch)
    assert_idle(app,root)

@pytest.mark.parametrize('point', [None,'import','connect','health'])
def test_awg_apply_and_rollback(setup, point, monkeypatch):
    app,driver,fetch,root=setup
    monkeypatch.setitem(globals(),'NEW','fcawg12345678')
    driver.failure=point
    if point:
        with pytest.raises(RuntimeError):app.connect(fetch,transport='awg')
        assert driver.live=={OLD}
    else:
        result=app.connect(fetch,transport='awg')
        assert result['transport']=='awg' and driver.live=={NEW}
    assert_idle(app,root)


def test_unknown_transport_cannot_fetch_or_mutate(setup):
    app,driver,fetch,root=setup
    with pytest.raises(ValueError):app.connect(lambda:pytest.fail('unexpected fetch'),transport='unknown')
    assert driver.live=={OLD} and driver.imports==0
