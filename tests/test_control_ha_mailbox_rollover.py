import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import control_ha_mailbox_rollover as rollover


@pytest.fixture
def staged(tmp_path, monkeypatch):
    tmp_path.chmod(0o700)
    monkeypatch.setattr(rollover, 'STATE_ROOT', tmp_path)
    monkeypatch.setattr(rollover, 'UNIT_ROOT', tmp_path / 'units')
    monkeypatch.setattr(rollover.os, 'geteuid', lambda: 0)
    monkeypatch.setattr(rollover.os, 'chown', lambda *args: None)
    monkeypatch.setattr(rollover, 'read', lambda path: json.loads(Path(path).read_bytes()))
    previous = tmp_path / 'previous.json'
    old_manifest = tmp_path / 'previous-manifest.json'
    old_manifest.write_text(json.dumps(dict(generation='a' * 64, support_public='b' * 128,
                                           replacement_plan_sha256='c' * 64)))
    dropin = tmp_path / 'units/family-connect-mailbox.service.d/zzzz-startup.conf'
    dropin.parent.mkdir(parents=True)
    dropin.write_text('original settings')
    plan = dict(unit='family-connect-mailbox.service', manifest=str(old_manifest), uid=os.getuid(), gid=os.getgid(),
                files={str(dropin): rollover.sha(dropin)},
                sources={'/opt/apps/family_connect/mailbox-pilot/app/messenger/server.py': 'c' * 64},
                argv=['/usr/bin/python3.14', '-m', 'messenger.server'],
                restart_argv=['/usr/bin/python3.14', '-I', '-B', '/old/startup.py', '--manifest', str(old_manifest)])
    previous.write_text(json.dumps(plan))
    selected = {name: 'unchanged' for name in rollover.LIMITS}
    selected.update(CPUQuotaPerSecUSec='1s', MemoryMax='805306368')
    monkeypatch.setattr(rollover, 'limits', lambda unit: dict(selected))
    state = SimpleNamespace(current='old', closed=False, busy=0, advances=0, lose=False, reloads=0)
    manifest = tmp_path / 'manifest-input.json'
    manifest.write_text(json.dumps(dict(schema=1, generation='d' * 64, support_public='b' * 128,
                                       replacement_plan_sha256='e' * 64, owner_binding_sha256='f' * 64)))
    root = tmp_path / 'next'

    class Controller:
        def __init__(self, filename):
            self.filename = Path(filename)
            self.plan = json.loads(self.filename.read_bytes())

        def call(self, value):
            if self.filename.name == 'control.json' and state.current == 'old':
                raise ValueError('MAILBOX_ACTIVE_MANIFEST')
            if value['action'] == 'reclose':
                state.closed = True
            elif value['action'] == 'advance':
                assert state.closed and state.busy == 0
                state.current = 'new'
                state.advances += 1
                if state.lose:
                    state.lose = False
                    raise TimeoutError('synthetic lost advance response')
            return dict(unit_verified=True, controller_uid=0, observed=dict(
                ticket=dict(process=dict(pid=123), manifest_sha256=rollover.sha(root / 'manifest.json') if
                            state.current == 'new' else 'a' * 64), consumed=None,
                fence=dict(new_link_admission='CLOSED' if state.closed else 'OPEN_LOCAL_ONLY',
                           opening_invalidated=state.current == 'old' and state.closed,
                           in_process_drained=state.busy == 0, accepted_target_work=state.busy)))

    monkeypatch.setattr(rollover, 'MailboxControl', Controller)
    monkeypatch.setattr(rollover, 'GenerationControl', Controller)

    def reload(command, **kwargs):
        assert command == ['systemctl', 'daemon-reload']
        state.reloads += 1

    monkeypatch.setattr(rollover.subprocess, 'run', reload)
    rollover.prepare(previous, root, manifest)
    return root, state, dropin, selected


def test_rollover_does_not_restart_mailbox_and_preserves_predecessor(staged):
    root, state, old_dropin, selected = staged
    first = rollover.activate(root)
    assert first['observed']['fence']['new_link_admission'] == 'CLOSED'
    assert state.advances == 1 and old_dropin.read_text() == 'original settings'
    retained = (root / 'predecessor-reclosure.json').read_bytes()
    assert rollover.activate(root) == first
    assert state.advances == 1 and (root / 'predecessor-reclosure.json').read_bytes() == retained


def test_response_loss_after_advance_is_reconciled_without_repeating_transition(staged):
    root, state, old_dropin, selected = staged
    state.lose = True
    with pytest.raises(TimeoutError):
        rollover.activate(root)
    assert state.current == 'new' and state.advances == 1
    assert rollover.activate(root)['observed']['fence']['new_link_admission'] == 'CLOSED'
    assert state.advances == 1


def test_busy_writer_retains_readback_and_leaves_closed_without_install(staged):
    root, state, old_dropin, selected = staged
    state.busy = 1
    with pytest.raises(ValueError, match='MAILBOX_BUSY_OR_NOT_INVALIDATED'):
        rollover.activate(root)
    assert state.closed and state.current == 'old' and state.advances == state.reloads == 0
    record = json.loads(next(root.glob('reclosure-readback-*.json')).read_bytes())
    assert record['observed']['fence']['accepted_target_work'] == 1
    assert not Path(json.loads((root / 'rollover.json').read_bytes())['dropin']).exists()


def test_changed_resource_limit_refuses_before_closure(staged):
    root, state, old_dropin, selected = staged
    selected['MemoryMax'] = '536870912'
    with pytest.raises(ValueError, match='MAILBOX_LIMITS_CHANGED'):
        rollover.activate(root)
    assert not state.closed and not state.advances


def test_controller_interruption_after_install_can_resume_without_opening(staged, monkeypatch):
    root, state, old_dropin, selected = staged
    original = rollover.subprocess.run

    def lost_controller(*args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(rollover.subprocess, 'run', lost_controller)
    with pytest.raises(KeyboardInterrupt):
        rollover.activate(root)
    assert state.closed and not state.advances
    monkeypatch.setattr(rollover.subprocess, 'run', original)
    rollover.activate(root)
    assert state.current == 'new' and state.advances == 1
