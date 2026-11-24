import base64
from copy import deepcopy
import json

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import ExtendedKeyUsageOID
import pytest

from control.friends import readiness_receipts, restricted, restricted_admin
from control.friends.access import Access
from scripts import control_ha_certificate_delta as delta
from scripts.control_ha_installed_current import COLUMNS
from scripts.referral_postgres_rehearsal import NOW
from scripts.restricted_postgres_rehearsal import synthetic_service, issue_proof


def snapshot(access):
    with access.db() as database:
        return {table: [dict(row) for row in database.execute('SELECT * FROM ' + table)] for table in COLUMNS}


def native_scenario(root, mode='legacy'):
    clock = [NOW]
    access = Access(root / 'access.db', clock=lambda: clock[0])
    access.initialize()
    restricted.migrate(access)
    service, device = synthetic_service(access)
    service.all_activated = mode != 'legacy'
    if service.all_activated:
        with access.db() as database:
            if mode == 'all_activated':
                database.execute('DELETE FROM restricted_grants')
            else:
                database.execute('UPDATE restricted_grants SET expires=?', (NOW - 60,))
    seed = json.loads(service.seed_source())
    def directory():
        return json.dumps(dict(seed, issued_at=restricted.iso(clock[0] - 1), expires_at=restricted.iso(clock[0] + 3599))).encode()
    service.seed_source = directory
    crl_path = root / 'revocations.pem'
    restricted_admin.publish_crl(service, crl_path, lifetime=14400)
    service.crl_source = crl_path.read_bytes
    service.fetch(issue_proof(service, device))
    before = snapshot(access)
    plan = dict(candidate=dict(authority=service.manifest, crl=service.crl_source().decode()),
        grant_plan=dict(before=before, after_grants=before['restricted_grants'], issued_at=NOW + 10))
    clock[0] = NOW + 3601
    service.fetch(issue_proof(service, device))
    current = snapshot(access)
    assert len(before['restricted_certificates']) == len(current['restricted_certificates']) == 1
    assert before['restricted_certificates'] != current['restricted_certificates']
    return dict(plan=plan, current=current, anchor=service.anchor, captured_at=clock[0], signer=service.signing_key,
                admission=dict(version=2, eligibility='all_activated') if service.all_activated else dict(devices=[]))


@pytest.fixture(scope='module')
def native_issuance(tmp_path_factory):
    return native_scenario(tmp_path_factory.mktemp('native-certificate-delta'))


@pytest.fixture
def inputs(native_issuance):
    return {key: deepcopy(value) if key in ('plan', 'current') else value for key, value in native_issuance.items()}


def inspect(inputs):
    return delta.inspect_delta(inputs['plan'], inputs['current'], inputs['anchor'], captured_at=inputs['captured_at'], admission=inputs['admission'])


@pytest.mark.parametrize('mode', ['all_activated', 'activated_expired_legacy_grant'])
def test_native_activated_issuance_does_not_require_a_persisted_grant(tmp_path, mode):
    inputs = native_scenario(tmp_path, mode)
    result = inspect(inputs)
    assert result['admission_mode'] == 'all_activated' and result['signed_added'] == 1
    assert result['recovery'] == 'BLOCKED' and result['challenge_proof'] == 'NOT_RECONSTRUCTED'
    inputs['admission'] = dict(devices=[])
    with pytest.raises(delta.DeltaRefused, match='GRANT_REQUIRED|GRANT_EXPIRY'):
        inspect(inputs)


@pytest.mark.parametrize('kind', ['device_revoke', 'missing_invite', 'grant_revoke', 'grant_family', 'wrong_revision'])
def test_activated_mode_keeps_membership_and_revision_checks(tmp_path, kind):
    inputs = native_scenario(tmp_path, 'all_activated')
    current, before = inputs['current'], inputs['plan']['grant_plan']['before']
    row = current['restricted_certificates'][0]
    if kind == 'device_revoke':
        current['devices'][0]['revoked'] = 1
        before['devices'] = deepcopy(current['devices'])
    elif kind == 'missing_invite':
        current['invites'] = before['invites'] = []
    elif kind.startswith('grant'):
        grants = [dict(device=row['device'], family='0' * 32 if kind == 'grant_family' else 'a' * 32,
                       revision=row['revision'], expires=None, revoked=1 if kind == 'grant_revoke' else 0)]
        current['restricted_grants'] = inputs['plan']['grant_plan']['after_grants'] = grants
    else:
        row['revision'] += 1
        original = x509.load_pem_x509_certificate(row['certificate'].encode())
        resign(inputs, subject=x509.Name([x509.NameAttribute(attribute.oid, 'revision=' + str(row['revision'])
            if attribute.value.startswith('revision=') else attribute.value) for attribute in original.subject]))
    with pytest.raises(delta.DeltaRefused):
        inspect(inputs)


