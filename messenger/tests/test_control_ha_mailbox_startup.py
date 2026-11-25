import copy
import json
import os

import pytest
import RNS

from messenger.relay import Spool, PUT_PATH
from messenger.tests.test_control_ha_mailbox_fence import GENERATION, envelope
from messenger.tests.test_control_ha_mailbox_links import dispatch, native_link
from scripts import control_ha_mailbox_fence as barrier
from scripts import control_ha_mailbox_links as lineage
from scripts import control_ha_mailbox_startup as bootstrap


def write(path, value):
    path.write_text(json.dumps(value))
    path.chmod(0o600)
    return path


@pytest.fixture
def configured(tmp_path):
    support, peer = RNS.Identity(), RNS.Identity()
    manifest = dict(schema=1, generation=GENERATION, support_public=support.get_public_key().hex(),
                    owner_binding_sha256='b' * 64, replacement_plan_sha256='c' * 64)
    path = write(tmp_path / 'manifest.json', manifest)
    return path, manifest, support, peer


@pytest.fixture
def created(configured, tmp_path, chat_runtime):
    path, manifest, support, peer = configured
    startup = bootstrap.Startup(path, owner_uid=os.getuid())
    spool = Spool(tmp_path / 'spool')
    try:
        relay = startup.create(RNS.Identity(), spool, allowed_public=[support.get_public_key(), peer.get_public_key()])
        yield startup, relay, support, peer
    finally:
        if startup.fence is not None:
            fence = startup.fence
            for name, function in fence.functions.items():
                function.__code__ = fence.originals[name].__code__
            fence.link_class.__init__.__code__ = fence.constructor.__code__
            for module, slot in ((fence.module, barrier.SLOT), (fence.link_module, lineage.SLOT)):
                if vars(module).get(slot) is fence:
                    delattr(module, slot)
            RNS.Transport.deregister_destination(fence.relay.destination)
        spool.close()


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'schema', 'extra', 'generation', 'public', 'owner', 'plan',
                                    'mode', 'link', 'hardlink', 'directory'])
def test_invalid_required_manifest_refuses_before_any_listener(configured, tmp_path, change):
    path, manifest, support, peer = configured
    if change == 'missing':
        path.unlink()
    elif change == 'duplicate':
        path.write_text('{"schema":1,"schema":1}')
    elif change in ('schema', 'extra', 'generation', 'public', 'owner', 'plan'):
        field = dict(public='support_public', owner='owner_binding_sha256', plan='replacement_plan_sha256').get(change, change)
        manifest[field] = True if change == 'schema' else 'invalid'
        write(path, manifest)
    elif change == 'mode':
        path.chmod(0o666)
    elif change == 'link':
        other = path.with_name('actual.json')
        path.rename(other)
        path.symlink_to(other)
    elif change == 'hardlink':
        os.link(path, tmp_path / 'alias.json')
    else:
        path.unlink()
        path.mkdir()
    with pytest.raises((ValueError, OSError)):
        bootstrap.Startup(path, owner_uid=os.getuid())


def test_guard_is_installed_before_native_destination_is_published(created):
    startup, relay, support, peer = created
    assert RNS.Transport.destinations_map[relay.destination.hash] is relay.destination
    assert relay.respond(PUT_PATH, envelope(peer), None, support, 0) == ['unavailable']
    assert relay.respond(PUT_PATH, envelope(support), None, peer, 0)[0] == 'stored'
    observed = startup.observe()
    assert observed['closed_before_publication'] and observed['restart_defaults_closed']
    assert observed['fence']['new_link_admission'] == 'CLOSED'
    assert not observed['owner_exit_verified'] and not observed['installed_unit_verified']
    assert not observed['activation_ready'] and not observed['capture_permitted']
    assert support.get_public_key().hex() not in json.dumps(observed)
    with pytest.raises(ValueError, match='MANIFEST_REQUIRES_FENCE'):
        startup.fence.abort(GENERATION)


def test_wrong_control_owner_and_writable_parent_are_rejected(configured, tmp_path):
    path, manifest, support, peer = configured
    with pytest.raises(ValueError, match='UNSAFE_CONTROL'):
        bootstrap.Startup(path, owner_uid=os.getuid() + 1)
    tmp_path.chmod(0o777)
    try:
        with pytest.raises(ValueError, match='UNSAFE_CONTROL_PARENT'):
            bootstrap.Startup(path, owner_uid=os.getuid())
    finally:
        tmp_path.chmod(0o700)


