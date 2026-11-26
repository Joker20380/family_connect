"""Stage and activate a closed support generation without restarting other mailbox clients."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import subprocess

from scripts import control_ha_legacy_support as admission
from scripts.control_ha_mailbox_control import MailboxControl, sha
from scripts.control_ha_mailbox_generation import GenerationControl
from scripts.control_ha_mailbox_startup import encoded, owned, unique
from scripts.control_ha_support_replace import controller_lock, put


SOURCES = ('control_ha_mailbox_control.py', 'control_ha_mailbox_startup.py', 'control_ha_mailbox_fence.py',
           'control_ha_mailbox_links.py', 'control_ha_legacy_support.py', 'control_ha_mailbox_generation.py')
LIMITS = ('CPUQuotaPerSecUSec', 'MemoryMax', 'KillMode', 'KillSignal', 'SendSIGKILL', 'TimeoutStopUSec')
STATE_ROOT = Path('/opt/apps/family_connect/state-ha02')
UNIT_ROOT = Path('/etc/systemd/system')


def read(path):
    return json.loads(owned(path, os.geteuid()), object_pairs_hook=unique)


def call(controller, action, payload=None):
    return controller.call(dict(action=action, payload=payload, nonce=secrets.token_hex(32)))


def limits(unit):
    raw = subprocess.check_output(['systemctl', 'show', unit, '--property=' + ','.join(LIMITS)], text=True, timeout=10)
    return dict(row.split('=', 1) for row in raw.splitlines())


def save(path, value, gid=None):
    admission.write(path, value)
    if gid is not None:
        os.chown(path, 0, gid)
        path.chmod(0o640)


def prepare(previous_path, root, manifest_path):
    admission.require(os.geteuid() == 0, 'ROOT_GENERATION_REQUIRED')
    previous = MailboxControl(previous_path)
    admission.require(previous.plan['unit'] == 'family-connect-mailbox.service', 'PRODUCTION_MAILBOX_SCOPE')
    root = Path(root).absolute()
    admission.require(root.parent == STATE_ROOT, 'ROLLOVER_PATH_SCOPE')
    manifest = read(manifest_path)
    old = call(previous, 'observe')
    old_manifest = read(previous.plan['manifest'])
    admission.require(manifest['support_public'] == old_manifest['support_public'] and
                      manifest['generation'] != old_manifest['generation'] and
                      manifest['replacement_plan_sha256'] != old_manifest['replacement_plan_sha256'],
                      'NEW_MANIFEST_BINDINGS')
    baseline_limits = limits(previous.plan['unit'])
    admission.require(baseline_limits['CPUQuotaPerSecUSec'] == '1s' and
                      baseline_limits['MemoryMax'] == '805306368', 'NL1_RESOURCE_LIMITS_CHANGED')
    memory = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    admission.require(int(memory['MemAvailable'].split()[0]) >= 262144, 'NL1_MEMORY_PREFLIGHT')
    root.mkdir(mode=0o750)
    os.chown(root, 0, previous.plan['gid'])
    (root / 'scripts').mkdir(mode=0o750)
    os.chown(root / 'scripts', 0, previous.plan['gid'])
    staged = {}
    for name in SOURCES:
        target = root / 'scripts' / name
        put(target, admission.read(Path(__file__).with_name(name)))
        os.chown(target, 0, previous.plan['gid'])
        target.chmod(0o640)
        staged[str(target)] = sha(target)
    application = Path('/opt/apps/family_connect/mailbox-pilot/app')
    admission.require(str(application / 'messenger/server.py') in previous.plan['sources'], 'MAILBOX_APPLICATION_PIN')
    for filename, module in (('startup.py', 'control_ha_mailbox_startup'),
                             ('endpoint.py', 'control_ha_mailbox_generation')):
        content = ('import sys\nsys.path[:0]=' + repr([str(root), str(application)]) + '\nfrom scripts.' + module +
                   ' import main\nmain()\n').encode()
        put(root / filename, content)
        os.chown(root / filename, 0, previous.plan['gid'])
        (root / filename).chmod(0o640)
        staged[str(root / filename)] = sha(root / filename)
    save(root / 'manifest.json', manifest, previous.plan['gid'])
    startup_arguments = list(previous.plan['restart_argv'])
    admission.require(startup_arguments.count('--manifest') == 1 and startup_arguments[:3] ==
                      [previous.plan['argv'][0], '-I', '-B'], 'MAILBOX_STARTUP_ARGUMENTS')
    startup_arguments[3] = str(root / 'startup.py')
    startup_arguments[startup_arguments.index('--manifest') + 1] = str(root / 'manifest.json')
    confs = [Path(filename).name for filename in previous.plan['files'] if filename.endswith('.conf')]
    admission.require(bool(confs), 'MAILBOX_STARTUP_DROPIN')
    dropin = UNIT_ROOT / (previous.plan['unit'] + '.d') / (sorted(confs)[-1][:-5] + '.resume.conf')
    admission.require(not dropin.exists() and len(dropin.name) < 240, 'NEW_MAILBOX_DROPIN_REQUIRED')
    content = ('[Service]\nExecStart=\nExecStart=' + shlex.join(startup_arguments) + '\n').encode()
    put(root / 'startup.conf', content)
    runtime = root / 'control'
    runtime.mkdir(mode=0o750)
    os.chown(runtime, 0, previous.plan['gid'])
    current = dict(previous.plan, restart_argv=startup_arguments, runtime=str(runtime),
                   files={**previous.plan['files'], str(dropin): hashlib.sha256(content).hexdigest()},
                   sources={**previous.plan['sources'], **staged})
    save(root / 'transition.json', current)
    save(root / 'control.json', dict(current, manifest=str(root / 'manifest.json')))
    save(root / 'rollover.json', dict(schema=1, previous=str(Path(previous_path).absolute()),
         previous_sha256=sha(previous_path), dropin=str(dropin), dropin_sha256=hashlib.sha256(content).hexdigest(),
         manifest_sha256=sha(root / 'manifest.json'), limits=baseline_limits,
         prepared_process=old['observed']['ticket']['process'], capture_permitted=False))
    return root


def activate(root):
    root = Path(root).absolute()
    admission.require(os.geteuid() == 0 and root.parent == STATE_ROOT,
                      'ROOT_ROLLOVER_SCOPE')
    with controller_lock(root):
        operation = read(root / 'rollover.json')
        admission.require(operation['schema'] == 1 and sha(operation['previous']) == operation['previous_sha256'] and
                          sha(root / 'manifest.json') == operation['manifest_sha256'] and
                          sha(root / 'startup.conf') == operation['dropin_sha256'], 'ROLLOVER_INPUT_CHANGED')
        previous = MailboxControl(operation['previous'])
        admission.require(limits(previous.plan['unit']) == operation['limits'], 'MAILBOX_LIMITS_CHANGED')
        dropin = Path(operation['dropin'])
        if not dropin.exists():
            old = call(previous, 'observe')
            call(previous, 'reclose', dict(action='RECLOSE', ticket=old['observed']['ticket']))
            reclosed = call(previous, 'observe')
            save(root / ('reclosure-readback-' + secrets.token_hex(8) + '.json'), reclosed)
            fence = reclosed['observed']['fence']
            admission.require(fence['new_link_admission'] == 'CLOSED' and fence['opening_invalidated'] is True and
                              fence['in_process_drained'] is True and fence['accepted_target_work'] == 0,
                              'MAILBOX_BUSY_OR_NOT_INVALIDATED')
            if not (root / 'predecessor-reclosure.json').exists():
                save(root / 'predecessor-reclosure.json', reclosed)
            put(dropin, admission.read(root / 'startup.conf'))
            dropin.chmod(0o644)
        admission.require(sha(dropin) == operation['dropin_sha256'] and
                          (root / 'predecessor-reclosure.json').is_file(), 'ROLLOVER_INSTALL_CHANGED')
        subprocess.run(['systemctl', 'daemon-reload'], capture_output=True, check=True, timeout=10)
        current = GenerationControl(root / 'control.json')
        try:
            response = call(current, 'observe')
        except ValueError as error:
            if str(error) != 'MAILBOX_ACTIVE_MANIFEST':
                raise
            transition = GenerationControl(root / 'transition.json')
            old = call(transition, 'observe')
            call(transition, 'advance', dict(action='ADVANCE_CLOSED_GENERATION', ticket=old['observed']['ticket'],
                 manifest=str(root / 'manifest.json'), manifest_sha256=operation['manifest_sha256']))
            response = call(current, 'observe')
        admission.require(limits(previous.plan['unit']) == operation['limits'], 'MAILBOX_LIMITS_CHANGED')
        observed = response['observed']
        admission.require(observed['ticket']['manifest_sha256'] == operation['manifest_sha256'] and
                          observed['fence']['new_link_admission'] == 'CLOSED' and
                          observed['fence']['in_process_drained'] is True and observed['fence']['accepted_target_work'] == 0 and
                          observed['fence']['opening_invalidated'] is False and observed['consumed'] is None,
                          'NEW_GENERATION_NOT_READY')
        if not (root / 'advanced.json').exists():
            save(root / 'advanced.json', response)
        return response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--prepare-from', type=Path)
    parser.add_argument('--manifest', type=Path)
    args = parser.parse_args()
    if args.prepare_from:
        admission.require(args.manifest is not None, 'MANIFEST_REQUIRED')
        prepare(args.prepare_from, args.root, args.manifest)
        print(encoded(dict(result='GENERATION_PREPARED_NOT_OPEN', capture_permitted=False)).decode())
    else:
        print(encoded(activate(args.root)).decode())


if __name__ == '__main__':
    try:
        main()
    except (TimeoutError, subprocess.TimeoutExpired):
        print(encoded(dict(result='ROLLOVER_RESPONSE_UNKNOWN', capture_permitted=False)).decode())
        raise SystemExit(75) from None
    except Exception as error:
        reason = str(error)
        print(encoded(dict(result='ROLLOVER_REFUSED', capture_permitted=False,
              reason=reason if re.fullmatch('[A-Z][A-Z0-9_]{1,80}', reason) else type(error).__name__)).decode())
        raise SystemExit(78) from None
