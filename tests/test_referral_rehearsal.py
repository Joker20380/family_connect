from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.paid_postgres_rehearsal import require_current_restore
from scripts.referral_postgres_rehearsal import ReferralRehearsal


@pytest.mark.parametrize('mutation', ['claim', 'sponsor', 'invitation', 'revocation', 'proof', 'table'])
def test_restore_cannot_silently_lose_referral_state(mutation):
    current = dict(referral_claims=[dict(request='synthetic-request', sponsor='synthetic-parent', invite='synthetic-hash')],
                   invites=[dict(hash='synthetic-hash', revoked=1)], challenges=[dict(used=1)],
                   ha_referrals_schema=[dict(version=1)])
    restored = deepcopy(current)
    if mutation == 'claim':
        restored['referral_claims'].clear()
    elif mutation == 'sponsor':
        restored['referral_claims'][0]['sponsor'] = 'other-parent'
    elif mutation == 'invitation':
        restored['invites'][0]['hash'] = 'other-hash'
    elif mutation == 'revocation':
        restored['invites'][0]['revoked'] = 0
    elif mutation == 'proof':
        restored['challenges'][0]['used'] = 0
    else:
        del restored['ha_referrals_schema']
    with pytest.raises(ValueError, match='RESTORE_WOULD_LOSE_OR_CHANGE_ACKNOWLEDGED_STATE'):
        require_current_restore(current, restored)


def test_referral_runner_uses_temporary_owned_local_docker_only(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match='TEMPORARY_REHEARSAL_ONLY'):
        ReferralRehearsal(Path('/not-a-temporary-referral-rehearsal'))
    with pytest.raises(FileExistsError):
        ReferralRehearsal(tmp_path)
    linked = tmp_path / 'linked'
    linked.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='REHEARSAL_SYMLINK'):
        ReferralRehearsal(linked / 'new')
    monkeypatch.setenv('PGSERVICE', 'not-for-tests')
    monkeypatch.setenv('DOCKER_HOST', 'tcp://not-for-tests:2375')
    rehearsal = ReferralRehearsal(tmp_path / 'rehearsal')
    calls = []

    def command(arguments, **settings):
        calls.append((arguments, settings))
        return SimpleNamespace(returncode=0, stdout=b'wrong-owner', stderr=b'')

    monkeypatch.setattr('subprocess.run', command)
    rehearsal.container = 'a' * 64
    with pytest.raises(ValueError, match='REHEARSAL_CONTAINER_OWNERSHIP'):
        rehearsal.__exit__(None, None, None)
    assert len(calls) == 1
    assert calls[0][0][:4] == ['docker', '--host', 'unix:///var/run/docker.sock', 'inspect']
    assert not any(key.startswith(('PG', 'FC_HA_', 'DOCKER_')) for key in calls[0][1]['env'])
