import base64
from copy import deepcopy

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding

from control.friends import restricted
from scripts import control_ha_forward_checkpoint as forward
from scripts.control_ha_import import ImportRejected, encoded
from scripts.control_ha_recovery_bundle import parse
from scripts.referral_postgres_rehearsal import NOW
from test_multi_gateway_renewal import make_fleet


@pytest.fixture(scope='module')
def native_publications(tmp_path_factory):
    fleet = make_fleet(tmp_path_factory.mktemp('forward-publications'), now=NOW)
    authorities = {'NL': encoded(fleet.service.manifest),
                   'NL2': (fleet.nodes['RU'].live / 'gateways/nl-amsterdam-2/issuer.json').read_bytes()}
    publications = {node: (fleet.nodes[node].live / 'directory.json').read_bytes() for node in forward.GATEWAYS}
    floors = {node: restricted.delegation(parse(raw), fleet.service.anchor, NOW)[0]['sequence']
              for node, raw in authorities.items()}
    return dict(authorities=authorities, publications=publications, gateway_ids=fleet.identities,
        minimum_authority_sequences=floors, issuer=dict(delegation=authorities['NL'], directory=publications['NL']),
        anchor=fleet.service.anchor, captured_at=NOW, now=NOW), fleet.root_key


@pytest.fixture
def materials(native_publications):
    return deepcopy(native_publications[0])


def resign(materials, signer, node, change):
    envelope = parse(materials['authorities'][node])
    value = parse(base64.b64decode(envelope['payload'], validate=True))
    change(value)
    raw = encoded(value)
    materials['authorities'][node] = encoded(dict(payload=base64.b64encode(raw).decode(),
        signature=base64.b64encode(signer.sign(restricted.DOMAIN + raw)).decode()))
    if node == 'NL':
        materials['issuer']['delegation'] = materials['authorities'][node]


def publication(materials, node, change):
    value = parse(materials['publications'][node])
    change(value)
    materials['publications'][node] = encoded(value)
    if node == 'NL':
        materials['issuer']['directory'] = materials['publications'][node]


def test_two_native_publications_are_validated_without_changing_bytes(materials):
    before = deepcopy(materials)
    assert forward.check_publications(**materials) is None
    assert materials == before


@pytest.mark.parametrize('field', ['authorities', 'publications', 'gateway_ids'])
def test_swapping_nodes_is_not_equivalent_to_the_right_fleet(materials, field):
    materials[field]['NL'], materials[field]['NL2'] = materials[field]['NL2'], materials[field]['NL']
    with pytest.raises(ImportRejected):
        forward.check_publications(**materials)


@pytest.mark.parametrize('field', ['authorities', 'publications', 'gateway_ids', 'minimum_authority_sequences'])
@pytest.mark.parametrize('node', ['NL', 'NL2', 'extra'])
def test_exact_two_node_coverage(materials, field, node):
    if node == 'extra':
        materials[field][node] = materials[field]['NL']
    else:
        del materials[field][node]
    with pytest.raises(ImportRejected):
        forward.check_publications(**materials)


def test_duplicate_gateway_identity_refuses(materials):
    materials['gateway_ids']['NL2'] = materials['gateway_ids']['NL']
    with pytest.raises(ImportRejected, match='FORWARD_GATEWAY_ALIASED'):
        forward.check_publications(**materials)


@pytest.mark.parametrize('node', ['NL', 'NL2'])
@pytest.mark.parametrize('floor', [True, 0, -1, 2**53, 999])
def test_authority_floor_is_independent_and_cannot_be_lowered(materials, node, floor):
    materials['minimum_authority_sequences'][node] = floor
    with pytest.raises(ImportRejected, match='FORWARD_AUTHORITY_(FLOORS|ROLLBACK)'):
        forward.check_publications(**materials)


@pytest.mark.parametrize('node', ['NL', 'NL2'])
@pytest.mark.parametrize('change', [dict(gateway='f' * 32), dict(expires_at=NOW),
    dict(issued_at=NOW + 1), dict(sequence=True), dict(minimum_revision=True)])
def test_even_root_signed_bad_scope_or_time_refuses(materials, native_publications, node, change):
    resign(materials, native_publications[1], node, lambda value: value.update(change))
    with pytest.raises(ImportRejected):
        forward.check_publications(**materials)


@pytest.mark.parametrize('node', ['NL', 'NL2'])
def test_delegation_must_already_be_valid_at_capture(materials, native_publications, node):
    materials['captured_at'] = NOW - 2
    resign(materials, native_publications[1], node, lambda value: value.update(issued_at=NOW - 1))
    with pytest.raises(ImportRejected, match='FORWARD_PUBLICATION_INVALID'):
        forward.check_publications(**materials)


