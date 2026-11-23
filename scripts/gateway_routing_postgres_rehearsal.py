"""Owned synthetic gateway assignment recovery; no live routing or file publication."""
import argparse
import base64
import json
from pathlib import Path
import signal
from types import SimpleNamespace

from control.friends.access import Access
from control.friends import gateway_routing as routing, gateway_selection as selection, support_ids
from control.friends.gateway_routing_postgres import initialize_synthetic_routing
from control.friends.paid_postgres import initialize_synthetic_paid
from control.friends.support_postgres import initialize_synthetic_support
from provisioning.friends_catalog import DOMAIN, GATEWAY_CHOICES
from scripts.chat_postgres_rehearsal import activate, refused_value
from scripts.control_ha_rehearsal import private_file, require
from scripts.enrollment_postgres_rehearsal import Rehearsal
from scripts.paid_postgres_rehearsal import PaidRehearsal, apply, snapshot, require_current_restore
from scripts.referral_postgres_rehearsal import NOW, proof, refused

ROOT = Path(__file__).resolve().parents[1]


def signed_catalog(envelope, signer, *, sequence=None):
    payload = json.loads(base64.b64decode(envelope['payload']))
    if sequence is not None:
        payload['sequence'] = sequence
    raw = routing.canonical(payload)
    return dict(payload=base64.b64encode(raw).decode(), signature=base64.b64encode(signer.sign(DOMAIN + raw)).decode())


def scenario(access, root, *, signer=None):
    vectors = json.loads((ROOT / 'tests/vectors/friends-selection-v3.json').read_bytes())
    if signer is not None:
        vectors['legacy_catalogs'] = [signed_catalog(envelope, signer) for envelope in vectors['legacy_catalogs']]
        vectors['anchor'] = base64.b64encode(signer.public_key().public_bytes_raw()).decode()
        vectors['cases'][0]['reply']['catalog'] = signed_catalog(vectors['cases'][0]['reply']['catalog'], signer)
    envelopes = [routing.canonical(envelope) for envelope in vectors['legacy_catalogs']]
    hashes = [routing.digest(raw) for raw in envelopes]
    raw = routing.canonical(dict(schema=1, generation=1, legacy=hashes[0], admit=hashes[1], catalogs=[
        dict(node=target, sha256=sha) for target, sha in zip((*GATEWAY_CHOICES, GATEWAY_CHOICES[0]), hashes)]))
    anchor = base64.b64decode(vectors['anchor'])
    policy = routing.Policy(raw, anchor, dict(zip(hashes, envelopes)))
    directory = root / 'gateway-routing'
    directory.mkdir(mode=0o700)
    catalog = routing.canonical(vectors['cases'][0]['reply']['catalog'])
    files = {'anchor.pub': base64.b64encode(anchor), policy.sha256 + '.policy.json': raw,
             routing.digest(catalog) + '.selection.json': catalog}
    files.update({sha + '.catalog.json': envelope for sha, envelope in zip(hashes, envelopes)})
    for name, content in files.items():
        private_file(directory / name, content)
    request = dict(schema=1, action='install-selection', operation_id='selection-synthetic-01',
        policy_sha256=policy.sha256, catalog_sha256=routing.digest(catalog), previous_sha256=None)
    return SimpleNamespace(access=access, root=root, directory=directory, envelopes=envelopes, hashes=hashes,
        anchor=anchor, policy=policy, request=request, owner=activate(access))


def replacement(node):
    raw = routing.canonical(node.policy.value | dict(generation=2, admit=node.hashes[2]))
    policy = routing.Policy(raw, node.anchor, dict(zip(node.hashes, node.envelopes)))
    private_file(node.directory / (policy.sha256 + '.policy.json'), raw)
    return policy


