import json
import os
from pathlib import Path
import secrets
import time
import subprocess
import uuid
import sys

import pytest
import RNS

from messenger.tests.conftest import chat_runtime
from messenger.tests.test_control_ha_mailbox_links import dispatch, envelope, native_link
from messenger.relay import Spool
from messenger.codec import identity
from scripts import control_ha_handoff as handoff
from scripts import control_ha_mailbox_fence as barrier
from scripts import control_ha_mailbox_links as lineage
from scripts import control_ha_support_replace as replace
from scripts import control_ha_support_witness as witness
from scripts.control_ha_mailbox_startup import Startup, encoded
from scripts.control_ha_mailbox_control import MailboxControl, wake_control
from test_control_ha_legacy_support import installed, read, wait_for
from test_control_ha_support_replace import service


def test_mailbox_wakeup_interrupts_blocked_main_without_completing_wait(tmp_path):
    directory = tmp_path / 'ready'
    directory.mkdir(mode=0o700)
    source = Path(__file__).resolve().parents[1]
    script = ('import sys,threading\nfrom pathlib import Path\nsys.path.insert(0,sys.argv[1])\n'
              'from scripts.control_ha_mailbox_startup import arm_control_wakeup\n'
              'arm_control_wakeup(sys.argv[2])\n'
              'threading.Event().wait(60)\nPath(sys.argv[3]).touch()\n')
    completed, output = tmp_path / 'wait-completed', tmp_path / 'callback'
    process = subprocess.Popen([sys.executable, '-I', '-B', '-c', script, str(source), str(directory), str(completed)])
    try:
        wait_for(lambda: list(directory.glob('*.json')))
        bound = replace.admission.binding(process.pid)
        wait_for(lambda: 'futex' in Path(f'/proc/{process.pid}/wchan').read_text())
        probe = tmp_path / 'callback.py'
        probe.write_text('from pathlib import Path\n' + f'Path({str(output)!r}).touch()\n')
        sys.remote_exec(process.pid, str(probe))
        assert not output.exists()
        wake_control(bound, directory, os.getuid())
        wait_for(output.exists)
        assert not completed.exists() and process.poll() is None
    finally:
        process.terminate()
        process.wait(timeout=5)


def test_mailbox_wakeup_refuses_missing_stale_and_uncaught_readiness(tmp_path, monkeypatch):
    from scripts import control_ha_mailbox_control as control
    process = replace.admission.binding(os.getpid())
    with pytest.raises(ValueError, match='MAILBOX_WAKEUP_NOT_READY'):
        wake_control(process, tmp_path, os.getuid())
    path = tmp_path / (str(process['pid']) + '-' + process['start'] + '.json')
    path.write_bytes(encoded(dict(schema=1, process=dict(process, start='stale'), signal=10)))
    path.chmod(0o600)
    monkeypatch.setattr(control.os, 'pidfd_open', lambda *args: pytest.fail('must not signal before validation'))
    with pytest.raises(ValueError, match='MAILBOX_WAKEUP_BINDING'):
        wake_control(process, tmp_path, os.getuid())
    path.write_bytes(encoded(dict(schema=1, process=process, signal=int(control.signal.SIGUSR1))))
    monkeypatch.setattr(control.admission, 'read', lambda *args: b'SigCgt:\t00000000\n')
    with pytest.raises(ValueError, match='MAILBOX_WAKEUP_NOT_CAUGHT'):
        wake_control(process, tmp_path, os.getuid())


def test_joint_supervisor_retains_unit_accounting_and_terminal_stop():
    plan = dict(handoff=True, unit='family-connect-support.service', root='/root/handoff')
    unit = handoff.supervisor_unit(plan, '/opt/support/bin/python', '/root/channel.json')
    assert 'After=family-connect-support.service\n' in unit
    assert 'RestartPreventExitStatus=78\n' in unit and 'RemainAfterExit=yes\n' in unit
    assert '/handoff.py --mailbox-channel /root/channel.json --run /root/handoff\n' in unit
    assert '/runner.py' not in unit
    with pytest.raises(ValueError, match='HANDOFF_SUPERVISOR_COMMAND'):
        handoff.supervisor_unit(plan, '/opt/support/bin/python', '/root/channel\nInjected=true')


