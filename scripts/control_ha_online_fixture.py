"""Compose native synthetic renewal and application stores; no live capture entry point."""
from pathlib import Path
import sys

from control.friends import restricted_admin
from scripts.control_ha_import import encoded
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_maintenance_fixture import artifacts_for_maintenance
from scripts.control_ha_online_capsule import assemble
from scripts.control_ha_recovery_bundle import parse
from scripts.control_ha_rehearsal import require
from scripts.control_ha_sqlite_fixture import joint_fixture, refresh_fixture
from scripts.referral_postgres_rehearsal import NOW

TESTS = Path(__file__).resolve().parents[1] / 'tests'
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from test_multi_gateway_renewal import make_fleet
from test_online_renewal import Crash, enable
from test_control_ha_renewal_v1 import OPERATION, capture
from credential_renewal import atomic


def online_fixture(root, *, interrupt=False, history=False):
    fleet_root = root / 'native'
    fleet_root.mkdir(mode=0o700)
    fleet = make_fleet(fleet_root, now=NOW - (36000 if history else 12000))
    if history:
        for operation in ('ha-online-history-0001', 'ha-online-history-0002'):
            enable(fleet)
            require(fleet.controller.run_online(operation, schedule_seconds=0)['result'] == 'COMMITTED',
                    'ONLINE_HISTORY_FIXTURE_NOT_COMMITTED')
    enable(fleet)
    restricted_admin.grant(fleet.service.access, fleet.device.reference, fleet.family, NOW + 86400)
    fixture = joint_fixture(fleet_root, authority=(fleet.service, fleet.device))
    crl = fixture.service.crl_source()
    atomic(fleet.nodes['RU'].live / 'revocations.pem', crl)
    fixture.service.crl_source = lambda: (fleet.nodes['RU'].live / 'revocations.pem').read_bytes()
    from cryptography import x509
    number = x509.load_pem_x509_crl(crl).extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
    for slot in ('NL', 'NL2'):
        path = fleet.nodes[slot].live / 'gateway.json'
        profile = parse(path.read_bytes())
        profile.update(revocations=crl.decode(), minimum_crl=number)
        atomic(path, encoded(profile))
    def fault(phase):
        if interrupt and phase == 'ONLINE_COMMIT_DECIDED':
            raise Crash()
    fleet.controller.fault = fault
    try:
        result = fleet.controller.run_online(OPERATION, schedule_seconds=0)
        require(not interrupt and result['result'] == 'COMMITTED', 'ONLINE_FIXTURE_NOT_COMMITTED')
    except Crash:
        require(interrupt, 'ONLINE_FIXTURE_UNEXPECTED_CRASH')
    renewal = capture(fleet)
    refresh_fixture(fixture)
    artifacts, bounded = artifacts_for_maintenance(fixture)
    artifacts['maintenance_state'] = assemble(bounded['settled'], renewal, fixture.stores,
                                              artifacts['issuer_material'], CHECKPOINT, history=history)
    return fixture, artifacts, bounded
