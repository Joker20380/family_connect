from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.paid_postgres_rehearsal import require_current_restore
from scripts.referral_postgres_rehearsal import ReferralRehearsal
from scripts.support_postgres_rehearsal import SupportRehearsal
from scripts.restricted_admin_postgres_rehearsal import RestrictedAdminRehearsal
from scripts.restricted_postgres_rehearsal import RestrictedRehearsal
from scripts.chat_postgres_rehearsal import ChatRehearsal, refused_value
from scripts.gateway_routing_postgres_rehearsal import RoutingRehearsal
from scripts.crl_postgres_rehearsal import CRLRehearsal
from scripts.metadata_postgres_rehearsal import MetadataRehearsal
from scripts.diagnostics_postgres_rehearsal import DiagnosticsRehearsal
from scripts.notices_postgres_rehearsal import NoticesRehearsal


def test_chat_recovery_requires_exact_refusal_not_any_error():
    def denied(reason):
        raise ValueError(reason)

    refused_value(lambda: denied('expected'), 'expected')
    with pytest.raises(ValueError, match='UNEXPECTED_REFUSAL'):
        refused_value(lambda: denied('other'), 'expected')
    with pytest.raises(ValueError, match='EXPECTED_REFUSAL'):
        refused_value(lambda: None, 'expected')


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


@pytest.mark.parametrize('runner', [ReferralRehearsal, SupportRehearsal, RestrictedAdminRehearsal, RestrictedRehearsal, ChatRehearsal, RoutingRehearsal, CRLRehearsal, MetadataRehearsal, DiagnosticsRehearsal, NoticesRehearsal])
def test_writer_runner_uses_temporary_owned_local_docker_only(tmp_path, monkeypatch, runner):
    with pytest.raises(ValueError, match='TEMPORARY_REHEARSAL_ONLY'):
        runner(Path('/not-a-temporary-writer-rehearsal'))
    with pytest.raises(FileExistsError):
        runner(tmp_path)
    linked = tmp_path / 'linked'
    linked.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='REHEARSAL_SYMLINK'):
        runner(linked / 'new')
    monkeypatch.setenv('PGSERVICE', 'not-for-tests')
    monkeypatch.setenv('DOCKER_HOST', 'tcp://not-for-tests:2375')
    rehearsal = runner(tmp_path / 'rehearsal')
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
