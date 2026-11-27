"""Read-only accepted-forward-support observer; never resume, reclose, inject code or issue authority."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import socket
import subprocess

from scripts import control_ha_handoff as handoff
from scripts import control_ha_support_replace as replace
from scripts import control_ha_support_witness as witness
from scripts.control_ha_mailbox_startup import encoded, owned, unique


def document(path):
    return json.loads(owned(path, os.geteuid()), object_pairs_hook=unique)


def observe(root, mailbox, *, baseline_variant=None):
    current = replace.Replacement(root, baseline_variant=baseline_variant)
    plan = current.plan
    require = replace.require
    state = current.validate()
    require(not current.has('terminal-failure') and not (current.drain / 'error.json').exists() and
            not (current.drain / 'error.json').is_symlink(),
            'OBSERVER_TERMINAL_EVIDENCE')
    names = ('plan.json', 'accepted.json', 'handoff-open.json', 'handoff-ticket.json', 'resume-request.json')
    history = {name: replace.digest(current.root / name) for name in names}
    accepted = document(current.root / 'accepted.json')
    opened = document(current.root / 'handoff-open.json')
    binding = replace.admission.binding(current.live(state, plan['new_argv']))
    require(binding == accepted['binding'] == opened['candidate_binding'] and
            accepted['archive_sha256'] == replace.CANDIDATE and accepted['legacy_uncertainty_preserved'] is True,
            'OBSERVER_ACCEPTED_BINDING')
    authority = replace.digest(plan['start_authority'])
    require(document(plan['start_authority']) == dict(schema=1, binding=binding, archive_sha256=replace.CANDIDATE),
            'OBSERVER_AUTHORITY_CHANGED')
    require(all(state[key] == value for key, value in replace.SETTINGS.items()) and
            state['NeedDaemonReload'] == 'no', 'PAIRED_SETTINGS')
    attestation = current.participant / ('readback-' + str(binding['pid']) + '-' + binding['start']) / 'result.json'
    retained = json.loads(replace.admission.read(attestation))
    require(retained == dict(binding=binding, uid=plan['uid'], archive_sha256=replace.CANDIDATE,
                            capture_permitted=False), 'OBSERVER_RETAINED_ATTESTATION')
    replace.admission.visible_to(binding['pid'], Path(plan['gate']))
    descriptor = os.open(Path(plan['gate']) / 'operations.lock', os.O_RDONLY | os.O_NOFOLLOW)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            raise ValueError('LIFETIME_GATE_NOT_HELD')
    finally:
        os.close(descriptor)
    collector = None
    if current.baseline_variant == replace.admission.MANDATORY_COLLECTOR_BASELINE and not plan['user']:
        require(plan['baseline'] == '/opt/family-connect-support/app', 'OBSERVER_INSTALLED_PATH')
        code = ('import sys;sys.path.insert(0,"/opt/family-connect-support/app");'
                'from provisioning.owner_capture import configured_gate,INSTALLED_GATE;'
                'gate=configured_gate();assert gate.directory==INSTALLED_GATE;print("MANDATORY_BOUND")')
        result = subprocess.run([plan['executable'], '-I', '-B', '-c', code], capture_output=True,
                                timeout=5, env={'PATH': '/usr/bin:/bin'})
        require(result.returncode == 0 and result.stdout == b'MANDATORY_BOUND\n' and not result.stderr,
                'OBSERVER_COLLECTOR_BINDING')
        collector = 'MANDATORY_BOUND_NO_ENVIRONMENT'
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(5)
        connection.connect(plan['socket'])
        connection.sendall(b'{"operation":"notification_cursor","arguments":{}}\n')
        cursor = json.loads(connection.makefile('rb').readline(16385), object_pairs_hook=unique)
    require(cursor.get('ok') is True, 'OBSERVER_CURSOR_IPC')
    request = document(current.root / 'resume-request.json')['request']
    witness.validate_ticket(request['ticket'], plan, history['plan.json'])
    remote = mailbox.call('observe')
    require(remote.get('unit_verified') is True and remote.get('restart_guard_verified') is True and
            remote.get('controller_uid') == os.geteuid(), 'INDEPENDENT_MAILBOX_REQUIRED')
    observed = remote['observed']
    require(observed['ticket'] == request['ticket'] and observed['capture_permitted'] is False and
            observed['consumed']['request_sha256'] == witness.sha(request), 'OBSERVER_REMOTE_BINDING')
    fence = observed['fence']
    require(fence['new_link_admission'] == 'OPEN_LOCAL_ONLY' and fence['opening_invalidated'] is False and
            fence['accepted_target_work'] == 0 and fence['direct_support_writes_closed'] is True and
            fence['old_links_excluded'] is True, 'OBSERVER_REMOTE_NOT_NORMAL')
    current.validate()
    require(replace.admission.binding(binding['pid']) == binding and
            replace.digest(plan['start_authority']) == authority and
            all(replace.digest(current.root / name) == digest for name, digest in history.items()),
            'OBSERVER_INTERVAL_CHANGED')
    return dict(result='ACCEPTED_SUPPORT_READ_ONLY_NORMAL', binding=binding, archive_sha256=replace.CANDIDATE,
                authority_sha256=authority, history=history, baseline_variant=current.baseline_variant,
                source_pins=replace.admission.COLLECTOR_VARIANTS.get(current.baseline_variant, {}),
                collector_binding=collector, generation=request['ticket']['generation'],
                cursor_sha256=witness.sha(cursor), history_settled=False, capture_permitted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--mailbox-channel', type=Path, required=True)
    parser.add_argument('--collector-baseline', choices=replace.admission.COLLECTOR_VARIANTS)
    args = parser.parse_args()
    print(encoded(observe(args.root, handoff.SSHMailbox(args.mailbox_channel),
                          baseline_variant=args.collector_baseline)).decode())


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        reason = str(error)
        print(encoded(dict(result='READ_ONLY_OBSERVER_REFUSED', reason=reason if re.fullmatch(
            '[A-Z][A-Z0-9_]{1,80}', reason) else type(error).__name__, capture_permitted=False)).decode())
        raise SystemExit(78) from None