@pytest.mark.parametrize('policy', [None, {}, {'version': True, 'eligibility': 'all_activated'},
    {'version': 2, 'eligibility': 'everyone'}, {'devices': [True]}, {'devices': ['*'], 'override': True}])
def test_admission_shape_cannot_select_a_permissive_default(inputs, policy):
    inputs['admission'] = policy
    with pytest.raises(delta.DeltaRefused, match='ADMISSION_'):
        inspect(inputs)


def resign(inputs, *, row=None, subject=None, public=None, issuer=None, extensions=None, before=None, after=None, signer=None):
    row = inputs['current']['restricted_certificates'][0] if row is None else row
    original = x509.load_pem_x509_certificate(row['certificate'].encode())
    builder = (x509.CertificateBuilder().subject_name(subject or original.subject).issuer_name(issuer or original.issuer)
        .public_key(public or original.public_key()).serial_number(original.serial_number)
        .not_valid_before(before or original.not_valid_before_utc).not_valid_after(after or original.not_valid_after_utc))
    for extension in original.extensions if extensions is None else extensions:
        builder = builder.add_extension(extension.value, extension.critical)
    value = builder.sign(signer or inputs['signer'], None)
    row.update(certificate=value.public_bytes(Encoding.PEM).decode(), expires=int(value.not_valid_after_utc.timestamp()))


def test_native_issue_expiry_pruning_and_new_proof_are_content_compatible(inputs):
    before = deepcopy(inputs['plan']), deepcopy(inputs['current'])
    result = inspect(inputs)
    assert result['result'] == 'CERTIFICATE_CONTENT_COMPATIBLE_NOT_AUTHORIZED'
    assert result['signed_added'] == result['expired_removed'] == 1 and result['retained'] == 0
    assert result['recovery'] == 'BLOCKED' and result['activation'] == 'FORBIDDEN'
    assert not result['snapshot_barrier'] and result['challenge_proof'] == 'NOT_RECONSTRUCTED'
    assert result['entitlement_history'] == 'NOT_VERIFIED'
    assert (inputs['plan'], inputs['current']) == before
    output = json.dumps(result)
    for row in inputs['current']['restricted_certificates']:
        assert row['device'] not in output and row['serial'] not in output and row['certificate'] not in output


def test_native_protocol_constants_do_not_drift():
    assert delta.DOMAIN == restricted.DOMAIN and delta.PROTOCOL == restricted.PROTOCOL
    assert delta.MAX_LIFETIME == restricted.MAX_TEST_LIFETIME
    assert delta.CLOCK_SKEW == readiness_receipts.CLOCK_SKEW_SECONDS


def test_retained_expired_rows_are_not_rewritten_or_authorized(inputs):
    inputs['current']['restricted_certificates'] = deepcopy(inputs['plan']['grant_plan']['before']['restricted_certificates'])
    result = inspect(inputs)
    assert result['retained'] == 1 and result['expired_removed'] == result['signed_added'] == 0
    assert result['recovery'] == 'BLOCKED'


