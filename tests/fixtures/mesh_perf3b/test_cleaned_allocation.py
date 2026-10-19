import json

import pytest

from test_owner_handoff import fixtures, handoff, setup


def test_sealed_api_cannot_allocate_new_id_after_never_armed_cleanup(setup):
    service, owner, now, first, _, _ = setup
    with service.access.db() as database:
        handoff.return_only(database, owner.reference, 'test-operation')
    current = service.fetch(fixtures.proof(service, owner))
    with service.access.db() as database:
        handoff.cleanup(database, owner.reference, 'test-operation', current)
        before = dict(handoff.read(database, owner.reference))
    assert before['phase'] == 'CLEANED'
    assert before['canary'] is None and before['return_view'] is None
    assert json.loads(before['floor']) == handoff.floor(current)
    with pytest.raises(ValueError):
        with service.access.db() as database:
            handoff.prepare(database, 'new-operation-not-replay', owner.reference,
                            first['directory']['family'], first['directory']['seeds'][0]['gateway'],
                            now + 2400, now)
    with service.access.db() as database:
        assert dict(handoff.read(database, owner.reference)) == before


def test_sealed_api_preserves_tombstone_on_same_id_replay(setup):
    service, owner, now, first, _, _ = setup
    with service.access.db() as database:
        handoff.return_only(database, owner.reference, 'test-operation')
    current = service.fetch(fixtures.proof(service, owner))
    with service.access.db() as database:
        handoff.cleanup(database, owner.reference, 'test-operation', current)
        before = dict(handoff.read(database, owner.reference))
    with pytest.raises(ValueError):
        with service.access.db() as database:
            handoff.prepare(database, 'test-operation', owner.reference,
                            first['directory']['family'], first['directory']['seeds'][0]['gateway'],
                            now + 2400, now)
    with service.access.db() as database:
        assert dict(handoff.read(database, owner.reference)) == before
