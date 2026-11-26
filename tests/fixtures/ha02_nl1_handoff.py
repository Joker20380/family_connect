"""Explicit synthetic NL1 qualification only; never operates the working service."""
import base64
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import secrets
import shlex
import socket
import subprocess
import sys
import time

WORKING = 'family-connect-mailbox.service'
PYTHON = '/opt/apps/family_connect/mailbox-pilot/venv/bin/python'
APP = '/opt/apps/family_connect/mailbox-pilot/app'
FIELDS = ('MainPID', 'ControlPID', 'ActiveState', 'SubState', 'NRestarts', 'FragmentPath', 'DropInPaths',
          'User', 'Group', 'WorkingDirectory', 'ControlGroup')
CONFIG = ('Type', 'ExecStartPre', 'ExecStart', 'Restart', 'RestartUSec', 'TimeoutStopUSec', 'KillMode',
          'UMask', 'NoNewPrivileges', 'ProtectSystem', 'ProtectHome', 'PrivateDevices', 'PrivateTmp',
          'ProtectKernelTunables', 'ProtectKernelModules', 'ProtectControlGroups', 'RestrictSUIDSGID',
          'LockPersonality', 'RestrictAddressFamilies', 'CapabilityBoundingSet', 'ReadWritePaths',
          'Environment', 'MemoryMax', 'TasksMax', 'CPUQuotaPerSecUSec', 'LimitNOFILE',
          'LogRateLimitIntervalUSec', 'LogRateLimitBurst')


def state(unit, fields=FIELDS):
    raw = subprocess.check_output(['systemctl', 'show', unit, '--property=' + ','.join(fields)], text=True)
    return dict(line.split('=', 1) for line in raw.splitlines())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def working():
    observed = state(WORKING)
    assert observed['MainPID'] == '3705' and observed['NRestarts'] == '0'
    assert observed['ActiveState'] == 'active' and observed['SubState'] == 'running'
    files = {name: digest(name) for name in (observed['FragmentPath'], *shlex.split(observed['DropInPaths']))}
    source = {name: digest(Path(APP) / 'messenger' / (name + '.py')) for name in ('relay', 'server', 'codec', 'membership')}
    process = Path('/proc') / observed['MainPID']
    return dict(state=observed, files=files, sources=source,
                configuration_sha256=hashlib.sha256(json.dumps(state(WORKING, CONFIG), sort_keys=True).encode()).hexdigest(),
                process={name: digest(process / name) for name in ('cmdline', 'cgroup')},
                start=(process / 'stat').read_text().rsplit(')', 1)[1].split()[19])


def write(path, raw, uid=0, gid=0, mode=0o640):
    with path.open('xb') as output:
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())
    os.chown(path, uid, gid)
    path.chmod(mode)


def request(runtime, action):
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(30)
        connection.connect(str(runtime / 'control.sock'))
        connection.sendall(json.dumps(dict(action=action)).encode() + b'\n')
        return json.loads(connection.makefile('rb').readline(16384))


def ready(unit, runtime):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            observed = request(runtime, 'status')
            if observed['ticket']['process']['pid'] == int(state(unit)['MainPID']):
                return observed
        except (OSError, ValueError, KeyError):
            pass
        time.sleep(.05)
    raise ValueError('LAB_STARTUP_INCOMPLETE')


def controlled(entry, plan, action, payload=None):
    result = subprocess.run([PYTHON, '-I', '-B', str(entry), '--plan', str(plan)],
        input=json.dumps(dict(action=action, payload=payload, nonce=secrets.token_hex(32))),
        text=True, capture_output=True, timeout=15)
    assert result.returncode == 0, result.stdout[-4096:]
    return json.loads(result.stdout)


