"""Owned native stopped/offline/emergency fixtures; not installed inventory."""
import base64

from scripts.control_ha_import import encoded
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_maintenance_fixture import artifacts_for_maintenance
from scripts.control_ha_online_fixture import native_fixture
from scripts.control_ha_recovery_bundle import parse
from scripts.control_ha_rehearsal import require
from scripts.control_ha_sqlite_fixture import refresh_fixture
from scripts.control_ha_stopped_capsule import assemble_stopped
from scripts.control_ha_stopped_v1 import STOPPED_PURPOSE

from test_control_ha_renewal_v1 import OPERATION, capture
from test_multi_gateway_renewal import approve, offline_sign
from test_activated_maintenance import activate, proof
from maintenance_policy import MaintenanceAuthorization


def stopped_fixture(root, *, mode, emergency_boundary='ONLINE_NL_PUBLISHED'):
    require(mode in ('stopped', 'offline', 'emergency'), 'STOPPED_FIXTURE_MODE')
    fixture, fleet = native_fixture(root)
    if mode == 'emergency':
        victim = activate(fleet.service)
        fleet.service.fetch(proof(fleet.service, victim))
        def revoke(phase):
            if phase == emergency_boundary:
                fleet.service.access.revoke_device(victim.reference)
        fleet.controller.fault = revoke
        result = fleet.controller.run_online(OPERATION, schedule_seconds=0)
        require(result['result'] == 'ONLINE_EMERGENCY_REQUIRED', 'STOPPED_FIXTURE_EMERGENCY_MISSING')
        fleet.controller.fault = lambda phase: None
        request = fleet.controller.recover_online_emergency(OPERATION)['request']
        approval = MaintenanceAuthorization(OPERATION, request['expected_state_sha256'], fleet.now, fleet.now + 900)
        result = fleet.controller.recover_online_emergency(OPERATION, approval=approval)
        require(result['result'] == 'EMERGENCY_RECOVERED', 'STOPPED_FIXTURE_NOT_RECOVERED')
    else:
        bundle = (offline_sign(fleet, fleet.nodes['RU'].authority_request(OPERATION)) if mode == 'offline' else None)
        result = fleet.controller.run(OPERATION, authority_handoff=bundle, approval=approve(fleet, OPERATION))
        require(result['result'] == 'COMMITTED', 'STOPPED_FIXTURE_NOT_COMMITTED')
    fixture.service.manifest = parse(fleet.nodes['RU'].read('issuer.json')[0])
    renewal = capture(fleet, purpose=STOPPED_PURPOSE)
    publication = encoded(dict(schema=1, directories={slot: base64.b64encode(
        fleet.nodes['RU'].directory_destination(slot).read_bytes()).decode() for slot in ('NL', 'NL2')}))
    refresh_fixture(fixture)
    artifacts, bounded = artifacts_for_maintenance(fixture)
    artifacts['maintenance_state'] = assemble_stopped(bounded['settled'], renewal, publication,
        fixture.stores, artifacts['issuer_material'], CHECKPOINT)
    return fixture, artifacts, bounded
