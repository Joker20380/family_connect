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
from scripts.control_ha_import_rehearsal import ImportRehearsal
from scripts.control_ha_sqlite_rehearsal import SQLiteImportRehearsal
from scripts.control_ha_bundle_rehearsal import BundleRehearsal
from scripts.control_ha_external_rehearsal import ExternalRehearsal
from scripts.control_ha_receiver_rehearsal import ReceiverRehearsal
from scripts.control_ha_maintenance_rehearsal import MaintenanceRehearsal
from scripts.control_ha_online_rehearsal import OnlineRehearsal
from scripts.control_ha_stopped_rehearsal import StoppedRehearsal


def test_stopped_contract_partitions_preserve_every_gate(tmp_path, monkeypatch):
    runner = StoppedRehearsal(tmp_path / 'stopped-contracts')
    calls = []
    def contracts(self):
        calls.extend(self.CONTRACT_FILES)
        for extension in ('log', 'xml'):
            (self.root / ('contracts.' + extension)).write_text(self.CONTRACT_FILES[0])
        return 7
    monkeypatch.setattr(OnlineRehearsal, 'contracts', contracts)
    expected = StoppedRehearsal.CONTRACT_FILES
    assert runner.contracts() == 7 * len(expected)
    assert calls == list(expected) and runner.CONTRACT_FILES == expected
    for source in expected:
        assert (runner.root / (Path(source).stem + '.log')).read_text() == source
        assert (runner.root / (Path(source).stem + '.xml')).read_text() == source


def test_stopped_contract_partition_failure_is_not_a_pass(tmp_path, monkeypatch):
    runner = StoppedRehearsal(tmp_path / 'stopped-failure')
    def contracts(self):
        raise RuntimeError('CONTRACTS_SKIPPED')
    monkeypatch.setattr(OnlineRehearsal, 'contracts', contracts)
    expected = StoppedRehearsal.CONTRACT_FILES
    with pytest.raises(RuntimeError, match='CONTRACTS_SKIPPED'):
        runner.contracts()
    assert runner.CONTRACT_FILES == expected


def test_stopped_contract_deadline_is_bounded_without_changing_other_runners(tmp_path, monkeypatch):
    runner = StoppedRehearsal(tmp_path / 'stopped-deadline')
    runner.port = 54321
    def command(arguments, **settings):
        assert settings['timeout'] == 300
        target = next(argument.removeprefix('--junitxml=') for argument in arguments if argument.startswith('--junitxml='))
        Path(target).write_text('<testsuites><testsuite tests="1" skipped="0"/></testsuites>')
        return SimpleNamespace(returncode=0, stdout=b'passed', stderr=b'')
    monkeypatch.setattr('subprocess.run', command)
    assert runner.contracts() == len(StoppedRehearsal.CONTRACT_FILES)
    assert OnlineRehearsal.CONTRACT_TIMEOUT == 120


def test_stopped_parent_is_validated_before_creation(tmp_path, monkeypatch):
    from scripts.control_ha_stopped_rehearsal import main
    destination = tmp_path / 'outside'
    monkeypatch.setattr('sys.argv', ['stopped-rehearsal', '--workdir', str(destination)])
    monkeypatch.setattr('tempfile.gettempdir', lambda: str(tmp_path / 'allowed'))
    with pytest.raises(ValueError, match='TEMPORARY_REHEARSAL_ONLY'):
        main()
    assert not destination.exists()


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


@pytest.mark.parametrize('runner', [ReferralRehearsal, SupportRehearsal, RestrictedAdminRehearsal, RestrictedRehearsal, ChatRehearsal, RoutingRehearsal, CRLRehearsal, MetadataRehearsal, DiagnosticsRehearsal, NoticesRehearsal, ImportRehearsal, SQLiteImportRehearsal, BundleRehearsal, ExternalRehearsal, ReceiverRehearsal, MaintenanceRehearsal, OnlineRehearsal, StoppedRehearsal])
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
