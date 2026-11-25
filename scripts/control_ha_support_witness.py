"""Independent OWNER replacement sample; never a mailbox opening or capture permit."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import select
import time
import uuid

from scripts import control_ha_legacy_support as admission
from scripts import control_ha_support_replace as replace
from scripts.control_ha_mailbox_startup import encoded, owned, unique


def sha(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def document(path, uid):
    return json.loads(owned(path, uid), object_pairs_hook=unique)


def validate_ticket(ticket, plan, plan_sha256):
    admission.require(type(ticket) is dict and set(ticket) == {
        'schema', 'generation', 'manifest_sha256', 'process', 'challenge',
        'support_public_sha256', 'owner_binding_sha256', 'replacement_plan_sha256'}, 'MAILBOX_TICKET_SHAPE')
    admission.require(type(ticket['schema']) is int and ticket['schema'] == 1, 'MAILBOX_TICKET_SCHEMA')
    for name in ('generation', 'manifest_sha256', 'challenge', 'support_public_sha256',
                 'owner_binding_sha256', 'replacement_plan_sha256'):
        admission.require(type(ticket[name]) is str and re.fullmatch('[0-9a-f]{64}', ticket[name]),
                          'MAILBOX_TICKET_DIGEST')
    process = ticket['process']
    admission.require(type(process) is dict and set(process) == {'pid', 'start', 'boot', 'command', 'cgroup'},
                      'MAILBOX_PROCESS_SHAPE')
    admission.require(type(process['pid']) is int and process['pid'] > 1 and type(process['start']) is str and
                      re.fullmatch('[0-9]+', process['start']) and type(process['boot']) is str and
                      str(uuid.UUID(process['boot'])) == process['boot'], 'MAILBOX_PROCESS_BINDING')
    for name in ('command', 'cgroup'):
        admission.require(type(process[name]) is str and re.fullmatch('[0-9a-f]{64}', process[name]),
                          'MAILBOX_PROCESS_DIGEST')
    admission.require(ticket['owner_binding_sha256'] == sha(plan['old_binding']) and
                      ticket['replacement_plan_sha256'] == plan_sha256, 'OWNER_TICKET_BINDING')
    arguments = plan['old_argv']
    admission.require(arguments.count('--sender-public') == 1, 'OWNER_SENDER_ARGUMENT')
    public = arguments[arguments.index('--sender-public') + 1]
    admission.require(re.fullmatch('[0-9a-f]{128}', public) and
                      ticket['support_public_sha256'] == hashlib.sha256(bytes.fromhex(public)).hexdigest(),
                      'OWNER_SENDER_BINDING')


def evidence(replacement):
    plan = replacement.plan
    admission.require(not any(replacement.has(name) for name in
                              ('rollback-intent', 'rolled-back', 'aborted')), 'REPLACEMENT_NOT_COMMITTED')
    records = {name: document(replacement.root / (name + '.json'), os.geteuid()) for name in
               ('drain-intent', 'commit-intent', 'old-exited', 'install-intent', 'candidate-start-intent', 'accepted')}
    state = records['old-exited']['state']
    admission.require(state['MainPID'] == state['ControlPID'] == '0' and
                      (state['ActiveState'] in ('inactive', 'failed') or
                       (state['ActiveState'], state['SubState']) == ('active', 'exited')) and
                      state['ExecMainCode'] == '1' and state['ExecMainStatus'] == '0' and
                      state['NRestarts'] == plan['before']['NRestarts'], 'INDEPENDENT_OLD_EXIT')
    admission.require(records['old-exited']['legacy_uncertainty_preserved'] is True and
                      records['old-exited']['capture_permitted'] is False, 'OLD_EXIT_SCOPE')
    request_raw = owned(replacement.drain / 'request.json', plan['uid'])
    request = json.loads(request_raw, object_pairs_hook=unique)
    admission.require(request['binding'] == plan['old_binding'] and request['baseline'] == plan['baseline_pins'] and
                      request['root'] == plan['baseline'], 'DRAIN_PLAN_BINDING')
    expected = dict(binding=plan['old_binding'], request_sha256=hashlib.sha256(request_raw).hexdigest(),
                    capture_permitted=False)
    admission.require(all(document(replacement.drain / name, plan['uid']) == expected for name in
                          ('ready.json', 'commit.json')), 'QUIESCENT_COMMIT_BINDING')
    admission.require(document(replacement.drain / 'committed.json', plan['uid']) ==
                      dict(binding=plan['old_binding'], irreversible=True, capture_permitted=False), 'EXIT_COMMIT_BINDING')
    admission.require(document(replacement.drain / 'exited.json', plan['uid']) ==
                      dict(binding=plan['old_binding'], final_persistence=True, stores_closed=True,
                           workers=0, exit_code=0, capture_permitted=False), 'FINAL_PERSISTENCE_RECEIPT')
    admission.require(not any((replacement.drain / name).exists() for name in ('error.json', 'restored.json')),
                      'DRAIN_REFUSED')
    admission.require(all(replace.digest(replacement.drain / name) == value for name, value in
                          records['drain-intent']['pins'].items()), 'DRAIN_SOURCE_CHANGED')
    accepted = records['accepted']
    admission.require(accepted['archive_sha256'] == replace.CANDIDATE and accepted['data_restored'] is False and
                      accepted['legacy_uncertainty_preserved'] is True and accepted['capture_permitted'] is False,
                      'ACCEPTANCE_SCOPE')
    return records


def sample(root, ticket):
    ticket = json.loads(encoded(ticket), object_pairs_hook=unique)
    replacement = replace.Replacement(root)
    admission.require(replacement.manager.user or os.geteuid() == 0, 'ROOT_WITNESS_REQUIRED')
    with replace.controller_lock(replacement.root):
        admission.require(not replacement.terminal_failure(), 'TERMINAL_RECONCILIATION_REQUIRED')
        plan_raw = owned(replacement.root / 'plan.json', os.geteuid())
        admission.require(encoded(json.loads(plan_raw, object_pairs_hook=unique)) == encoded(replacement.plan),
                          'PLAN_CHANGED')
        plan_sha256 = hashlib.sha256(plan_raw).hexdigest()
        validate_ticket(ticket, replacement.plan, plan_sha256)
        records = evidence(replacement)
        old = replacement.plan['old_binding']
        admission.require(old['boot'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip() and
                          not (Path('/proc') / str(old['pid'])).exists(), 'OLD_PROCESS_ABSENCE_UNPROVEN')
        state = replacement.validate()
        candidate = records['accepted']['binding']
        admission.require(str(candidate['pid']) == state['MainPID'] and candidate != old and
                          state['NRestarts'] == replacement.plan['before']['NRestarts'], 'ACCEPTED_RUNTIME_CHANGED')
        descriptor = os.pidfd_open(candidate['pid'])
        try:
            admission.require(not select.select([descriptor], [], [], 0)[0] and
                              replacement.verify(state) == candidate, 'CANDIDATE_NOT_LIVE')
            reservation = dict(schema=1, ticket_sha256=sha(ticket), plan_sha256=plan_sha256,
                               accepted_sha256=sha(records['accepted']), opening_permitted=False,
                               capture_permitted=False)
            if replacement.has('handoff-reserved'):
                retained = document(replacement.root / 'handoff-reserved.json', os.geteuid())
                admission.require(encoded({name: value for name, value in retained.items() if name != 'at'}) ==
                                  encoded(reservation), 'HANDOFF_ALREADY_BOUND')
            else:
                replacement.record('handoff-reserved', **reservation)
            admission.require(evidence(replacement) == records and replacement.validate() == state and
                              owned(replacement.root / 'plan.json', os.geteuid()) == plan_raw and
                              admission.binding(candidate['pid']) == candidate and
                              not select.select([descriptor], [], [], 0)[0], 'WITNESS_CHANGED')
            return dict(schema=1, result='OWNER_REPLACEMENT_SAMPLED', sampled_at_ns=time.time_ns(),
                        ticket_sha256=sha(ticket), plan_sha256=plan_sha256, old_binding=old,
                        candidate_binding=candidate, archive_sha256=replace.CANDIDATE,
                        accepted_sha256=sha(records['accepted']), reservation_sha256=sha(reservation),
                        evidence_sha256=sha(records), owner_exit_verified=True,
                        independent_controller=True, controller_uid=os.geteuid(), rollback_requires_mailbox_reclosure=True,
                        fixture=replacement.manager.user or replacement.manager.fixture,
                        mailbox_live_verified=False, opening_permitted=False, capture_permitted=False,
                        legacy_uncertainty_preserved=True)
        finally:
            os.close(descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--ticket', required=True, type=Path)
    arguments = parser.parse_args()
    print(json.dumps(sample(arguments.run, document(arguments.ticket, os.geteuid())), sort_keys=True))


if __name__ == '__main__':
    main()