@pytest.mark.parametrize('kind', ['scope', 'duplicate_device', 'row_limit', 'boolean_revision', 'private_pem', 'unsupported_algorithm'])
def test_malformed_inputs_refuse_without_payload(inputs, monkeypatch, kind):
    if kind == 'scope':
        inputs['current']['unknown'] = []
    elif kind == 'duplicate_device':
        inputs['current']['devices'] *= 2
        inputs['plan']['grant_plan']['before']['devices'] *= 2
    elif kind == 'row_limit':
        inputs['current']['restricted_certificates'] *= 4097
    elif kind == 'boolean_revision':
        inputs['current']['restricted_certificates'][0]['revision'] = True
    elif kind == 'private_pem':
        inputs['current']['restricted_certificates'][0]['certificate'] = 'PRIVATE_INVALID_PAYLOAD'
    else:
        from cryptography.exceptions import UnsupportedAlgorithm
        def unsupported(*arguments):
            raise UnsupportedAlgorithm('PRIVATE_INVALID_PAYLOAD')
        monkeypatch.setattr(x509, 'load_pem_x509_certificate', unsupported)
    with pytest.raises(delta.DeltaRefused) as failure:
        inspect(inputs)
    assert 'PRIVATE' not in str(failure.value)


@pytest.mark.parametrize('table', sorted(delta.TABLES - {'restricted_certificates'}))
def test_other_table_changes_remain_refused(inputs, table):
    inputs['current'][table] = []
    with pytest.raises(delta.DeltaRefused, match='NON_CERTIFICATE_DRIFT'):
        inspect(inputs)


@pytest.mark.parametrize('kind', ['root', 'signature', 'crl_signature', 'crl_floor', 'expired_trust', 'future_capture', 'boolean_time'])
def test_trust_and_time_fail_closed(inputs, kind):
    if kind == 'root':
        inputs['anchor'] = Ed25519PrivateKey.generate().public_key().public_bytes_raw()
    elif kind == 'signature':
        inputs['plan']['candidate']['authority']['signature'] = base64.b64encode(b'\0' * 64).decode()
    elif kind == 'crl_signature':
        crl = x509.load_pem_x509_crl(inputs['plan']['candidate']['crl'].encode())
        builder = x509.CertificateRevocationListBuilder().issuer_name(crl.issuer).last_update(crl.last_update_utc).next_update(crl.next_update_utc)
        for extension in crl.extensions:
            builder = builder.add_extension(extension.value, extension.critical)
        inputs['plan']['candidate']['crl'] = builder.sign(Ed25519PrivateKey.generate(), None).public_bytes(Encoding.PEM).decode()
    elif kind == 'crl_floor':
        inputs['current']['restricted_crl_sequence'][0]['sequence'] += 1
    elif kind == 'expired_trust':
        inputs['captured_at'] += 86400
    elif kind == 'future_capture':
        inputs['captured_at'] = NOW
    else:
        inputs['captured_at'] = True
    with pytest.raises(delta.DeltaRefused):
        inspect(inputs)


@pytest.mark.parametrize('kind', ['signature', 'key', 'device', 'revision', 'serial', 'row_expiry', 'family', 'role',
    'eku', 'ca', 'san', 'unknown_extension', 'not_yet_valid', 'expired', 'backdated', 'long_ttl', 'duplicate'])
def test_added_certificate_semantics_refuse_even_with_valid_ca_signature(inputs, kind):
    row = inputs['current']['restricted_certificates'][0]
    original = x509.load_pem_x509_certificate(row['certificate'].encode())
    if kind == 'signature':
        resign(inputs, signer=Ed25519PrivateKey.generate())
    elif kind == 'key':
        resign(inputs, public=Ed25519PrivateKey.generate().public_key())
    elif kind == 'device':
        row['device'] = '0' * 32
    elif kind == 'revision':
        row['revision'] += 1
    elif kind == 'serial':
        row['serial'] = str(int(row['serial']) + 1)
    elif kind == 'row_expiry':
        row['expires'] += 1
    elif kind in ('family', 'role'):
        attributes = [x509.NameAttribute(attribute.oid, attribute.value.replace('role=device', 'role=gateway')
            if kind == 'role' else ('family=' + '0' * 32 if attribute.value.startswith('family=') else attribute.value))
            for attribute in original.subject]
        resign(inputs, subject=x509.Name(attributes))
    elif kind in ('eku', 'ca', 'san', 'unknown_extension'):
        extensions = list(original.extensions)
        if kind == 'eku':
            extensions[1] = x509.Extension(x509.ExtensionOID.EXTENDED_KEY_USAGE, True, x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]))
        elif kind == 'ca':
            extensions[0] = x509.Extension(x509.ExtensionOID.BASIC_CONSTRAINTS, True, x509.BasicConstraints(ca=True, path_length=0))
        elif kind == 'san':
            extensions[2] = x509.Extension(x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME, False,
                x509.SubjectAlternativeName([x509.UniformResourceIdentifier('urn:wrong:identity')]))
        else:
            extensions.append(x509.Extension(x509.ExtensionOID.SUBJECT_KEY_IDENTIFIER, False,
                x509.SubjectKeyIdentifier.from_public_key(original.public_key())))
        resign(inputs, extensions=extensions)
    elif kind == 'not_yet_valid':
        resign(inputs, before=restricted.utc(inputs['captured_at'] + 1))
    elif kind == 'expired':
        resign(inputs, after=restricted.utc(inputs['captured_at']))
    elif kind == 'backdated':
        resign(inputs, before=restricted.utc(NOW - delta.CLOCK_SKEW - 1))
    elif kind == 'long_ttl':
        resign(inputs, after=restricted.utc(inputs['captured_at'] + 20000))
    else:
        inputs['current']['restricted_certificates'].append(dict(row))
    with pytest.raises(delta.DeltaRefused):
        inspect(inputs)


