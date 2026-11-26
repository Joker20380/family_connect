"""Resumable OWNER/NL1 support handoff and code-only recovery, never capture authority."""
import argparse
import json
import os
import pwd
from pathlib import Path
import secrets
import re
import shlex
import subprocess

from scripts import control_ha_legacy_support as admission
from scripts import control_ha_support_replace as replace
from scripts import control_ha_support_witness as witness
from scripts.control_ha_mailbox_startup import encoded, owned, unique


def supervisor_unit(plan, interpreter, channel):
    admission.require(plan.get('handoff') is True and re.fullmatch('[A-Za-z0-9_./:@+-]+', str(channel)),
                      'HANDOFF_SUPERVISOR_COMMAND')
    original = replace.supervisor_unit(plan, interpreter)
    return original.replace('/runner.py --run ', '/handoff.py --mailbox-channel ' + str(channel) + ' --run ')


class SSHMailbox:
    def __init__(self, path):
        admission.require(os.geteuid() == 0, 'ROOT_HANDOFF_REQUIRED')
        value = json.loads(owned(path, 0), object_pairs_hook=unique)
        admission.require(set(value) == {'host', 'interpreter', 'entry', 'plan', 'local_uid'} and
                          value['host'] == 'root@185.10.158.212', 'NL1_CHANNEL_SCOPE')
        admission.require(type(value['local_uid']) is int and value['local_uid'] >= 0, 'NL1_TRANSPORT_UID')
        account = pwd.getpwuid(value['local_uid'])
        environment = dict(PATH='/usr/bin:/bin', HOME=account.pw_dir, USER=account.pw_name, LOGNAME=account.pw_name)
        if 'SSH_AUTH_SOCK' in os.environ:
            environment['SSH_AUTH_SOCK'] = os.environ['SSH_AUTH_SOCK']
        self.transport = dict(user=account.pw_uid, group=account.pw_gid, extra_groups=[], env=environment)
        for name in ('entry', 'plan', 'interpreter'):
            path = Path(value[name])
            admission.require(path.is_absolute() and '..' not in path.parts and
                              str(path).startswith('/opt/apps/family_connect/'), 'NL1_PATH_SCOPE')
        self.command = ['/usr/bin/ssh', '-oBatchMode=yes', '-oStrictHostKeyChecking=yes', value['host'],
                        shlex.join([value['interpreter'], '-I', '-B', value['entry'], '--plan', value['plan']])]

    def call(self, action, payload=None):
        nonce = secrets.token_hex(32)
        value = dict(action=action, nonce=nonce, payload=payload)
        result = subprocess.run(self.command, input=encoded(value), capture_output=True, timeout=20,
                                **getattr(self, 'transport', {}))
        if result.returncode not in (0, 75, 78) or not result.stdout:
            raise ConnectionError('NL1_RESPONSE_UNKNOWN')
        admission.require(len(result.stdout) <= 65536, 'NL1_RESPONSE_SIZE')
        response = json.loads(result.stdout, object_pairs_hook=unique)
        admission.require(response['nonce'] == nonce and response['controller_uid'] == 0, 'NL1_AUTHENTICATION')
        if result.returncode:
            admission.require(response.get('result') == 'REFUSED' and response.get('incomplete') is True and
                              re.fullmatch('[A-Z][A-Z0-9_]{1,80}', response['reason']), 'NL1_REFUSAL_SHAPE')
            if result.returncode == 75 and response.get('retryable') is True:
                raise ConnectionError(response['reason'])
            raise ValueError(response['reason'])
        return response


