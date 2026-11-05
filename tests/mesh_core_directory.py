import json
from pathlib import Path
import shlex
import socket
import subprocess
import sys
import time
import zipfile

from online_package_stand import private_file
from scripts import package_online_renewal as package


def publish_seed_directories(stand, snapshot):
    with zipfile.ZipFile(snapshot) as archive:
        manifest = json.loads(archive.read('source-manifest.json'))
    assert manifest['source_commit'] == stand.manifest['source_commit']
    assert manifest['entrypoint'] == 'control.friends.profile_snapshot'
    root = stand.root/'snapshot-routes'
    root.mkdir(mode=0o700)
    capsule = private_file(root/'snapshot.pyz', snapshot.read_bytes())
    wrapper = private_file(root/'snapshot-route.py', (package.ROOT/'tests/fixtures/mesh_snapshot.py').read_bytes())
    host_key = stand.root/'ssh/host'
    client_key = stand.root/'ssh/client'
    public = client_key.with_suffix('.pub').read_text().strip()
    known = private_file(root/'known_hosts', b''.join(
        (address+' '+host_key.with_suffix('.pub').read_text()).encode() for address in ('127.0.0.2', '127.0.0.3')))
    routes = {}
    for slot, address, gateway_id in (('NL', '127.0.0.2', 'nl-amsterdam-1'), ('NL2', '127.0.0.3', 'nl-amsterdam-2')):
        config = json.loads(stand.configs[slot].read_bytes())
        helper = private_file(root/(slot+'-helper'), ('#!/bin/sh\nexec '+shlex.join(
            [sys.executable, '-E', '-s', '-B', str(stand.extracted/'renewal/node.py'), '--config', str(stand.configs[slot])])+'\n').encode())
        helper.chmod(0o750)
        binding = private_file(root/(slot+'-snapshot.json'), package.encode(dict(schema=1,
            profile_locator=config['profile_locator'], profile_locator_sha256=config['profile_locator_sha256'],
            renewal_helper=str(helper), renewal_helper_sha256=package.digest(helper.read_bytes()),
            renewal_helper_metadata=dict(uid=0, gid=0, mode=0o750))))
        command = shlex.join([sys.executable, '-I', '-B', str(wrapper), str(capsule), str(binding)])
        keys = private_file(root/(slot+'-authorized'), ('restrict,command="'+command+'" '+public+'\n').encode())
        ssh_config = private_file(root/(slot+'-sshd'), ('ListenAddress '+address+'\nPort 22\nHostKey '+str(host_key)+
            '\nAuthorizedKeysFile '+str(keys)+'\nPermitRootLogin prohibit-password\nPasswordAuthentication no\n'
            'KbdInteractiveAuthentication no\nUsePAM no\nLogLevel ERROR\nPidFile '+str(root/(slot+'-pid'))+'\n').encode())
        process = subprocess.Popen(['/usr/sbin/sshd', '-D', '-e', '-f', str(ssh_config)],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        stand.processes.append(process)
        deadline = time.monotonic()+5
        while True:
            try:
                with socket.create_connection((address, 22), timeout=.1):
                    break
            except OSError:
                assert process.poll() is None and time.monotonic() < deadline
                time.sleep(.02)
        routes[gateway_id] = dict(gateway=stand.fleet.identities[slot],
            ssh=dict(key=str(client_key), known_hosts=str(known), target='root@'+address))
    configuration = json.loads(stand.configs['RU'].read_bytes())
    configuration['snapshot_target'] = 'root@127.0.0.2'
    private_file(stand.configs['RU'], package.encode(configuration))
    route_file = private_file(root/'routes.json', package.encode(dict(schema=1, gateways=routes)))
    result = subprocess.run([sys.executable, '-E', '-s', '-B', str(stand.extracted/'renewal/scheduled_evaluate.py'),
        '--config', str(stand.configs['RU']), '--ssh-key', str(client_key), '--known-hosts', str(known),
        '--gateway-routes', str(route_file), '--directory-only'], cwd=stand.root, capture_output=True, timeout=60)
    receipt = json.loads(result.stdout)
    assert result.returncode == 0 and receipt['result'] == 'DIRECTORIES_SYNCED', receipt
    for slot in ('NL', 'NL2'):
        assert stand.fleet.nodes['RU'].directory_destination(slot).read_bytes() == (stand.fleet.nodes[slot].live/'directory.json').read_bytes()
    return dict(result=receipt, snapshot_sha256=package.digest(capsule.read_bytes()),
                snapshot_source=manifest['source_commit'], route_adapter_sha256=package.digest(wrapper.read_bytes()))
