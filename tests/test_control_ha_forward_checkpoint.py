from contextlib import closing
from copy import deepcopy
from dataclasses import asdict
import secrets
import shutil
import sqlite3

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from control.friends import restricted, restricted_admin
from control.friends.access import Access, EnrollmentTransaction
from scripts import control_ha_forward_checkpoint as forward
from scripts import control_ha_legacy_custody as custody
from scripts.control_ha_import import ImportRejected, digest, encoded
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_maintenance_fixture import artifacts_for_maintenance
from scripts.control_ha_online_capsule import bind_current
from scripts.control_ha_online_fixture import native_fixture
from scripts.control_ha_receiver_v1 import preflight_receivers
from scripts.control_ha_recovery_bundle import parse, seal
from scripts.control_ha_sqlite_fixture import refresh_fixture
from scripts.referral_postgres_rehearsal import NOW
from scripts.restricted_postgres_rehearsal import issue_proof
from test_control_ha_current_audit import NativeServiceBarrier, current, native_current, rewrite, sealed
from test_control_ha_legacy_custody import write
from test_control_ha_renewal_v1 import OPERATION


@pytest.fixture
def candidate(current):
    return candidate_for(current)


def candidate_for(current):
    state = current['recovered']
    recovery_key = secrets.token_bytes(32)
    recovery_bundle, recovery_checkpoint = seal(state.stores, state.references, state.artifacts,
        CHECKPOINT, state.bootstrap, current['anchor'], recovery_key, now=NOW)
    history_bundle, history_checkpoint = sealed(current)
    sources = {node: dict(runtime_sha256=digest(b'runtime'), configuration_sha256=digest(node.encode()))
               for node in forward.NODES}
    issuer = Ed25519PrivateKey.from_private_bytes(state.artifacts['issuer_material']['runtime-key'])
    plan = parse((current['roots']['coordinator'] / 'plan.json').read_bytes())
    gateway_ids = plan['gateway_ids']
    authorities = current.get('authorities', {
        'NL': encoded(plan['candidate']['authority']), 'NL2': encoded(plan['secondary']['candidate']['authority'])})
    floors = {node: restricted.delegation(parse(raw), current['anchor'], NOW)[0]['sequence']
              for node, raw in authorities.items()}
    request = forward.request_for(recovery_checkpoint, history_checkpoint, sequence=2, captured_at=NOW,
        expires_at=NOW + 300, sources=sources, publications=current['publications'],
        issuer_public_sha256=digest(issuer.public_key().public_bytes_raw()), gateway_ids=gateway_ids, authorities=authorities)
    signer = Ed25519PrivateKey.generate()
    number = x509.load_pem_x509_crl(state.artifacts['issuer_material']['crl']).extensions.get_extension_for_class(
        x509.CRLNumber).value.crl_number
    return dict(current=current, signer=signer, request=request, signature=signer.sign(forward.DOMAIN + request),
        trusted_key=signer.public_key().public_bytes_raw(), expected_request_sha256=digest(request),
        recovery_checkpoint=recovery_checkpoint, history_checkpoint=history_checkpoint,
        arguments=dict(minimum_sequence=1, minimum_crl=number, now=NOW, recovery_bundle=recovery_bundle, recovery_key=recovery_key,
            history_bundle=history_bundle, history_key=current['key'], anchor=current['anchor'],
            sources=sources, publications=dict(current['publications']), gateway_ids=gateway_ids,
            authorities=authorities, minimum_authority_sequences=floors))


def verify(candidate, **overrides):
    return forward.verify(candidate['request'], candidate['signature'], candidate['trusted_key'],
                          candidate['expected_request_sha256'], **dict(candidate['arguments'], **overrides))


def authorize(candidate, change):
    document = parse(candidate['request'])
    change(document)
    candidate['request'] = encoded(document)
    candidate['expected_request_sha256'] = digest(candidate['request'])
    candidate['signature'] = candidate['signer'].sign(forward.DOMAIN + candidate['request'])


def recapture_history(candidate):
    bundle, checkpoint = sealed(candidate['current'])
    candidate['arguments']['history_bundle'] = bundle
    authorize(candidate, lambda value: value.update(history=asdict(checkpoint)))


