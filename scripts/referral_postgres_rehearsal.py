"""Disposable referral recovery rehearsal; never selects a production database."""
import argparse
import json
from pathlib import Path
import signal

from control.friends.access import Access, Rejected
from control.friends.referrals import Referrals
from control.friends.referrals_postgres import initialize_synthetic_referrals
from device_identity.device import DeviceIdentity
from scripts.control_ha_rehearsal import private_file, require
from scripts.enrollment_postgres_rehearsal import Rehearsal
from scripts.paid_postgres_rehearsal import PaidRehearsal, require_current_restore, snapshot

NOW = 1800000000


def proof(access, device, purpose, invitation=''):
    challenge = access.challenge(device.public_identity, device.wireguard_public_key, purpose, invitation)
    return device.prove_transport_key(challenge['challenge'])


def refused(attempt):
    try:
        attempt()
    except Rejected:
        return
    raise RuntimeError('Restored referral accepted a forbidden operation')


class ReferralRehearsal(PaidRehearsal):
    CONTRACT_FILES = (*PaidRehearsal.CONTRACT_FILES, 'tests/test_referral_repository.py')

    def referral_recovery(self):
        repository = self.repository()
        repository.initialize_synthetic()
        initialize_synthetic_referrals(repository)
        access = Access(None, clock=lambda: NOW, enrollment_repository=repository)
        service = Referrals(access, b'x' * 32)
        parent = DeviceIdentity.generate()
        access.complete(proof(access, parent, 'activate', access.invite()), 'activate')
        issue_proof = proof(access, parent, 'refer')
        issued = service.issue(issue_proof)
        token = issued['url'].split('#')[1]
        with repository.transaction() as transaction:
            transaction.database.execute('INSERT INTO field_support_audit'
                '(timestamp,support_id,previous_state,new_state,outcome) VALUES (%s,%s,%s,%s,%s)',
                (NOW, transaction.registered(parent.reference), 0, 1, 'synthetic-only'))
        old_backup = self.dump(repository, 'before-claims.dump')
        first_id, second_id, revoked_id = '1' * 32, '2' * 32, '3' * 32
        first = service.claim(token, first_id)
        child = DeviceIdentity.generate()
        activation_proof = proof(access, child, 'activate', first['invitation'])
        identity = access.complete(activation_proof, 'activate')
        second = service.claim(token, second_id)
        revoked = service.claim(token, revoked_id)
        with repository.transaction() as transaction:
            transaction.database.execute('UPDATE invites SET revoked=1 WHERE hash=%s',
                                         (access.code_hash(revoked['invitation']),))
        access.revoke_device(parent.reference)
        committed = snapshot(repository)
        unfinished = repository.connect()
        try:
            repository.configure(unfinished)
            unfinished.execute('INSERT INTO invites(hash) VALUES (%s)', ('f' * 64,))
            unfinished.execute('INSERT INTO referral_claims(request,sponsor,invite,created) VALUES (%s,%s,%s,%s)',
                               ('e' * 64, parent.reference, 'f' * 64, NOW))
            require(self.owned(), 'REHEARSAL_CONTAINER_MISSING')
            self.docker('kill', '--signal', 'KILL', self.container)
        finally:
            unfinished.close()
        self.docker('start', self.container)
        self.refresh_port()
        repository.port = self.port
        self.wait_ready()
        require_current_restore(committed, snapshot(repository))
        require(service.claim(token, first_id) == dict(first, status='activated'), 'ACKNOWLEDGED_CLAIM_CHANGED')
        require(service.claim(token, second_id) == second, 'ACKNOWLEDGED_INVITATION_CHANGED')
        refused(lambda: service.issue(issue_proof))
        refused(lambda: access.complete(activation_proof, 'activate'))
        refused(lambda: service.claim(token, revoked_id))
        refused(lambda: service.claim(token, '4' * 32))
        require_current_restore(committed, snapshot(repository))
        backup = self.dump(repository, 'current-referrals.dump')
        with Rehearsal(self.root / 'stale-restore') as target:
            stale = self.restore(target, repository, old_backup)
            try:
                require_current_restore(committed, snapshot(stale))
            except ValueError as error:
                require(str(error) == 'RESTORE_WOULD_LOSE_OR_CHANGE_ACKNOWLEDGED_STATE', 'UNEXPECTED_RESTORE_ERROR')
            else:
                raise RuntimeError('Stale referral restore accepted')
        with Rehearsal(self.root / 'current-restore') as target:
            restored = self.restore(target, repository, backup)
            require_current_restore(committed, snapshot(restored))
            recovered_access = Access(None, clock=lambda: NOW, enrollment_repository=restored)
            recovered = Referrals(recovered_access, b'x' * 32)
            require(recovered.claim(token, first_id) == dict(first, status='activated'), 'RESTORED_ACTIVATION_CHANGED')
            require(recovered.claim(token, second_id) == second, 'RESTORED_INVITATION_CHANGED')
            refused(lambda: recovered.issue(issue_proof))
            refused(lambda: recovered_access.complete(activation_proof, 'activate'))
            refused(lambda: recovered.claim(token, revoked_id))
            refused(lambda: recovered.claim(token, '4' * 32))
            require_current_restore(committed, snapshot(restored))
            reconnect = proof(recovered_access, child, 'nl')
            require(recovered_access.complete(reconnect, 'nl') == identity, 'RESTORED_IDENTITY_CHANGED')
            pending_child = DeviceIdentity.generate()
            recovered_access.complete(proof(recovered_access, pending_child, 'activate', second['invitation']), 'activate')
            require(recovered.claim(token, second_id)['status'] == 'activated', 'RESTORED_PENDING_INVITE_UNUSABLE')
        return {table: len(records) for table, records in committed.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', required=True, type=Path)
    args = parser.parse_args()
    with ReferralRehearsal(args.workdir) as rehearsal:
        tests = rehearsal.contracts()
        restored = rehearsal.referral_recovery()
        receipt = dict(schema=1, result='ISOLATED_REFERRAL_POSTGRES_PASS', contracts=tests,
            postgres=rehearsal.manifest['version'], driver='psycopg3.3.9', synthetic_only=True,
            crash_recovery='PASS', uncommitted_invitation_and_claim='ROLLED_BACK', stale_restore='REFUSED',
            current_restore='EXACT_ALL_LAB_TABLES', restored_rows=restored, proof_replay='REFUSED',
            claim_ack_loss='IDEMPOTENT', pending_invitation_activation='PASS', revocation='PRESERVED',
            production_writes=0, reverse_migration='NOT_IMPLEMENTED', replication='NOT_IMPLEMENTED')
    receipt['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(receipt, indent=2).encode())
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, terminate)
    main()
