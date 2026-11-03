import base64
import re

from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from credential_renewal import THRESHOLD, VALIDITY, canonical, digest, parse, require, spki, utc


def membership(value):
    require(type(value) is dict and set(value) == {'NL','NL2'}
            and all(type(identity) is str and re.fullmatch('[0-9a-f]{32}',identity) for identity in value.values())
            and len(set(value.values())) == 2, 'GATEWAY_SET_INVALID')
    return parse(canonical(value))


def selected(plan, slot):
    return plan['secondary'] if slot == 'NL2' else plan


def authorities(envelopes, validator, identities, now):
    identities = membership(identities)
    require(type(envelopes) is dict and set(envelopes) == set(identities), 'GATEWAY_AUTHORITY_BINDING')
    parsed = {slot:validator.delegation_parser(envelope,validator.anchor,now) for slot,envelope in envelopes.items()}
    require(all(parsed[slot][0]['gateway'] == identity for slot,identity in identities.items())
            and all(parsed['NL'][0][name] == parsed['NL2'][0][name]
                    for name in ('family','authority','minimum_revision')), 'GATEWAY_AUTHORITY_BINDING')
    return parsed


def authority_request(primary, secondary, validator, identities, now):
    parsed = authorities({'NL':primary['previous_authority'],'NL2':secondary},validator,identities,now)
    successor = dict(primary['successor_payload'],gateway=identities['NL2'],sequence=parsed['NL2'][0]['sequence']+1)
    other = dict(primary,previous_authority=secondary,successor_payload=successor)
    return dict(schema=2,operation_id=primary['operation_id'],gateway_ids=membership(identities),
                requests={'NL':primary,'NL2':other})


def verify_handoff(raw, validator, previous, identities, operation, now):
    from offline_handoff import verify
    value = parse(raw)
    require(type(value) is dict and set(value) == {'schema','gateway_ids','bundles'}
            and type(value['schema']) is int and value['schema'] == 1
            and value['gateway_ids'] == membership(identities)
            and type(value['bundles']) is dict and set(value['bundles']) == set(identities), 'FLEET_HANDOFF_SCHEMA')
    authorities(previous,validator,identities,now)
    successor = {slot:verify(base64.b64decode(value['bundles'][slot],validate=True),validator,
        previous[slot],operation,now) for slot in identities}
    authorities(successor,validator,identities,now)
    return successor


def shared(primary, secondary, identities):
    identities = membership(identities)
    primary_value,primary_trust,_,_,primary_leaf = primary
    secondary_value,secondary_trust,_,_,secondary_leaf = secondary
    require(all(primary_trust[name] == secondary_trust[name] for name in ('family','authority','minimum_revision')),
            'GATEWAY_AUTHORITY_BINDING')
    require(primary_trust['gateway'] == identities['NL'] and secondary_trust['gateway'] == identities['NL2'],
            'GATEWAY_SET_BINDING')
    require(all(primary_value[name] == secondary_value[name] for name in ('crl','grants')), 'GATEWAY_SHARED_STATE_MISMATCH')
    require(spki(primary_leaf.public_key()) != spki(secondary_leaf.public_key()), 'GATEWAY_KEY_CLONED')
    certificate_binding(primary,identities['NL'])
    certificate_binding(secondary,identities['NL2'])


def certificate_binding(validated, identity):
    from control.friends.restricted import PROTOCOL
    _,trust,_,crl,leaf = validated
    require(trust['gateway'] == identity, 'GATEWAY_BINDING')
    require(crl.get_revoked_certificate_by_serial_number(leaf.serial_number) is None, 'GATEWAY_REVOKED')
    claims = [attribute.value for attribute in leaf.subject.get_attributes_for_oid(NameOID.ORGANIZATIONAL_UNIT_NAME)]
    revisions = [claim.removeprefix('revision=') for claim in claims if claim.startswith('revision=')]
    require(len(claims) == 4 and len(revisions) == 1 and re.fullmatch('[0-9]{1,19}',revisions[0])
            and trust['minimum_revision'] <= int(revisions[0]) <= 2**63-1
            and set(claims) == {'protocol='+PROTOCOL,'family='+trust['family'],'role=gateway','revision='+revisions[0]}
            and [attribute.value for attribute in leaf.subject.get_attributes_for_oid(NameOID.SERIAL_NUMBER)]
                == [identity], 'GATEWAY_CERTIFICATE_BINDING')
    require(not leaf.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
            and list(leaf.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value)
                == [ExtendedKeyUsageOID.SERVER_AUTH], 'GATEWAY_CERTIFICATE_ROLE')
    identities = leaf.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(
        x509.UniformResourceIdentifier)
    prefix = 'urn:family-connect:identity:'
    require(len(identities) == 1 and re.fullmatch(prefix+'[0-9a-f]{128}',identities[0]), 'GATEWAY_CERTIFICATE_IDENTITY')
    public = bytes.fromhex(identities[0][len(prefix):])
    require(digest(public)[:32] == identity
            and leaf.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw) == public[32:], 'GATEWAY_CERTIFICATE_IDENTITY')