@pytest.mark.parametrize('field', ['family', 'minimum_revision'])
def test_same_root_does_not_allow_secondary_family_or_policy_drift(materials, native_publications, field):
    value = 'f' * 32 if field == 'family' else 2
    resign(materials, native_publications[1], 'NL2', lambda document: document.update({field: value}))
    if field == 'family':
        publication(materials, 'NL2', lambda document: document.update(family=value))
    with pytest.raises(ImportRejected, match='FORWARD_SHARED_AUTHORITY'):
        forward.check_publications(**materials)


@pytest.mark.parametrize('with_extensions', [True, False])
def test_secondary_ca_change_is_not_implicitly_authorized(materials, native_publications, with_extensions):
    _, authority = restricted.delegation(parse(materials['authorities']['NL2']), materials['anchor'], NOW)
    key = Ed25519PrivateKey.generate()
    builder = (x509.CertificateBuilder().subject_name(authority.subject).issuer_name(authority.subject)
        .public_key(key.public_key()).serial_number(authority.serial_number)
        .not_valid_before(authority.not_valid_before_utc).not_valid_after(authority.not_valid_after_utc))
    if with_extensions:
        for extension in authority.extensions:
            builder = builder.add_extension(extension.value, extension.critical)
    changed = builder.sign(key, None).public_bytes(Encoding.PEM).decode()
    resign(materials, native_publications[1], 'NL2', lambda value: value.update(authority=changed))
    with pytest.raises(ImportRejected, match='FORWARD_(SHARED_AUTHORITY|PUBLICATION_INVALID)'):
        forward.check_publications(**materials)


@pytest.mark.parametrize('node', ['NL', 'NL2'])
def test_wrong_root_signature_is_not_fresh_owner_authorization(materials, node):
    resign(materials, Ed25519PrivateKey.generate(), node, lambda value: value.update(sequence=2))
    with pytest.raises(ImportRejected, match='FORWARD_PUBLICATION_INVALID'):
        forward.check_publications(**materials)


@pytest.mark.parametrize('node', ['NL', 'NL2'])
@pytest.mark.parametrize('kind', ['expired', 'future', 'overlong', 'gateway', 'family', 'transport',
    'url', 'duplicate-seed', 'version', 'extra', 'empty'])
def test_native_directory_rules_apply_to_both_nodes(materials, node, kind):
    def change(value):
        if kind == 'expired':
            value.update(issued_at=restricted.iso(NOW - 120), expires_at=restricted.iso(NOW))
        elif kind == 'future':
            value.update(issued_at=restricted.iso(NOW + 1), expires_at=restricted.iso(NOW + 120))
        elif kind == 'overlong':
            value.update(issued_at=restricted.iso(NOW), expires_at=restricted.iso(NOW + restricted.MAX_TEST_LIFETIME + 1))
        elif kind == 'gateway':
            value['seeds'][0]['gateway'] = 'f' * 32
        elif kind == 'family':
            value['family'] = 'f' * 32
        elif kind == 'transport':
            value['seeds'][0]['transport'] = 'mesh'
        elif kind == 'url':
            value['seeds'][0]['join_url'] = 'http://invalid.example/room'
        elif kind == 'duplicate-seed':
            value['seeds'].append(dict(value['seeds'][0]))
        elif kind == 'version':
            value['version'] = True
        elif kind == 'extra':
            value['extra'] = 'unrecognized'
        else:
            value['seeds'] = []
    publication(materials, node, change)
    with pytest.raises(ImportRejected, match='FORWARD_PUBLICATION_INVALID'):
        forward.check_publications(**materials)


@pytest.mark.parametrize('node', ['NL', 'NL2'])
def test_directory_must_already_exist_at_capture(materials, node):
    materials['captured_at'] = NOW - 2
    publication(materials, node, lambda value: value.update(issued_at=restricted.iso(NOW - 1),
                                                           expires_at=restricted.iso(NOW + 119)))
    with pytest.raises(ImportRejected, match='FORWARD_PUBLICATION_INVALID'):
        forward.check_publications(**materials)


@pytest.mark.parametrize('now', ['expiry', NOW - 1, True])
def test_verification_time_is_not_authorization_lifetime(materials, now):
    materials['now'] = restricted.timestamp(parse(materials['publications']['NL2'])['expires_at']) if now == 'expiry' else now
    with pytest.raises(ImportRejected):
        forward.check_publications(**materials)


@pytest.mark.parametrize('field,raw', [('authorities', b'{}'), ('authorities', b' ' * 16385),
    ('publications', b' ' * 8193), ('publications', b'{"version":1,"version":1}'),
    ('authorities', b'{"payload":"","payload":"","signature":""}')])
def test_bounded_malformed_and_duplicate_documents_refuse(materials, field, raw):
    materials[field]['NL2'] = raw
    with pytest.raises(ImportRejected):
        forward.check_publications(**materials)