def test_root_controller_uses_existing_owner_ssh_custody_without_copying_keys(monkeypatch):
    account = handoff.pwd.getpwuid(os.getuid())
    value = dict(host='root@185.10.158.212', local_uid=account.pw_uid,
                 interpreter='/opt/apps/family_connect/venv/bin/python',
                 entry='/opt/apps/family_connect/handoff/entry.py', plan='/opt/apps/family_connect/handoff/plan.json')
    monkeypatch.setattr(handoff.os, 'geteuid', lambda: 0)
    monkeypatch.setattr(handoff, 'owned', lambda *args: encoded(value))
    channel = handoff.SSHMailbox('/root/channel.json')
    assert channel.transport['user'] == account.pw_uid and channel.transport['group'] == account.pw_gid
    assert channel.transport['extra_groups'] == [] and channel.transport['env']['HOME'] == account.pw_dir
    assert '-oStrictHostKeyChecking=yes' in channel.command and '-oBatchMode=yes' in channel.command
    assert not any('IdentityFile' in item or 'StrictHostKeyChecking=no' in item for item in channel.command)
    value['local_uid'] = True
    with pytest.raises(ValueError, match='NL1_TRANSPORT_UID'):
        handoff.SSHMailbox('/root/channel.json')


class Mailbox:
    def __init__(self, root, plan):
        self.root, self.plan = root, plan
        self.support = identity(bytes.fromhex(
            plan['old_argv'][plan['old_argv'].index('--sender-public') + 1]))
        self.peer = RNS.Identity()
        self.path = root / 'manifest.json'
        self.write(self.path, dict(schema=1, generation=secrets.token_hex(32),
            support_public=self.support.get_public_key().hex(), owner_binding_sha256=witness.sha(plan['old_binding']),
            replacement_plan_sha256=replace.digest(Path(plan['root']) / 'plan.json')))
        self.start()

    def write(self, path, value):
        path.write_bytes(encoded(value))
        path.chmod(0o600)

    def start(self):
        self.startup = Startup(self.path, owner_uid=os.getuid())
        self.spool = Spool(self.root / 'spool')
        self.relay = self.startup.create(RNS.Identity(), self.spool,
            allowed_public=[self.support.get_public_key(), self.peer.get_public_key()])

    def close(self):
        fence = self.startup.fence
        for name, function in fence.functions.items():
            function.__code__ = fence.originals[name].__code__
        fence.link_class.__init__.__code__ = fence.constructor.__code__
        for module, slot in ((fence.module, barrier.SLOT), (fence.link_module, lineage.SLOT)):
            if vars(module).get(slot) is fence:
                delattr(module, slot)
        RNS.Transport.deregister_destination(self.relay.destination)
        self.spool.close()

    def call(self, action, payload=None):
        nonce = secrets.token_hex(32)
        if action == 'reclose':
            self.write(self.startup.seal, dict(schema=1, generation=self.startup.manifest['generation'],
                manifest_sha256=self.startup.digest, opening_invalidated=True))
        request = self.root / (nonce + '.json')
        if action != 'observe':
            self.write(request, payload)
        observed = self.startup.observe() if action == 'observe' else getattr(self.startup, action)(request)
        return dict(nonce=nonce, observed=observed, unit_verified=True, restart_guard_verified=True, controller_uid=os.getuid())


@pytest.fixture
def paired(service, tmp_path, chat_runtime):
    manager, plan, root, data = service
    directory = tmp_path / 'mailbox'
    directory.mkdir(mode=0o700)
    mailbox = Mailbox(directory, plan)
    try:
        yield manager, plan, root, data, mailbox
    finally:
        mailbox.close()


def run(root, mailbox, recover=False):
    deadline = time.monotonic() + 20
    while True:
        result = handoff.Handoff(root, mailbox).run(recover=recover)
        if not result.startswith('WAITING_'):
            return result
        assert time.monotonic() < deadline, result