class RoutingRehearsal(PaidRehearsal):
    CONTRACT_FILES = ('tests/test_enrollment_repository.py', 'tests/test_gateway_routing_repository.py')

    def routing_recovery(self):
        repository = self.repository()
        repository.initialize_synthetic()
        initialize_synthetic_routing(repository)
        initialize_synthetic_paid(repository)
        initialize_synthetic_support(repository)
        access = Access(None, clock=lambda: NOW, enrollment_repository=repository)
        node = scenario(access, self.root)
        denied = activate(access)
        old_backup = self.dump(repository, 'before-routing.dump')
        routing.install(access, node.policy, node.envelopes[0])
        selection.install(access, node.root, node.request)
        consumed = proof(access, node.owner, 'nl')
        access.complete(consumed, 'nl')
        newcomer = activate(access)
        routing.configuration(access, node.root, 'nl', newcomer.reference)
        movement = dict(device=node.owner.reference, expected=node.hashes[0], destination=node.hashes[1],
                        operation_id='synthetic-routing-move')
        routing.move(access, node.policy, **movement)
        access.revoke_device(denied.reference)
        pending = proof(access, newcomer, 'nl')
        alias = support_ids.request(access, dict(proof=proof(access, node.owner, 'support'), platform='android',
            app_version='0.1.18-beta126', version_code=126))['device_support_id']
        with repository.transaction() as transaction:
            apply(transaction.paid(), alias)
        served = routing.configuration(access, node.root, 'nl', node.owner.reference)
        selected = selection.configuration(access, node.root, GATEWAY_CHOICES[0], node.owner.reference)
        committed = snapshot(repository)
        unfinished = repository.connect()
        try:
            repository.configure(unfinished)
            unfinished.execute('UPDATE gateway_assignments SET sequence=sequence+100')
            unfinished.execute('UPDATE gateway_routing_state SET generation=generation+100')
            unfinished.execute('UPDATE challenges SET used=1')
            unfinished.execute('UPDATE devices SET revoked=0')
            require(self.owned(), 'REHEARSAL_CONTAINER_MISSING')
            self.docker('kill', '--signal', 'KILL', self.container)
        finally:
            unfinished.close()
        self.docker('start', self.container)
        self.refresh_port()
        repository.port = self.port
        self.wait_ready()
        require_current_restore(committed, snapshot(repository))
        backup = self.dump(repository, 'current-routing.dump')
        with Rehearsal(self.root / 'stale-restore') as target:
            stale = self.restore(target, repository, old_backup)
            refused_value(lambda: require_current_restore(committed, snapshot(stale)),
                          'RESTORE_WOULD_LOSE_OR_CHANGE_ACKNOWLEDGED_STATE')
        with Rehearsal(self.root / 'current-restore') as target:
            restored = self.restore(target, repository, backup)
            require_current_restore(committed, snapshot(restored))
            recovered = Access(None, clock=lambda: NOW, enrollment_repository=restored)
            refused(lambda: recovered.complete(consumed, 'nl'))
            refused(lambda: routing.configuration(recovered, node.root, 'nl', denied.reference))
            refused(lambda: selection.configuration(recovered, node.root, GATEWAY_CHOICES[1], denied.reference))
            require(routing.move(recovered, node.policy, **movement)['result'] == 'UNCHANGED', 'ROUTING_REPLAYED')
            require(selection.install(recovered, node.root, node.request)['result'] == 'UNCHANGED', 'SELECTION_REPLAYED')
            require(routing.configuration(recovered, node.root, 'nl', node.owner.reference) == served, 'ROUTE_CHANGED')
            require(selection.configuration(recovered, node.root, GATEWAY_CHOICES[0], node.owner.reference) == selected,
                    'SELECTION_CHANGED')
            with restored.transaction() as transaction:
                require(apply(transaction.paid(), alias)['duplicate'], 'PAYMENT_REPLAYED')
            require_current_restore(committed, snapshot(restored))
            for table in ('gateway_assignment_events', 'gateway_selection_events'):
                import psycopg
                try:
                    with restored.transaction() as transaction:
                        transaction.database.execute('DELETE FROM ' + table)
                except psycopg.errors.CheckViolation:
                    pass
                else:
                    raise ValueError('RESTORED_APPEND_ONLY_TRIGGER_MISSING')
            recovered.complete(pending, 'nl')
            refused(lambda: recovered.complete(pending, 'nl'))
            routing.move(recovered, node.policy, device=node.owner.reference, expected=node.hashes[1],
                destination=node.hashes[2], operation_id='synthetic-forward-rollback')
            require(routing.configuration(recovered, node.root, 'nl', node.owner.reference)[1] == '192.0.2.20',
                    'FORWARD_ROLLBACK_FAILED')
            updated = replacement(node)
            routing.replace_policy(recovered, node.policy, updated)
            refused_value(lambda: selection.configuration(recovered, node.root, GATEWAY_CHOICES[0], node.owner.reference),
                          'Gateway routing rejected')
        return {table: len(records) for table, records in committed.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', required=True, type=Path)
    args = parser.parse_args()
    with RoutingRehearsal(args.workdir) as rehearsal:
        tests = rehearsal.contracts()
        restored = rehearsal.routing_recovery()
        result = dict(schema=1, result='ISOLATED_ROUTING_POSTGRES_PASS', contracts=tests,
            postgres=rehearsal.manifest['version'], synthetic_only=True, crash_recovery='PASS',
            current_restore='EXACT_ALL_LAB_TABLES', stale_restore='REFUSED', restored_rows=restored,
            operation_replay='UNCHANGED', append_only_triggers='PRESERVED', forward_catalog_rollback='PASS',
            consumed_proofs='REFUSED', pending_proof='CONSUMED_ONCE', production_writes=0,
            signed_files='RETAINED_NOT_RESTORED', replication='NOT_IMPLEMENTED', reverse_migration='NOT_IMPLEMENTED')
    result['owned_container_cleanup'] = 'PASS'
    private_file(args.workdir / 'receipt.json', json.dumps(result, indent=2).encode())
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, terminate)
    main()
