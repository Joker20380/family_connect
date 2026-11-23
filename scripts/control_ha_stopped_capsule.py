"""Import settled stopped-renewal evidence, never resume a host or authorize an outage."""
from dataclasses import replace

from scripts.control_ha_import import ImportRejected, digest, encoded, require
from scripts.control_ha_maintenance_v1 import (ADAPTER as BOUNDED_ADAPTER, PARTS as BOUNDED_PARTS,
    STOPPED_RENEWAL_FORMAT, MaintenanceRecoveryInputs, inspect_maintenance)
from scripts.control_ha_online_capsule import MAPPING, PARTS as ONLINE_PARTS, bind_current, binding_for
from scripts.control_ha_receiver_v1 import preflight_receivers
from scripts.control_ha_recovery_bundle import parse
from scripts.control_ha_renewal_v1 import PARTS as RENEWAL_PARTS
from scripts.control_ha_stopped_v1 import inspect_stopped

ADAPTER = 'family-connect/stopped-renewal-capsule/v1/not-for-activation'
PARTS = ONLINE_PARTS | {'publication.json'}


class StoppedRecoveryInputs(MaintenanceRecoveryInputs):
    def summary(self):
        value = super().summary()
        value.update(result='ISOLATED_STOPPED_CAPSULE_PREFLIGHT_PASS', stopped_adapter=ADAPTER,
                     maintenance_scope='ONE_COMPLETED_STOPPED_OFFLINE_OR_EMERGENCY_RENEWAL',
                     approval_replay='NOT_AUTHORIZED', history='UNSUPPORTED_REFUSED', full_dr='NOT_QUALIFIED')
        return value


def binding(stores, issuer, checkpoint, renewal, publication):
    return dict(binding_for(stores, issuer, checkpoint, renewal), format=STOPPED_RENEWAL_FORMAT,
                publication_sha256=digest(publication))


def declaration(value):
    return dict(format=STOPPED_RENEWAL_FORMAT, evidence_sha256=digest(encoded(value)))


def assemble_stopped(bounded, renewal, publication, stores, issuer, checkpoint):
    require(set(bounded) == BOUNDED_PARTS, 'STOPPED_BOUNDED_PARTS')
    manifest = binding(stores, issuer, checkpoint, renewal, publication)
    result = dict(bounded)
    for name in BOUNDED_PARTS - {'capture.json'}:
        document = parse(result[name])
        require(document['renewal'] == dict(format='none-declared/v1', coordinator=[], node=[]),
                'STOPPED_EXISTING_RENEWAL')
        document['renewal'] = declaration(manifest)
        result[name] = encoded(document)
    result.update({MAPPING[name]: raw for name, raw in renewal.items()})
    result.update({'binding.json': encoded(manifest), 'publication.json': publication})
    return result


def inspect_stopped_inputs(recovered, checkpoint, anchor, *, now):
    try:
        parts, issuer = recovered.artifacts['maintenance_state'], recovered.artifacts['issuer_material']
        require(set(parts) == PARTS, 'STOPPED_CAPSULE_PARTS')
        renewal = {name: parts[MAPPING[name]] for name in RENEWAL_PARTS}
        expected = binding(recovered.stores, issuer, checkpoint, renewal, parts['publication.json'])
        require(parts['binding.json'] == encoded(expected), 'STOPPED_CAPSULE_BINDING')
        plan, directories, mode = inspect_stopped(renewal, parts['publication.json'], anchor, now)
        require(parse(renewal['capture.json'])['captured_at'] == parse(parts['capture.json'])['captured_at'],
                'STOPPED_CAPTURE_TIME')
        bounded = inspect_maintenance({name: parts[name] for name in BOUNDED_PARTS}, issuer, now=now,
                                       renewal=declaration(expected))
        require(bounded['settled'], 'MAINTENANCE_UNSETTLED_REQUIRES_RECONCILIATION')
        bind_current(recovered, plan, directories['NL'])
        return dict(result='BOUND_COMPLETED_STOPPED_RENEWAL', mode=mode, nodes=3, database_tables=5,
                    activation='FORBIDDEN', host_resume='NOT_AUTHORIZED', approval_replay='NOT_AUTHORIZED')
    except ImportRejected:
        raise
    except (ValueError, KeyError, TypeError, AttributeError, OverflowError, RecursionError):
        raise ImportRejected('STOPPED_CAPSULE_INVALID') from None


def preflight_stopped(bundle, key, expected, anchor, *, now):
    recovered = preflight_receivers(bundle, key, expected, anchor, now=now)
    inspect_stopped_inputs(recovered, expected.checkpoint, anchor, now=now)
    snapshot = replace(recovered.snapshot, external_digests=recovered.snapshot.external_digests +
                       (('maintenance-adapter', digest(BOUNDED_ADAPTER.encode())),
                        ('stopped-maintenance-adapter', digest(ADAPTER.encode())),))
    return StoppedRecoveryInputs(snapshot, recovered.stores, recovered.references, recovered.artifacts, recovered.bootstrap)