def notice_snapshot(data, pid, *, seed=False):
    output = data / (uuid.uuid4().hex + '.json')
    probe = output.with_suffix('.py')
    code = ('import hashlib,json,sys\nfrom pathlib import Path\nfrom contextlib import nullcontext\n'
            'from provisioning import support_worker\n'
            'frame=sys._getframe()\n'
            'while frame is not None and frame.f_code is not support_worker.main.__code__:frame=frame.f_back\n'
            'assert frame is not None\nowner=frame.f_locals["owner"]\n'
            'gate=getattr(owner,"capture_gate",None)\n'
            'with gate.operation() if gate is not None else nullcontext(),owner.store._lock,owner.store._db:\n')
    if seed:
        code += (' owner.notifications.create("handoff-synthetic",'
                 '{"device":"fixture-device","pseudonym":"fixture","public":None},'
                 '{"kind":"fixture"},"synthetic notice",1000)\n'
                 ' owner.store._put("subscription-cursor",{"position":42,"position_hash":"fixture-anchor","highwater":42})\n')
    code += (' value={"job":owner.store._get("subscription-job:handoff-synthetic"),"cursor":owner.notifications.cursor()}\n'
             ' result={"digest":hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest(),'
             '"status":value["job"]["status"],"cursor":value["cursor"]["cursor"]}\n'
             f' Path({str(output)!r}).write_text(json.dumps(result))\n')
    probe.write_text(code)
    probe.chmod(0o644)
    sys.remote_exec(pid, str(probe))
    wait_for(output.exists)
    return read(output)


@pytest.mark.parametrize('service', [True], indirect=True)
def test_joint_handoff_reclosure_code_recovery_preserves_current_data(paired, monkeypatch):
    manager, plan, root, data, mailbox = paired
    assert run(root, mailbox) == 'HANDOFF_OPEN_CAPTURE_DENIED'
    assert run(root, mailbox) == 'HANDOFF_OPEN_CAPTURE_DENIED'
    reservation = (root / 'handoff-reserved.json').read_bytes()
    dispatch(native_link(mailbox.relay, mailbox.support), envelope(mailbox.peer), monkeypatch)
    dispatch(native_link(mailbox.relay, mailbox.peer), envelope(mailbox.support), monkeypatch)
    assert mailbox.spool.stats()['count'] == 2
    with pytest.raises(ValueError, match='MAILBOX_RECLOSURE_REQUIRED'):
        replace.Replacement(root).run(recover=True)
    with pytest.raises(ValueError, match='MAILBOX_RECLOSURE_REQUIRED'):
        replace.Replacement(root)._rollback_locked(reclosure={})
    assert run(root, mailbox, recover=True) == 'ROLLED_BACK'
    assert run(root, mailbox) == 'ROLLED_BACK'
    assert (root / 'handoff-reserved.json').read_bytes() == reservation
    assert read(root / 'rolled-back.json')['data_restored'] is False
    assert mailbox.spool.stats()['count'] == 2
    dispatch(native_link(mailbox.relay, mailbox.support), envelope(mailbox.peer), monkeypatch)
    dispatch(native_link(mailbox.relay, mailbox.peer), envelope(mailbox.support), monkeypatch)
    assert mailbox.spool.stats()['count'] == 3
    assert all((Path(plan['gate']) / 'pending' / name).exists() for name in plan['pending'])


class ControllerDied(BaseException):
    pass


@pytest.mark.parametrize('code,reason,retryable,error', [
    (75, 'MAILBOX_PROBE_UNAVAILABLE', True, ConnectionError),
    (78, 'MAILBOX_CONTROL_SOURCE_CHANGED', False, ValueError),
    (255, None, False, ConnectionError)])
def test_channel_distinguishes_waiting_terminal_and_missing_response(monkeypatch, code, reason, retryable, error):
    channel = handoff.SSHMailbox.__new__(handoff.SSHMailbox)
    channel.command = ['synthetic-ssh']
    def response(command, **options):
        value = json.loads(options['input'])
        reply = encoded(dict(nonce=value['nonce'], controller_uid=0, result='REFUSED', incomplete=True,
                             reason=reason, retryable=retryable)) if code != 255 else b''
        return subprocess.CompletedProcess(command, code, reply, b'')
    monkeypatch.setattr(handoff.subprocess, 'run', response)
    with pytest.raises(error):
        channel.call('observe')


