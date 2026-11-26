"""Cold OWNER forward resume; never rewrite an old authority or claim external settlement."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import time

from scripts import control_ha_handoff as handoff
from scripts import control_ha_support_replace as replace
from scripts import control_ha_support_witness as witness
from scripts.control_ha_mailbox_startup import encoded, owned, unique


def document(path):
    return json.loads(owned(path, os.geteuid()), object_pairs_hook=unique)


def account_empty(plan):
    if plan['user']:
        return
    for process in Path('/proc').iterdir():
        if not process.name.isdecimal():
            continue
        try:
            status = (process / 'status').read_text()
            identifiers = next(line.split()[1:] for line in status.splitlines() if line.startswith('Uid:'))
            replace.require(str(plan['uid']) not in identifiers, 'OWNER_UID_WRITER_PRESENT')
        except FileNotFoundError:
            continue


def unadmitted_absence(previous):
    replace.require(previous.has('candidate-start-intent') and previous.has('handoff-ticket') and
                    not Path(previous.plan['start_authority']).exists() and
                    not Path(previous.plan['start_authority']).is_symlink(), 'UNADMITTED_ATTEMPT_REQUIRED')
    state = previous.validate()
    replace.empty(state, previous.plan['before']['ControlGroup'])
    account_empty(previous.plan)
    intended = document(previous.root / 'candidate-binding-intent.json')['binding']
    matches = []
    directory = previous.participant / 'refusals'
    for path in directory.iterdir():
        value = json.loads(owned(path, previous.plan['uid']), object_pairs_hook=unique)
        if (value.get('result') == 'START_AUTHORITY_REFUSED' and value.get('phase') == 'authority' and
                value.get('reason') == 'START_AUTHORITY_MISSING' and value.get('binding') == intended and
                value.get('admission_permitted') is False):
            matches.append((path, value))
    replace.require(len(matches) == 1, 'UNADMITTED_REFUSAL_PROOF_REQUIRED')
    previous_proof = document(previous.root / 'predecessor.json')['absence']
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    replace.require(previous_proof['boot'] == boot and intended['boot'] == boot, 'UNADMITTED_BOOT_CHANGED')
    path, diagnostic = matches[0]
    names = ('plan.json', 'predecessor.json', 'candidate-start-intent.json', 'candidate-binding-intent.json',
             'handoff-ticket.json')
    return dict(schema=1, result='PREVIOUS_PROCESS_ABSENT', reason='UNADMITTED_START_REFUSAL', boot=boot,
                old_binding=previous.plan['old_binding'], history={name: replace.digest(previous.root / name) for name in names},
                refusal_sha256=replace.digest(path), unadmitted_binding=intended,
                service_empty=True, graceful_exit_proven=False, settlement_proven=False, capture_permitted=False)


def absence(previous):
    replace.require(not previous.terminal_failure(), 'PREDECESSOR_TERMINAL_FAILURE')
    if not previous.has('accepted'):
        return unadmitted_absence(previous)
    accepted = document(previous.root / 'accepted.json')
    opened = document(previous.root / 'handoff-open.json')
    replace.require(accepted['archive_sha256'] == replace.CANDIDATE and
                    opened['candidate_binding'] == accepted['binding'] and
                    accepted['legacy_uncertainty_preserved'] is True, 'ACCEPTED_PREDECESSOR_REQUIRED')
    state = previous.validate()
    replace.empty(state, previous.plan['before']['ControlGroup'])
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    cold = boot != accepted['binding']['boot']
    if not cold:
        last_pid = subprocess.check_output([*previous.manager.command, 'show', previous.manager.unit,
                                           '--property=ExecMainPID', '--value'], text=True, timeout=10).strip()
        replace.require(last_pid == str(accepted['binding']['pid']) and
                        state['ExecMainStatus'] == '0' and state['ExecMainCode'] == '1', 'CLEAN_EXIT_OR_NEW_BOOT_REQUIRED')
    expected = dict(schema=1, binding=accepted['binding'], archive_sha256=replace.CANDIDATE)
    replace.require(document(previous.plan['start_authority']) == expected, 'PREDECESSOR_AUTHORITY_CHANGED')
    account_empty(previous.plan)
    replace.empty(previous.manager.state(), previous.plan['before']['ControlGroup'])
    return dict(schema=1, result='PREVIOUS_PROCESS_ABSENT', reason='BOOT_CHANGED' if cold else 'CLEAN_UNIT_EXIT',
                boot=boot, old_binding=accepted['binding'],
                history={name: replace.digest(previous.root / name) for name in
                         ('accepted.json', 'handoff-open.json', 'plan.json')},
                accepted_sha256=replace.digest(previous.root / 'accepted.json'),
                handoff_sha256=replace.digest(previous.root / 'handoff-open.json'),
                plan_sha256=replace.digest(previous.root / 'plan.json'), authority_sha256=replace.digest(
                    previous.plan['start_authority']), service_empty=True, uid_census_empty=True,
                uid_census_scope='fixture-unit-only' if previous.plan['user'] else 'service-account',
                graceful_exit_proven=not cold, settlement_proven=False, capture_permitted=False)


def prepare(previous_root, root, participant):
    previous = replace.Replacement(previous_root)
    root, participant = Path(root).absolute(), Path(participant).absolute()
    replace.require(os.geteuid() == 0 or previous.plan['user'], 'ROOT_RESUME_REQUIRED')
    if not previous.plan['user'] and not previous.manager.fixture:
        replace.require(root.parent == Path('/opt/family-connect-support') and
                        participant.parent == Path('/var/lib/family-connect-support'), 'RESUME_PATH_SCOPE')
    with replace.controller_lock(previous.root):
        proof = absence(previous)
        before = previous.manager.state()
        original = previous.plan
        root.mkdir(mode=0o700)
        participant.mkdir(mode=0o700)
        drain = participant / 'drain'
        drain.mkdir(mode=0o700)
        repo = Path(__file__).resolve().parents[1]
        sources = (*replace.SOURCES, 'scripts/control_ha_support_resume.py', 'scripts/control_ha_mailbox_generation.py',
                   'scripts/control_ha_mailbox_rollover.py')
        for name in sources:
            target = root / name
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            replace.put(target, replace.admission.read(repo / name))
        replace.put(drain / 'admission.py', replace.admission.read(root / 'scripts/control_ha_legacy_support.py'))
        replace.own(participant, original['uid'], original['gid'])
        identity = hashlib.sha256(os.fsencode(root)).hexdigest()[:24]
        entry = Path(original['artifact']).with_name('support-resume-' + identity + '.entry.py')
        authority = entry.with_suffix('.authority.json')
        diagnostics = participant / 'refusals'
        diagnostics.mkdir(mode=0o700)
        os.chown(diagnostics, original['uid'], original['gid'])
        replace.require(not entry.exists() and not entry.is_symlink() and
                        not authority.exists() and not authority.is_symlink(), 'NEW_RESUME_PATHS_REQUIRED')
        replace.put(entry, replace.admission.read(root / 'scripts/control_ha_support_entry.py'))
        entry.chmod(0o644)
        arguments = original['new_argv']
        options = arguments[arguments.index('--store'):]
        replace.require(arguments.count(original['entry']) == 1, 'PREDECESSOR_ENTRY_ARGUMENT')
        prefix = arguments[:arguments.index(original['entry'])]
        newer = [*prefix, str(entry), '--refusal-directory', str(diagnostics),
                 original['artifact'], str(authority), str(os.geteuid()), *options]
        replace.require(all(re.fullmatch('[A-Za-z0-9_./:@+-]+', value) for value in newer), 'RESUME_COMMAND')
        dropin = Path(original['dropin']).with_suffix('.resume.conf')
        replace.require(not dropin.exists() and not dropin.is_symlink() and len(dropin.name) < 240,
                        'NEW_RESUME_DROPIN_REQUIRED')
        content = ('[Service]\nExecStart=\nExecStart=' + ' '.join(newer) +
                   '\nRestart=no\nKillMode=mixed\nKillSignal=SIGTERM\nSendSIGKILL=no\nTimeoutStopSec=infinity\n').encode()
        replace.put(root / 'support.conf', content)
        plan = dict(original, root=str(root), participant=str(participant), before=before,
                    old_binding=proof['old_binding'], old_argv=arguments, new_argv=newer,
                    files=replace.files(before), entry=str(entry), start_authority=str(authority),
                    sources={name: replace.digest(root / name) for name in sources}, dropin=str(dropin),
                    dropin_sha256=hashlib.sha256(content).hexdigest(), handoff=True,
                    pending=sorted(path.name for path in (Path(original['gate']) / 'pending').iterdir()))
        replace.require(previous.manager.state() == before, 'PRESTATE_CHANGED')
        replace.admission.write(root / 'plan.json', plan)
        replace.admission.write(root / 'predecessor.json', dict(root=str(previous.root), absence=proof))
        return plan


class Resume:
    def __init__(self, root, mailbox):
        self.replacement = replace.Replacement(root)
        self.root = self.replacement.root
        self.mailbox = mailbox
        self.predecessor = document(self.root / 'predecessor.json')

    def predecessor_closure(self):
        proof = self.predecessor['absence']
        previous_root = Path(self.predecessor['root'])
        replace.require(all(replace.digest(previous_root / filename) == expected for filename, expected in
                            proof['history'].items()), 'PREDECESSOR_HISTORY_CHANGED')
        reclosure = document(self.root / 'predecessor-reclosure.json')
        old = reclosure['observed']
        saved = document(previous_root / 'handoff-ticket.json')['ticket']
        replace.require(reclosure.get('unit_verified') is True and reclosure.get('controller_uid') == os.geteuid() and
                        all(old['ticket'][name] == saved[name] for name in ('generation', 'manifest_sha256',
                            'support_public_sha256', 'owner_binding_sha256', 'replacement_plan_sha256')) and
                        old['fence']['new_link_admission'] == 'CLOSED' and old['fence']['opening_invalidated'] is True and
                        old['fence']['in_process_drained'] is True and old['fence']['accepted_target_work'] == 0,
                        'PREDECESSOR_RECLOSURE_REQUIRED')
        return reclosure

    def observe(self):
        response = self.mailbox.call('observe')
        replace.require(response.get('unit_verified') is True and response.get('restart_guard_verified') is True and
                        response.get('controller_uid') == os.geteuid(), 'INDEPENDENT_MAILBOX_REQUIRED')
        observed = response['observed']
        witness.validate_ticket(observed['ticket'], self.replacement.plan, replace.digest(self.root / 'plan.json'))
        replace.require(observed['capture_permitted'] is False, 'MAILBOX_CAPTURE_SCOPE')
        return response

    def sample(self, ticket):
        current = self.replacement
        replace.require(not current.terminal_failure(), 'RESUME_TERMINAL_FAILURE')
        witness.validate_ticket(ticket, current.plan, replace.digest(self.root / 'plan.json'))
        proof = self.predecessor['absence']
        replace.require(proof['boot'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip() and
                        proof['old_binding'] == current.plan['old_binding'] and
                        ((proof['reason'] == 'BOOT_CHANGED' and proof['boot'] != proof['old_binding']['boot']) or
                         (proof['reason'] == 'CLEAN_UNIT_EXIT' and proof['graceful_exit_proven'] is True) or
                         (proof['reason'] == 'UNADMITTED_START_REFUSAL' and proof['unadmitted_binding']['boot'] == proof['boot'])),
                        'RESUME_BOOT_CHANGED')
        accepted = document(self.root / 'accepted.json')
        bound = current.verify(current.validate())
        replace.require(bound == accepted['binding'], 'RESUME_PROCESS_CHANGED')
        replace.require(document(current.plan['start_authority']) ==
                        dict(schema=1, binding=bound, archive_sha256=replace.CANDIDATE), 'RESUME_AUTHORITY_CHANGED')
        self.predecessor_closure()
        reservation = dict(schema=1, ticket_sha256=witness.sha(ticket), plan_sha256=replace.digest(self.root / 'plan.json'),
                           accepted_sha256=replace.digest(self.root / 'accepted.json'),
                           opening_permitted=False, capture_permitted=False)
        current.record('handoff-reserved', **reservation)
        retained = document(self.root / 'handoff-reserved.json')
        retained.pop('at', None)
        replace.require(retained == reservation, 'RESUME_RESERVATION_CHANGED')
        result = dict(schema=1, result='OWNER_FORWARD_RESUME_SAMPLED', controller_uid=os.geteuid(),
                      fixture=current.manager.user or current.manager.fixture, ticket_sha256=witness.sha(ticket),
                      plan_sha256=reservation['plan_sha256'], old_binding=current.plan['old_binding'],
                      candidate_binding=bound, archive_sha256=replace.CANDIDATE,
                      accepted_sha256=reservation['accepted_sha256'], reservation_sha256=witness.sha(reservation),
                      predecessor_sha256=replace.digest(self.root / 'predecessor.json'),
                      reclosure_sha256=replace.digest(self.root / 'predecessor-reclosure.json'),
                      absence_sha256=witness.sha(proof), old_process_absent=True, independent_controller=True,
                      legacy_uncertainty_preserved=True, data_restored=False, capture_permitted=False,
                      opening_permitted=False, settlement_proven=False)
        return dict(action='OWNER_FORWARD_RESUME', ticket=ticket, witness=result, reservation=reservation)

    def run(self):
        try:
            return self._run()
        except (TimeoutError, subprocess.TimeoutExpired):
            self.replacement.record('resume-response-unknown-' + secrets.token_hex(8),
                                    capture_permitted=False, result='RECONCILIATION_REQUIRED')
            raise
        except Exception as error:
            reason = str(error)
            reason = reason if re.fullmatch('[A-Z][A-Z0-9_]{1,80}', reason) else 'RESUME_VALIDATION_FAILED'
            closure = dict(confirmed=False, drained=False)
            try:
                observed = self.observe()['observed']
                self.mailbox.call('reclose', dict(action='RECLOSE', ticket=observed['ticket']))
                fresh = self.observe()
                fence = fresh['observed']['fence']
                closure = dict(confirmed=fence['new_link_admission'] == 'CLOSED' and fence['opening_invalidated'] is True,
                               drained=fence['in_process_drained'] is True and fence['accepted_target_work'] == 0,
                               readback_sha256=witness.sha(fresh))
            except Exception:
                pass
            self.replacement.record('resume-refusal-' + secrets.token_hex(8), reason=reason, closure=closure,
                                    capture_permitted=False, admission_permitted=False)
            raise

    def _run(self):
        current = self.replacement
        with replace.controller_lock(self.root):
            replace.require(not current.terminal_failure(), 'RESUME_TERMINAL_FAILURE')
            proof = self.predecessor['absence']
            replace.require(proof['boot'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                            'RESUME_BOOT_CHANGED')
            response = self.observe()
            observed, state = response['observed'], current.validate()
            ticket = observed['ticket']
            current.record('handoff-ticket', ticket=ticket, capture_permitted=False)
            replace.require(document(self.root / 'handoff-ticket.json')['ticket'] == ticket, 'RESUME_TICKET_CHANGED')
            if not current.has('accepted'):
                fence = observed['fence']
                replace.require(fence['new_link_admission'] == 'CLOSED' and fence['opening_invalidated'] is False and
                                fence['in_process_drained'] is True and fence['accepted_target_work'] == 0 and
                                observed['consumed'] is None, 'NEW_CLOSED_DRAINED_GENERATION_REQUIRED')
                self.predecessor_closure()
                if not current.dropin.exists():
                    replace.empty(state, current.plan['before']['ControlGroup'])
                    current.record('install-intent', dropin_sha256=current.plan['dropin_sha256'])
                    replace.put(current.dropin, replace.admission.read(self.root / 'support.conf'))
                    current.dropin.chmod(0o644)
                current.manager.call('daemon-reload')
                state = current.validate()
                if state['MainPID'] == '0':
                    replace.require(not current.has('candidate-start-intent'), 'RESUME_ATTEMPT_ENDED')
                    replace.empty(state, current.plan['before']['ControlGroup'])
                    current.manager.call('stop', current.manager.unit)
                    current.record('candidate-start-intent')
                    current.manager.call('start', current.manager.unit)
                deadline = time.monotonic() + 5
                while True:
                    try:
                        current.admit_candidate()
                        bound = current.verify(current.validate())
                        break
                    except (OSError, ValueError):
                        if time.monotonic() >= deadline:
                            raise
                        time.sleep(.05)
                current.record('accepted', binding=bound, archive_sha256=replace.CANDIDATE,
                               data_restored=False, legacy_uncertainty_preserved=True, capture_permitted=False)
            request = self.sample(ticket)
            current.record('resume-request', request=request, capture_permitted=False)
            replace.require(document(self.root / 'resume-request.json')['request'] == request, 'RESUME_REQUEST_CHANGED')
            self.mailbox.call('resume', request)
            response = self.observe()
            opened = response['observed']
            replace.require(opened['ticket'] == ticket and opened['fence']['new_link_admission'] == 'OPEN_LOCAL_ONLY' and
                            opened['fence']['opening_invalidated'] is False and
                            opened['consumed']['request_sha256'] == witness.sha(request), 'RESUME_OPEN_UNCONFIRMED')
            replace.require(current.verify(current.validate()) == request['witness']['candidate_binding'],
                            'RESUME_PROCESS_CHANGED')
            current.record('handoff-open', candidate_binding=request['witness']['candidate_binding'],
                           readback_sha256=witness.sha(response), legacy_uncertainty_preserved=True, capture_permitted=False)
            return 'FORWARD_RESUME_OPEN_CAPTURE_DENIED'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--prepare-from', type=Path)
    parser.add_argument('--participant', type=Path)
    parser.add_argument('--mailbox-channel', type=Path)
    args = parser.parse_args()
    if args.prepare_from:
        replace.require(args.participant is not None, 'PARTICIPANT_REQUIRED')
        prepare(args.prepare_from, args.root, args.participant)
        result = 'RESUME_PREPARED_NOT_AUTHORIZED'
    else:
        replace.require(args.mailbox_channel is not None, 'MAILBOX_CHANNEL_REQUIRED')
        result = Resume(args.root, handoff.SSHMailbox(args.mailbox_channel)).run()
    print(encoded(dict(result=result, capture_permitted=False)).decode())


if __name__ == '__main__':
    try:
        main()
    except (TimeoutError, subprocess.TimeoutExpired):
        print(encoded(dict(result='RESPONSE_UNKNOWN', capture_permitted=False)).decode())
        raise SystemExit(75) from None
    except Exception as error:
        reason = str(error)
        print(encoded(dict(result='RESUME_REFUSED', capture_permitted=False,
                           reason=reason if re.fullmatch('[A-Z][A-Z0-9_]{1,80}', reason) else type(error).__name__)).decode())
        raise SystemExit(78) from None
