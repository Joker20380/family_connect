import base64
import json
import os
from pathlib import Path
import secrets

import pytest

from scripts import control_ha_handoff as handoff
from scripts import control_ha_support_replace as replace
from scripts import control_ha_support_resume as resume
from scripts import control_ha_support_witness as witness
from test_control_ha_support_handoff_system import RemoteFixture, SOURCES
from test_control_ha_support_replace_system import system_service
from test_control_ha_support_handoff import notice_snapshot
from test_control_ha_legacy_support import wait_for


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('system_service', [True], indirect=True)
def test_actual_root_owner_nl1_forward_generation_without_working_changes(system_service):
    if os.environ.get('FC_TEST_HA02_NL1') != '1':
        pytest.skip('requires authorized synthetic OWNER/NL1 qualification')
    manager, plan, root, data, guard = system_service
    original = Path(plan['root'])
    remote = RemoteFixture(original)
    public = plan['old_argv'][plan['old_argv'].index('--sender-public') + 1]
    manifest = dict(schema=1, generation=secrets.token_hex(32), support_public=public,
                    owner_binding_sha256=witness.sha(plan['old_binding']),
                    replacement_plan_sha256=replace.digest(original / 'plan.json'))
    prepared = False
    try:
        location = remote.call('prepare', manifest=manifest,
            sources={name: base64.b64encode((ROOT / name).read_bytes()).decode() for name in SOURCES},
            synthetic_sender=base64.b64encode((data / 'sender.identity').read_bytes()).decode())
        prepared = True
        channel = original / 'mailbox-channel.json'
        replace.admission.write(channel, dict(host='root@185.10.158.212', local_uid=remote.account.pw_uid,
            **{name: location[name] for name in ('entry', 'plan', 'interpreter')}))
        guard.write_text(handoff.supervisor_unit(plan, os.environ['FC_TEST_SUPPORT_PYTHON'], channel))
        manager.call('daemon-reload')
        manager.call('start', guard.name)
        wait_for(lambda: (original / 'handoff-open.json').exists(), seconds=45)
        controller = handoff.Handoff(original, handoff.SSHMailbox(channel))
        assert controller.run() == 'HANDOFF_OPEN_CAPTURE_DENIED'
        before = notice_snapshot(data, int(manager.state()['MainPID']), seed=True)
        authority = Path(plan['start_authority']).read_bytes()
        assert controller.run(pause=True) == 'SUPPORT_IDENTITY_PAUSED'
        manager.call('kill', '--signal=SIGTERM', '--kill-whom=main', manager.unit)
        wait_for(lambda: manager.state()['MainPID'] == '0', seconds=15)
        newer = root / 'resume-controller'
        next_plan = resume.prepare(original, newer, data / 'resume')
        manifest = dict(manifest, generation=secrets.token_hex(32),
                        owner_binding_sha256=witness.sha(next_plan['old_binding']),
                        replacement_plan_sha256=replace.digest(newer / 'plan.json'))
        advanced = remote.call('generation', manifest=manifest)
        replace.admission.write(newer / 'predecessor-reclosure.json', advanced['predecessor_reclosure'])
        channel = newer / 'mailbox-channel.json'
        replace.admission.write(channel, dict(host='root@185.10.158.212', local_uid=remote.account.pw_uid,
            **{name: advanced[name] for name in ('entry', 'plan', 'interpreter')}))
        assert resume.Resume(newer, handoff.SSHMailbox(channel)).run() == 'FORWARD_RESUME_OPEN_CAPTURE_DENIED'
        assert resume.Resume(newer, handoff.SSHMailbox(channel)).run() == 'FORWARD_RESUME_OPEN_CAPTURE_DENIED'
        assert notice_snapshot(data, int(manager.state()['MainPID'])) == before
        assert Path(plan['start_authority']).read_bytes() == authority
        assert remote.call('support') == ['stored']
        assert remote.call('peer') == ['stored']
        status = remote.call('status')
        assert status['consumed'] and status['fence']['new_link_admission'] == 'OPEN_LOCAL_ONLY'
        restarted = remote.call('restart')
        assert restarted['ticket']['process'] != status['ticket']['process']
        assert restarted['fence']['new_link_admission'] == 'CLOSED' and restarted['consumed'] is None
        with pytest.raises(ValueError, match='RESUME_TICKET_CHANGED'):
            resume.Resume(newer, handoff.SSHMailbox(channel)).run()
        assert remote.call('status')['fence']['opening_invalidated']
        current_authority = Path(next_plan['start_authority']).read_bytes()
        manager.call('restart', manager.unit)
        wait_for(lambda: manager.state()['MainPID'] == '0')
        assert manager.state()['ExecMainStatus'] == '78'
        refusals = list((data / 'resume/refusals').glob('*.json'))
        assert len(refusals) == 1
        refused = json.loads(refusals[0].read_bytes())
        assert refused['phase'] == 'authority' and refused['reason'] == 'START_AUTHORITY_CHANGED'
        assert Path(next_plan['start_authority']).read_bytes() == current_authority
    finally:
        if prepared:
            remote.call('stop')
