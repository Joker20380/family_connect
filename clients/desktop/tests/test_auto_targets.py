import base64
import copy
from dataclasses import replace
import json
import os
import threading
import time

import pytest

from test_auto_platform import platform, Guard
from test_auto_configuration import response, PRIVATE, PUBLIC, FIXTURE
from auto_configuration import NormalOwner, Preference, Target, TargetChoices, verified
from auto_platform import Platform
from auto_policy import Context, Failure, GuardedHost
from mesh_materials import CacheStore


TARGETS = (Target('model-only', 'nl-a', 'nl', 20), Target('model-only', 'nl-b', 'nl', 60),
           Target('model-only', 'de-a', 'de', 10))


def test_target_refresh_preserves_id_not_country_or_position():
    preference = Preference('model-only', 'nl-b', 'tcp', 'P0')
    model = TargetChoices(TARGETS, preference)
    model.refresh([replace(target, load=40) for target in reversed(TARGETS)])
    assert model.selected_next == preference
    assert [target.reference for target in model.targets if target.country == 'nl'] == ['nl-b', 'nl-a']
    model.refresh([TARGETS[0], TARGETS[2]])
    assert model.selected_next == preference and not model.snapshot()['available']
    with pytest.raises(ValueError):
        model.refresh([TARGETS[0], TARGETS[0]])
    assert len(model.targets) == 2


@pytest.fixture
def application(platform, tmp_path):
    host, guard, _, normal, mesh, underlay, events, material = platform
    cache = tmp_path / 'floor'
    cache.mkdir(mode=0o700)
    storage = CacheStore(cache, 1000, expected_owner=os.getuid())
    calls = []
    def native(request, cancel, deadline):
        calls.append(copy.deepcopy(request))
        assert host.selection_snapshot()['assignment'] is None
        if request['action'] == 'validate':
            return dict(schema=1, id=request['id'], ok=True, code='VALIDATED_MATERIAL',
                        public=base64.b64encode(PUBLIC).decode())
        return response(request['id'])
    host.normal_owner = NormalOwner(storage, native)
    boundary = GuardedHost(guard, host, 7)
    try:
        yield host, boundary, storage, calls, platform
    finally:
        storage.close()


def call(boundary, operation, candidate=None, context=None):
    return boundary.call(dict(generation=boundary.generation, operation=operation, candidate=candidate), context or Context(30000))


def test_real_legacy_admission_and_guard_applied_boundary(application, monkeypatch):
    host, boundary, storage, calls, parts = application
    _, guard, _, normal, mesh, _, events, material = parts
    assert host.selection_snapshot()['assignment'] is None
    offline = verified(response(), 1, 'nl', PRIVATE)
    with pytest.raises(ValueError):
        host.normal_owner.assignment(offline, guard.generation, 'P1')
    call(boundary, 'configure')
    assert [request['action'] for request in calls] == ['validate', 'fetch', 'inspect']
    state = host.selection_snapshot()
    assert state['assignment']['target'] == dict(provider='friends-legacy-v1', reference='legacy-nl', country='nl', load=None)
    assert state['assignment']['gateway_id'] is None and state['applied'] is None
    assert state['assignment']['owner_generation'] == guard.generation
    with pytest.raises(ValueError):
        host.normal_owner.assignment(host.configuration, 'b'*32, 'P1')
    with pytest.raises(ValueError):
        replace(host.assignment, gateway_id='legacy-nl')
    ready = guard.ready
    def observed_ready(*args):
        assert host.selection_snapshot()['applied'] is None
        assert 'prepare-tcp' in events and 'open-tcp' in events
        ready(*args)
    monkeypatch.setattr(guard, 'ready', observed_ready)
    call(boundary, 'open', 'tcp')
    active = host.selection_snapshot()['applied']
    assert active['owner_generation'] == guard.generation and active['transport'] == 'tcp'
    assert active['assignment'] == state['assignment'] and active['requested_profile'] == 'P1'
    before, stored, native_calls, mesh_state = list(events), storage.read(), len(calls), mesh.snapshot()
    host.refresh_targets(TARGETS)
    host.select_next(Preference('model-only', 'nl-b', 'awg', 'P0'))
    host.refresh_targets([replace(target, load=1) for target in reversed(TARGETS)])
    state = host.selection_snapshot()
    assert state['selected_next']['target_reference'] == 'nl-b' and state['connection']['target_reference'] == 'legacy-nl'
    assert state['applied'] == active and state['assignment'] == active['assignment']
    assert host.selected == 'tcp' and host.snapshot()['capabilities'] == ['awg', 'tcp']
    assert not state['dynamic_fleet'] and events == before and len(calls) == native_calls
    assert storage.read() == stored and mesh.snapshot() == mesh_state
    public = json.dumps(state) + repr(host.assignment) + repr(host.active) + repr(host.choices.selected_next)
    for secret in (response()['response']['tcp_id'], material['identity'], material['wireguard_private'],
                   FIXTURE['wireguard_key'], host.configuration.tcp, host.configuration.awg):
        assert secret not in public
    call(boundary, 'close')
    assert host.selection_snapshot()['applied'] is None
    call(boundary, 'release')
    assert host.selection_snapshot()['assignment'] is None