@pytest.mark.parametrize('service', [True], indirect=True)
@pytest.mark.parametrize('boundary', ['handoff-ticket', 'handoff-reserved', 'handoff-witness',
                                    'handoff-consume-intent', 'handoff-open'])
def test_controller_death_resumes_same_bound_handoff(paired, monkeypatch, boundary):
    manager, plan, root, data, mailbox = paired
    original = replace.Replacement.record
    def crash(self, name, **values):
        original(self, name, **values)
        if name == boundary:
            raise ControllerDied()
    with monkeypatch.context() as fault:
        fault.setattr(replace.Replacement, 'record', crash)
        with pytest.raises(ControllerDied):
            run(root, mailbox)
    assert run(root, mailbox) == 'HANDOFF_OPEN_CAPTURE_DENIED'
    assert run(root, mailbox, recover=True) == 'ROLLED_BACK'


@pytest.mark.parametrize('service', [True], indirect=True)
def test_lost_consume_reply_does_not_issue_a_second_witness(paired, monkeypatch):
    manager, plan, root, data, mailbox = paired
    original = mailbox.call
    def lost(action, payload=None):
        result = original(action, payload)
        if action == 'consume':
            raise ConnectionError('synthetic lost response')
        return result
    with monkeypatch.context() as fault:
        fault.setattr(mailbox, 'call', lost)
        with pytest.raises(ConnectionError):
            run(root, mailbox)
    first = read(root / 'handoff-witness.json')
    assert run(root, mailbox) == 'HANDOFF_OPEN_CAPTURE_DENIED'
    assert read(root / 'handoff-witness.json') == first
    assert run(root, mailbox, recover=True) == 'ROLLED_BACK'


@pytest.mark.parametrize('service', [True], indirect=True)
def test_lost_reclosure_reply_keeps_recovery_intent_and_never_reopens(paired, monkeypatch):
    manager, plan, root, data, mailbox = paired
    assert run(root, mailbox) == 'HANDOFF_OPEN_CAPTURE_DENIED'
    original = mailbox.call
    def lost(action, payload=None):
        result = original(action, payload)
        if action == 'reclose':
            raise ConnectionError('synthetic lost response')
        return result
    with monkeypatch.context() as fault:
        fault.setattr(mailbox, 'call', lost)
        with pytest.raises(ConnectionError):
            run(root, mailbox, recover=True)
    assert mailbox.startup.observe()['fence']['opening_invalidated']
    assert not (root / 'rollback-intent.json').exists()
    assert run(root, mailbox) == 'ROLLED_BACK'


@pytest.mark.parametrize('service', [True], indirect=True)
@pytest.mark.parametrize('restart', ['mailbox', 'candidate'])
def test_restart_invalidates_old_authority_before_recovery(paired, restart):
    manager, plan, root, data, mailbox = paired
    assert run(root, mailbox) == 'HANDOFF_OPEN_CAPTURE_DENIED'
    if restart == 'mailbox':
        mailbox.close()
        mailbox.start()
        assert run(root, mailbox) == 'ROLLED_BACK'
    else:
        manager.call('restart', manager.unit)
        wait_for(lambda: manager.state()['MainPID'] == '0')
        assert run(root, mailbox) == 'MANUAL_RECONCILIATION_REQUIRED'
        assert mailbox.startup.observe()['fence']['opening_invalidated']
        assert run(root, mailbox, recover=True) == 'ROLLED_BACK'
    assert mailbox.startup.observe()['fence']['new_link_admission'] == 'CLOSED'
    assert all((Path(plan['gate']) / 'pending' / name).exists() for name in plan['pending'])