def test_unexpired_deletion_and_same_serial_replacement_refuse(inputs):
    baseline = inputs['plan']['grant_plan']['before']['restricted_certificates'][0]
    resign(inputs, row=baseline, after=restricted.utc(inputs['captured_at'] + 50))
    with pytest.raises(delta.DeltaRefused, match='UNEXPIRED_CERTIFICATE_REMOVED'):
        inspect(inputs)
    inputs['current']['restricted_certificates'] = [dict(baseline, expires=baseline['expires'] + 1)]
    with pytest.raises(delta.DeltaRefused, match='RETAINED_CERTIFICATE_CHANGED'):
        inspect(inputs)


@pytest.mark.parametrize('kind', ['device_revoke', 'invite_revoke', 'grant_revoke', 'grant_revision', 'grant_family', 'grant_expiry', 'missing_invite'])
def test_membership_must_match_even_if_baseline_rebound(inputs, kind):
    if kind.startswith('device'):
        table, field, value = 'devices', 'revoked', 1
    elif kind.startswith('invite'):
        table, field, value = 'invites', 'revoked', 1
    elif kind == 'grant_revoke':
        table, field, value = 'restricted_grants', 'revoked', 1
    elif kind == 'grant_revision':
        table, field, value = 'restricted_grants', 'revision', 2
    elif kind == 'grant_family':
        table, field, value = 'restricted_grants', 'family', '0' * 32
    elif kind == 'grant_expiry':
        table, field, value = 'restricted_grants', 'expires', inputs['captured_at']
    else:
        inputs['current']['invites'] = []
        inputs['plan']['grant_plan']['before']['invites'] = []
        with pytest.raises(delta.DeltaRefused):
            inspect(inputs)
        return
    inputs['current'][table][0][field] = value
    inputs['plan']['grant_plan']['before'][table] = deepcopy(inputs['current'][table])
    if table == 'restricted_grants':
        inputs['plan']['grant_plan']['after_grants'] = deepcopy(inputs['current'][table])
    with pytest.raises(delta.DeltaRefused):
        inspect(inputs)


def test_new_revoked_serial_is_not_content_compatible(inputs):
    crl = x509.load_pem_x509_crl(inputs['plan']['candidate']['crl'].encode())
    serial = int(inputs['current']['restricted_certificates'][0]['serial'])
    builder = (x509.CertificateRevocationListBuilder().issuer_name(crl.issuer).last_update(crl.last_update_utc)
        .next_update(crl.next_update_utc).add_revoked_certificate(x509.RevokedCertificateBuilder()
            .serial_number(serial).revocation_date(restricted.utc(inputs['captured_at'])).build()))
    for extension in crl.extensions:
        builder = builder.add_extension(extension.value, extension.critical)
    inputs['plan']['candidate']['crl'] = builder.sign(inputs['signer'], None).public_bytes(Encoding.PEM).decode()
    with pytest.raises(delta.DeltaRefused, match='ADDED_CERTIFICATE_REVOKED'):
        inspect(inputs)