def test_source_removed_readback_preserves_all_bytes_without_history_authority(candidate):
    current = candidate['current']
    before = custody.inspect(candidate['arguments']['history_bundle'], current['key'], candidate['history_checkpoint'])
    for root in current['roots'].values():
        shutil.rmtree(root)
    qualified = verify(candidate)
    assert qualified.current.stores == current['recovered'].stores
    assert qualified.current.artifacts == current['recovered'].artifacts
    assert qualified.history.trees == before.trees
    assert qualified.authorities == candidate['arguments']['authorities']
    assert qualified.publications == candidate['arguments']['publications']
    summary = qualified.summary()
    assert summary['result'] == 'FORWARD_CHECKPOINT_OFFLINE_QUALIFIED'
    assert summary['activation'] == 'FORBIDDEN'
    assert summary['database_import'] == summary['host_resume'] == 'NOT_AUTHORIZED'
    assert summary['capture_consistency'] == summary['full_recovery'] == 'NOT_QUALIFIED'
    assert summary['publication_semantics'] == 'BOTH_GATEWAYS_CHECKED_OFFLINE'
    assert summary['live_publication'] == 'NOT_ATTESTED'
    assert not hasattr(qualified, 'snapshot')
    assert 'runtime-key' not in repr(qualified)


def test_post_renewal_native_write_binds_fresh_state_not_old_baseline(candidate):
    state = candidate['current']['recovered']
    with closing(sqlite3.connect(':memory:')) as database:
        database.deserialize(state.stores['registry'])
        EnrollmentTransaction(database, '?').add_invitation(digest(b'new-current-invitation'))
        database.commit()
        stores = dict(state.stores, registry=database.serialize())
    bundle, checkpoint = seal(stores, state.references, state.artifacts, CHECKPOINT, state.bootstrap,
        candidate['arguments']['anchor'], candidate['arguments']['recovery_key'], now=NOW)
    with pytest.raises(ImportRejected, match='BUNDLE_CHECKPOINT_MISMATCH'):
        verify(candidate, recovery_bundle=bundle)
    candidate['arguments']['recovery_bundle'] = bundle
    authorize(candidate, lambda value: value.update(recovery=asdict(checkpoint)))
    qualified = verify(candidate)
    assert qualified.current.stores == stores
    assert qualified.current.snapshot.counts['invites'] == state.snapshot.counts['invites'] + 1
    plan = parse((candidate['current']['roots']['coordinator'] / 'plan.json').read_bytes())
    with pytest.raises(ImportRejected, match='ONLINE_CAPSULE_DATABASE_MISMATCH'):
        bind_current(qualified.current, plan, candidate['arguments']['publications']['NL'])


def test_native_post_renewal_certificate_and_consumed_proof_survive_source_removal(tmp_path):
    root = tmp_path / 'source'
    root.mkdir(mode=0o700)
    fixture, fleet = native_fixture(root)
    for slot, node in fleet.nodes.items():
        node.barrier = NativeServiceBarrier(node, slot, fleet.clock)
    assert fleet.controller.run(OPERATION, scheduled=True, approved_leaf_crl_schedule=True)['result'] == 'COMMITTED'
    fixture.service.manifest = parse(fleet.nodes['RU'].read('issuer.json')[0])
    restricted_admin.grant(fixture.service.access, fixture.child.reference, fleet.family, NOW + 3600)
    proof = issue_proof(fixture.service, fixture.child)
    fixture.service.fetch(proof)
    with pytest.raises(restricted.Rejected):
        fixture.service.fetch(proof)
    refresh_fixture(fixture)
    artifacts, _ = artifacts_for_maintenance(fixture)
    key = secrets.token_bytes(32)
    bundle, checkpoint = seal(fixture.stores, fixture.external, artifacts, CHECKPOINT, fixture.bootstrap,
                              fixture.service.anchor, key, now=NOW)
    current = dict(recovered=preflight_receivers(bundle, key, checkpoint, fixture.service.anchor, now=NOW),
        roots=dict(coordinator=fleet.controller.root, RU=fleet.nodes['RU'].state,
                   NL1=fleet.nodes['NL'].state, NL2=fleet.nodes['NL2'].state), key=key, anchor=fixture.service.anchor,
        publications={slot: fleet.nodes['RU'].directory_destination(slot).read_bytes() for slot in ('NL', 'NL2')},
        authorities={'NL': fleet.nodes['RU'].read('issuer.json')[0],
                     'NL2': fleet.nodes['RU'].read('issuer-NL2.json')[0]})
    plan = parse((fleet.controller.root / 'plan.json').read_bytes())
    candidate = candidate_for(current)
    shutil.rmtree(root)
    qualified = verify(candidate)
    assert qualified.current.stores == fixture.stores
    assert qualified.current.artifacts == artifacts
    with pytest.raises(ImportRejected, match='ONLINE_CAPSULE_DATABASE_MISMATCH'):
        bind_current(qualified.current, plan, current['publications']['NL'])
    with closing(sqlite3.connect(':memory:')) as database:
        database.deserialize(qualified.current.stores['registry'])
        assert database.execute('SELECT used FROM challenges WHERE nonce=?',
                                (digest(proof['challenge'].encode()),)).fetchone() == (1,)
    restored = tmp_path / 'isolated' / 'registry.sqlite'
    write(restored, qualified.current.stores['registry'])
    issuer = qualified.current.artifacts['issuer_material']
    service = restricted.RestrictedReadiness(Access(restored, clock=lambda: NOW), manifest=parse(issuer['delegation']),
        anchor=current['anchor'], signing_key=Ed25519PrivateKey.from_private_bytes(issuer['runtime-key']),
        seed_source=lambda: issuer['directory'], crl_source=lambda: issuer['crl'])
    with pytest.raises(restricted.Rejected):
        service.fetch(proof)
    assert service.fetch(issue_proof(service, fixture.child))['device'] == fixture.child.reference


