import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'linux'))
import auto_policy as policy


def status():
    return dict(generation=1, state='CONNECTED', desired_connected=True, retry_at_ms=0,
                events=[dict(event='candidate_succeeded', state='CONNECTED', elapsed_ms=10)], events_dropped=0)


@pytest.mark.parametrize('frame', [
    dict(reply=dict(schema=1, id=1, ok=True, snapshot=status())),
    dict(host_call=dict(schema=1, id=1, generation=1, operation='open', candidate='restricted', budget_ms=200000)),
    dict(host_call=dict(schema=1, id=2, generation=1, operation='configure', budget_ms=30000)),
    dict(host_cancel=dict(schema=1, id=2))])
def test_exact_native_frames(frame):
    before = copy.deepcopy(frame)
    kind, result = policy.validate_frame(frame)
    assert result == frame[kind]
    assert before == frame


@pytest.mark.parametrize('frame', [
    {}, {'host_cancel': {'schema': True, 'id': 1}},
    {'host_call': dict(schema=1, id=1, generation=1, operation='exec', budget_ms=1)},
    {'host_call': dict(schema=1, id=1, generation=1, operation='open', candidate='awg', budget_ms=20001)},
    {'host_call': dict(schema=1, id=1, generation=1, operation='remember', candidate='restricted', budget_ms=1000)},
    {'host_call': dict(schema=1, id=1, generation=1, operation='release', budget_ms=1000, candidate='awg')},
    {'host_call': dict(schema=1, id=1, generation=1, operation='configure', budget_ms=1000, profile='private')},
    {'host_cancel': dict(schema=1, id=1, command='shell')},
    {'reply': dict(schema=1, id=1, ok=True, error='INTERNAL', snapshot=status())},
    {'reply': dict(schema=1, id=1, ok=True, snapshot={**status(), 'private_key': 'private'})},
    {'reply': dict(schema=1, id=1, ok=True, snapshot={**status(), 'events': [status()['events'][0]] * 129})},
    {'reply': dict(schema=1, id=1, ok=True, snapshot={**status(), 'events': [dict(event='https://room/private', state='CONNECTED', elapsed_ms=1)]})},
    {'reply': dict(schema=1, id=1, ok=True, snapshot={**status(), 'selected': 'QUIC'})}])
def test_unbounded_privileged_or_unknown_fields_are_rejected(frame):
    with pytest.raises((ValueError, TypeError)):
        policy.validate_frame(frame)


class Guard:
    def __init__(self, events):
        self.events, self.record = events, None

    def acquire(self):
        self.events.append('guard-acquire')
        self.record = {}

    def prepare(self, plan):
        assert plan == {'kind': 'awg'}
        self.events.append('guard-probe')

    def ready(self, index, ipv6):
        assert index == 3 and ipv6 is False
        self.events.append('guard-ready')

    def block(self):
        self.events.append('guard-block')

    def release(self):
        self.events.append('guard-release')
        self.record = None


class Platform:
    def __init__(self, events):
        self.events, self.cancel_open = events, False

    def configure(self, context):
        self.events.append('configure')
        return ['awg', 'tcp']

    def prepare(self, context, candidate):
        self.events.append('prepare-' + candidate)
        return dict(kind='awg')

    def open(self, context, candidate):
        self.events.append('open-' + candidate)
        if self.cancel_open:
            context.cancel.set()
        return 3, False

    def close(self, context):
        self.events.append('close')

    def release(self, context):
        self.events.append('release')

    def remember(self, context, candidate):
        self.events.append('remember-' + candidate)


def call(host, action, generation=5, candidate=None):
    return host.call(dict(operation=action, generation=generation, candidate=candidate), policy.Context(1000))


def test_guard_order_wraps_platform_without_another_recovery_machine():
    events = []
    host = policy.GuardedHost(Guard(events), Platform(events), 5)
    assert call(host, 'configure') == ['awg', 'tcp']
    call(host, 'close')
    call(host, 'open', candidate='awg')
    call(host, 'remember', candidate='awg')
    call(host, 'close')
    call(host, 'release')
    host.abort()
    assert events == ['guard-acquire', 'configure', 'guard-block', 'close', 'prepare-awg', 'guard-probe',
                      'open-awg', 'guard-ready', 'remember-awg', 'guard-block', 'close', 'release', 'guard-release']


def test_late_open_after_cancel_never_marks_guard_ready():
    events = []
    platform = Platform(events)
    host = policy.GuardedHost(Guard(events), platform, 5)
    call(host, 'configure')
    platform.cancel_open = True
    with pytest.raises(policy.Failure, match='CANCELLED'):
        call(host, 'open', candidate='awg')
    assert 'guard-ready' not in events
    host.abort()
    assert events[-2:] == ['guard-block', 'close']
    assert 'guard-release' not in events


def test_wrong_generation_cannot_touch_platform_or_firewall():
    events = []
    host = policy.GuardedHost(Guard(events), Platform(events), 5)
    with pytest.raises(ValueError):
        call(host, 'configure', generation=4)
    assert events == []


def test_restricted_success_cannot_be_an_awg_fallback():
    events = []
    host = policy.GuardedHost(Guard(events), Platform(events), 5)
    call(host, 'configure')
    with pytest.raises(ValueError):
        call(host, 'open', candidate='restricted')
    assert 'guard-probe' not in events and 'guard-ready' not in events


def test_partial_close_is_not_followed_by_guard_release():
    events = []
    host = policy.GuardedHost(Guard(events), Platform(events), 5)
    call(host, 'configure')

    def failed(context):
        raise OSError('private details')

    host.platform.close = failed
    with pytest.raises(OSError):
        call(host, 'close')
    assert events[-1] == 'guard-block'
    assert 'guard-release' not in events


def test_no_root_policy_owner_in_gui_context(monkeypatch):
    monkeypatch.setattr(policy.os, 'geteuid', lambda: 1000)
    with pytest.raises(PermissionError):
        policy.PolicyProcess(None, '/never-executed')


def test_snapshot_detaches_and_failure_has_no_raw_detail():
    original = status()
    copied = policy.snapshot(original)
    copied['events'][0]['state'] = 'FAILED'
    assert original['events'][0]['state'] == 'CONNECTED'
    failure = policy.Failure('https://private/token', temporary=True)
    assert str(failure) == 'INTERNAL' and failure.temporary is False