def test_transport_pin_failure_leaves_no_public_destination(configured, tmp_path, chat_runtime, monkeypatch):
    path, manifest, support, peer = configured
    startup = bootstrap.Startup(path, owner_uid=os.getuid())
    spool = Spool(tmp_path / 'spool')
    identity = RNS.Identity()
    target = RNS.Destination.hash(identity, 'lxmf', 'propagation')
    original = vars(RNS.Transport)['register_destination']
    monkeypatch.setattr(bootstrap, 'TRANSPORT_SHA256', '0' * 64)
    try:
        with pytest.raises(ValueError, match='TRANSPORT_SOURCE_PIN'):
            startup.create(identity, spool, allowed_public=[support.get_public_key(), peer.get_public_key()])
        assert startup.fence is None and not startup.published
        assert target not in RNS.Transport.destinations_map
        assert vars(RNS.Transport)['register_destination'] is original
    finally:
        spool.close()


@pytest.mark.parametrize('field', ['process', 'challenge', 'manifest_sha256', 'generation', 'owner_binding_sha256',
                                  'replacement_plan_sha256', 'schema'])
def test_stale_or_mutated_local_request_never_opens(created, tmp_path, field):
    startup, relay, support, peer = created
    ticket = copy.deepcopy(startup.ticket())
    ticket[field] = True if field == 'schema' else 'stale'
    request = write(tmp_path / 'open.json', dict(action='LOCAL_QUALIFICATION_ONLY', ticket=ticket))
    with pytest.raises(ValueError, match='STALE_OR_UNBOUND_TICKET'):
        startup.open_for_qualification(request)
    assert startup.observe()['fence']['new_link_admission'] == 'CLOSED'


def test_fresh_local_ticket_only_allows_new_native_links(created, tmp_path, monkeypatch):
    startup, relay, support, peer = created
    old = native_link(relay, support)
    request = write(tmp_path / 'open.json', dict(action='LOCAL_QUALIFICATION_ONLY', ticket=startup.ticket()))
    observed = startup.open_for_qualification(request)
    assert observed['fence']['new_link_admission'] == 'OPEN_LOCAL_ONLY'
    assert not observed['owner_exit_verified'] and not observed['activation_ready']
    dispatch(old, envelope(peer), monkeypatch)
    assert relay.spool.stats()['count'] == 0
    dispatch(native_link(relay, support), envelope(peer), monkeypatch)
    assert relay.spool.stats()['count'] == 1
    with pytest.raises(ValueError, match='ONE_OPEN_ONLY'):
        startup.open_for_qualification(request)


def test_manifest_drift_and_unsafe_request_refuse_open(created, tmp_path):
    startup, relay, support, peer = created
    request = write(tmp_path / 'open.json', dict(action='LOCAL_QUALIFICATION_ONLY', ticket=startup.ticket()))
    request.chmod(0o666)
    with pytest.raises(ValueError, match='UNSAFE_CONTROL_FILE'):
        startup.open_for_qualification(request)
    request.chmod(0o600)
    startup.path.write_text(startup.path.read_text() + '\n')
    with pytest.raises(ValueError, match='MANIFEST_CHANGED'):
        startup.open_for_qualification(request)
    assert startup.fence.epoch is None


def test_failed_guard_install_never_publishes_destination(configured, tmp_path, chat_runtime, monkeypatch):
    path, manifest, support, peer = configured
    startup = bootstrap.Startup(path, owner_uid=os.getuid())
    spool = Spool(tmp_path / 'spool')
    node = RNS.Identity()
    target = RNS.Destination.hash(node, 'lxmf', 'propagation')
    original = vars(RNS.Transport)['register_destination']

    def fail(self):
        assert target not in RNS.Transport.destinations_map
        assert all(destination.hash != target for destination in RNS.Transport.destinations)
        raise ValueError('SYNTHETIC_INSTALL_FAILURE')

    monkeypatch.setattr(bootstrap.PersistentLinkFence, 'install', fail)
    try:
        with pytest.raises(ValueError, match='SYNTHETIC_INSTALL_FAILURE'):
            startup.create(node, spool, allowed_public=[support.get_public_key(), peer.get_public_key()])
        assert not startup.published
        assert target not in RNS.Transport.destinations_map
        assert vars(RNS.Transport)['register_destination'] is original
    finally:
        spool.close()
