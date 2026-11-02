"""Offline Ubuntu container install/config/permissions check, not live service acceptance."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess


def main():
    if not Path('/.dockerenv').is_file() or os.geteuid() != 0:
        raise ValueError('isolated root container required')
    spec = importlib.util.spec_from_file_location('standby', '/source/standby-node.py')
    node = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(node)
    real_command = node.command
    def command(argv, **kwargs):
        if argv[:2] == ['systemctl', 'show']:
            return b'not-found\n'
        if argv[0] in ('ss', 'iptables-save') or argv[:2] == ['systemctl', 'daemon-reload']:
            return b''
        if argv == ['ip', '-j', '-4', 'route']:
            return b'[{"dst":"default","dev":"eth0"}]'
        return real_command(argv, **kwargs)
    node.command = command
    custody = Path('/qualification-source')
    custody.mkdir(mode=0o700)
    files = {}
    for name in (*node.NATIVE, 'standby-node.py', 'awg-gateway.py'):
        raw = Path('/source', name).read_bytes()
        node.write(custody / name, raw)
        files[name] = hashlib.sha256(raw).hexdigest()
    manifest = dict(schema=1, target='1.1.1.1', operation_id='offline-standby-install-01',
                    source_commit='1' * 40, files=files)
    os.umask(0o077)
    node.manifest_check(manifest, custody, manifest['target'])
    node.prepare(manifest, custody)
    node.require(json.loads((node.STATE / 'prepared.json').read_bytes())['result'] == 'PREPARED_UNPUBLISHED')
    result = subprocess.run(['runuser', '-u', 'fc-friends', '--', '/bin/cat',
                             str(node.ROOT / 'friends-awg/server.conf')], capture_output=True)
    node.require(result.returncode != 0)
    node.require(not node.SYSCTL.exists())
    print(json.dumps(dict(result='PASS', native_config_test='PASS', unit_verify='PASS',
        tcp_service_user_read='PASS', awg_private_denial='PASS', real_service_start='NOT_RUN',
        real_network_rules='NOT_RUN', external_data_plane='NOT_RUN')))


if __name__ == '__main__':
    main()
