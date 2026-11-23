"""Bind one completed online renewal to canonical recovery inputs; never activate hosts."""
import base64
from dataclasses import replace

from cryptography import x509

from scripts.control_ha_external_v1 import records
from scripts.control_ha_import import ImportRejected, digest, encoded, require
from scripts.control_ha_maintenance_v1 import (ADAPTER as BOUNDED_ADAPTER, ONLINE_RENEWAL_FORMAT,
                                              ONLINE_HISTORY_FORMAT,
                                              MaintenanceRecoveryInputs, PARTS as BOUNDED_PARTS, inspect_maintenance)
from scripts.control_ha_receiver_v1 import preflight_receivers
from scripts.control_ha_recovery_bundle import parse
from scripts.control_ha_renewal_v1 import PARTS as RENEWAL_PARTS, decode_document, evidence_digest, inspect_renewal

ADAPTER = 'family-connect/online-renewal-capsule/v1/not-for-activation'
FORMAT = ONLINE_RENEWAL_FORMAT
HISTORY_ADAPTER = 'family-connect/online-renewal-capsule/v2/retained-history/not-for-activation'
MAPPING = {name: 'renewal-' + name.lower() for name in RENEWAL_PARTS}
PARTS = BOUNDED_PARTS | frozenset(MAPPING.values()) | {'binding.json'}
DATABASE_TABLES = ('devices', 'invites', 'restricted_grants', 'restricted_certificates', 'restricted_crl_sequence')


class OnlineRecoveryInputs(MaintenanceRecoveryInputs):
    def summary(self):
        value = super().summary()
        value.update(result='ISOLATED_ONLINE_CAPSULE_PREFLIGHT_PASS', online_adapter=ADAPTER,
                     maintenance_scope='ONE_BOUNDED_JOURNAL_PER_NODE_AND_ONE_COMPLETED_ONLINE_RENEWAL',
                     canonical_renewal_binding='EXACT', history='UNSUPPORTED_REFUSED', full_dr='NOT_QUALIFIED')
        return value


class HistoryRecoveryInputs(OnlineRecoveryInputs):
    def summary(self):
        value = super().summary()
        value.update(online_adapter=HISTORY_ADAPTER, history='RETAINED_COMPLETED_ONLINE_CHAIN',
                     maintenance_scope='BOUNDED_JOURNALS_AND_TWO_TO_EIGHT_COMPLETED_ONLINE_OPERATIONS')
        return value


def renewal_declaration(checksum, *, history=False):
    return dict(format=ONLINE_HISTORY_FORMAT if history else FORMAT, evidence_sha256=checksum)


def binding_for(stores, issuer, checkpoint, renewal, *, history=False):
    return dict(schema=1, format=ONLINE_HISTORY_FORMAT if history else FORMAT, checkpoint=checkpoint,
                stores={name: digest(raw) for name, raw in stores.items()},
                issuer={name: digest(raw) for name, raw in issuer.items()}, renewal_sha256=evidence_digest(renewal))


def assemble(bounded, renewal, stores, issuer, checkpoint, *, history=False):
    require(set(bounded) == BOUNDED_PARTS, 'ONLINE_CAPSULE_BOUNDED_COVERAGE')
    binding = binding_for(stores, issuer, checkpoint, renewal, history=history)
    result = dict(bounded)
    for name in sorted(BOUNDED_PARTS - {'capture.json'}):
        document = parse(bounded[name])
        require(document['renewal'] == dict(format='none-declared/v1', coordinator=[], node=[]),
                'ONLINE_CAPSULE_EXISTING_RENEWAL')
        document['renewal'] = renewal_declaration(binding['renewal_sha256'], history=history)
        result[name] = encoded(document)
    result.update({MAPPING[name]: raw for name, raw in renewal.items()})
    result['binding.json'] = encoded(binding)
    return result


