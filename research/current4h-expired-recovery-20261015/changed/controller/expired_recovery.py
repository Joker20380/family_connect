import base64
from dataclasses import dataclass
import hmac
import re

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from credential_renewal import DAY, VALIDITY, Rejected, canonical, digest, parse, require, spki, utc
from grant_cutover import GRANT_FIELDS


PURPOSE = 'EXPIRED_PREDECESSOR_RECOVERY'
DOMAIN = b'family-connect/expired-predecessor-recovery/v1\0'
ISSUER_DOMAIN = b'family-connect/restricted-issuer/v1\0'
UPDATES = ['authority', 'grants', 'leaf', 'crl', 'profile', 'directory']


@dataclass(frozen=True)
class HistoricalPredecessor:
    encoded: bytes
    trust: dict
    issuer: object
    crl: object
    leaf: object

    @property
    def snapshot(self):
        return parse(self.encoded)


@dataclass(frozen=True)
class RecoveryAuthorization:
    request: dict
    authority: dict
    predecessor: HistoricalPredecessor


def fields(value, names):
    require(type(value) is dict and set(value) == set(names.split()), 'RECOVERY_SCHEMA')


def historical(raw, anchor):
    try:
        value = parse(raw)
        fields(value, 'schema authority crl certificate grants')
        require(type(value['schema']) is int and value['schema'] == 1, 'RECOVERY_SCHEMA')
        envelope = value['authority']
        fields(envelope, 'payload signature')
        payload = base64.b64decode(envelope['payload'], validate=True)
        require(len(payload) <= 8192, 'RECOVERY_SCHEMA')
        Ed25519PublicKey.from_public_bytes(anchor).verify(
            base64.b64decode(envelope['signature'], validate=True), ISSUER_DOMAIN + payload)
        trust = parse(payload)
        fields(trust, 'version sequence family gateway authority minimum_revision issued_at expires_at')
        require(type(trust['version']) is int and trust['version'] == 1, 'RECOVERY_SCHEMA')
        require(type(trust['sequence']) is int and 0 < trust['sequence'] < 2**53, 'RECOVERY_FLOOR')
        require(type(trust['minimum_revision']) is int and 0 < trust['minimum_revision'] < 2**31,
                'RECOVERY_FLOOR')
        require(all(type(trust[name]) is str and re.fullmatch('[0-9a-f]{32}', trust[name])
                    for name in ('family', 'gateway')), 'RECOVERY_SCOPE')
        require(all(type(trust[name]) is int for name in ('issued_at', 'expires_at'))
                and 0 < trust['expires_at'] - trust['issued_at'] <= VALIDITY['authority'], 'RECOVERY_INTERVAL')
        issuer = x509.load_pem_x509_certificate(trust['authority'].encode())
        require(issuer.public_bytes(Encoding.PEM).decode() == trust['authority']
                and isinstance(issuer.public_key(), Ed25519PublicKey), 'RECOVERY_ISSUER')
        issuer.verify_directly_issued_by(issuer)
        require(issuer.extensions.get_extension_for_class(x509.BasicConstraints).value.ca, 'RECOVERY_ISSUER')
        usage = issuer.extensions.get_extension_for_class(x509.KeyUsage).value
        require(usage.key_cert_sign and usage.crl_sign, 'RECOVERY_ISSUER')
        require(0 < (issuer.not_valid_after_utc - issuer.not_valid_before_utc).total_seconds()
                <= VALIDITY['authority'] + 5, 'RECOVERY_INTERVAL')
        require(int(issuer.not_valid_before_utc.timestamp()) <= trust['issued_at']
                and trust['expires_at'] <= int(issuer.not_valid_after_utc.timestamp()), 'RECOVERY_INTERVAL')
        crl = x509.load_pem_x509_crl(value['crl'].encode())
        leaf = x509.load_pem_x509_certificate(value['certificate'].encode())
        require(crl.public_bytes(Encoding.PEM).decode() == value['crl']
                and crl.issuer == issuer.subject and crl.is_signature_valid(issuer.public_key()), 'RECOVERY_CRL')
        leaf.verify_directly_issued_by(issuer)
        from control.friends.restricted import PROTOCOL
        require(leaf.public_bytes(Encoding.PEM).decode() == value['certificate']
                and isinstance(leaf.public_key(), Ed25519PublicKey)
                and not leaf.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
                and ExtendedKeyUsageOID.SERVER_AUTH in leaf.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value,
                'RECOVERY_GATEWAY_BINDING')
        require([entry.value for entry in leaf.subject.get_attributes_for_oid(NameOID.SERIAL_NUMBER)] == [trust['gateway']],
                'RECOVERY_GATEWAY_BINDING')
        attributes = [entry.value for entry in leaf.subject.get_attributes_for_oid(NameOID.ORGANIZATIONAL_UNIT_NAME)]
        require(len(attributes) == 4 and set(attributes[:3]) == {'protocol='+PROTOCOL, 'family='+trust['family'], 'role=gateway'}
                and re.fullmatch('revision=[1-9][0-9]*', attributes[3])
                and int(attributes[3].split('=')[1]) >= trust['minimum_revision'], 'RECOVERY_GATEWAY_BINDING')
        identifiers = leaf.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.UniformResourceIdentifier)
        require(len(identifiers) == 1 and re.fullmatch('urn:family-connect:identity:[0-9a-f]{128}', identifiers[0]),
                'RECOVERY_GATEWAY_BINDING')
        identity = bytes.fromhex(identifiers[0].split(':')[-1])
        require(digest(identity)[:32] == trust['gateway'] and identity[32:] == leaf.public_key().public_bytes_raw(),
                'RECOVERY_GATEWAY_BINDING')
        require(leaf.extensions.get_extension_for_class(x509.AuthorityKeyIdentifier).value.key_identifier
                == issuer.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value.digest, 'RECOVERY_ISSUER')
        require(0 < (leaf.not_valid_after_utc - leaf.not_valid_before_utc).total_seconds() <= VALIDITY['leaf'] + 5
                and 0 < (crl.next_update_utc - crl.last_update_utc).total_seconds() <= VALIDITY['crl'], 'RECOVERY_INTERVAL')
        require(issuer.not_valid_before_utc <= min(leaf.not_valid_before_utc, crl.last_update_utc)
                and max(leaf.not_valid_after_utc, crl.next_update_utc) <= issuer.not_valid_after_utc, 'RECOVERY_INTERVAL')
        number = crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
        require(type(number) is int and 0 < number < 2**53, 'RECOVERY_FLOOR')
        require(type(value['grants']) is list and 0 < len(value['grants']) <= 256, 'RECOVERY_SCHEMA')
        seen = set()
        for row in value['grants']:
            fields(row, ' '.join(GRANT_FIELDS))
            require(type(row['device']) is str and re.fullmatch('[0-9a-f]{32}', row['device'])
                    and row['device'] not in seen, 'RECOVERY_SCOPE')
            seen.add(row['device'])
            require(row['family'] == trust['family'] and type(row['revision']) is int
                    and trust['minimum_revision'] <= row['revision'] < 2**31
                    and type(row['revoked']) is int and row['revoked'] in (0, 1)
                    and type(row['expires']) is int and row['expires'] <= trust['expires_at'], 'RECOVERY_FLOOR')
        return HistoricalPredecessor(canonical(value), trust, issuer, crl, leaf)
    except Rejected:
        raise
    except Exception:
        raise Rejected('RECOVERY_PREDECESSOR_UNTRUSTED') from None


