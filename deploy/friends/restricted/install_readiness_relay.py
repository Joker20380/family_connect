"""Install the pinned, stateless readiness extension without changing RNS identity."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from control_plane_cutover import FileCutover, atomic, canonical, digest, read, require


UNIT = 'family-connect-reticulum.service'
BASE = Path('/opt/apps/family_connect/reticulum')
EXPECTED = {
    'reticulum.py': '242169510d0fe902e1c1b2d4952766a11e7817ab462f34eaf8ffd6465320cd9a',
    'runtime.py': 'd51ff8985acae834e67c8dfe30b611dfd6088bafd4c2473ab4a2375987cfb599',
}


def service():
    return dict(line.split('=', 1) for line in subprocess.check_output([
        'systemctl', 'show', UNIT,
        '--property=MainPID,ActiveState,SubState,NRestarts,User,Group,WorkingDirectory,DropInPaths,ExecStart'
    ], text=True, timeout=10).splitlines())


def identity_digest():
    files = sorted((BASE / 'state/identity').rglob('*'))
    return digest(canonical({str(path.relative_to(BASE)): hashlib.sha256(path.read_bytes()).hexdigest()
                             for path in files if path.is_file()}))


def updated_preview_manifest(root, candidate):
    manifest = json.loads(read(root / 'manifest.json'))
    require(manifest.get('schema_version') == 1 and manifest.get('preview') is True)
    files = manifest['files']
    require(manifest['bundle_id'] == digest(json.dumps(files, sort_keys=True).encode()))
    for name, expected in files.items():
        path = Path(name)
        require(not path.is_absolute() and '..' not in path.parts)
        if name in {'provisioning/' + key for key in EXPECTED}:
            require(expected == EXPECTED[path.name])
            require(digest(read(root / path)) in (expected, digest(candidate[path.name])))
        else:
            require(digest(read(root / path)) == expected)
    require(all('provisioning/' + name in files for name in EXPECTED))
    require('provisioning/readiness_relay.py' not in files)
    files = dict(files, **{'provisioning/' + name: digest(raw) for name, raw in candidate.items()})
    return canonical(dict(manifest, files=files, bundle_id=digest(json.dumps(files, sort_keys=True).encode())))


def main():
    os.umask(0o077)
    stage = Path(sys.argv[1]).resolve()
    lock = (stage / 'operator.lock').open('a')
    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    manifest = json.loads(read(stage / 'manifest.json'))
    require(set(manifest) == {'operation', 'files'})
    require(manifest['operation'] == 'existing-users-readiness-relay-20261019-01')
    require(set(manifest['files']) == {'reticulum.py', 'runtime.py', 'readiness_relay.py'})
    candidate = {name: read(stage / name) for name in manifest['files']}
    require(all(digest(raw) == manifest['files'][name] for name, raw in candidate.items()))
    for name, raw in candidate.items():
        compile(raw, name, 'exec')
    state = stage / 'transaction'
    if (state / 'transaction.json').exists():
        raise RuntimeError('EXISTING_INTENT_REQUIRES_READBACK_NOT_AUTOMATIC_RESTART')
    before = service()
    require(before['ActiveState'] == 'active' and before['SubState'] == 'running')
    require(before['User'] == before['Group'] == 'fc-relay')
    require(before['WorkingDirectory'] == str(BASE / 'app') and not before['DropInPaths'])
    command = (str(BASE / 'venv/bin/python') + ' ' + str(BASE / 'app/scripts/run_control_preview.py') +
               ' control serve --state ' + str(BASE / 'state/relay') + ' --identity ' +
               str(BASE / 'state/identity') + ' --rns-config ' + str(BASE / 'state/rns'))
    require('argv[]=' + command + ' ;' in before['ExecStart'])
    app = BASE / 'app/provisioning'
    require(all(digest(read(app / name)) == value for name, value in EXPECTED.items()))
    require(not (app / 'readiness_relay.py').exists())
    require(digest(read(BASE / 'app/scripts/run_control_preview.py')) ==
            '018e56ca0e5eda7c05aa77877c9e5f3c7e0fe14e727253585421679ab9a879f5')
    dropin = Path('/etc/systemd/system/' + UNIT + '.d/90-existing-users-readiness.conf')
    dropin.parent.mkdir(mode=0o755, exist_ok=True)
    require(not dropin.exists())
    override = ('[Service]\nExecStart=\nExecStart=' + command + ' --friends-readiness-relay\n').encode()
    preview = updated_preview_manifest(BASE / 'app', candidate)
    identity = identity_digest()
    transaction = FileCutover(state, manifest)
    intent = transaction.prepare([(app / name, raw, 0o644) for name, raw in candidate.items()] +
                                 [(dropin, override, 0o644), (BASE / 'app/manifest.json', preview, 0o644)])
    atomic(state / 'service-before.json', canonical(before))
    subprocess.run(['systemctl', 'stop', UNIT], check=True, timeout=30)
    try:
        transaction.apply(intent)
        subprocess.run(['systemctl', 'daemon-reload'], check=True, timeout=15)
        subprocess.run(['runuser', '-u', 'fc-relay', '--', str(BASE / 'venv/bin/python'), '-B', '-c',
                        'from provisioning.readiness_relay import ReadinessRelay; from provisioning.reticulum import ReticulumControlProvider'],
                       cwd=BASE / 'app', check=True, timeout=15)
        subprocess.run(['runuser', '-u', 'fc-relay', '--', str(BASE / 'venv/bin/python'), '-B',
                        str(BASE / 'app/scripts/run_control_preview.py'), 'verify'],
                       check=True, stdout=subprocess.DEVNULL, timeout=15)
        atomic(state / 'start-intent.json', canonical({'start_count': 1}))
        subprocess.run(['systemctl', 'start', UNIT], check=True, timeout=30)
        after = service()
        require(after['ActiveState'] == 'active' and after['SubState'] == 'running')
        require('--friends-readiness-relay' in after['ExecStart'])
        require(identity_digest() == identity)
        receipt = dict(result='STARTED_AWAITING_PROTOCOL_READBACK', before_pid=before['MainPID'],
                       after=after, manifest=manifest, identity_unchanged=True)
        atomic(state / 'receipt.json', canonical(receipt))
        print(json.dumps(receipt))
    except Exception:
        subprocess.run(['systemctl', 'stop', UNIT], check=True, timeout=30)
        for index, item in enumerate(intent['files']):
            target = Path(item['path'])
            current = read(target)
            require((None if current is None else digest(current)) in (item['before'], item['after_sha256']))
            if item['before'] is not None:
                atomic(target, read(state / ('before-' + str(index))), 0o644)
            elif target.exists():
                target.unlink()
        subprocess.run(['systemctl', 'daemon-reload'], check=True, timeout=15)
        subprocess.run(['systemctl', 'start', UNIT], check=True, timeout=30)
        atomic(state / 'rollback.json', canonical(dict(result='ORIGINAL_CODE_RESTORED', after=service(),
                                                       identity_unchanged=identity_digest() == identity)))
        raise


if __name__ == '__main__':
    main()
