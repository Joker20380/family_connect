"""Owned local PG recovery of a preflighted retained snapshot, never a live target."""
import json
from pathlib import Path

from control.friends.access import Access, Rejected
from control.friends import paid_beta
from device_identity.device import DeviceIdentity
from scripts.control_ha_import import ImportRejected, import_snapshot
from scripts.control_ha_installed_composite import Prepared
from scripts.control_ha_rehearsal import private_file, require
from scripts.paid_postgres_rehearsal import PaidRehearsal, snapshot, require_current_restore


def qualify(prepared, root, *, now):
    require(type(prepared) is Prepared and type(now) is int and now > 0, 'INSTALLED_PREFLIGHT_REQUIRED')
    root = Path(root)
    frozen = prepared.snapshot
    with PaidRehearsal(root) as lab:
        repository = lab.repository()
        require(import_snapshot(repository, frozen)['result'] == 'IMPORTED', 'IMPORT_REQUIRED')
        imported = snapshot(repository)
        before = lab.dump(repository, 'retained-import.dump')
        unfinished = repository.connect()
        try:
            repository.configure(unfinished)
            unfinished.execute('UPDATE devices SET revoked=1')
            require(lab.owned(), 'REHEARSAL_OWNERSHIP')
            lab.docker('kill', '--signal', 'KILL', lab.container)
        finally:
            unfinished.close()
        lab.docker('start', lab.container)
        lab.refresh_port()
        repository.port = lab.port
        lab.wait_ready()
        require_current_restore(imported, snapshot(repository))
        require(import_snapshot(repository, frozen)['result'] == 'EXACT_RETRY', 'CRASH_IMPORT_CHANGED')
        with PaidRehearsal(root / 'restored') as target:
            restored = lab.restore(target, repository, before)
            require_current_restore(imported, snapshot(restored))
            require(import_snapshot(restored, frozen)['result'] == 'EXACT_RETRY', 'RESTORED_IMPORT_CHANGED')
            with restored.transaction() as transaction:
                paid = transaction.database.execute('SELECT device,paid_until,grace_until FROM paid_beta_subscriptions').fetchall()
                future = max([now] + [max(row['paid_until'], row['grace_until'] or 0) for row in paid]) + 1
                require(all(not paid_beta.effective_subscription_state(transaction.paid(), row['device'], future).allowed
                            for row in paid), 'EXPIRED_PAID_ACCESS')
            access = Access(None, clock=lambda: now, enrollment_repository=restored)
            device = DeviceIdentity.generate()
            invitation = access.invite()
            pending = access.challenge(device.public_identity, device.wireguard_public_key, 'activate', invitation)
            proof = device.prove_transport_key(pending['challenge'])
            access.complete(proof, 'activate')
            acknowledged = snapshot(restored)
            require(len(acknowledged['devices']) == len(imported['devices']) + 1, 'NEW_ACK_MISSING')
            require(acknowledged['paid_beta_events'] == imported['paid_beta_events'], 'PAID_HISTORY_CHANGED')
            require(all(acknowledged[name] == rows for name, rows in imported.items()
                        if name.startswith('restricted_owner_handoff')), 'HANDOFF_HISTORY_CHANGED')
            current = target.dump(restored, 'after-ack.dump')
        with PaidRehearsal(root / 'stale') as target:
            stale = lab.restore(target, repository, before)
            try:
                require_current_restore(acknowledged, snapshot(stale))
            except ValueError as error:
                require(str(error) == 'RESTORE_WOULD_LOSE_OR_CHANGE_ACKNOWLEDGED_STATE', 'UNEXPECTED_STALE_REFUSAL')
            else:
                raise ValueError('STALE_RESTORE_ACCEPTED')
        with PaidRehearsal(root / 'current') as target:
            current_repository = lab.restore(target, repository, current)
            require_current_restore(acknowledged, snapshot(current_repository))
            access = Access(None, clock=lambda: now, enrollment_repository=current_repository)
            try:
                access.complete(proof, 'activate')
            except Rejected:
                pass
            else:
                raise ValueError('ACK_PROOF_REUSED')
            try:
                import_snapshot(current_repository, frozen)
            except ImportRejected:
                pass
            else:
                raise ValueError('OLD_IMPORT_ACCEPTED_AFTER_ACK')
        receipt = dict(result='INSTALLED_CANONICAL_PG_RECOVERY_PASS', postgres=lab.manifest['version'],
            source_tables=len(frozen.counts), source_rows=sum(frozen.counts.values()), target_tables=len(imported),
            imported_rows={name: len(rows) for name, rows in imported.items()}, paid_expiry_denials=len(paid),
            crash_recovery='EXACT', current_restore='EXACT', stale_restore='REFUSED', old_import_after_ack='REFUSED',
            new_acknowledged_devices=1, consumed_proof_replay='REFUSED', handoff='RETAINED_READ_ONLY',
            activation=False, full_recovery=False, fleet_pair_fence=False, independent_forward_trust=False)
    receipt['owned_container_cleanup'] = 'PASS'
    private_file(root / 'receipt.json', json.dumps(receipt, sort_keys=True).encode())
    return receipt