@pytest.mark.parametrize('floor', [True, 0, -1, 2**63 - 1])
def test_independently_retained_crl_floor_cannot_be_lowered(candidate, floor):
    with pytest.raises(ImportRejected, match='FORWARD_CRL_ROLLBACK'):
        verify(candidate, minimum_crl=floor)


@pytest.mark.parametrize('node', sorted(forward.NODES))
def test_current_node_must_be_settled_even_with_fresh_authorization(candidate, node):
    rewrite(candidate['current'], node, 'completed.json',
            lambda value: value[OPERATION].update(result='UNKNOWN'))
    recapture_history(candidate)
    with pytest.raises(ImportRejected, match='FORWARD_UNSETTLED_NODE'):
        verify(candidate)


def test_signed_bundle_does_not_skip_bounded_maintenance_authentication(candidate):
    state = candidate['current']['recovered']
    artifacts = deepcopy(state.artifacts)
    name = next(name for name in artifacts['maintenance_state'] if name != 'capture.json')
    node = parse(artifacts['maintenance_state'][name])
    node['renewal'] = dict(format='unknown-renewal/v99')
    artifacts['maintenance_state'][name] = encoded(node)
    bundle, checkpoint = seal(state.stores, state.references, artifacts, CHECKPOINT, state.bootstrap,
        candidate['arguments']['anchor'], candidate['arguments']['recovery_key'], now=NOW)
    candidate['arguments']['recovery_bundle'] = bundle
    authorize(candidate, lambda value: value.update(recovery=asdict(checkpoint)))
    with pytest.raises(ImportRejected, match='MAINTENANCE_RENEWAL_UNSUPPORTED'):
        verify(candidate)


@pytest.mark.parametrize('field', sorted(forward.FIELDS))
def test_any_unsigned_request_change_is_refused(candidate, field):
    document = parse(candidate['request'])
    del document[field]
    candidate['request'] = encoded(document)
    with pytest.raises(ImportRejected):
        verify(candidate)


@pytest.mark.parametrize('change', [dict(version=True), dict(purpose=custody.PURPOSE),
    dict(action='RESUME_HOST'), dict(action='CAPTURE_PRODUCTION'), dict(action='IMPORT_DATABASE'),
    dict(action='APPROVE_OLD_OPERATION'), dict(sequence=True), dict(sequence=0),
    dict(checkpoint_id='f' * 32), dict(captured_at=True), dict(expires_at=NOW),
    dict(expires_at=NOW + forward.MAX_LIFETIME + 1), dict(extra='permit'),
    dict(issuer_public_sha256='bad'), dict(sources={}), dict(publications={})])
