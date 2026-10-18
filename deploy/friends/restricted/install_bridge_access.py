"""Install the pinned v2 control plane; never renew or roll back credentials here."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile


BASE_SOURCE = '5109a7c92ddd1937fe75ed7199866855a8cc20279bc226c35475d4cc81330145'
BASE_API = {'RU': '12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed',
            'NL': '9faaa1c27f534e71774f5b4f34872e87747f391409c4958562694f07f86d64d1'}
ROOT = Path('/opt/apps/family_connect/friends-restricted')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def systemctl(*arguments):
    return subprocess.check_output(['systemctl', *arguments], timeout=45, text=True).strip()


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('--role', choices=('RU', 'NL'), required=True)
    parser.add_argument('--capsule', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    assert os.geteuid() == 0
    assert sha(args.capsule.read_bytes()) == args.sha256
    with tarfile.open(args.capsule, 'r:gz') as archive:
        members = archive.getmembers()
        assert all(member.isfile() and member.size < 5_000_000 for member in members)
        assert len({member.name for member in members}) == len(members)
        content = {member.name: archive.extractfile(member).read() for member in members}
    manifest = json.loads(content['manifest.json'])
    assert set(content) == {'manifest.json', 'bridge-access-v2.pyz'} | {
        'management/' + name for name in manifest['source_files']}
    assert manifest['admission_mode'] == 'all_activated' and manifest['authority_days'] == 90
    assert sha(content['bridge-access-v2.pyz']) == manifest['api_sha256']
    assert all('/' not in name and name.endswith('.py') and sha(content['management/' + name]) == expected
               for name, expected in manifest['source_files'].items())
    canonical = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    assert sha(canonical(manifest['source_files'])) == manifest['source_sha256']
    renewal = ROOT / 'renewal'
    sys.path.insert(0, str(renewal))
    from node import construct
    from credential_renewal import atomic, parse, read_private
    config = parse(read_private(renewal / 'node.json'))
    assert config['role'] == args.role and config['source_sha256'] == BASE_SOURCE
    assert config['api_sha256'] == BASE_API[args.role]
    node, source = construct(renewal / 'node.json')
    assert source == BASE_SOURCE and not (node.state / 'owner.json').exists()
    assert not (node.state / 'authority-request.json').exists()
    backup = ROOT / 'bridge-v2-backup-20261018'
    backup.mkdir(mode=0o700, exist_ok=False)
    saved = {'node.json': read_private(renewal / 'node.json')}
    saved.update({name: read_private(renewal / name) for name in config['source_files']})
    if args.role == 'RU':
        controller = parse(read_private(renewal / 'controller.json'))
        record = parse(read_private(Path(controller['coordinator_state']) / 'transaction.json'))
        assert record['state'] == 'COMMITTED' and record['commit_decided']
        saved['controller.json'] = read_private(renewal / 'controller.json')
        saved['admission.json'] = read_private(ROOT / 'admission.json')
        assert set(json.loads(saved['admission.json'])) == {'devices'}
        command = systemctl('show', 'family-connect-friends-http-candidate.service', '--property=ExecStart', '--value')
        assert config['api_archive'] in command and '--port 18086' in command
    for name, raw in saved.items():
        atomic(backup / name, raw)
    receipt = dict(role=args.role, capsule_sha256=args.sha256, source_before=source,
                   source_after=manifest['source_sha256'], state='BACKED_UP', credentials_changed=False)
    atomic(backup / 'installation.json', canonical(receipt))
    if args.role == 'RU':
        systemctl('stop', 'family-connect-credential-renewal.timer')
        active = systemctl('show', 'family-connect-credential-renewal.service', '--property=ActiveState', '--value')
        assert active in ('inactive', 'failed'), 'Renewal still running; reconcile before retry'
    with node.operation.lock():
        assert not (node.state / 'owner.json').exists()
        if args.role == 'RU':
            systemctl('stop', 'family-connect-friends-http-candidate.service')
        receipt['state'] = 'INSTALLING'
        atomic(backup / 'installation.json', canonical(receipt))
        api = ROOT.parent / 'friends-access/bridge-access-v2-20261018.pyz'
        assert not api.exists(), 'Immutable API already exists; inspect instead of overwriting'
        atomic(api, content['bridge-access-v2.pyz'])
        for name in manifest['source_files']:
            atomic(renewal / name, content['management/' + name])
        config.update(api_archive=str(api), api_sha256=manifest['api_sha256'],
                      source_files=manifest['source_files'], source_sha256=manifest['source_sha256'],
                      admission_mode='all_activated')
        if args.role == 'RU':
            atomic(ROOT / 'admission.json', canonical(dict(version=2, eligibility='all_activated')))
        atomic(renewal / 'node.json', canonical(config))
        if args.role == 'RU':
            controller['nl_source_sha256'] = manifest['source_sha256']
            atomic(renewal / 'controller.json', canonical(controller))
            dropin = Path('/etc/systemd/system/family-connect-friends-http-candidate.service.d')
            dropin.mkdir(mode=0o755, exist_ok=True)
            path = dropin / 'zz-bridge-access-v2.conf'
            with path.open('x') as output:
                output.write('[Service]\nExecStart=\nExecStart=/opt/apps/family_connect/friends-access/venv/bin/python -I '
                             + str(api) + ' --port 18086\n')
                output.flush()
                os.fsync(output.fileno())
            systemctl('daemon-reload')
            systemctl('start', 'family-connect-friends-http-candidate.service')
            assert str(api) in systemctl('show', 'family-connect-friends-http-candidate.service', '--property=ExecStart', '--value')
        receipt['state'] = 'INSTALLED_PENDING_COORDINATED_RENEWAL'
        atomic(backup / 'installation.json', canonical(receipt))
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
