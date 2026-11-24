"""Authenticated retained-node/canonical parity and isolated revocation, never dispatch."""
from dataclasses import dataclass, field
import json
from pathlib import Path
import uuid

from control.friends import paid_beta, transport_policy as policy
from control.friends.access import Access
from scripts import control_ha_node_capture as capture
from scripts import control_ha_node_restore as recovery
from scripts import control_ha_node_qualify as native
from scripts.control_ha_external_v1 import records
from scripts.control_ha_import import digest, encoded, import_snapshot, ImportRejected
from scripts.control_ha_installed_composite import Prepared
from scripts.control_ha_rehearsal import private_file, require
from scripts.paid_postgres_rehearsal import PaidRehearsal, snapshot, require_current_restore

PROFILE = 'family-connect/retained-canonical-node-parity/v1/offline-only'


@dataclass(frozen=True, repr=False)
class Joint:
    canonical: Prepared = field(repr=False)
    points: tuple = field(repr=False)

    @property
    def fingerprint(self):
        return digest(encoded(dict(profile=PROFILE, canonical=self.canonical.snapshot.fingerprint,
            nodes={slot: json.loads(pin) for slot, files, manifest, pin in self.points})))


def prepare(canonical, inputs):
    require(type(canonical) is Prepared, 'CANONICAL_PREFLIGHT_REQUIRED')
    require(type(inputs) is dict and set(inputs) == set(capture.NODES), 'JOINT_NODE_COVERAGE')
    points = []
    for slot in sorted(capture.NODES):
        capsule, key, checkpoint = inputs[slot]
        files, manifest = recovery.unseal(capsule, key, checkpoint)
        require(manifest['slot'] == slot, 'JOINT_NODE_BINDING')
        recovery.validate(files, manifest)
        points.append((slot, tuple(sorted(files.items())), encoded(manifest), encoded(checkpoint)))
    return Joint(canonical, tuple(points))


def compare(database, joint):
    require(type(joint) is Joint, 'JOINT_PREFLIGHT_REQUIRED')
    database = paid_beta.transaction(database)
    identities = {row['device'] for row in records(joint.canonical.snapshot)['devices']}
    require({row['device'] for row in database.devices()} == identities, 'CANONICAL_DEVICE_COVERAGE')
    summaries = {}
    for slot, bodies, manifest_raw, pin in joint.points:
        files, manifest = dict(bodies), json.loads(manifest_raw)
        summary = recovery.validate(files, manifest)
        cached = recovery.document(files['state.json'])['records']
        require(set(cached) == identities, 'RECEIVER_DEVICE_COVERAGE')
        for identity, value in cached.items():
            observed = value['decision']['observed_at']
            envelope = policy.read_snapshot(database, manifest['node'], observed, device=identity)
            policy.validate(envelope, manifest['node'], observed)
            require(envelope['decisions'] == [value['decision']], 'CANONICAL_RECEIVER_DECISION_MISMATCH')
        summaries[slot] = dict(records=len(cached), peers=summary['peers'], sequence_floor=summary['sequence_floor'])
    return dict(result='RETAINED_CANONICAL_NODE_PARITY_PASS', fingerprint=joint.fingerprint, nodes=summaries,
        decisions=sum(item['records'] for item in summaries.values()),
        allocated_peers=sum(item['peers'] for item in summaries.values()),
        comparison_time='ORIGINAL_DECISION_TIME', activation=False, fleet_fence=False,
        independent_forward_trust=False, full_recovery=False)