def test_even_a_valid_signature_cannot_expand_scope_or_fix_malformed_claims(candidate, change):
    authorize(candidate, lambda value: value.update(change))
    with pytest.raises(ImportRejected):
        verify(candidate)


@pytest.mark.parametrize('kind', ['wrong-key', 'unsigned', 'wrong-domain', 'mutated-signature', 'wrong-pin'])
def test_independent_authority_and_pin_are_required(candidate, kind):
    if kind == 'wrong-key':
        candidate['trusted_key'] = Ed25519PrivateKey.generate().public_key().public_bytes_raw()
    elif kind == 'unsigned':
        candidate['signature'] = b''
    elif kind == 'wrong-domain':
        candidate['signature'] = candidate['signer'].sign(candidate['request'])
    elif kind == 'mutated-signature':
        candidate['signature'] = bytes([candidate['signature'][0] ^ 1]) + candidate['signature'][1:]
    else:
        candidate['expected_request_sha256'] = '0' * 64
    with pytest.raises(ImportRejected, match='FORWARD_(SIGNATURE|REQUEST_PIN)'):
        verify(candidate)


@pytest.mark.parametrize('arguments', [dict(minimum_sequence=2), dict(minimum_sequence=3),
    dict(minimum_sequence=True), dict(minimum_sequence=-1), dict(now=NOW - 1),
    dict(now=NOW + 300), dict(now=NOW + 301), dict(now=True)])
def test_freshness_and_external_replay_floor(candidate, arguments):
    with pytest.raises(ImportRejected, match='FORWARD_(STALE_SEQUENCE|EXPIRED_OR_FUTURE)'):
        verify(candidate, **arguments)


@pytest.mark.parametrize('node', sorted(forward.NODES))
@pytest.mark.parametrize('field', ['runtime_sha256', 'configuration_sha256'])
def test_each_actual_source_identity_must_match(candidate, node, field):
    sources = deepcopy(candidate['arguments']['sources'])
    sources[node][field] = '0' * 64
    with pytest.raises(ImportRejected, match='FORWARD_SOURCE_MISMATCH'):
        verify(candidate, sources=sources)


@pytest.mark.parametrize('field', ['recovery_bundle', 'history_bundle', 'recovery_key', 'history_key', 'anchor'])
def test_opaque_inputs_and_keys_cannot_be_substituted(candidate, field):
    raw = candidate['arguments'][field]
    with pytest.raises(ImportRejected):
        verify(candidate, **{field: bytes([raw[0] ^ 1]) + raw[1:]})


@pytest.mark.parametrize('node', ['NL', 'NL2'])
def test_every_publication_is_exactly_bound(candidate, node):
    publications = dict(candidate['arguments']['publications'])
    publications[node] += b' '
    with pytest.raises(ImportRejected, match='FORWARD_PUBLICATION_MISMATCH'):
        verify(candidate, publications=publications)


@pytest.mark.parametrize('node', ['NL', 'NL2'])
def test_delegation_bytes_are_bound_to_the_fresh_authorization(candidate, node):
    authorities = dict(candidate['arguments']['authorities'])
    authorities[node] += b' '
    with pytest.raises(ImportRejected, match='FORWARD_GATEWAY_MISMATCH'):
        verify(candidate, authorities=authorities)


@pytest.mark.parametrize('kind', ['expired', 'other-node', 'wrong-family'])
def test_fresh_authorization_does_not_legitimize_bad_secondary_publication(candidate, kind):
    publications = dict(candidate['arguments']['publications'])
    value = parse(publications['NL2'])
    if kind == 'expired':
        value.update(issued_at=restricted.iso(NOW - 1), expires_at=restricted.iso(NOW))
    elif kind == 'other-node':
        value['seeds'][0]['gateway'] = candidate['arguments']['gateway_ids']['NL']
    else:
        value['family'] = 'f' * 32
    publications['NL2'] = encoded(value)
    candidate['arguments']['publications'] = publications
    authorize(candidate, lambda document: document.update(publications=forward.publication_hashes(publications)))
    with pytest.raises(ImportRejected, match='FORWARD_PUBLICATION_INVALID'):
        verify(candidate)