def main():
    value = json.loads(sys.stdin.buffer.read(2 * 1024 * 1024))
    assert os.geteuid() == 0 and re.fullmatch('[0-9a-f]{32}', value['identifier'])
    unit = 'fc-ha-mailbox-handoff-fixture-' + value['identifier'] + '.service'
    root = Path('/opt/apps/family_connect/state-ha02') / unit.removesuffix('.service')
    runtime = Path('/run') / ('fc-ha-nl1-' + value['identifier'])
    assert len(os.fsencode(runtime / 'support/control.sock')) < 108
    account = pwd.getpwnam('fc-mailbox')
    assert account.pw_uid == 996 and account.pw_gid == 982
    before = working()
    action = value['action']
    if action == 'prepare':
        assert state(unit, ('LoadState',))['LoadState'] == 'not-found' and not root.exists()
        root.parent.mkdir(mode=0o755, exist_ok=True)
        root.mkdir(mode=0o750)
        os.chown(root, 0, account.pw_gid)
        for name, raw in value['sources'].items():
            relative = Path(name)
            assert not relative.is_absolute() and '..' not in relative.parts and relative.parts[0] in ('scripts', 'tests', 'messenger')
            target = root / relative
            target.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
            for parent in target.parents:
                if parent == root:
                    break
                os.chown(parent, 0, account.pw_gid)
                parent.chmod(0o750)
            write(target, base64.b64decode(raw, validate=True), gid=account.pw_gid)
        runtime.mkdir(mode=0o700)
        os.chown(runtime, account.pw_uid, account.pw_gid)
        sender = runtime / 'support'
        sender.mkdir(mode=0o700)
        os.chown(sender, account.pw_uid, account.pw_gid)
        write(sender / 'synthetic.identity', base64.b64decode(value['synthetic_sender'], validate=True),
              account.pw_uid, account.pw_gid, 0o600)
        initialize = ('import json,sys;from pathlib import Path;import RNS\nroot=Path(sys.argv[1]);'
                      'support=RNS.Identity.from_file(str(root/"support/synthetic.identity"));'
                      'peer=RNS.Identity();(root/"peer").mkdir(mode=0o700);'
                      'peer.to_file(str(root/"peer/synthetic.identity"));'
                      'print(json.dumps([support.get_public_key().hex(),peer.get_public_key().hex()]))')
        publics = json.loads(subprocess.check_output([PYTHON, '-I', '-B', '-c', initialize, str(runtime)],
                                                     user=account.pw_uid, group=account.pw_gid, text=True))
        assert publics[0] == value['manifest']['support_public']
        for name, data in (('allowed.json', publics), ('manifest.json', value['manifest']), ('working-before.json', before)):
            write(root / name, json.dumps(data, sort_keys=True).encode(), gid=account.pw_gid)
        control = root / 'control-runtime'
        control.mkdir(mode=0o750)
        os.chown(control, 0, account.pw_gid)
        responses = runtime / 'control-responses'
        responses.mkdir(mode=0o700)
        os.chown(responses, account.pw_uid, account.pw_gid)
        wakeup = runtime / 'control-ready'
        wakeup.mkdir(mode=0o700)
        os.chown(wakeup, account.pw_uid, account.pw_gid)
        entry = root / 'control-entry.py'
        write(entry, ('import sys\nsys.path[:0]=' + repr([str(root), APP]) + '\n'
                     'from scripts.control_ha_mailbox_control import main\nmain()\n').encode(), gid=account.pw_gid)
        arguments = [PYTHON, '-B', str(root / 'tests/fixtures/mailbox_startup.py'), str(runtime),
                     str(root / 'manifest.json'), str(root / 'allowed.json'), '0']
        properties = dict(Type='simple', Restart='no', User='fc-mailbox', Group='fc-mailbox',
                          PrivateNetwork='yes', PrivateTmp='yes', ProtectSystem='strict', ProtectHome='yes',
                          NoNewPrivileges='yes', UMask='0077', MemoryMax='512M', TasksMax='96', CPUQuota='40%',
                          ReadWritePaths=str(runtime), WorkingDirectory=str(runtime),
                          SendSIGKILL='no', TimeoutStopSec='infinity', RemainAfterExit='yes')
        content = '[Service]\n' + ''.join(name + '=' + item + '\n' for name, item in properties.items())
        content += ('Environment=PYTHONPATH=' + APP + ' FC_TEST_ROOT_HANDOFF=1 PYTHONDONTWRITEBYTECODE=1 ' +
                    'FC_TEST_CONTROL_READY=' + str(wakeup) + '\n')
        content += 'ExecStart=' + ' '.join(arguments) + '\n'
        write(root / 'retained-unit.conf', content.encode())
        write(Path('/run/systemd/system') / unit, content.encode(), mode=0o644)
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        assert working() == before
        subprocess.run(['systemctl', 'start', unit], check=True)
        try:
            observed = ready(unit, runtime)
        except BaseException:
            write(root / 'startup-incomplete.json', json.dumps(dict(complete=False, manager=state(unit))).encode())
            journal = subprocess.check_output(['journalctl', '-u', unit, '-o', 'json', '--no-pager'])
            write(root / 'startup-journal.jsonl', journal, mode=0o600)
            subprocess.run(['systemctl', 'stop', '--no-block', unit], check=True)
            raise
        assert observed['uid'] == account.pw_uid and not observed['manifest_writable']
        current = state(unit)
        files = {name: digest(name) for name in (current['FragmentPath'], *shlex.split(current['DropInPaths']))}
        sources = {str(root / name): digest(root / name) for name in value['sources']}
        sources[str(entry)] = digest(entry)
        sources.update({str(Path(APP) / 'messenger' / (name + '.py')): fingerprint for name, fingerprint in before['sources'].items()})
        plan = dict(schema=1, unit=unit, user=False, manifest=str(root / 'manifest.json'), argv=arguments,
                    restart_argv=arguments, files=files, sources=sources, interpreter=str(Path(PYTHON).resolve()),
                    interpreter_sha256=digest(PYTHON), runtime=str(control), response_directory=str(responses),
                    wakeup_directory=str(wakeup), uid=account.pw_uid, gid=account.pw_gid)
        write(root / 'control.json', json.dumps(plan).encode(), gid=account.pw_gid)
        result = dict(entry=str(entry), plan=str(root / 'control.json'), interpreter=PYTHON, observed=observed,
                      manager_state=state(unit, ('MainPID', 'ControlPID', 'ActiveState', 'SubState', 'NeedDaemonReload')))
    elif action == 'generation':
        assert working() == json.loads((root / 'working-before.json').read_bytes())
        manifest = value['manifest']
        generation = manifest['generation']
        assert re.fullmatch('[0-9a-f]{64}', generation)
        original = json.loads((root / 'control.json').read_bytes())
        observed = controlled(root / 'control-entry.py', root / 'control.json', 'observe')
        controlled(root / 'control-entry.py', root / 'control.json', 'reclose',
                   dict(action='RECLOSE', ticket=observed['observed']['ticket']))
        reclosure = controlled(root / 'control-entry.py', root / 'control.json', 'observe')
        fence = reclosure['observed']['fence']
        assert fence['opening_invalidated'] and fence['in_process_drained'] and fence['accepted_target_work'] == 0
        new_manifest = root / ('manifest-' + generation + '.json')
        write(new_manifest, json.dumps(manifest).encode(), gid=account.pw_gid)
        entry = root / 'generation-entry.py'
        write(entry, ('import sys\nsys.path[:0]=' + repr([str(root), APP]) + '\n'
              'from scripts.control_ha_mailbox_generation import main\nmain()\n').encode(), gid=account.pw_gid)
        arguments = list(original['restart_argv'])
        arguments[4] = str(new_manifest)
        dropins = Path('/run/systemd/system') / (unit + '.d')
        dropins.mkdir(mode=0o755)
        dropin = dropins / 'zz-generation.conf'
        content = ('[Service]\nExecStart=\nExecStart=' + ' '.join(arguments) + '\n').encode()
        write(dropin, content, mode=0o644)
        write(root / 'retained-generation.conf', content)
        transition = dict(original, restart_argv=arguments,
                          files={**original['files'], str(dropin): digest(dropin)},
                          sources={**original['sources'], str(entry): digest(entry)})
        transition_path = root / ('transition-' + generation + '.json')
        current_path = root / ('control-' + generation + '.json')
        write(transition_path, json.dumps(transition).encode(), gid=account.pw_gid)
        write(current_path, json.dumps(dict(transition, manifest=str(new_manifest))).encode(), gid=account.pw_gid)
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        controlled(entry, transition_path, 'advance', dict(action='ADVANCE_CLOSED_GENERATION',
                   ticket=reclosure['observed']['ticket'], manifest=str(new_manifest), manifest_sha256=digest(new_manifest)))
        result = dict(entry=str(entry), plan=str(current_path), interpreter=PYTHON,
                      predecessor_reclosure=reclosure, observed=controlled(entry, current_path, 'observe'))
        write(root / 'generation-result.json', json.dumps(result).encode())
    elif action in ('status', 'support', 'peer'):
        assert working() == json.loads((root / 'working-before.json').read_bytes())
        result = request(runtime, action)
    elif action == 'restart':
        assert working() == json.loads((root / 'working-before.json').read_bytes())
        subprocess.run(['systemctl', 'restart', unit], check=True)
        result = ready(unit, runtime)
    elif action == 'stop':
        assert working() == json.loads((root / 'working-before.json').read_bytes())
        request(runtime, 'stop')
        subprocess.run(['systemctl', 'stop', unit], check=True)
        current = state(unit)
        assert current['MainPID'] == current['ControlPID'] == '0'
        path = Path('/run/systemd/system') / unit
        assert path.read_bytes() == (root / 'retained-unit.conf').read_bytes()
        dropins = path.with_name(path.name + '.d')
        if dropins.exists():
            assert list(dropins.iterdir()) == [dropins / 'zz-generation.conf']
            assert (dropins / 'zz-generation.conf').read_bytes() == (root / 'retained-generation.conf').read_bytes()
            (dropins / 'zz-generation.conf').unlink()
            dropins.rmdir()
        path.unlink()
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        result = dict(stopped=True, data_retained=True)
    else:
        raise ValueError('UNKNOWN_LAB_ACTION')
    assert working() == before
    print(json.dumps(dict(result=result, working_unchanged=True)), flush=True)


if __name__ == '__main__':
    main()
