import copy
import hashlib
import os

import pytest

from messenger.tests.test_control_ha_mailbox_startup import configured, created, write, OLD_BINDING
from messenger.tests.test_control_ha_mailbox_fence import envelope
from messenger.tests.test_control_ha_mailbox_links import dispatch, native_link
from scripts import control_ha_mailbox_generation as generation
from scripts import control_ha_mailbox_startup as mailbox


def sealed(startup, tmp_path):
    write(startup.seal, dict(schema=1, generation=startup.manifest['generation'],
                            manifest_sha256=startup.digest, opening_invalidated=True))
    return startup.reclose(write(tmp_path / 'reclose.json', dict(action='RECLOSE', ticket=startup.ticket())))


def transition(startup, tmp_path):
    manifest = dict(startup.manifest, generation='d' * 64, replacement_plan_sha256='b' * 64)
    target = write(tmp_path / 'next.json', manifest)
    return write(tmp_path / 'advance.json', dict(action='ADVANCE_CLOSED_GENERATION', ticket=startup.ticket(),
                 manifest=str(target), manifest_sha256=hashlib.sha256(target.read_bytes()).hexdigest()))


def resume_request(startup):
    ticket = startup.ticket()
    reservation = dict(schema=1, ticket_sha256=generation.digest(ticket), plan_sha256=ticket['replacement_plan_sha256'],
                       accepted_sha256='d' * 64, opening_permitted=False, capture_permitted=False)
    witness = dict(schema=1, result='OWNER_FORWARD_RESUME_SAMPLED', controller_uid=os.getuid(), fixture=os.getuid() != 0,
                   ticket_sha256=generation.digest(ticket), plan_sha256=ticket['replacement_plan_sha256'],
                   old_binding=OLD_BINDING, candidate_binding=dict(OLD_BINDING, pid=456),
                   archive_sha256='621009b8df9baffb81e0d9069cfa52b3781e7dd7bf4e435dd89740e38cae5739',
                   accepted_sha256='d' * 64, reservation_sha256=generation.digest(reservation),
                   predecessor_sha256='1' * 64, reclosure_sha256='2' * 64, absence_sha256='3' * 64,
                   old_process_absent=True, independent_controller=True, legacy_uncertainty_preserved=True,
                   data_restored=False, capture_permitted=False, opening_permitted=False, settlement_proven=False)
    return dict(action='OWNER_FORWARD_RESUME', ticket=ticket, witness=witness, reservation=reservation)


def test_generation_requires_persistent_reclosure_and_preserves_old_bytes(created, tmp_path, monkeypatch):
    startup, relay, support, peer = created
    monkeypatch.setattr(mailbox, 'ACTIVE', startup)
    request = transition(startup, tmp_path)
    old_manifest = startup.path.read_bytes()
    with pytest.raises(FileNotFoundError):
        generation.advance(startup, request)
    sealed(startup, tmp_path)
    seal = startup.seal.read_bytes()
    result = generation.advance(startup, request)
    fresh = mailbox.ACTIVE
    assert fresh is not startup and fresh.fence is startup.fence
    assert result['fence']['new_link_admission'] == 'CLOSED'
    assert result['consumed'] is None and not result['fence']['opening_invalidated']
    assert startup.path.read_bytes() == old_manifest and startup.seal.read_bytes() == seal
    assert result['ticket']['challenge'] != startup.challenge


def test_old_link_and_ticket_never_authorize_new_generation(created, tmp_path, monkeypatch):
    startup, relay, support, peer = created
    monkeypatch.setattr(mailbox, 'ACTIVE', startup)
    first = write(tmp_path / 'resume-first.json', resume_request(startup))
    generation.consume(startup, first)
    old_link = native_link(relay, support)
    dispatch(old_link, envelope(peer), monkeypatch)
    assert relay.spool.stats()['count'] == 1
    request = transition(startup, tmp_path)
    sealed(startup, tmp_path)
    generation.advance(startup, request)
    fresh = mailbox.ACTIVE
    with pytest.raises(ValueError, match='STALE_RESUME_TICKET'):
        generation.consume(fresh, first)
    second = write(tmp_path / 'resume-second.json', resume_request(fresh))
    opened = generation.consume(fresh, second)
    assert generation.consume(fresh, second) == opened
    dispatch(old_link, envelope(peer), monkeypatch)
    assert relay.spool.stats()['count'] == 1
    dispatch(native_link(relay, support), envelope(peer), monkeypatch)
    assert relay.spool.stats()['count'] == 2
    assert opened['capture_permitted'] is False
    sealed(fresh, tmp_path)
    with pytest.raises(ValueError, match='OPENING_INVALIDATED'):
        generation.consume(fresh, second)


def test_busy_generation_is_not_rotated(created, tmp_path, monkeypatch):
    startup, relay, support, peer = created
    monkeypatch.setattr(mailbox, 'ACTIVE', startup)
    sealed(startup, tmp_path)
    request = transition(startup, tmp_path)
    startup.fence.admitted.add('synthetic-inflight')
    try:
        with pytest.raises(ValueError, match='PREDECESSOR_WORK_BUSY'):
            generation.advance(startup, request)
        assert mailbox.ACTIVE is startup and startup.fence.sealed
    finally:
        startup.fence.admitted.clear()


@pytest.mark.parametrize('mutation', ['authority', 'ticket', 'old', 'candidate', 'capture', 'settlement',
                                     'restore', 'uncertainty', 'absence', 'reservation', 'archive', 'extra'])
def test_invalid_resume_never_opens(created, tmp_path, mutation):
    startup, relay, support, peer = created
    value = copy.deepcopy(resume_request(startup))
    fields = dict(authority=('controller_uid', -1), old=('old_binding', {}),
                  candidate=('candidate_binding', OLD_BINDING), capture=('capture_permitted', True),
                  settlement=('settlement_proven', True), restore=('data_restored', True),
                  uncertainty=('legacy_uncertainty_preserved', False), absence=('absence_sha256', ''),
                  archive=('archive_sha256', '0' * 64), extra=('extra', True))
    if mutation in fields:
        field, changed = fields[mutation]
        value['witness'][field] = changed
    elif mutation == 'ticket':
        value['ticket']['challenge'] = '0' * 64
    else:
        value['reservation']['schema'] = True
    with pytest.raises(ValueError):
        generation.consume(startup, write(tmp_path / 'invalid.json', value))
    assert startup.observe()['fence']['new_link_admission'] == 'CLOSED' and startup.consumed is None


def test_lost_response_is_reconciled_by_current_observation_not_old_retry(created, tmp_path, monkeypatch):
    startup, relay, support, peer = created
    monkeypatch.setattr(mailbox, 'ACTIVE', startup)
    request = transition(startup, tmp_path)
    sealed(startup, tmp_path)
    generation.advance(startup, request)
    current = mailbox.ACTIVE.observe()
    assert current['ticket']['generation'] == 'd' * 64
    with pytest.raises(ValueError, match='STALE_PREDECESSOR'):
        generation.advance(startup, request)
    assert mailbox.ACTIVE.observe() == current