def bound_profile(validated, gateway, identity):
    value,trust,_,crl,_ = validated
    require(type(gateway) is dict and set(gateway) == {'family','gateway','minimum_revision','minimum_crl',
            'authority','certificate','revocations','profile_sha256'}
            and type(gateway['minimum_revision']) is int, 'GATEWAY_PROFILE_SCHEMA')
    require(trust['gateway'] == identity and all(gateway[name] == trust[name]
            for name in ('family','gateway','minimum_revision','authority'))
            and gateway['certificate'] == value['certificate'] and gateway['revocations'] == value['crl'],
            'GATEWAY_BINDING')
    sequence = crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
    require(type(gateway['minimum_crl']) is int and 0 < gateway['minimum_crl'] <= sequence, 'GATEWAY_CRL_FLOOR')
    require(type(gateway['profile_sha256']) is str and re.fullmatch('[0-9a-f]{64}',gateway['profile_sha256']),
            'GATEWAY_PROFILE_HASH')
    certificate_binding(validated,identity)


def validate(plan, validator, now, identities, *, recovery=False, authorization=None):
    require(plan['schema'] == 2 and plan['gateway_ids'] == membership(identities)
            and type(plan['secondary']) is dict
            and set(plan['secondary']) == {'previous','candidate','nl_profile_sha256'}
            and type(plan['secondary']['nl_profile_sha256']) is str
            and re.fullmatch('[0-9a-f]{64}',plan['secondary']['nl_profile_sha256']), 'GATEWAY_PLAN_SCHEMA')
    validation_time = plan['grant_plan']['issued_at'] if recovery else now
    secondary = plan['secondary']
    if authorization is not None:
        from expired_recovery import transition
        require(authorization.secondary is not None and authorization.request['gateway_ids'] == identities,
                'RECOVERY_SCOPE')
        require(canonical(plan['previous']) == authorization.predecessor.encoded
                and canonical(secondary['previous']) == authorization.secondary.predecessor.encoded,
                'RECOVERY_PREDECESSOR_DIGEST')
        shared(authorization.predecessor.material,authorization.secondary.predecessor.material,identities)
        shared(transition(validator,authorization,plan['candidate'],now),
               transition(validator,authorization.secondary,secondary['candidate'],now),identities)
        return
    validator.transition(canonical(secondary['previous']),canonical(secondary['candidate']),validation_time,
                         revoke=True,expired_leaf_predecessor=True)
    for phase in ('previous','candidate'):
        options = {'expired_leaf_predecessor':True} if phase == 'previous' else {}
        primary = validator.validate(canonical(plan[phase]),validation_time,**options)
        other = validator.validate(canonical(secondary[phase]),validation_time,**options)
        shared(primary,other,identities)


def prepare(plan, gateway, manifest, identities, validator, signer, now, *, successor_manifest=None, authorization=None):
    previous = dict(plan['previous'],authority=manifest,certificate=gateway['certificate'])
    if authorization is None:
        old = validator.validate(canonical(previous),now,expired_leaf_predecessor=True)
        primary = validator.validate(canonical(plan['previous']),now,expired_leaf_predecessor=True)
    else:
        require(authorization.secondary is not None and canonical(previous) == authorization.secondary.predecessor.encoded
                and canonical(plan['previous']) == authorization.predecessor.encoded, 'RECOVERY_PREDECESSOR_DIGEST')
        old,primary = authorization.secondary.predecessor.material,authorization.predecessor.material
    shared(primary,old,identities)
    bound_profile(old,gateway,identities['NL2'])
    _,_,_,_,leaf = old
    candidate_manifest = manifest if successor_manifest is None else successor_manifest
    trust,issuer = validator.delegation_parser(candidate_manifest,validator.anchor,now)
    successor = gateway['certificate']
    if int(leaf.not_valid_after_utc.timestamp()) - now <= THRESHOLD['leaf']:
        issued = max(now-5,int(issuer.not_valid_before_utc.timestamp()))
        require(trust['expires_at'] >= issued+VALIDITY['leaf'], 'OFFLINE_AUTHORITY_RENEWAL_REQUIRED')
        builder = (x509.CertificateBuilder().subject_name(leaf.subject).issuer_name(issuer.subject)
            .public_key(leaf.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(utc(issued)).not_valid_after(utc(issued+VALIDITY['leaf'])))
        for extension in leaf.extensions:
            builder = builder.add_extension(extension.value,extension.critical)
        successor = builder.sign(signer,None).public_bytes(Encoding.PEM).decode()
    candidate = dict(plan['candidate'],authority=candidate_manifest,certificate=successor)
    return dict(previous=previous,candidate=candidate,nl_profile_sha256=gateway['profile_sha256'])