def floors(predecessor):
    require(type(predecessor) is HistoricalPredecessor, 'RECOVERY_TYPE')
    return dict(authority=predecessor.trust['sequence'], minimum_revision=predecessor.trust['minimum_revision'],
                crl=predecessor.crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number,
                grants={row['device']: row['revision'] for row in predecessor.snapshot['grants']})


def request_check(request, validator, now, *, accepted_at=None):
    fields(request, 'schema purpose operation_id predecessor predecessor_sha256 scope floors checkpoint expected grant_scope updates successor_payload created_at expires_at')
    require(type(request['schema']) is int and request['schema'] == 3 and request['purpose'] == PURPOSE, 'RECOVERY_PURPOSE')
    require(type(request['operation_id']) is str and re.fullmatch('[a-z0-9-]{16,96}', request['operation_id']), 'OPERATION_ID')
    require(all(type(request[name]) is int for name in ('created_at', 'expires_at'))
            and 0 < request['expires_at'] - request['created_at'] <= DAY, 'RECOVERY_APPROVAL_EXPIRED')
    observed = now if accepted_at is None else accepted_at
    require(type(observed) is int and request['created_at'] <= observed <= now < request['expires_at'],
            'RECOVERY_APPROVAL_EXPIRED')
    predecessor = historical(canonical(request['predecessor']), validator.anchor)
    require(predecessor.trust['expires_at'] <= request['created_at']
            and predecessor.leaf.not_valid_after_utc <= utc(request['created_at'])
            and predecessor.crl.next_update_utc <= utc(request['created_at'])
            and all(row['revoked'] or row['expires'] <= request['created_at']
                    for row in predecessor.snapshot['grants']), 'RECOVERY_NOT_REQUIRED')
    require(digest(predecessor.encoded) == request['predecessor_sha256'], 'RECOVERY_PREDECESSOR_DIGEST')
    require(request['scope'] == {name: predecessor.trust[name] for name in ('family', 'gateway')}
            and request['floors'] == floors(predecessor), 'RECOVERY_SCOPE_OR_FLOOR')
    fields(request['checkpoint'], 'operation_id plan_sha256 snapshot_sha256')
    require(set(request['expected']) == {'RU', 'NL'}, 'RECOVERY_SCHEMA')
    approved = request['grant_scope']
    require(type(approved) is list and approved == sorted(set(approved)) and bool(approved)
            and approved == sorted(row['device'] for row in predecessor.snapshot['grants'] if not row['revoked']),
            'RECOVERY_GRANT_SCOPE')
    require(request['updates'] == UPDATES, 'RECOVERY_UPDATE_SCOPE')
    successor = request['successor_payload']
    require(type(successor) is dict and set(successor) == set(predecessor.trust), 'RECOVERY_SCHEMA')
    require(all(successor[name] == predecessor.trust[name] for name in ('version', 'family', 'gateway', 'minimum_revision'))
            and successor['sequence'] == predecessor.trust['sequence'] + 1, 'RECOVERY_SCOPE_OR_FLOOR')
    require(type(successor['issued_at']) is int and type(successor['expires_at']) is int
            and successor['expires_at'] - successor['issued_at'] == VALIDITY['authority']
            and successor['issued_at'] <= now < successor['expires_at']
            and successor['expires_at'] > predecessor.trust['expires_at'], 'RECOVERY_SUCCESSOR_INVALID')
    issuer = x509.load_pem_x509_certificate(successor['authority'].encode())
    issuer.verify_directly_issued_by(issuer)
    require(hmac.compare_digest(spki(issuer.public_key()), spki(predecessor.issuer.public_key()))
            and issuer.subject == predecessor.issuer.subject and issuer.issuer == predecessor.issuer.issuer
            and tuple(issuer.extensions) == tuple(predecessor.issuer.extensions), 'RECOVERY_ISSUER')
    require(int(issuer.not_valid_before_utc.timestamp()) == successor['issued_at']
            and int(issuer.not_valid_after_utc.timestamp()) == successor['expires_at'], 'RECOVERY_INTERVAL')
    return predecessor


