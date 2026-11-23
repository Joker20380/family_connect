"""Joint application-produced SQLite fixture; temporary keys, never live inputs."""
from contextlib import closing
from copy import copy
from dataclasses import dataclass, field
import hashlib
import json
import secrets
import sqlite3

import RNS
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from control.friends import chat_service, diagnostics, gateway_routing, gateway_selection
from control.friends import notices, readiness_receipts, restricted, restricted_admin, support, support_ids
from control.friends import technical_metadata as metadata, transport_policy
from control.friends.access import Access
from control.friends.chat import ChatAccess
from control.friends.referrals import Referrals
from device_identity.device import DeviceIdentity
from provisioning.friends_catalog import GATEWAY_CHOICES
from scripts.chat_postgres_rehearsal import activate, request as chat_request, service_proof
from scripts.control_ha_import import TABLES, STORES, VERSION, PURPOSE, reference_sets, digest
from scripts.control_ha_import_fixture import CHECKPOINT
from scripts.control_ha_rehearsal import private_file, require
from scripts.diagnostics_postgres_rehearsal import report as diagnostic_report, request_value as diagnostic_request
from scripts.gateway_routing_postgres_rehearsal import scenario
from scripts.metadata_postgres_rehearsal import report as metadata_report, request_value as metadata_request
from scripts.notices_postgres_rehearsal import notice, edit, request_value as notice_request
from scripts.paid_postgres_rehearsal import apply
from scripts.referral_postgres_rehearsal import NOW, proof, refused
from scripts.restricted_postgres_rehearsal import synthetic_service, issue_proof, receipt, ack_proof
from scripts.service_notices import Notices


def image(path):
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as source:
        with closing(sqlite3.connect(':memory:')) as target:
            source.backup(target)
            target.execute('PRAGMA journal_mode=MEMORY')
            return target.serialize()


