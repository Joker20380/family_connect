import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

from scripts import control_ha_support_replace as replace
from scripts import control_ha_support_witness as witness
from scripts.control_ha_mailbox_startup import Startup, encoded
from test_control_ha_legacy_support import installed, read, wait_for
from test_control_ha_support_replace import service, eventually


def ticket_for(root, plan):
    path = root / 'mailbox-manifest.json'
    public = plan['old_argv'][plan['old_argv'].index('--sender-public') + 1]
    path.write_bytes(encoded(dict(schema=1, generation='a' * 64, support_public=public,
                                 owner_binding_sha256=witness.sha(plan['old_binding']),
                                 replacement_plan_sha256=replace.digest(root / 'plan.json'))))
    path.chmod(0o600)
    return Startup(path, owner_uid=os.geteuid()).ticket()


def test_independent_live_witness_binds_ticket_and_blocks_legacy_rollback(service):
    manager, plan, root, data = service
    ticket = ticket_for(root, plan)
    with pytest.raises(FileNotFoundError):
        witness.sample(root, ticket)
    assert not (root / 'handoff-reserved.json').exists()
    assert eventually(root) == 'ACCEPTED'
    result = witness.sample(root, ticket)
    assert result['owner_exit_verified'] is True
    assert result['fixture'] is True
    assert result['ticket_sha256'] == witness.sha(ticket)
    assert result['candidate_binding']['pid'] == int(manager.state()['MainPID'])
    assert not result['mailbox_live_verified'] and not result['opening_permitted'] and not result['capture_permitted']
    assert witness.sample(root, ticket)['candidate_binding'] == result['candidate_binding']
    assert eventually(root) == 'ALREADY_ACCEPTED'
    for call in (lambda: eventually(root, recover=True), lambda: replace.Replacement(root).rollback()):
        with pytest.raises(ValueError, match='MAILBOX_RECLOSURE_REQUIRED'):
            call()
    assert not (root / 'rollback-intent.json').exists()
    assert manager.state()['MainPID'] == str(result['candidate_binding']['pid'])
    assert all((Path(plan['gate']) / 'pending' / name).exists() for name in plan['pending'])
    changed = dict(ticket, challenge='d' * 64)
    with pytest.raises(ValueError, match='HANDOFF_ALREADY_BOUND'):
        witness.sample(root, changed)


def test_witness_rejects_unbound_ticket_fields_without_reservation(service):
    manager, plan, root, data = service
    ticket = ticket_for(root, plan)
    assert eventually(root) == 'ACCEPTED'
    variants = [dict(ticket, schema=True), dict(ticket, extra=1), dict(ticket, process={}),
                dict(ticket, process=dict(ticket['process'], pid=True)),
                dict(ticket, process=dict(ticket['process'], boot='invalid'))]
    variants += [dict(ticket, **{name: 'wrong'}) for name in
                 ('generation', 'manifest_sha256', 'challenge', 'owner_binding_sha256', 'replacement_plan_sha256')]
    variants += [dict(ticket, **{name: 'c' * 64}) for name in ('owner_binding_sha256', 'replacement_plan_sha256')]
    variants.append(dict(ticket, support_public_sha256='c' * 64))
    for changed in variants:
        with pytest.raises(ValueError):
            witness.sample(root, changed)
        assert not (root / 'handoff-reserved.json').exists()
    assert eventually(root, recover=True) == 'ROLLED_BACK'
    with pytest.raises(ValueError, match='REPLACEMENT_NOT_COMMITTED'):
        witness.sample(root, ticket)


@pytest.mark.parametrize('name', ['old-exited.json', 'accepted.json', 'drain/ready.json', 'drain/commit.json',
                                 'drain/committed.json', 'drain/exited.json'])
def test_witness_requires_complete_nonforged_evidence(service, name):
    manager, plan, root, data = service
    ticket = ticket_for(root, plan)
    assert eventually(root) == 'ACCEPTED'
    path = Path(plan['participant']) / name if name.startswith('drain/') else root / name
    value = read(path)
    if name == 'old-exited.json':
        value['state']['ControlPID'] = '123'
    elif name == 'accepted.json':
        value['binding']['pid'] = os.getpid()
    elif name in ('drain/ready.json', 'drain/commit.json'):
        value['request_sha256'] = '0' * 64
    else:
        value['capture_permitted'] = True
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        witness.sample(root, ticket)
    assert not (root / 'handoff-reserved.json').exists()


def test_witness_and_recovery_share_controller_lock(service):
    manager, plan, root, data = service
    ticket = ticket_for(root, plan)
    assert eventually(root) == 'ACCEPTED'
    with replace.controller_lock(root):
        with pytest.raises(BlockingIOError):
            witness.sample(root, ticket)
        with pytest.raises(BlockingIOError):
            replace.Replacement(root).run(recover=True)
        with pytest.raises(BlockingIOError):
            replace.Replacement(root).rollback()
    assert not (root / 'handoff-reserved.json').exists()


def test_controller_death_after_durable_reservation_never_unlocks_rollback(service):
    manager, plan, root, data = service
    ticket = ticket_for(root, plan)
    assert eventually(root) == 'ACCEPTED'
    source = Path(__file__).resolve().parents[1]
    code = ('import os,sys,json;sys.path.insert(0,sys.argv[1]);'
            'from scripts import control_ha_support_replace as replacement;'
            'from scripts.control_ha_support_witness import sample;record=replacement.Replacement.record\n'
            'def crash(self,name,**value):\n'
            ' record(self,name,**value)\n'
            ' if name=="handoff-reserved":os._exit(71)\n'
            'replacement.Replacement.record=crash\n'
            'sample(sys.argv[2],json.loads(sys.argv[3]))\n')
    child = subprocess.run([sys.executable, '-I', '-c', code, str(source), str(root), json.dumps(ticket)],
                           capture_output=True, timeout=15)
    assert child.returncode == 71, child.stderr.decode()
    with pytest.raises(ValueError, match='MAILBOX_RECLOSURE_REQUIRED'):
        eventually(root, recover=True)
    result = witness.sample(root, ticket)
    assert result['owner_exit_verified'] is True
    assert not result['opening_permitted']