class Handoff:
    def __init__(self, root, mailbox):
        self.replacement = replace.Replacement(root)
        self.root, self.mailbox = Path(root), mailbox
        admission.require(self.replacement.plan.get('handoff') is True, 'RESTART_GUARDED_PLAN_REQUIRED')

    def read(self, name):
        return json.loads(owned(self.root / (name + '.json'), os.geteuid()), object_pairs_hook=unique)

    def record(self, name, **values):
        self.replacement.record(name, **values)

    def observe(self):
        response = self.mailbox.call('observe')
        observed = response['observed']
        admission.require(response.get('unit_verified') is True and response.get('controller_uid') == os.geteuid(),
                          'INDEPENDENT_MAILBOX_READBACK')
        startup_closed = observed.get('closed_before_publication') is True and observed.get('restart_defaults_closed') is True
        admission.require((startup_closed or observed.get('live_adoption') is True) and
                          response.get('restart_guard_verified') is True and observed.get('capture_permitted') is False,
                          'PERSISTENT_MAILBOX_GUARD_REQUIRED')
        admission.require(observed.get('root_owned_manifest') is (os.geteuid() == 0), 'MAILBOX_MANIFEST_AUTHORITY')
        witness.validate_ticket(observed['ticket'], self.replacement.plan, replace.digest(self.root / 'plan.json'))
        return response

    def reclosure(self):
        saved = self.read('handoff-ticket')['ticket']
        response = self.observe()
        ticket = response['observed']['ticket']
        admission.require(all(ticket[name] == saved[name] for name in
                              ('generation', 'manifest_sha256', 'owner_binding_sha256', 'replacement_plan_sha256',
                               'support_public_sha256')), 'MAILBOX_GENERATION_CHANGED')
        self.mailbox.call('reclose', dict(action='RECLOSE', ticket=ticket))
        response = self.observe()
        observed = response['observed']
        fence = observed['fence']
        admission.require(observed['ticket'] == ticket and fence['new_link_admission'] == 'CLOSED' and
                          fence['opening_invalidated'] is True, 'MAILBOX_RECLOSURE_UNCONFIRMED')
        if not fence['in_process_drained'] or fence['accepted_target_work'] != 0:
            return None
        return dict(result='CLOSED_DRAINED_INVALIDATED', reservation_ticket_sha256=witness.sha(saved),
                    plan_sha256=replace.digest(self.root / 'plan.json'), readback_sha256=witness.sha(response),
                    mailbox_process=ticket['process'], nonce=response['nonce'], fresh_readback=True,
                    capture_permitted=False)

    def recover(self):
        self.record('handoff-recovery-intent', data_restore_allowed=False, capture_permitted=False)
        proof = self.reclosure()
        if proof is None:
            return 'WAITING_MAILBOX_DRAIN'
        if not self.replacement.has('handoff-reserved'):
            return self.replacement.run(recover=True)
        def fresh():
            proof = self.reclosure()
            admission.require(proof is not None, 'MAILBOX_DRAIN_CHANGED')
            return proof
        return self.replacement.recover_reclosed(fresh)

    def candidate_failure(self):
        self.record('handoff-recovery-intent', reason='CANDIDATE_NOT_LIVE', data_restore_allowed=False)
        self.reclosure()
        return 'MANUAL_RECONCILIATION_REQUIRED'

    def pause(self):
        self.record('handoff-pause-intent', notice_queue_preserved=True, capture_permitted=False)
        if self.reclosure() is None:
            return 'WAITING_MAILBOX_DRAIN'
        self.replacement.verify(self.replacement.validate())
        self.record('handoff-paused', notice_queue_preserved=True, capture_permitted=False)
        return 'SUPPORT_IDENTITY_PAUSED'

    def run(self, recover=False, pause=False):
        directory = self.root / 'handoff-controller'
        directory.mkdir(mode=0o700, exist_ok=True)
        with replace.controller_lock(directory):
            if self.replacement.terminal_failure():
                return 'MANUAL_RECONCILIATION_REQUIRED'
            if self.replacement.has('handoff-ticket') and (recover or self.replacement.has('handoff-recovery-intent')):
                return self.recover()
            if self.replacement.has('handoff-pause-intent'):
                return self.pause()
            if pause:
                admission.require(self.replacement.has('handoff-open'), 'HANDOFF_NOT_OPEN')
                return self.pause()
            response = self.observe()
            observed = response['observed']
            ticket = observed['ticket']
            if not self.replacement.has('handoff-ticket'):
                fence = observed['fence']
                admission.require(fence['new_link_admission'] == 'CLOSED' and fence['in_process_drained'] is True and
                                  fence['accepted_target_work'] == 0 and not fence['opening_invalidated'],
                                  'CURRENT_CLOSED_DRAINED_MAILBOX_REQUIRED')
                self.record('handoff-ticket', ticket=ticket, readback_sha256=witness.sha(response),
                            capture_permitted=False)
            if recover:
                return self.recover()
            saved = self.read('handoff-ticket')['ticket']
            if ticket != saved or observed['fence']['opening_invalidated']:
                self.record('handoff-recovery-intent', reason='MAILBOX_RESTART_OR_RECLOSURE', data_restore_allowed=False)
                return self.recover()
            try:
                result = self.replacement.run()
            except (ValueError, OSError):
                return self.candidate_failure()
            if result not in ('ACCEPTED', 'ALREADY_ACCEPTED'):
                if result in ('ROLLED_BACK', 'ABORTED'):
                    self.reclosure()
                return result
            try:
                sampled = witness.sample(self.root, ticket)
            except (ValueError, OSError):
                return self.candidate_failure()
            reservation = self.read('handoff-reserved')
            reservation.pop('at', None)
            if not self.replacement.has('handoff-witness'):
                self.record('handoff-witness', witness=sampled, reservation=reservation)
            retained = self.read('handoff-witness')
            admission.require(all(sampled[name] == retained['witness'][name] for name in
                                  ('candidate_binding', 'reservation_sha256', 'accepted_sha256', 'evidence_sha256')),
                              'HANDOFF_CANDIDATE_CHANGED')
            request = dict(action='OWNER_HANDOFF', ticket=ticket, witness=retained['witness'],
                           reservation=retained['reservation'])
            self.record('handoff-consume-intent', request_sha256=witness.sha(request), capture_permitted=False)
            self.mailbox.call('consume', request)
            response = self.observe()
            opened = response['observed']
            admission.require(opened['ticket'] == ticket and opened['fence']['new_link_admission'] == 'OPEN_LOCAL_ONLY'
                              and not opened['fence']['opening_invalidated'] and
                              opened['consumed']['request_sha256'] == witness.sha(request), 'HANDOFF_OPEN_UNCONFIRMED')
            try:
                current = witness.sample(self.root, ticket)
            except (ValueError, OSError):
                return self.candidate_failure()
            admission.require(current['candidate_binding'] == sampled['candidate_binding'], 'HANDOFF_CANDIDATE_CHANGED')
            self.record('handoff-open', readback_sha256=witness.sha(response), candidate_binding=current['candidate_binding'],
                        capture_permitted=False, legacy_uncertainty_preserved=True)
            return 'HANDOFF_OPEN_CAPTURE_DENIED'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--mailbox-channel', required=True, type=Path)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--recover', action='store_true')
    action.add_argument('--pause', action='store_true')
    args = parser.parse_args()
    try:
        result = Handoff(args.run, SSHMailbox(args.mailbox_channel)).run(recover=args.recover, pause=args.pause)
    except (subprocess.TimeoutExpired, OSError) as error:
        print(json.dumps(dict(result='RESPONSE_UNKNOWN', reason=type(error).__name__, capture_permitted=False)))
        raise SystemExit(75) from None
    except ValueError as error:
        reason = str(error)
        print(json.dumps(dict(result='MANUAL_RECONCILIATION_REQUIRED', capture_permitted=False,
                              reason=reason if re.fullmatch('[A-Z][A-Z0-9_]{1,80}', reason) else type(error).__name__)))
        raise SystemExit(78) from None
    terminal = args.run / 'terminal-failure.json'
    if result == 'MANUAL_RECONCILIATION_REQUIRED' and terminal.exists():
        print(owned(terminal, os.geteuid()).decode())
    else:
        print(json.dumps(dict(result=result, capture_permitted=False)))
    if result.startswith('WAITING_'):
        raise SystemExit(75)
    if result == 'MANUAL_RECONCILIATION_REQUIRED':
        raise SystemExit(78)


if __name__ == '__main__':
    main()