@pytest.mark.parametrize('failure', ['ready', 'cancel-ready', 'cancel-published', 'deadline-published'])
def test_failed_or_cancelled_apply_never_leaves_active_metadata(application, monkeypatch, failure):
    host, boundary, _, _, parts = application
    guard = parts[1]
    call(boundary, 'configure')
    context = Context(30000)
    ready, applied = guard.ready, host.applied
    def failed_ready(*args):
        if failure == 'ready':
            raise OSError('synthetic guard failure')
        ready(*args)
        context.cancel.set()
    def interrupted_publish(*args):
        applied(*args)
        if failure == 'cancel-published':
            context.cancel.set()
        else:
            context.deadline = time.monotonic() - 1
    if failure in ('ready', 'cancel-ready'):
        monkeypatch.setattr(guard, 'ready', failed_ready)
    else:
        monkeypatch.setattr(host, 'applied', interrupted_publish)
    with pytest.raises((OSError, Failure)):
        call(boundary, 'open', 'tcp', context)
    assert host.selection_snapshot()['applied'] is None and host.active is None


def test_close_error_and_cancel_health_clear_applied_without_changing_next(application, monkeypatch):
    host, boundary, _, _, parts = application
    call(boundary, 'configure')
    call(boundary, 'open', 'tcp')
    before = host.selection_snapshot()['selected_next']
    def failed_close(context):
        assert host.selection_snapshot()['applied'] is None
        raise OSError('synthetic close failure')
    monkeypatch.setattr(parts[3], 'close', failed_close)
    with pytest.raises(Failure):
        call(boundary, 'close')
    assert host.selection_snapshot()['applied'] is None
    assert host.selection_snapshot()['selected_next'] == before


def test_late_fetch_and_old_owner_cannot_publish_into_next_generation(application, tmp_path):
    host, boundary, storage, _, parts = application
    entered, finish = threading.Event(), threading.Event()
    errors = []
    original = host.normal_owner.native
    def delayed(request, cancel, deadline):
        result = original(request, cancel, deadline)
        if request['action'] == 'fetch':
            entered.set()
            assert finish.wait(3)
        return result
    host.normal_owner.native = delayed
    context = Context(30000)
    def configure():
        try:
            call(boundary, 'configure', context=context)
        except Failure as failure:
            errors.append(failure.category)
    thread = threading.Thread(target=configure)
    thread.start()
    try:
        assert entered.wait(3)
        context.cancel.set()
    finally:
        finish.set()
        thread.join(3)
    assert not thread.is_alive() and errors == ['CANCELLED']
    assert host.selection_snapshot()['assignment'] is None and storage.read() is None
    call(boundary, 'close')
    call(boundary, 'release')
    _, _, _, normal, mesh, underlay, events, material = parts
    guard = Guard(tmp_path, events)
    guard.generation = 'b'*32
    def native(request, cancel, deadline):
        if request['action'] == 'validate':
            return dict(schema=1, id=1, ok=True, code='VALIDATED_MATERIAL', public=base64.b64encode(PUBLIC).decode())
        return response(request['id'])
    current = Platform(guard, NormalOwner(storage, native), mesh, material, normal=normal,
                       underlying=underlay, capabilities=lambda *args: ['tcp'])
    new_boundary = GuardedHost(guard, current, 8)
    call(new_boundary, 'configure')
    call(new_boundary, 'open', 'tcp')
    state, before = current.selection_snapshot(), list(events)
    with pytest.raises(ValueError):
        host.applied(Context(30000), 'tcp')
    with pytest.raises(ValueError):
        new_boundary.call(dict(generation=7, operation='open', candidate='tcp'), Context(30000))
    assert current.selection_snapshot() == state and events == before
    call(new_boundary, 'close')
    call(new_boundary, 'release')


def test_generation_change_during_native_result_never_reaches_apply(application):
    host, boundary, _, _, parts = application
    guard, events = parts[1], parts[6]
    original = host.normal_owner.native
    def stale(request, cancel, deadline):
        result = original(request, cancel, deadline)
        if request['action'] == 'inspect':
            guard.generation = 'b'*32
        return result
    host.normal_owner.native = stale
    with pytest.raises(Failure):
        call(boundary, 'configure')
    state = host.selection_snapshot()
    assert state['assignment'] is None and state['applied'] is None
    with pytest.raises(ValueError):
        call(boundary, 'open', 'tcp')
    assert not any(event.startswith(('prepare-', 'open-')) for event in events)


def test_mesh_applied_metadata_does_not_invent_legacy_assignment(platform):
    host, guard, owner, _, mesh, _, events, _ = platform
    owner.error = 'NETWORK'
    boundary = GuardedHost(guard, host, 7)
    assert call(boundary, 'configure') == []
    call(boundary, 'open', 'restricted')
    state = host.selection_snapshot()
    assert state['assignment'] is None and state['applied']['assignment'] is None
    assert state['applied']['transport'] == 'restricted' and not state['dynamic_fleet']
    native_context, before = mesh.snapshot(), list(events)
    host.select_next(Preference('friends-legacy-v1', 'legacy-ru', '', 'P0'))
    assert mesh.snapshot() == native_context and events == before
    assert host.selection_snapshot()['applied'] == state['applied']
    call(boundary, 'close')
    call(boundary, 'release')