@pytest.mark.parametrize('service', [True], indirect=True)
def test_selected_identity_pause_keeps_other_clients_and_queue(paired, monkeypatch):
    manager, plan, root, data, mailbox = paired
    assert run(root, mailbox) == 'HANDOFF_OPEN_CAPTURE_DENIED'
    pid = manager.state()['MainPID']
    notice = notice_snapshot(data, int(pid), seed=True)
    assert notice['status'] == 'saved' and notice['cursor'] == 42
    dispatch(native_link(mailbox.relay, mailbox.peer), envelope(mailbox.support), monkeypatch)
    assert handoff.Handoff(root, mailbox).run(pause=True) == 'SUPPORT_IDENTITY_PAUSED'
    assert run(root, mailbox) == 'SUPPORT_IDENTITY_PAUSED'
    assert manager.state()['MainPID'] == pid
    assert notice_snapshot(data, int(pid)) == notice
    dispatch(native_link(mailbox.relay, mailbox.support), envelope(mailbox.peer), monkeypatch)
    dispatch(native_link(mailbox.relay, mailbox.peer), envelope(mailbox.support), monkeypatch)
    assert mailbox.spool.stats()['count'] == 2
    assert run(root, mailbox, recover=True) == 'ROLLED_BACK'
    assert mailbox.spool.stats()['count'] == 2
    assert notice_snapshot(data, int(manager.state()['MainPID'])) == notice


@pytest.mark.parametrize('service', [True], indirect=True)
@pytest.mark.parametrize('boundary', ['handoff-recovery-intent', 'handoff-reclosed',
                                    'candidate-stop-intent', 'rollback-dropin-removed'])
def test_controller_death_during_recovery_cannot_reopen_or_rewind(paired, monkeypatch, boundary):
    manager, plan, root, data, mailbox = paired
    assert run(root, mailbox) == 'HANDOFF_OPEN_CAPTURE_DENIED'
    original = replace.Replacement.record
    def crash(self, name, **values):
        original(self, name, **values)
        if name == boundary:
            raise ControllerDied()
    with monkeypatch.context() as fault:
        fault.setattr(replace.Replacement, 'record', crash)
        with pytest.raises(ControllerDied):
            run(root, mailbox, recover=True)
    assert run(root, mailbox) == 'ROLLED_BACK'
    assert mailbox.startup.observe()['fence']['opening_invalidated']
    assert read(root / 'rolled-back.json')['data_restored'] is False


@pytest.mark.parametrize('service', [True], indirect=True)
def test_terminal_bridge_refuses_entire_handoff_without_remote_actions(paired, monkeypatch):
    manager, plan, root, data, mailbox = paired
    controller = handoff.Handoff(root, mailbox)
    controller.replacement.drain.mkdir(mode=0o700)
    replace.admission.write(controller.replacement.drain / 'error.json',
        dict(irreversible=True, reason='SYNTHETIC_TERMINAL', capture_permitted=False))
    def forbidden(*arguments):
        raise AssertionError('terminal handoff attempted mailbox action')
    monkeypatch.setattr(mailbox, 'call', forbidden)
    assert controller.run() == 'MANUAL_RECONCILIATION_REQUIRED'
    receipt = read(root / 'terminal-failure.json')
    assert receipt['reason'] == 'SYNTHETIC_TERMINAL' and 'error.json' in receipt['evidence']
    assert not (root / 'handoff-reserved.json').exists()
    assert not (root / 'install-intent.json').exists()
    assert manager.state()['MainPID'] == str(plan['old_binding']['pid'])


@pytest.mark.parametrize('service', [True], indirect=True)
def test_live_adoption_without_independent_restart_guard_cannot_stop_owner(paired, monkeypatch):
    manager, plan, root, data, mailbox = paired
    original = mailbox.call
    def unguarded(action, payload=None):
        result = original(action, payload)
        result['observed'].update(closed_before_publication=False, restart_defaults_closed=False, live_adoption=True)
        result['restart_guard_verified'] = False
        return result
    monkeypatch.setattr(mailbox, 'call', unguarded)
    with pytest.raises(ValueError, match='PERSISTENT_MAILBOX_GUARD_REQUIRED'):
        run(root, mailbox)
    assert not (root / 'drain-intent.json').exists()
    assert manager.state()['MainPID'] == str(plan['old_binding']['pid'])


