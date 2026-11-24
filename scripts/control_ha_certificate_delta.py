"""Bounded certificate-content compatibility, not issuance or recovery authorization."""
import base64
import hashlib
import json
import re


DOMAIN = b'family-connect/restricted-issuer/v1\0'
PROTOCOL = 'family-connect-5n3-test-v1'
MAX_LIFETIME = 14400
CLOCK_SKEW = 5
TABLES = frozenset(('devices', 'invites', 'restricted_grants', 'restricted_certificates', 'restricted_crl_sequence'))


class DeltaRefused(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise DeltaRefused(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def unique(items):
    result = {}
    for name, value in items:
        require(name not in result, 'DUPLICATE_FIELD')
        result[name] = value
    return result


def decode(value, size):
    require(type(value) is str and len(value) <= 32768, 'BASE64_SHAPE')
    raw = base64.b64decode(value, validate=True)
    require(len(raw) == size and base64.b64encode(raw).decode() == value, 'BASE64_SHAPE')
    return raw


def trusted_material(plan, anchor, now):
    from cryptography import x509
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.hazmat.primitives.serialization import Encoding
    require(type(anchor) is bytes and len(anchor) == 32 and type(now) is int, 'TRUST_INPUT')
    envelope = plan['candidate']['authority']
    require(type(envelope) is dict and set(envelope) == {'payload', 'signature'}, 'DELEGATION_SHAPE')
    require(type(envelope['payload']) is str and len(envelope['payload']) <= 12000, 'DELEGATION_BOUNDS')
    payload = base64.b64decode(envelope['payload'], validate=True)
    require(len(payload) <= 8192, 'DELEGATION_BOUNDS')
    Ed25519PublicKey.from_public_bytes(anchor).verify(decode(envelope['signature'], 64), DOMAIN + payload)
    trust = json.loads(payload, object_pairs_hook=unique)
    require(type(trust) is dict and set(trust) == set('version sequence family gateway authority minimum_revision issued_at expires_at'.split()),
            'DELEGATION_FIELDS')
    require(type(trust['version']) is int and trust['version'] == 1 and type(trust['sequence']) is int
            and 0 < trust['sequence'] < 2**53 and type(trust['minimum_revision']) is int
            and 0 < trust['minimum_revision'] < 2**31, 'DELEGATION_COUNTERS')
    require(all(type(trust[name]) is str and re.fullmatch('[0-9a-f]{32}', trust[name]) for name in ('family', 'gateway')),
            'DELEGATION_IDENTITIES')
    require(type(trust['issued_at']) is int and type(trust['expires_at']) is int
            and trust['issued_at'] <= now < trust['expires_at'], 'DELEGATION_TIME')
    authority = x509.load_pem_x509_certificate(trust['authority'].encode())
    require(authority.public_bytes(Encoding.PEM).decode() == trust['authority']
            and isinstance(authority.public_key(), Ed25519PublicKey), 'AUTHORITY_ENCODING')
    authority.verify_directly_issued_by(authority)
    usage = authority.extensions.get_extension_for_class(x509.KeyUsage).value
    require(authority.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
            and usage.key_cert_sign and usage.crl_sign, 'AUTHORITY_ROLE')
    require(authority.not_valid_before_utc.timestamp() <= now < trust['expires_at'] <= authority.not_valid_after_utc.timestamp(),
            'AUTHORITY_TIME')
    crl_raw = plan['candidate']['crl'].encode()
    require(len(crl_raw) <= 16384, 'CRL_BOUNDS')
    crl = x509.load_pem_x509_crl(crl_raw)
    require(crl.public_bytes(Encoding.PEM) == crl_raw and crl.issuer == authority.subject
            and crl.is_signature_valid(authority.public_key()), 'CRL_SIGNATURE')
    require(crl.last_update_utc.timestamp() <= now < crl.next_update_utc.timestamp()
            and 0 < (crl.next_update_utc - crl.last_update_utc).total_seconds() <= MAX_LIFETIME, 'CRL_TIME')
    number = crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
    require(type(number) is int and 0 < number < 2**53, 'CRL_NUMBER')
    return trust, authority, crl, number


def keyed(rows, field):
    require(type(rows) is list and len(rows) <= 4096, 'ROW_BOUNDS')
    result = {}
    for row in rows:
        require(type(row) is dict and type(row[field]) is str and row[field] not in result, 'ROW_IDENTITY')
        result[row[field]] = row
    return result


def admission_mode(policy):
    require(type(policy) is dict, 'ADMISSION_SHAPE')
    if set(policy) == {'version', 'eligibility'}:
        require(type(policy['version']) is int and policy['version'] == 2
                and policy['eligibility'] == 'all_activated', 'ADMISSION_MODE')
        return 'all_activated'
    require(set(policy) == {'devices'} and type(policy['devices']) is list and len(policy['devices']) <= 256
            and all(type(device) is str and (device == '*' or re.fullmatch('[0-9a-f]{32}', device))
                    for device in policy['devices']), 'ADMISSION_MODE')
    return 'legacy'


def certificate(row, devices, authority, family):
    from cryptography import x509
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.hazmat.primitives.serialization import Encoding
    from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
    require(set(row) == {'device', 'revision', 'serial', 'expires', 'certificate'}
            and type(row['revision']) is int and 0 < row['revision'] < 2**31
            and type(row['expires']) is int and type(row['certificate']) is str
            and len(row['certificate']) <= 16384, 'CERTIFICATE_ROW')
    device = devices[row['device']]
    public = decode(device['public'], 64)
    decode(device['wg'], 32)
    require(hashlib.sha256(public).hexdigest()[:32] == row['device'], 'DEVICE_BINDING')
    value = x509.load_pem_x509_certificate(row['certificate'].encode())
    value.verify_directly_issued_by(authority)
    require(value.public_bytes(Encoding.PEM).decode() == row['certificate']
            and isinstance(value.public_key(), Ed25519PublicKey)
            and value.public_key().public_bytes_raw() == public[32:]
            and str(value.serial_number) == row['serial']
            and int(value.not_valid_after_utc.timestamp()) == row['expires'], 'CERTIFICATE_BINDING')
    subject = x509.Name([x509.NameAttribute(NameOID.SERIAL_NUMBER, row['device']), *[
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, item) for item in (
            'protocol=' + PROTOCOL, 'family=' + family, 'role=device', 'revision=' + str(row['revision']))]])
    require(value.subject == subject, 'CERTIFICATE_SUBJECT')
    expected = [
        (True, x509.BasicConstraints(ca=False, path_length=None)),
        (True, x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH])),
        (False, x509.SubjectAlternativeName([x509.UniformResourceIdentifier('urn:family-connect:identity:' + public.hex()),
                                            x509.DNSName('gateway.family-connect.test')])),
    ]
    require(len(value.extensions) == len(expected) and all(extension.critical == critical and extension.value == content
            for extension, (critical, content) in zip(value.extensions, expected)), 'CERTIFICATE_EXTENSIONS')
    require(authority.not_valid_before_utc <= value.not_valid_before_utc < value.not_valid_after_utc <= authority.not_valid_after_utc
            and (value.not_valid_after_utc - value.not_valid_before_utc).total_seconds() <= MAX_LIFETIME + CLOCK_SKEW,
            'CERTIFICATE_WINDOW')
    return value


