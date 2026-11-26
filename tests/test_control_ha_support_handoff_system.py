import base64
import hashlib
import json
import os
from pathlib import Path
import pwd
import secrets
import shlex
import subprocess
import uuid

import pytest

from scripts import control_ha_handoff as handoff
from scripts import control_ha_support_replace as replace
from scripts import control_ha_support_witness as witness
from test_control_ha_support_replace_system import system_service
from test_control_ha_legacy_support import wait_for
from test_control_ha_support_handoff import notice_snapshot


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ('scripts/control_ha_mailbox_control.py', 'scripts/control_ha_mailbox_startup.py',
           'scripts/control_ha_mailbox_generation.py',
           'scripts/control_ha_mailbox_fence.py', 'scripts/control_ha_mailbox_links.py',
           'scripts/control_ha_legacy_support.py', 'tests/fixtures/mailbox_startup.py',
           'tests/fixtures/mailbox_links_system.py', 'messenger/tests/mailbox_links_peer.py')


class RemoteFixture:
    def __init__(self, root):
        self.root, self.identifier = root, uuid.uuid4().hex
        self.account = pwd.getpwnam('joker')
        helper = (ROOT / 'tests/fixtures/ha02_nl1_handoff.py').read_text()
        self.command = ['/usr/bin/ssh', '-oBatchMode=yes', '-oStrictHostKeyChecking=yes', 'root@185.10.158.212',
                        shlex.join(['/usr/bin/python3', '-c', helper])]

    def call(self, action, **values):
        environment = dict(os.environ, HOME=self.account.pw_dir, USER=self.account.pw_name, LOGNAME=self.account.pw_name)
        result = subprocess.run(self.command, input=json.dumps(dict(action=action, identifier=self.identifier, **values)),
                                text=True, capture_output=True, timeout=60, user=self.account.pw_uid,
                                group=self.account.pw_gid, extra_groups=[], env=environment)
        assert result.returncode == 0, result.stderr[-4096:]
        response = json.loads(result.stdout)
        assert response['working_unchanged'] is True
        replace.admission.write(self.root / ('nl1-' + action + '-' + uuid.uuid4().hex + '.json'), response)
        return response['result']


@pytest.mark.parametrize('system_service', [True], indirect=True)
def test_actual_owner_nl1_joint_handoff_reclosure_recovery(system_service):
    if os.environ.get('FC_TEST_HA02_NL1') != '1':
        pytest.skip('requires explicitly authorized synthetic OWNER/NL1 qualification')
    manager, plan, root, data, guard_path = system_service
    controller = Path(plan['root'])
    remote = RemoteFixture(controller)
    public = plan['old_argv'][plan['old_argv'].index('--sender-public') + 1]
    manifest = dict(schema=1, generation=secrets.token_hex(32), support_public=public,
                    owner_binding_sha256=witness.sha(plan['old_binding']),
                    replacement_plan_sha256=replace.digest(controller / 'plan.json'))
    prepared = False
    try:
        location = remote.call('prepare', manifest=manifest,
            sources={name: base64.b64encode((ROOT / name).read_bytes()).decode() for name in SOURCES},
            synthetic_sender=base64.b64encode((data / 'sender.identity').read_bytes()).decode())
        prepared = True
        assert location['manager_state']['NeedDaemonReload'] == 'no', location['manager_state']
        assert location['observed']['fence']['new_link_admission'] == 'CLOSED'
        assert remote.call('support') == ['unavailable']
        channel = controller / 'mailbox-channel.json'
        replace.admission.write(channel, dict(host='root@185.10.158.212', local_uid=remote.account.pw_uid,
            **{name: location[name] for name in ('entry', 'plan', 'interpreter')}))
        guard_path.write_text(handoff.supervisor_unit(plan, os.environ['FC_TEST_SUPPORT_PYTHON'], channel))
        manager.call('daemon-reload')
        manager.call('start', guard_path.name)
        wait_for(lambda: (controller / 'handoff-open.json').exists(), seconds=40)
        manager.call('stop', guard_path.name)
        notice = notice_snapshot(data, int(manager.state()['MainPID']), seed=True)
        assert notice['status'] == 'saved' and notice['cursor'] == 42
        observed = remote.call('status')
        assert observed['consumed'] and observed['fence']['new_link_admission'] == 'OPEN_LOCAL_ONLY'
        assert remote.call('support') == ['stored'] and remote.call('peer') == ['stored']
        reservation = (controller / 'handoff-reserved.json').read_bytes()
        executor = handoff.Handoff(controller, handoff.SSHMailbox(channel))
        assert executor.run(pause=True) == 'SUPPORT_IDENTITY_PAUSED'
        assert notice_snapshot(data, int(manager.state()['MainPID'])) == notice
        assert remote.call('support') == ['unavailable'] and remote.call('peer') == ['stored']
        restarted = remote.call('restart')
        assert restarted['fence']['opening_invalidated'] and restarted['fence']['new_link_admission'] == 'CLOSED'
        assert remote.call('support') == ['unavailable']
        assert executor.run(recover=True) == 'ROLLED_BACK'
        assert notice_snapshot(data, int(manager.state()['MainPID'])) == notice
        assert (controller / 'handoff-reserved.json').read_bytes() == reservation
        assert all((Path(plan['gate']) / 'pending' / name).exists() for name in plan['pending'])
        assert remote.call('status')['count'] == 3
        assert remote.call('peer') == ['stored'] and remote.call('status')['count'] == 4
        replace.admission.write(controller / 'joint-root-nl1-accepted.json', dict(
            result='SYNTHETIC_JOINT_HANDOFF_RECOVERY_PASS', working_installed=False,
            mailbox_rows=4, current_data_preserved=True, reservation_sha256=hashlib.sha256(reservation).hexdigest(),
            root_controller=True, actual_service_uids=True, capture_permitted=False))
    finally:
        journal = subprocess.check_output(['journalctl', '-u', guard_path.name, '-n', '80', '-o', 'json', '--no-pager'])
        replace.admission.write(controller / 'guard-diagnostic.json', dict(complete=False,
            records=[json.loads(line) for line in journal.splitlines()]))
        for line in journal.splitlines():
            message = json.loads(line).get('MESSAGE', '')
            if message.startswith('{'):
                value = json.loads(message)
                print('BOUNDED_JOINT_DIAGNOSTIC ' + json.dumps({key: value[key] for key in
                      ('result', 'reason', 'capture_permitted') if key in value}), flush=True)
        if prepared:
            remote.call('stop')