@pytest.mark.parametrize('service', [True], indirect=True)
def test_independent_native_mailbox_process_and_owner_complete_joint_recovery(service, tmp_path):
    manager, plan, root, data = service
    source = Path(__file__).resolve().parents[1]
    directory = tmp_path / 'remote'
    directory.mkdir(mode=0o750)
    runtime = directory / 'runtime'
    runtime.mkdir(mode=0o700)
    controls = directory / 'control'
    controls.mkdir(mode=0o750)
    (controls / 'responses').mkdir(mode=0o700)
    public = plan['old_argv'][plan['old_argv'].index('--sender-public') + 1]
    manifest = directory / 'manifest.json'
    manifest.write_bytes(encoded(dict(schema=1, generation=secrets.token_hex(32), support_public=public,
        owner_binding_sha256=witness.sha(plan['old_binding']), replacement_plan_sha256=replace.digest(root / 'plan.json'))))
    manifest.chmod(0o600)
    allowed = directory / 'allowed.json'
    allowed.write_bytes(encoded([public, RNS.Identity().get_public_key().hex()]))
    interpreter = os.environ['FC_TEST_SUPPORT_PYTHON']
    arguments = [interpreter, '-I', '-B', str(source / 'tests/fixtures/mailbox_startup.py'),
                 str(runtime), str(manifest), str(allowed), str(os.getuid())]
    unit = 'fc-ha-mailbox-handoff-test-' + uuid.uuid4().hex + '.service'
    unit_path = Path(os.environ['XDG_RUNTIME_DIR']) / 'systemd/user' / unit
    unit_path.write_text('[Service]\nType=simple\nRestart=on-failure\nEnvironment=FC_TEST_PTRACER_ANY=1\n'
                         'ExecStart=' + ' '.join(arguments) + '\n')
    files = ['scripts/control_ha_mailbox_startup.py', 'scripts/control_ha_mailbox_links.py',
             'scripts/control_ha_mailbox_fence.py', 'scripts/control_ha_legacy_support.py',
             'tests/fixtures/mailbox_startup.py']
    control_plan = directory / 'control-plan.json'
    control_plan.write_bytes(encoded(dict(schema=1, unit=unit, user=True, manifest=str(manifest), argv=arguments,
        restart_argv=arguments,
        files={str(unit_path): replace.digest(unit_path)}, sources={str(source / name): replace.digest(source / name)
        for name in files}, interpreter=str(Path(interpreter).resolve()),
        interpreter_sha256=replace.digest(Path(interpreter).resolve()), runtime=str(controls), uid=os.getuid(), gid=os.getgid())))
    control_plan.chmod(0o600)
    class Endpoint:
        def call(self, action, payload=None):
            return MailboxControl(control_plan).call(dict(action=action, nonce=secrets.token_hex(32), payload=payload))
    endpoint = Endpoint()
    try:
        subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', '--user', 'start', unit], check=True)
        wait_for(lambda: (runtime / 'control.sock').exists())
        first = endpoint.call('observe')
        assert first['observed']['ticket']['process']['pid'] != os.getpid()
        assert run(root, endpoint) == 'HANDOFF_OPEN_CAPTURE_DENIED'
        assert run(root, endpoint, recover=True) == 'ROLLED_BACK'
        observed = endpoint.call('observe')['observed']
        assert observed['fence']['opening_invalidated'] and observed['fence']['in_process_drained']
        subprocess.run(['systemctl', '--user', 'restart', unit], check=True)
        deadline = time.monotonic() + 8
        while True:
            try:
                observed = endpoint.call('observe')['observed']
                break
            except (ValueError, OSError):
                assert time.monotonic() < deadline
                time.sleep(.01)
        assert observed['ticket'] != first['observed']['ticket']
        assert observed['fence']['opening_invalidated'] and observed['fence']['new_link_admission'] == 'CLOSED'
    finally:
        subprocess.run(['systemctl', '--user', 'stop', unit], check=False, capture_output=True)
        unit_path.unlink()
        subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', '--user', 'reset-failed', unit], check=False, capture_output=True)
