import json
import hashlib
import os
from pathlib import Path
import secrets

import pytest

from scripts import control_ha_mailbox_generation as generation
from scripts import control_ha_mailbox_startup as startup
from scripts import control_ha_support_resume as resume
from scripts import control_ha_support_replace as replace
from test_control_ha_support_handoff import paired, run, notice_snapshot, chat_runtime
from test_control_ha_support_replace import service
from test_control_ha_legacy_support import installed, wait_for, read, install_collector_sources


class Channel:
    def __init__(self, mailbox):
        self.mailbox = mailbox
        self.lose_response = False

    def call(self, action, payload=None):
        if action != 'resume':
            return self.mailbox.call(action, payload)
        request = self.mailbox.root / (secrets.token_hex(16) + '.json')
        self.mailbox.write(request, payload)
        observed = generation.consume(self.mailbox.startup, request)
        if self.lose_response:
            self.lose_response = False
            raise TimeoutError('synthetic response loss')
        return dict(observed=observed, controller_uid=os.getuid(), unit_verified=True, restart_guard_verified=True)


def prepared(paired, monkeypatch, installed_collectors=False):
    manager, plan, root, data, mailbox = paired
    assert run(root, mailbox) == 'HANDOFF_OPEN_CAPTURE_DENIED'
    before = notice_snapshot(data, int(manager.state()['MainPID']), seed=True)
    authority = Path(plan['start_authority']).read_bytes()
    history = {name: (root / name).read_bytes() for name in ('accepted.json', 'handoff-reserved.json', 'handoff-open.json')}
    mailbox.call('reclose', dict(action='RECLOSE', ticket=mailbox.startup.ticket()))
    reclosure = mailbox.call('observe')
    manager.call('kill', '--signal=SIGTERM', '--kill-whom=main', manager.unit)
    wait_for(lambda: manager.state()['MainPID'] == '0', seconds=15)
    stopped = manager.state()
    assert stopped['ExecMainCode'] == '1' and stopped['ExecMainStatus'] == '0', {
        name: stopped[name] for name in ('ActiveState', 'SubState', 'MainPID', 'ExecMainCode', 'ExecMainStatus')}
    newer = root.with_name(root.name + '-resume')
    if installed_collectors:
        install_collector_sources(Path(plan['baseline']))
        with pytest.raises(ValueError, match='SOURCE_CLOSURE'):
            resume.absence(replace.Replacement(root))
    stage_generation(root, newer, data / 'resume', mailbox, reclosure, monkeypatch,
                     installed_collectors=installed_collectors)
    return newer, Channel(mailbox), before, authority, history


def stage_generation(previous, newer, participant, mailbox, reclosure, monkeypatch, installed_collectors=False):
    next_plan = resume.prepare(previous, newer, participant, installed_collectors=installed_collectors)
    interpreter = os.environ['FC_TEST_SUPPORT_PYTHON']
    wrapper = Path(__file__).parent / 'fixtures/support_ptracer.py'
    raw = (newer / 'support.conf').read_bytes().replace(('ExecStart=' + interpreter).encode(),
        ('ExecStart=' + interpreter + ' -I -B ' + str(wrapper) + ' ' + interpreter).encode())
    (newer / 'support.conf').write_bytes(raw)
    next_plan['dropin_sha256'] = hashlib.sha256(raw).hexdigest()
    (newer / 'plan.json').write_text(json.dumps(next_plan))
    replace.admission.write(newer / 'predecessor-reclosure.json', reclosure)
    manifest = dict(mailbox.startup.manifest, generation=secrets.token_hex(32),
                    owner_binding_sha256=generation.digest(next_plan['old_binding']),
                    replacement_plan_sha256=replace.digest(newer / 'plan.json'))
    manifest_path = mailbox.root / (newer.name + '.json')
    mailbox.write(manifest_path, manifest)
    request = mailbox.root / ('advance-' + newer.name + '.json')
    mailbox.write(request, dict(action='ADVANCE_CLOSED_GENERATION', ticket=mailbox.startup.ticket(),
                  manifest=str(manifest_path), manifest_sha256=replace.digest(manifest_path)))
    monkeypatch.setattr(startup, 'ACTIVE', mailbox.startup)
    generation.advance(mailbox.startup, request)
    mailbox.startup = startup.ACTIVE


@pytest.mark.parametrize('service', [True], indirect=True)
@pytest.mark.parametrize('lost', [False, True])
@pytest.mark.parametrize('installed_collectors', [False, True])
def test_forward_resume_new_process_retains_nonempty_queue_and_old_authority(paired, monkeypatch, lost, installed_collectors):
    manager, plan, root, data, mailbox = paired
    newer, channel, before, authority, history = prepared(paired, monkeypatch, installed_collectors)
    channel.lose_response = lost
    controller = resume.Resume(newer, channel)
    if lost:
        with pytest.raises(TimeoutError):
            controller.run()
        assert not (newer / 'handoff-open.json').exists()
    assert controller.run() == 'FORWARD_RESUME_OPEN_CAPTURE_DENIED'
    accepted = read(newer / 'accepted.json')
    assert accepted['binding'] != read(root / 'accepted.json')['binding']
    assert Path(plan['start_authority']).read_bytes() == authority
    assert {name: (root / name).read_bytes() for name in history} == history
    assert notice_snapshot(data, int(manager.state()['MainPID'])) == before
    assert controller.run() == 'FORWARD_RESUME_OPEN_CAPTURE_DENIED'
    assert read(newer / 'accepted.json') == accepted
    assert all((Path(plan['gate']) / 'pending' / name).exists() for name in plan['pending'])