def inspect_delta(plan, current, anchor, *, captured_at, admission):
    from cryptography import x509
    from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
    try:
        mode = admission_mode(admission)
        require(type(captured_at) is int and type(plan['grant_plan']['issued_at']) is int
                and 0 < plan['grant_plan']['issued_at'] <= captured_at, 'CAPTURE_TIME')
        require(type(current) is dict and set(current) == TABLES, 'CURRENT_SCOPE')
        before = plan['grant_plan']['before']
        require(type(before) is dict and set(before) == TABLES, 'BASELINE_SCOPE')
        require(all(type(current[table]) is list and type(before[table]) is list
                and len(current[table]) <= 4096 and len(before[table]) <= 4096 for table in TABLES)
                and len(canonical(current)) <= 16 * 1024 * 1024 and len(canonical(before)) <= 16 * 1024 * 1024, 'ROW_BOUNDS')
        trust, authority, crl, number = trusted_material(plan, anchor, captured_at)
        target = dict(before, restricted_grants=plan['grant_plan']['after_grants'],
                      restricted_crl_sequence=[dict(singleton=1, sequence=number)])
        require(all(canonical(sorted(current[table], key=canonical)) == canonical(sorted(target[table], key=canonical))
                for table in TABLES - {'restricted_certificates'}), 'NON_CERTIFICATE_DRIFT')
        devices = keyed(current['devices'], 'device')
        grants = keyed(current['restricted_grants'], 'device')
        invites = keyed([row for row in current['invites'] if row['device'] is not None], 'device')
        baseline = keyed(before['restricted_certificates'], 'serial')
        actual = keyed(current['restricted_certificates'], 'serial')
        retained, removed, added = baseline.keys() & actual.keys(), baseline.keys() - actual.keys(), actual.keys() - baseline.keys()
        require(all(actual[serial] == baseline[serial] for serial in retained), 'RETAINED_CERTIFICATE_CHANGED')
        for row in baseline.values():
            certificate(row, devices, authority, trust['family'])
        require(all(baseline[serial]['expires'] <= captured_at for serial in removed), 'UNEXPIRED_CERTIFICATE_REMOVED')
        for serial in added:
            row = actual[serial]
            value = certificate(row, devices, authority, trust['family'])
            device, invite = devices[row['device']], invites[row['device']]
            grant = grants.get(row['device'])
            require(all(type(record['revoked']) is int and record['revoked'] == 0 for record in (device, invite)),
                    'REVOKED_MEMBERSHIP')
            if grant is None:
                require(mode == 'all_activated' and row['revision'] == trust['minimum_revision'], 'GRANT_REQUIRED')
            else:
                require(type(grant['revoked']) is int and grant['revoked'] == 0, 'REVOKED_MEMBERSHIP')
                require(grant['family'] == trust['family'] and type(grant['revision']) is int
                        and grant['revision'] == row['revision'] >= trust['minimum_revision'], 'GRANT_BINDING')
                if mode == 'legacy':
                    require(grant['expires'] is None or (type(grant['expires']) is int and captured_at < row['expires'] <= grant['expires']),
                            'GRANT_EXPIRY')
            require(max(plan['grant_plan']['issued_at'], trust['issued_at']) - CLOCK_SKEW
                    <= value.not_valid_before_utc.timestamp() <= captured_at < row['expires']
                    <= min(trust['expires_at'], int(crl.next_update_utc.timestamp())), 'ADDED_CERTIFICATE_TIME')
            require(crl.get_revoked_certificate_by_serial_number(value.serial_number) is None, 'ADDED_CERTIFICATE_REVOKED')
        return dict(result='CERTIFICATE_CONTENT_COMPATIBLE_NOT_AUTHORIZED', retained=len(retained),
            expired_removed=len(removed), signed_added=len(added), non_certificate_tables_exact=4,
            admission_mode=mode,
            baseline_sha256=hashlib.sha256(canonical(target)).hexdigest(),
            current_sha256=hashlib.sha256(canonical(current)).hexdigest(),
            challenge_proof='NOT_RECONSTRUCTED', entitlement_history='NOT_VERIFIED',
            snapshot_barrier=False, recovery='BLOCKED', activation='FORBIDDEN')
    except DeltaRefused:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError,
            InvalidSignature, UnsupportedAlgorithm, x509.ExtensionNotFound, x509.DuplicateExtension):
        raise DeltaRefused('CERTIFICATE_DELTA_INVALID') from None