def revocation_readback(repository, joint, identity, root, now):
    results = {}
    for slot, bodies, manifest_raw, pin in joint.points:
        files, manifest = dict(bodies), json.loads(manifest_raw)
        engine, point, summary = native.receiver(files, manifest, root / slot)
        point['wall'] = now
        with repository.transaction() as transaction:
            envelope = policy.read_snapshot(transaction.paid(), manifest['node'], now, device=identity)
        decision = envelope['decisions'][0]
        require(not decision['identity_allowed'] and not decision['allowed'], 'REVOCATION_MISSING')
        with engine.operation():
            state = engine.accept(envelope)
            require(not engine.allowed(state['records'][identity]), 'RECEIVER_REVOCATION_LOST')
            retained = engine.path.read_bytes()
            engine.accept(envelope)
            require(engine.path.read_bytes() == retained, 'DUPLICATE_REVOCATION_CHANGED')
        point['boot'] = str(uuid.uuid4())
        restarted = type(engine)(engine.gateway, clock=engine.clock, monotonic=engine.monotonic, run=engine.run)
        require(not restarted.allowed(restarted.load()['records'][identity]), 'RESTART_REVOCATION_LOST')
        previous = recovery.document(files['state.json'])['records'][identity]['decision']
        boundary = previous['grace_until'] if previous['state'] == 'grace' else previous['paid_until']
        deadline = min(now + policy.LEASE_SECONDS, boundary) if previous['cohort'] else now + policy.LEASE_SECONDS
        attack = dict(envelope, decisions=[dict(previous, observed_at=now, valid_until=deadline)])
        with restarted.operation():
            try:
                restarted.accept(attack)
            except ValueError as error:
                require(str(error) == 'TERMINAL_DECISION', 'UNEXPECTED_REPLAY_REFUSAL')
            else:
                raise ValueError('PRE_REVOCATION_REPLAY_ACCEPTED')
        require(engine.path.read_bytes() == retained, 'REJECTED_REPLAY_CHANGED_STATE')
        results[slot] = dict(revocation='DENIED', duplicate='UNCHANGED', restarted='DENIED',
                             refreshed_old_allow='REFUSED', native_commands_executed=0)
    return results


def qualify(joint, root):
    require(type(joint) is Joint, 'JOINT_PREFLIGHT_REQUIRED')
    root = Path(root)
    now = max(json.loads(point[2])['captured_at_ns'] // 10**9 for point in joint.points) + 1
    with PaidRehearsal(root) as lab:
        repository = lab.repository()
        require(import_snapshot(repository, joint.canonical.snapshot)['result'] == 'IMPORTED', 'IMPORT_REQUIRED')
        imported = snapshot(repository)
        with repository.transaction() as transaction:
            parity = compare(transaction.paid(), joint)
            candidates = policy.read_snapshot(transaction.paid(), policy.NODES[0], now)['decisions']
        candidates = sorted((row for row in candidates if row['allowed']), key=lambda row: row['cohort'])
        require(candidates, 'ACTIVE_LAB_REVOCATION_TARGET_REQUIRED')
        identity = candidates[0]['device']
        before = lab.dump(repository, 'before-revocation.dump')
        safety = {slot: native.qualify(dict(bodies), json.loads(manifest), root / ('safety-' + slot))
                  for slot, bodies, manifest, pin in joint.points}
        require_current_restore(imported, snapshot(repository))
        with PaidRehearsal(root / 'fresh') as target:
            restored = lab.restore(target, repository, before)
            require_current_restore(imported, snapshot(restored))
            with restored.transaction() as transaction:
                require(compare(transaction.paid(), joint) == parity, 'RESTORED_PARITY_CHANGED')
            require(Access(None, enrollment_repository=restored).revoke_device(identity), 'NEW_REVOCATION_NOT_ACKNOWLEDGED')
            acknowledged = snapshot(restored)
            delivery = revocation_readback(restored, joint, identity, target.root, now)
            require_current_restore(acknowledged, snapshot(restored))
            after = target.dump(restored, 'after-revocation.dump')
        with PaidRehearsal(root / 'current') as target:
            restored = lab.restore(target, repository, after)
            require_current_restore(acknowledged, snapshot(restored))
            require(revocation_readback(restored, joint, identity, target.root, now) == delivery, 'RESTORED_DENIAL_CHANGED')
            try:
                import_snapshot(restored, joint.canonical.snapshot)
            except ImportRejected:
                pass
            else:
                raise ValueError('OLD_CANONICAL_IMPORT_ACCEPTED')
        with PaidRehearsal(root / 'stale') as target:
            stale = lab.restore(target, repository, before)
            try:
                require_current_restore(acknowledged, snapshot(stale))
            except ValueError as error:
                require(str(error) == 'RESTORE_WOULD_LOSE_OR_CHANGE_ACKNOWLEDGED_STATE', 'UNEXPECTED_STALE_REFUSAL')
            else:
                raise ValueError('STALE_REVOCATION_RESTORE_ACCEPTED')
        receipt = dict(parity, result='RETAINED_CANONICAL_NODE_RECOVERY_PASS', native_safety=safety,
            new_laboratory_revocations=1, restored_receiver_denials=delivery,
            stale_restore='REFUSED', old_import_after_ack='REFUSED', postgres=lab.manifest['version'],
            before_dump_sha256=digest(before), after_dump_sha256=digest(after),
            owned_container_cleanup='PASS')
    private_file(root / 'receipt.json', encoded(receipt))
    return receipt