def test_candidate_death_after_reservation_requires_reconciliation(service):
    manager, plan, root, data = service
    ticket = ticket_for(root, plan)
    assert eventually(root) == 'ACCEPTED'
    witness.sample(root, ticket)
    manager.call('stop', '--no-block', manager.unit)
    wait_for(lambda: manager.state()['MainPID'] == '0')
    with pytest.raises(ValueError):
        witness.sample(root, ticket)
    with pytest.raises(ValueError, match='MAILBOX_RECLOSURE_REQUIRED'):
        eventually(root, recover=True)
    assert (root / 'handoff-reserved.json').exists()
    manager.call('start', manager.unit)
    wait_for(lambda: manager.state()['MainPID'] != '0')
    with pytest.raises(ValueError, match='ACCEPTED_RUNTIME_CHANGED'):
        witness.sample(root, ticket)


def test_changed_source_and_unsafe_receipts_do_not_reserve_handoff(service):
    manager, plan, root, data = service
    ticket = ticket_for(root, plan)
    assert eventually(root) == 'ACCEPTED'
    for path in (root / 'scripts/control_ha_support_replace.py', root / 'support.conf'):
        raw = path.read_bytes()
        try:
            path.write_bytes(raw + b'\n')
            with pytest.raises(ValueError):
                witness.sample(root, ticket)
            assert not (root / 'handoff-reserved.json').exists()
        finally:
            path.write_bytes(raw)
    receipt = root / 'accepted.json'
    receipt.chmod(0o666)
    try:
        with pytest.raises(ValueError, match='UNSAFE_CONTROL_FILE'):
            witness.sample(root, ticket)
        assert not (root / 'handoff-reserved.json').exists()
    finally:
        receipt.chmod(0o600)
    assert eventually(root, recover=True) == 'ROLLED_BACK'


def test_dangling_reservation_cannot_bypass_rollback_refusal(tmp_path):
    replacement = replace.Replacement.__new__(replace.Replacement)
    replacement.root = tmp_path
    (tmp_path / 'handoff-reserved.json').symlink_to(tmp_path / 'absent')
    with pytest.raises(ValueError, match='MAILBOX_RECLOSURE_REQUIRED'):
        replacement.run(recover=True)
    with pytest.raises(ValueError, match='MAILBOX_RECLOSURE_REQUIRED'):
        replacement.rollback()


def test_empty_requires_no_control_process():
    with pytest.raises(ValueError, match='SERVICE_NOT_EMPTY'):
        replace.empty(dict(MainPID='0', ControlPID='123', ActiveState='inactive', ControlGroup=''), '')


def test_native_mailbox_ticket_binds_real_owner_but_does_not_open_admission(service):
    from messenger.tests.test_control_ha_mailbox_restart import prepare, request
    from messenger.tests.test_control_ha_mailbox_startup import write

    manager, plan, root, data = service
    runtime = data / 'mailbox'
    runtime.mkdir(mode=0o700)
    publics = prepare(runtime)
    publics[0] = plan['old_argv'][plan['old_argv'].index('--sender-public') + 1]
    shutil.copyfile(data / 'synthetic.identity', runtime / 'support/synthetic.identity')
    allowed = write(root / 'allowed.json', publics)
    ticket_for(root, plan)
    manifest = root / 'mailbox-manifest.json'
    source = Path(__file__).resolve().parents[1]
    processes = []

    def start():
        child = subprocess.Popen([sys.executable, '-B', str(source / 'tests/fixtures/mailbox_startup.py'),
                                  str(runtime), str(manifest), str(allowed), str(os.getuid())],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                 env={**os.environ, 'PYTHONPATH': str(source)})
        processes.append(child)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            assert child.poll() is None, child.communicate()[1]
            try:
                status = request(runtime, 'status')
                if status['ticket']['process']['pid'] == child.pid:
                    return child, status
            except (OSError, KeyError):
                pass
            time.sleep(.05)
        raise AssertionError('mailbox fixture startup timeout')

    try:
        first, status = start()
        assert status['fence']['new_link_admission'] == 'CLOSED'
        assert request(runtime, 'support') == ['unavailable']
        assert eventually(root) == 'ACCEPTED'
        result = witness.sample(root, status['ticket'])
        assert result['owner_exit_verified']
        refusal = request(runtime, 'open', path=str(write(root / 'witness.json', result)))
        assert refusal['reason'] == 'STALE_OR_UNBOUND_TICKET'
        assert request(runtime, 'support') == ['unavailable']
        assert request(runtime, 'peer') == ['stored']
        first.kill()
        assert first.wait(timeout=5) == -9
        second, restarted = start()
        assert restarted['ticket'] != status['ticket']
        assert restarted['fence']['new_link_admission'] == 'CLOSED'
        assert restarted['count'] == 1
        with pytest.raises(ValueError, match='HANDOFF_ALREADY_BOUND'):
            witness.sample(root, restarted['ticket'])
        assert request(runtime, 'support') == ['unavailable']
        assert request(runtime, 'stop') == {'count': 1}
        assert second.wait(timeout=5) == 0
    finally:
        for child in processes:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=5)
            child.stdout.close()
            child.stderr.close()