@pytest.mark.parametrize('service', [True], indirect=True)
def test_invalid_predecessor_reclosure_never_starts_writer(paired, monkeypatch):
    manager, plan, root, data, mailbox = paired
    newer, channel, before, authority, history = prepared(paired, monkeypatch)
    proof = read(newer / 'predecessor-reclosure.json')
    proof['observed']['fence']['accepted_target_work'] = 1
    (newer / 'predecessor-reclosure.json').write_text(json.dumps(proof))
    with pytest.raises(ValueError, match='PREDECESSOR_RECLOSURE_REQUIRED'):
        resume.Resume(newer, channel).run()
    assert manager.state()['MainPID'] == '0'
    assert not Path(read(newer / 'plan.json')['start_authority']).exists()
    assert not (newer / 'candidate-start-intent.json').exists()


@pytest.mark.parametrize('service', [True], indirect=True)
@pytest.mark.parametrize('changed', ['boot', 'ticket'])
def test_stale_boot_or_ticket_refuses_same_resume_operation(paired, monkeypatch, changed):
    manager, plan, root, data, mailbox = paired
    newer, channel, before, authority, history = prepared(paired, monkeypatch)
    controller = resume.Resume(newer, channel)
    if changed == 'boot':
        controller.predecessor['absence']['boot'] = 'previous-boot'
        reason = 'RESUME_BOOT_CHANGED'
    else:
        assert controller.run() == 'FORWARD_RESUME_OPEN_CAPTURE_DENIED'
        mailbox.startup.challenge = secrets.token_hex(32)
        reason = 'RESUME_TICKET_CHANGED'
    with pytest.raises(ValueError, match=reason):
        controller.run()
    refused = read(next(newer.glob('resume-refusal-*.json')))
    assert refused['reason'] == reason and refused['closure']['confirmed']
    assert mailbox.startup.observe()['fence']['opening_invalidated']


class ControllerInterrupted(BaseException):
    pass


@pytest.mark.parametrize('service', [True], indirect=True)
@pytest.mark.parametrize('boundary', ['install-intent', 'candidate-binding-intent', 'accepted', 'resume-request'])
def test_interrupted_controller_resumes_the_same_operation(paired, monkeypatch, boundary):
    manager, plan, root, data, mailbox = paired
    newer, channel, before, authority, history = prepared(paired, monkeypatch)
    record = replace.Replacement.record

    def interrupted(self, name, **values):
        record(self, name, **values)
        if self.root == newer and name == boundary:
            raise ControllerInterrupted()

    with monkeypatch.context() as fault:
        fault.setattr(replace.Replacement, 'record', interrupted)
        with pytest.raises(ControllerInterrupted):
            resume.Resume(newer, channel).run()
    assert resume.Resume(newer, channel).run() == 'FORWARD_RESUME_OPEN_CAPTURE_DENIED'
    assert notice_snapshot(data, int(manager.state()['MainPID'])) == before
    assert Path(plan['start_authority']).read_bytes() == authority


@pytest.mark.parametrize('service', [True], indirect=True)
def test_expired_unadmitted_start_is_not_silently_restarted(paired, monkeypatch):
    manager, plan, root, data, mailbox = paired
    newer, channel, before, authority, history = prepared(paired, monkeypatch)
    record = replace.Replacement.record

    def interrupted(self, name, **values):
        record(self, name, **values)
        if self.root == newer and name == 'candidate-binding-intent':
            raise ControllerInterrupted()

    with monkeypatch.context() as fault:
        fault.setattr(replace.Replacement, 'record', interrupted)
        with pytest.raises(ControllerInterrupted):
            resume.Resume(newer, channel).run()
    wait_for(lambda: manager.state()['MainPID'] == '0', seconds=10)
    diagnostic = read(next((data / 'resume/refusals').iterdir()))
    assert diagnostic['phase'] == 'authority' and diagnostic['reason'] == 'START_AUTHORITY_MISSING'
    with pytest.raises(ValueError, match='RESUME_ATTEMPT_ENDED'):
        resume.Resume(newer, channel).run()
    assert manager.state()['MainPID'] == '0'
    assert mailbox.startup.observe()['fence']['opening_invalidated']
    saved = next((data / 'resume/refusals').iterdir()).read_bytes()
    next_root = newer.with_name(newer.name + '-retry')
    stage_generation(newer, next_root, data / 'retry', mailbox, channel.call('observe'), monkeypatch)
    assert resume.Resume(next_root, Channel(mailbox)).run() == 'FORWARD_RESUME_OPEN_CAPTURE_DENIED'
    assert notice_snapshot(data, int(manager.state()['MainPID'])) == before
    assert next((data / 'resume/refusals').iterdir()).read_bytes() == saved
    assert Path(plan['start_authority']).read_bytes() == authority


@pytest.mark.parametrize('service', [True], indirect=True)
def test_terminal_predecessor_is_never_retried_or_rewritten(paired, monkeypatch):
    manager, plan, root, data, mailbox = paired
    newer, channel, before, authority, history = prepared(paired, monkeypatch)
    terminal = newer / 'terminal-failure.json'
    replace.admission.write(terminal, dict(reason='SYNTHETIC_TERMINAL', capture_permitted=False))
    retained = terminal.read_bytes()
    for _attempt in range(2):
        with pytest.raises(ValueError, match='RESUME_TERMINAL_FAILURE'):
            resume.Resume(newer, channel).run()
        assert terminal.read_bytes() == retained and manager.state()['MainPID'] == '0'
        assert not (newer / 'candidate-start-intent.json').exists()
    assert mailbox.startup.observe()['fence']['opening_invalidated']
