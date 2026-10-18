import base64
import hmac

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from credential_renewal import DAY, VALIDITY, Rejected, canonical, digest, parse, require, spki


DOMAIN = b'family-connect/renewal-authority-handoff/v2\0'


def verify(raw, validator, previous_authority, operation_id, now):
    try:
        bundle = parse(raw)
        require(set(bundle) == {'payload','signature'}, 'HANDOFF_SCHEMA')
        payload = base64.b64decode(bundle['payload'],validate=True)
        Ed25519PublicKey.from_public_bytes(validator.anchor).verify(base64.b64decode(bundle['signature'],validate=True),DOMAIN+payload)
        value = parse(payload)
        require(set(value) == {'schema','operation_id','previous_authority_sha256','authority','expires_at'}, 'HANDOFF_SCHEMA')
        require(value['schema'] == 2 and value['operation_id'] == operation_id
                and value['previous_authority_sha256'] == digest(canonical(previous_authority)), 'HANDOFF_BINDING')
        require(type(value['expires_at']) is int and now < value['expires_at'] <= now+DAY, 'HANDOFF_EXPIRED')
        previous,old_ca = validator.delegation_parser(previous_authority,validator.anchor,now)
        successor,new_ca = validator.delegation_parser(value['authority'],validator.anchor,now)
        require(successor['sequence'] == previous['sequence']+1, 'HANDOFF_REPLAY')
        require(all(previous[name] == successor[name] for name in ('family','gateway','minimum_revision')), 'HANDOFF_BINDING')
        require(hmac.compare_digest(spki(old_ca.public_key()),spki(new_ca.public_key())) and old_ca.subject == new_ca.subject,
                'ISSUER_SIGNING_KEY_MISMATCH')
        require(successor['expires_at']-successor['issued_at'] == validator.authority_validity
                and (new_ca.not_valid_after_utc-new_ca.not_valid_before_utc).total_seconds() == validator.authority_validity,
                'AUTHORITY_VALIDITY')
        require(successor['expires_at'] > previous['expires_at'], 'AUTHORITY_EXPIRY_ROLLBACK')
        require(tuple(new_ca.extensions) == tuple(old_ca.extensions), 'AUTHORITY_POLICY_CHANGED')
        return value['authority']
    except Rejected:
        raise
    except Exception:
        raise Rejected('HANDOFF_SIGNATURE_OR_SCHEMA') from None