def sign(request, validator, signer, now):
    require(signer.public_key().public_bytes_raw() == validator.anchor, 'TRUST_ROOT_KEY_MISMATCH')
    request_check(request, validator, now)
    payload = canonical(request['successor_payload'])
    authority = dict(payload=base64.b64encode(payload).decode(),
                     signature=base64.b64encode(signer.sign(ISSUER_DOMAIN + payload)).decode())
    validator.delegation_parser(authority, validator.anchor, now)
    payload = canonical(dict(request=request, authority=authority))
    return canonical(dict(payload=base64.b64encode(payload).decode(),
                          signature=base64.b64encode(signer.sign(DOMAIN + payload)).decode()))


def verify(raw, validator, operation, now, *, accepted_at=None):
    try:
        bundle = parse(raw)
        fields(bundle, 'payload signature')
        payload = base64.b64decode(bundle['payload'], validate=True)
        try:
            Ed25519PublicKey.from_public_bytes(validator.anchor).verify(
                base64.b64decode(bundle['signature'], validate=True), DOMAIN + payload)
        except Exception:
            raise Rejected('RECOVERY_SIGNATURE_INVALID') from None
        value = parse(payload)
        fields(value, 'request authority')
        request = value['request']
        predecessor = request_check(request, validator, now, accepted_at=accepted_at)
        require(request['operation_id'] == operation, 'RECOVERY_OPERATION_MISMATCH')
        trust, _ = validator.delegation_parser(value['authority'], validator.anchor, now)
        require(trust == request['successor_payload'], 'RECOVERY_SUCCESSOR_INVALID')
        return RecoveryAuthorization(request, value['authority'], predecessor)
    except Rejected:
        raise
    except Exception:
        raise Rejected('RECOVERY_SUCCESSOR_INVALID') from None


def transition(validator, authorization, candidate, now):
    require(type(authorization) is RecoveryAuthorization, 'RECOVERY_TYPE')
    old = authorization.predecessor
    try:
        validated = validator.validate(canonical(candidate), now)
    except Exception:
        raise Rejected('RECOVERY_STRICT_SUCCESSOR_INVALID') from None
    _, trust, issuer, crl, leaf = validated
    require(candidate['authority'] == authorization.authority, 'RECOVERY_SUCCESSOR_INVALID')
    require(spki(old.leaf.public_key()) == spki(leaf.public_key()) and old.leaf.subject == leaf.subject
            and tuple(old.leaf.extensions) == tuple(leaf.extensions), 'RECOVERY_GATEWAY_BINDING')
    require(leaf.not_valid_after_utc > old.leaf.not_valid_after_utc
            and crl.next_update_utc > old.crl.next_update_utc, 'RECOVERY_FLOOR')
    require(crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number == floors(old)['crl'] + 1,
            'RECOVERY_FLOOR')
    for entry in old.crl:
        successor = crl.get_revoked_certificate_by_serial_number(entry.serial_number)
        require(successor is not None and successor.revocation_date_utc == entry.revocation_date_utc
                and tuple(successor.extensions) == tuple(entry.extensions), 'REVOCATION_SET_LOSS')
    require(len(old.snapshot['grants']) == len(candidate['grants']), 'RECOVERY_GRANT_SCOPE')
    for before, after in zip(old.snapshot['grants'], candidate['grants']):
        require({key: value for key, value in before.items() if key not in ('revision', 'expires')}
                == {key: value for key, value in after.items() if key not in ('revision', 'expires')}, 'RECOVERY_GRANT_SCOPE')
        if before['device'] not in authorization.request['grant_scope']:
            require(after == before, 'RECOVERY_GRANT_SCOPE')
        else:
            require(after['revision'] == before['revision'] + 1 and after['expires'] > before['expires'], 'RECOVERY_FLOOR')
    return validated