def inspect_online_inputs(recovered, checkpoint, anchor, *, now, history=False):
    try:
        parts, issuer = recovered.artifacts['maintenance_state'], recovered.artifacts['issuer_material']
        require(set(parts) == PARTS, 'ONLINE_CAPSULE_PARTS')
        renewal = {name: parts[MAPPING[name]] for name in RENEWAL_PARTS}
        binding = parse(parts['binding.json'])
        require(encoded(binding) == encoded(binding_for(recovered.stores, issuer, checkpoint, renewal, history=history)),
                'ONLINE_CAPSULE_BINDING')
        if history:
            from scripts.control_ha_renewal_history import inspect_history
            evidence, renewal, operations = inspect_history(renewal, binding['renewal_sha256'], anchor, now)
        else:
            evidence = inspect_renewal(renewal, binding['renewal_sha256'], anchor, now)
            operations = 1
        require(evidence.state == 'COMMITTED', 'ONLINE_CAPSULE_UNSETTLED_REQUIRES_RECONCILIATION')
        require(parse(renewal['capture.json'])['captured_at'] == parse(parts['capture.json'])['captured_at'],
                'ONLINE_CAPSULE_CAPTURE_TIME')
        bounded = inspect_maintenance({name: parts[name] for name in BOUNDED_PARTS}, issuer, now=now,
                                       renewal=renewal_declaration(binding['renewal_sha256'], history=history))
        require(bounded['settled'], 'MAINTENANCE_UNSETTLED_REQUIRES_RECONCILIATION')
        _, coordinator = decode_document(renewal['coordinator.json'], 'coordinator', evidence.operation)
        plan = parse(coordinator['plan.json'])
        record = parse(coordinator['transaction.json'])
        bind_current(recovered, plan, base64.b64decode(record['published']['NL']['directory']['payload'], validate=True))
        return dict(result='BOUND_COMPLETED_RENEWAL', renewal_sha256=binding['renewal_sha256'],
                    database_tables=len(DATABASE_TABLES), operations=operations,
                    activation='FORBIDDEN', host_resume='NOT_AUTHORIZED')
    except ImportRejected:
        raise
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError, RecursionError):
        raise ImportRejected('ONLINE_CAPSULE_INVALID') from None


def bind_current(recovered, plan, directory):
    issuer = recovered.artifacts['issuer_material']
    require(parse(issuer['delegation']) == plan['candidate']['authority'] and
            issuer['crl'] == plan['candidate']['crl'].encode() and issuer['directory'] == directory,
            'ONLINE_CAPSULE_ISSUER_MISMATCH')
    number = x509.load_pem_x509_crl(issuer['crl']).extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
    before = plan['grant_plan']['before']
    require(set(before) == set(DATABASE_TABLES), 'ONLINE_CAPSULE_DATABASE_SCOPE')
    target = dict(before, restricted_grants=plan['grant_plan']['after_grants'],
                  restricted_crl_sequence=[dict(singleton=1, sequence=number)])
    current = records(recovered.snapshot)
    require(all(encoded(sorted(current[table], key=encoded)) == encoded(sorted(target[table], key=encoded))
                for table in DATABASE_TABLES), 'ONLINE_CAPSULE_DATABASE_MISMATCH')


def preflight_online(bundle, key, expected, anchor, *, now, history=False):
    recovered = preflight_receivers(bundle, key, expected, anchor, now=now)
    inspect_online_inputs(recovered, expected.checkpoint, anchor, now=now, history=history)
    snapshot = replace(recovered.snapshot, external_digests=recovered.snapshot.external_digests +
                       (('maintenance-adapter', digest(BOUNDED_ADAPTER.encode())),
                        ('online-maintenance-adapter', digest((HISTORY_ADAPTER if history else ADAPTER).encode())),))
    result_type = HistoryRecoveryInputs if history else OnlineRecoveryInputs
    return result_type(snapshot, recovered.stores, recovered.references, recovered.artifacts, recovered.bootstrap)
