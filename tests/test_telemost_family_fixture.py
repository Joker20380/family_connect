import json
import stat

import pytest
from cryptography import x509

from control.product.store import EnrollmentRejected
from device_identity.device import DeviceIdentity
from pilot.telemost_family_fixture import FixtureIssuer, generate


def test_issuer_uses_existing_authority_and_revocation(tmp_path):
    issuer = FixtureIssuer(tmp_path / 'issuer')
    family = issuer.family()
    device = issuer.enroll(family)
    certificate = issuer.issue(device, 'device')
    assert certificate.subject.get_attributes_for_oid(x509.NameOID.SERIAL_NUMBER)[0].value == device.reference
    issuer.store.revoke_device(device.reference)
    with pytest.raises(EnrollmentRejected):
        issuer.issue(device, 'device')
    with pytest.raises(EnrollmentRejected):
        issuer.issue(DeviceIdentity.generate(), 'device')
    assert [entry.serial_number for entry in issuer.revocations()] == [certificate.serial_number]


def test_fixture_permissions_and_distinct_authorized_families(tmp_path, capsys):
    directory = tmp_path / 'isolated'
    generate(directory)
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    profiles = {}
    for name in ('valid', 'gateway', 'wrong-family', 'revoked'):
        path = directory / (name + '.json')
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        profiles[name] = json.loads(path.read_text())
    correct = x509.load_pem_x509_certificate(profiles['valid']['certificate'].encode())
    wrong = x509.load_pem_x509_certificate(profiles['wrong-family']['certificate'].encode())
    assert correct.subject.get_attributes_for_oid(x509.NameOID.ORGANIZATIONAL_UNIT_NAME)[1].value != wrong.subject.get_attributes_for_oid(x509.NameOID.ORGANIZATIONAL_UNIT_NAME)[1].value
    output = capsys.readouterr().out
    assert 'PRIVATE KEY' not in output and profiles['valid']['family'] not in output
    with pytest.raises(FileExistsError):
        generate(directory)
