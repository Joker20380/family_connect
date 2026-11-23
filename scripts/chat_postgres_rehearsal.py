"""Disposable chat/support DB recovery, never mailbox or support file publication."""
import argparse
import json
from pathlib import Path
import signal

import RNS

from control.friends.access import Access
from control.friends.chat import ChatAccess
from control.friends.chat_postgres import initialize_synthetic_chat
from control.friends import chat_service, support, support_ids
from control.friends.paid_postgres import initialize_synthetic_paid
from control.friends.support_postgres import initialize_synthetic_support
from device_identity.device import DeviceIdentity
from messenger.admission import message
from scripts.control_ha_rehearsal import private_file, require
from scripts.enrollment_postgres_rehearsal import Rehearsal
from scripts.paid_postgres_rehearsal import PaidRehearsal, apply, snapshot, require_current_restore
from scripts.referral_postgres_rehearsal import NOW, proof, refused


def activate(access):
    device = DeviceIdentity.generate()
    access.complete(proof(access, device, 'activate', access.invite()), 'activate')
    return device


def request(registry, device, identity):
    public = identity.get_public_key().hex()
    value = registry.challenge(device.public_identity, device.wireguard_public_key, public)
    return dict(proof=device.prove_transport_key(value['challenge']), chat_public=public,
                chat_signature=identity.sign(message(public, device.reference, value['challenge'])).hex())


def service_proof(identity):
    public = identity.get_public_key().hex()
    return dict(public=public, signature=identity.sign(chat_service.message(public)).hex())


def refused_value(attempt, reason):
    try:
        attempt()
    except ValueError as error:
        require(str(error) == reason, 'UNEXPECTED_REFUSAL')
    else:
        raise ValueError('EXPECTED_REFUSAL')


class ChatRehearsal(PaidRehearsal):
    CONTRACT_FILES = ('tests/test_enrollment_repository.py', 'tests/test_chat_repository.py')

    def chat_recovery(self):
        repository = self.repository()
        repository.initialize_synthetic()
        initialize_synthetic_chat(repository)
        initialize_synthetic_paid(repository)
        initialize_synthetic_support(repository)
        access = Access(None, clock=lambda: NOW, enrollment_repository=repository)
        registry = ChatAccess(access)
        client, denied, pending_device = [activate(access) for _ in range(3)]
        client_identity, denied_identity, pending_identity = [RNS.Identity() for _ in range(3)]
        official, revoked_service = [service_proof(RNS.Identity()) for _ in range(2)]
        policy = self.root / 'synthetic-support.json'
        private_file(policy, json.dumps(dict(schema=2, sender_public=official['public'], revision=1, enabled=True)).encode())
        old_backup = self.dump(repository, 'before-chat.dump')
        chat_service.register(access, **official)
        chat_service.register(access, **revoked_service)
        chat_service.revoke(access, revoked_service['public'])
        consumed = request(registry, client, client_identity)
        result = registry.register(**consumed)
        registry.register(**request(registry, denied, denied_identity))
        denied_request = request(registry, denied, denied_identity)
        access.revoke_device(denied.reference)
        pending = request(registry, pending_device, pending_identity)
        lease = registry.snapshot()
        node = dict(sequence=lease['sequence'], expires_at=lease['expires_at'], host='127.0.0.1', port=4243,
                    public_key=official['public'])
        role = support.enroll(access, policy, client.reference, result['chat_public'], node['expires_at'])
        alias = support_ids.request(access, dict(proof=proof(access, client, 'support'), platform='android',
            app_version='0.1.18-beta126', version_code=126))['device_support_id']
        with repository.transaction() as transaction:
            apply(transaction.paid(), alias)
            transaction.database.execute('INSERT INTO field_support_audit'
                '(timestamp,support_id,previous_state,new_state,outcome) VALUES (%s,%s,%s,%s,%s)',
                (NOW, alias, 0, 0, 'synthetic-chat-coexistence'))
        projection = support.bindings(access, b'h' * 32, policy, node)
        members = registry.desired_members()
        committed = snapshot(repository)
        unfinished = repository.connect()
        try:
            repository.configure(unfinished)
            unfinished.execute('DELETE FROM chat_bindings')
            unfinished.execute('UPDATE chat_service_senders SET enabled=1')
            unfinished.execute('UPDATE chat_challenges SET used=1')
            unfinished.execute('UPDATE chat_sequence SET value=value+100')
            require(self.owned(), 'REHEARSAL_CONTAINER_MISSING')
            self.docker('kill', '--signal', 'KILL', self.container)
        finally:
            unfinished.close()
        self.docker('start', self.container)
        self.refresh_port()
        repository.port = self.port
        self.wait_ready()
        require_current_restore(committed, snapshot(repository))
        backup = self.dump(repository, 'current-chat.dump')
        with Rehearsal(self.root / 'stale-restore') as target:
            stale = self.restore(target, repository, old_backup)
            refused_value(lambda: require_current_restore(committed, snapshot(stale)),
                          'RESTORE_WOULD_LOSE_OR_CHANGE_ACKNOWLEDGED_STATE')
        with Rehearsal(self.root / 'current-restore') as target:
            restored = self.restore(target, repository, backup)
            require_current_restore(committed, snapshot(restored))
            recovered = Access(None, clock=lambda: NOW, enrollment_repository=restored)
            current = ChatAccess(recovered)
            refused(lambda: current.register(**consumed))
            refused(lambda: current.register(**denied_request))
            refused_value(lambda: chat_service.register(recovered, **revoked_service),
                          'Revoked service identity cannot be reactivated by replay')
            chat_service.register(recovered, **official)
            require(current.desired_members() == members, 'CHAT_MEMBERS_CHANGED')
            require(support.bindings(recovered, b'h' * 32, policy, node) == projection, 'SUPPORT_BINDINGS_CHANGED')
            require(support.enroll(recovered, policy, client.reference, result['chat_public'], node['expires_at']) == role,
                    'SUPPORT_ROLE_CHANGED')
            with restored.transaction() as transaction:
                require(apply(transaction.paid(), alias)['duplicate'], 'PAYMENT_REPLAYED')
            require_current_restore(committed, snapshot(restored))
            current.register(**pending)
            refused(lambda: current.register(**pending))
            require(current.snapshot()['sequence'] == lease['sequence'] + 1, 'CHAT_SEQUENCE_REWOUND')
        return {table: len(records) for table, records in committed.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', required=True, type=Path)
    args = parser.parse_args()
    with ChatRehearsal(args.workdir) as rehearsal:
        tests = rehearsal.contracts()
        restored = rehearsal.chat_recovery()
        result = dict(schema=1, result='ISOLATED_CHAT_POSTGRES_PASS', contracts=tests,
            postgres=rehearsal.manifest['version'], synthetic_only=True, crash_recovery='PASS',
            current_restore='EXACT_ALL_LAB_TABLES', stale_restore='REFUSED', restored_rows=restored,
            consumed_proofs='REFUSED', pending_chat_proof='CONSUMED_ONCE', service_revoke='PRESERVED',
            sequence='CONTINUES', support_binding='PRESERVED', production_writes=0,
            keys_and_policy='EPHEMERAL_RETAINED_NOT_RESTORED', mailbox_file_publication='NOT_MIGRATED',
            replication='NOT_IMPLEMENTED', reverse_migration='NOT_IMPLEMENTED')
    result['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(result, indent=2).encode())
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, terminate)
    main()
