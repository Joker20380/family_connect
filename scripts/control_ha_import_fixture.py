"""Generated storage-shape fixture, not accepted credentials or deployable policy."""
import json
import sqlite3

from control.friends.access import Access
from control.friends import paid_beta, support_ids
from device_identity.device import DeviceIdentity
from scripts.control_ha_import import TABLES, STORES, VERSION, PURPOSE, SOURCE_MARKER, source_ddl, digest, reference_sets
from scripts.paid_postgres_rehearsal import apply
from scripts.referral_postgres_rehearsal import NOW, proof

CHECKPOINT = '1' * 32


def bundle(root):
    access = Access(root / 'source.sqlite', clock=lambda: NOW)
    access.initialize()
    identity = DeviceIdentity.generate()
    access.complete(proof(access, identity, 'activate', access.invite()), 'activate')
    support_ids.request(access, dict(proof=proof(access, identity, 'support'), platform='android',
                                    app_version='0.1.18-beta126', version_code=126))
    pending = proof(access, identity, 'status')
    access.invite()
    with access.enrollment() as enrollment:
        paid_beta.migrate(enrollment.database)
        support = enrollment.registered(identity.reference)
        apply(enrollment.paid(), support)
        populated = {table.name: [dict(row) for row in enrollment.database.execute('SELECT * FROM ' + table.name)]
                     for table in TABLES[:7]}
    device = identity.reference
    hashes = {name: digest(('synthetic-' + name).encode()) for name in ('catalog', 'policy', 'payload', 'request')}
    grant = dict(device=device, family='f' * 32, revision=2, expires=NOW + 1000, revoked=0)
    notice = dict(id='a' * 32, revision=1, updated=NOW, title='Synthetic', body='Not a live notice')
    revised = notice | dict(revision=2, updated=NOW + 1, title='Synthetic edit')
    extra = {
        'field_support_audit': dict(id=41, timestamp=NOW, support_id=support, previous_state=0, new_state=1, outcome='synthetic'),
        'referral_links': dict(token='2' * 64, sponsor=device),
        'referral_claims': dict(request='3' * 32, sponsor=device, invite=populated['invites'][-1]['hash'], created=NOW),
        'restricted_grants': grant,
        'restricted_challenges': dict(nonce='4' * 32, revision=2, family=grant['family'], expires=NOW + 100),
        'restricted_certificates': dict(device=device, revision=2, serial='12345', expires=NOW + 1000,
                                        certificate='SYNTHETIC_STORAGE_SENTINEL_NOT_A_CERTIFICATE'),
        'restricted_readiness_results': dict(correlation='5' * 32, nonce='4' * 32, device=device, challenge_at=NOW,
            fetch_id=None, fetch_at=None, revision=None, minimum_crl=None, expires=None, ack=None, ack_at=None,
            gateway_binding='synthetic-binding'),
        'chat_bindings': dict(device=device, public='6' * 128, support_sender='7' * 128),
        'chat_challenges': dict(nonce='8' * 32, device=device, public='6' * 128, expires=NOW + 100, used=1),
        'chat_sequence': dict(id=1, value=17),
        'chat_service_senders': dict(public='7' * 128, enabled=0),
        'gateway_routing_state': dict(singleton=1, policy_sha256=hashes['policy'], generation=3),
        'gateway_assignments': dict(device=device, catalog_sha256=hashes['catalog'], node='nl-synthetic', sequence=4),
        'gateway_assignment_events': dict(operation_id='assign-1', request_sha256=hashes['request'], device=device,
                                          previous_sha256=hashes['catalog'], catalog_sha256=hashes['catalog']),
        'gateway_selection_events': dict(operation_id='select-1', request_sha256=hashes['request'],
                                         catalog_sha256=hashes['catalog'], policy_sha256=hashes['policy'], sequence=8),
        'restricted_crl_sequence': dict(singleton=1, sequence=7),
        'restricted_crl_publications': dict(operation_id='crl-1', request_sha256=hashes['request'], sequence=7,
            payload='SYNTHETIC_STORAGE_SENTINEL_NOT_A_CRL', payload_sha256=hashes['payload'],
            issued_at=NOW, expires_at=NOW + 1000, local_receipt=1),
        'device_metadata': dict(device=device, epoch=3, sequence=5, digest=hashes['payload'], enabled=0, received=NOW, payload='{}'),
        'snapshots': dict(device=device, support=support, received=NOW, report='{"synthetic":true}'),
        'admins': dict(name='Synthetic operator', digest='9' * 64, active=0),
        'device_admins': dict(device=device, name='Synthetic device', active=0),
        'events': dict(id=notice['id'], value=json.dumps(notice), position=3),
        'revisions': dict(id=notice['id'], value=json.dumps(revised)),
        'edit_operations': dict(id='edit-1', request='{}', result='{}', device=device,
                                before_value=json.dumps(notice), after_value=json.dumps(revised)),
    }
    populated.update({name: [row] for name, row in extra.items()})
    populated['events'].append(dict(id='b' * 32, value=json.dumps(notice | dict(id='b' * 32)), position=9))
    stores = {}
    for store in sorted(STORES):
        database = sqlite3.connect(':memory:')
        try:
            database.execute(SOURCE_MARKER)
            database.execute('INSERT INTO ha_import_source VALUES (?,?,?,?)', (VERSION, PURPOSE, store, CHECKPOINT))
            for table in TABLES:
                if table.store != store:
                    continue
                database.execute(source_ddl(table))
                columns = ['rowid' if table.name == 'events' and name == 'position' else name for name in table.columns]
                for row in populated[table.name]:
                    database.execute('INSERT INTO ' + table.name + '(' + ','.join(columns) + ') VALUES (' +
                                     ','.join(['?'] * len(columns)) + ')', tuple(row[name] for name in table.columns))
            database.commit()
            stores[store] = database.serialize()
        finally:
            database.close()
    rows = {table.name: tuple(tuple(row[column] for column in table.columns) for row in populated[table.name]) for table in TABLES}
    references = reference_sets(rows, CHECKPOINT)
    external = {role: json.dumps(dict(schema=VERSION, purpose=PURPOSE, role=role, checkpoint=CHECKPOINT,
                                     references=sorted(values))).encode() for role, values in references.items()}
    expected = {role: digest(raw) for role, raw in external.items()}
    return stores, external, expected, identity, pending