@pytest.mark.parametrize('node', ['NL', 'NL2'])
def test_new_checkpoint_sequence_does_not_lower_known_gateway_authority_floor(candidate, node):
    floors = dict(candidate['arguments']['minimum_authority_sequences'])
    floors[node] += 1
    with pytest.raises(ImportRejected, match='FORWARD_AUTHORITY_ROLLBACK'):
        verify(candidate, minimum_authority_sequences=floors)


def test_gateway_assignment_is_bound_not_inferred_from_secondary_content(candidate):
    identities = dict(candidate['arguments']['gateway_ids'], NL2='f' * 32)
    with pytest.raises(ImportRejected, match='FORWARD_GATEWAY_MISMATCH'):
        verify(candidate, gateway_ids=identities)


def test_material_readback_does_not_alias_callers_mapping(candidate):
    qualified = verify(candidate)
    candidate['arguments']['publications']['NL2'] = b'changed'
    candidate['arguments']['authorities']['NL2'] = b'changed'
    assert qualified.publications['NL2'] != b'changed'
    assert qualified.authorities['NL2'] != b'changed'


def test_input_maps_cannot_change_between_hash_and_semantic_checks(candidate, monkeypatch):
    original = forward.preflight_maintenance
    approved_publication = candidate['arguments']['publications']['NL2']
    approved_authority = candidate['arguments']['authorities']['NL2']
    def preflight(*args, **kwargs):
        publication = parse(approved_publication)
        publication['seeds'][0]['join_url'] = 'https://telemost.yandex.ru/j/changed-after-pin'
        candidate['arguments']['publications']['NL2'] = encoded(publication)
        candidate['arguments']['authorities']['NL2'] += b' '
        return original(*args, **kwargs)
    monkeypatch.setattr(forward, 'preflight_maintenance', preflight)
    qualified = verify(candidate)
    assert qualified.publications['NL2'] == approved_publication
    assert qualified.authorities['NL2'] == approved_authority


def test_signed_different_issuer_is_not_a_key_rotation_permit(candidate):
    authorize(candidate, lambda value: value.update(issuer_public_sha256='0' * 64))
    with pytest.raises(ImportRejected, match='FORWARD_ISSUER_MISMATCH'):
        verify(candidate)


@pytest.mark.parametrize('slot', ['coordinator', 'RU', 'NL1', 'NL2'])
def test_pending_current_owner_is_preserved_but_refuses_qualification(candidate, slot):
    write(candidate['current']['roots'][slot] / 'owner.json', b'{"state":"UNKNOWN"}')
    recapture_history(candidate)
    with pytest.raises(ImportRejected, match='FORWARD_PENDING'):
        verify(candidate)


@pytest.mark.parametrize('state', ['COMMIT_DECIDED', 'UNKNOWN', 'ROLLED_BACK'])
def test_unsettled_coordinator_is_not_historical_approval(candidate, state):
    rewrite(candidate['current'], 'coordinator', 'transaction.json', lambda value: value.update(state=state))
    recapture_history(candidate)
    with pytest.raises(ImportRejected, match='FORWARD_UNSETTLED_COORDINATOR'):
        verify(candidate)


def test_old_unknown_history_remains_opaque_not_replayed(candidate):
    root = candidate['current']['roots']['NL2']
    rewrite(candidate['current'], 'NL2', 'completed.json',
        lambda value: value.update(unknown_old_operation=dict(result='UNKNOWN')))
    write(root / 'archive/unknown_old_operation/pending.json', b'{"state":"PENDING","private":"retained"}')
    recapture_history(candidate)
    qualified = verify(candidate)
    assert qualified.history.trees['NL2']['entries']['archive/unknown_old_operation/pending.json']['body'] == (
        b'{"state":"PENDING","private":"retained"}')
    assert qualified.summary()['history'] == 'OPAQUE_NOT_EXECUTABLE'


def test_noncanonical_duplicate_and_oversized_requests_fail_closed(candidate):
    request = candidate['request']
    for raw in (b' ' + request, b'{"version":1,' + request[1:], b' ' * (forward.MAX_REQUEST + 1)):
        candidate['request'] = raw
        candidate['expected_request_sha256'] = digest(raw)
        candidate['signature'] = candidate['signer'].sign(forward.DOMAIN + raw)
        with pytest.raises(ImportRejected):
            verify(candidate)