def schema(raw):
    with closing(sqlite3.connect(':memory:')) as database:
        database.deserialize(raw)
        return [list(row) for row in database.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY name')]


@dataclass(repr=False)
class JointFixture:
    access: object
    service: object
    device: object
    child: object
    referral_secret: bytes = field(repr=False)
    token: str = field(repr=False)
    pending: dict = field(repr=False)
    consumed: dict = field(repr=False)
    paths: dict = field(repr=False)
    stores: dict = field(repr=False)
    external: dict = field(repr=False)
    expected: dict = field(repr=False)
    feeds: list = field(repr=False)
    bootstrap: bytes = field(repr=False)


def joint_fixture(root, *, authority=None):
    paths = {name: root / (name + '.sqlite') for name in STORES}
    if authority is None:
        access = Access(paths['registry'], clock=lambda: NOW)
        access.initialize()
        restricted.migrate(access)
        service, device = synthetic_service(access)
    else:
        service, device = authority
        access = service.access
        paths['registry'] = access.path
    alias = support_ids.request(access, dict(proof=proof(access, device, 'support'), platform='android',
        app_version='0.1.18-beta126', version_code=126))['device_support_id']
    with access.enrollment() as enrollment:
        apply(enrollment.paid(), alias, paid_until=NOW + 600)
        audit = enrollment.restricted_admin().begin_audit(NOW, alias, 0, 1)
        enrollment.restricted_admin().finish_audit(audit, 'APPLIED')
    secret = secrets.token_bytes(32)
    referrals = Referrals(access, secret)
    referrals.initialize()
    token = referrals.issue(proof(access, device, 'refer'))['url'].split('#')[1]
    invitation = referrals.claim(token, '1' * 32)['invitation']
    child = DeviceIdentity.generate()
    access.complete(proof(access, child, 'activate', invitation), 'activate')
    referrals.claim(token, '2' * 32)
    consumed = dict(restricted=issue_proof(service, device, 'a' * 32))
    response = service.fetch(consumed['restricted'], request_id='b' * 32)
    ack = receipt(response)
    readiness_receipts.acknowledge(service, dict(proof=ack_proof(service, device, ack), receipt=ack))
    pending = dict(restricted=issue_proof(service, device, 'c' * 32))
    revoked = activate(access)
    restricted_admin.grant(access, revoked.reference, 'a' * 32, NOW + 3600)
    service.fetch(issue_proof(service, revoked))
    with access.enrollment() as enrollment:
        enrollment.restricted_admin().revoke_grant(revoked.reference)
    access.revoke_device(revoked.reference)
    crl_file = root / 'revocations.pem'
    restricted_admin.publish_crl(service, crl_file)
    service.crl_source = crl_file.read_bytes
    chat = ChatAccess(access)
    chat.initialize()
    official = service_proof(RNS.Identity())
    chat_service.register(access, **official)
    consumed['chat'] = chat_request(chat, device, RNS.Identity())
    bound = chat.register(**consumed['chat'])
    pending['chat'] = chat_request(chat, child, RNS.Identity())
    policy = root / 'support.json'
    private_file(policy, json.dumps(dict(schema=2, sender_public=official['public'], revision=1, enabled=True)).encode())
    support.enroll(access, policy, device.reference, bound['chat_public'], NOW + 120)
    routing = scenario(access, root, signer=Ed25519PrivateKey.generate())
    gateway_routing.install(access, routing.policy, routing.envelopes[0])
    gateway_selection.install(access, root, routing.request)
    gateway_routing.move(access, routing.policy, device=device.reference, expected=routing.hashes[0],
        destination=routing.hashes[1], operation_id='joint-routing-move')
    metadata.request(access, paths['metadata'], metadata_request(access, device, metadata_report()))
    metadata.request(access, paths['metadata'], metadata_request(access, device, metadata_report(sequence=2, operation='revoke')))
    metadata.request(access, paths['metadata'], metadata_request(access, child, metadata_report()))
    diagnostics.request(access, paths['diagnostics'], diagnostic_request(access, device, diagnostic_report()))
    publisher = Notices(paths['notices'])
    try:
        publisher.grant_device(access, device.reference, 'Synthetic operator')
        publisher.grant_digest('Synthetic token', hashlib.sha256(secrets.token_hex(32).encode()).hexdigest())
        publisher.revoke('Synthetic token')
        access.complete(proof(access, device, 'notices-publish'), 'notices-publish')
        value = notice()
        publisher.publish('', ident=value['id'], kind=value['kind'], title=value['title'], body=value['body'],
            platforms=value['platforms'], lifetime=86400, now=NOW, device=device.reference)
        access.complete(proof(access, device, 'notices-edit'), 'notices-edit')
        publisher.edit_device(device.reference, edit(), now=NOW)
        feeds = [publisher.feed(now=NOW, version=version) for version in (1, 2)]
    finally:
        publisher.db.close()
    pending['notice'] = notice_request(access, device, 'edit', notice=edit(sequence=2, revision=2))
    pending['status'] = proof(access, child, 'status')
    pending['invitation'] = invitation
    pending['routing'] = routing
    fixture = JointFixture(access, service, device, child, secret, token, pending, consumed, paths, {}, {}, {}, feeds, b'')
    refresh_fixture(fixture)
    return fixture


def refresh_fixture(fixture):
    stores = {name: image(path) for name, path in fixture.paths.items()}
    rows = {}
    for name, raw in stores.items():
        with closing(sqlite3.connect(':memory:')) as database:
            database.deserialize(raw)
            for table in TABLES:
                if table.store != name:
                    continue
                if table.name == 'restricted_crl_publications':
                    rows[table.name] = ()
                    continue
                columns = ['rowid' if table.name == 'events' and column == 'position' else column for column in table.columns]
                rows[table.name] = tuple(database.execute('SELECT ' + ','.join(columns) + ' FROM ' + table.name))
    refs = reference_sets(rows, CHECKPOINT)
    external = {role: json.dumps(dict(schema=VERSION, purpose=PURPOSE, role=role, checkpoint=CHECKPOINT,
        references=sorted(values))).encode() for role, values in refs.items()}
    fixture.stores, fixture.external = stores, external
    fixture.expected = {role: digest(raw) for role, raw in external.items()}
    fixture.bootstrap = json.dumps(dict(version=1, checkpoint=CHECKPOINT, manifest=fixture.service.manifest,
                                       crl=fixture.service.crl_source().decode())).encode()


def exercise_import(fixture, repository):
    recovered = Access(None, clock=lambda: NOW, enrollment_repository=repository)
    with fixture.access.read_enrollment() as previous, recovered.read_enrollment() as current:
        for node in transport_policy.NODES:
            require(transport_policy.read_snapshot(previous.paid(), node, NOW) ==
                    transport_policy.read_snapshot(current.paid(), node, NOW), 'PAID_PROJECTION_CHANGED')
        require(current.crl().sequence() == previous.crl().sequence(), 'CRL_FLOOR_CHANGED')
        require(not current.database.execute('SELECT * FROM restricted_crl_publications').fetchall(), 'FABRICATED_CRL_HISTORY')
    require(metadata.read_repository(recovered) == metadata.read_all(fixture.paths['metadata'], NOW), 'METADATA_CHANGED')
    with recovered.read_enrollment() as current:
        alias = current.registered(fixture.device.reference)
    require(support_ids.lookup(recovered, alias, []) == support_ids.lookup(fixture.access, alias, []), 'SUPPORT_CHANGED')
    routing = fixture.pending['routing']
    require(gateway_routing.configuration(recovered, routing.root, 'nl', fixture.device.reference) ==
            gateway_routing.configuration(fixture.access, routing.root, 'nl', fixture.device.reference), 'ROUTING_CHANGED')
    require(gateway_selection.configuration(recovered, routing.root, GATEWAY_CHOICES[0], fixture.device.reference) ==
            gateway_selection.configuration(fixture.access, routing.root, GATEWAY_CHOICES[0], fixture.device.reference), 'SELECTION_CHANGED')
    require(diagnostics.read_repository(recovered, alias) == diagnostics.read(fixture.paths['diagnostics'], alias, NOW), 'DIAGNOSTICS_CHANGED')
    require([notices.feed_repository(recovered, version) for version in (1, 2)] == fixture.feeds, 'NOTICE_FEEDS_CHANGED')
    require(Referrals(recovered, fixture.referral_secret).claim(fixture.token, '1' * 32)['invitation'] ==
            fixture.pending['invitation'], 'REFERRAL_REPLAY_CHANGED')
    recovered.complete(fixture.pending['status'], 'status')
    refused(lambda: recovered.complete(fixture.pending['status'], 'status'))
    chat = ChatAccess(recovered)
    refused(lambda: chat.register(**fixture.consumed['chat']))
    chat.register(**fixture.pending['chat'])
    imported_service = copy(fixture.service)
    imported_service.access = recovered
    require(readiness_receipts.readback(imported_service, 'a' * 32, fixture.device.reference) ==
            readiness_receipts.readback(fixture.service, 'a' * 32, fixture.device.reference), 'READINESS_CHANGED')
    refused(lambda: imported_service.fetch(fixture.consumed['restricted']))
    imported_service.fetch(fixture.pending['restricted'])
    with recovered.read_enrollment() as current:
        floor = current.crl().sequence()
    candidate = restricted_admin.prepare_crl(imported_service, 'joint-first-outbox', fixture.service.crl_source())
    require(candidate['sequence'] > floor and not candidate['local_receipt'], 'CRL_FLOOR_REGRESSED')
    notices.device_request_repository(recovered, 'edit', fixture.pending['notice'])
    refused(lambda: metadata.request_repository(recovered,
        metadata_request(recovered, fixture.device, metadata_report(sequence=3))))
    with recovered.enrollment() as current:
        require(apply(current.paid(), alias, paid_until=NOW + 600)['duplicate'], 'PAYMENT_REPLAYED')
        audit = current.restricted_admin().begin_audit(NOW, alias, 1, 1)
        require(audit == 2, 'AUDIT_SEQUENCE_REGRESSED')
        current.restricted_admin().finish_audit(audit, 'APPLIED')
    return dict(paid_nodes=3, proof_once=True, referral_replay=True, metadata_tombstone=True,
                diagnostics=True, notices=True, chat=True, readiness=True, crl_floor=True,
                routing=True, support=True, payment_replay=True, audit_next_id=audit)
