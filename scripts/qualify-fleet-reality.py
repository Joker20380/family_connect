"""Exact-native synthetic loopback TLS check, never a node acceptance receipt."""

import argparse
import base64
import os
from pathlib import Path
import platform
import secrets
import subprocess
import tempfile
import time
from types import SimpleNamespace
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from fleet.bundle import verify
from fleet.contracts import canonical, digest, fail, load
from fleet.operator_harness import Harness, command, stop_process
from fleet.private_files import write_private
from fleet.role_config import SNI, tcp_config


def qualify(package, output):
    if (not Path('/.dockerenv').exists() or platform.machine()!='x86_64'
            or 'VERSION_ID="24.04"' not in Path('/etc/os-release').read_text()):
        fail('isolated_ubuntu24_container_required')
    os.umask(0o077)
    key=Ed25519PublicKey.from_public_bytes((package/'bundle.pub').read_bytes())
    manifest,contents=verify(package/'A-first',key)
    repository=Path(__file__).resolve().parents[1]
    for name in ('role_config.py','operator_harness.py'):
        if (repository/'fleet'/name).read_bytes()!=contents['runtime/fleet/'+name]:
            fail('loopback_qualification_source_binding')
    private=X25519PrivateKey.generate()
    def encoded(value):
        return base64.urlsafe_b64encode(value).decode().rstrip('=')
    material=dict(scope='DISPOSABLE_FLEET_REHEARSAL',uuid=str(uuid.uuid4()),short_id=secrets.token_hex(8),
        private_key=encoded(private.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption())),
        public_key=encoded(private.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)),sni=SNI,destination=SNI+':443')
    with tempfile.TemporaryDirectory(prefix='fc-synthetic-reality-') as temporary:
        directory=Path(temporary)
        write_private(directory/'xray',contents['bin/xray'],mode=0o500)
        config=load(tcp_config(canonical(material)))
        config['inbounds'][0]['listen']='127.0.0.1'
        write_private(directory/'server.json',canonical(config))
        write_private(directory/'client.json',canonical({name:material[name] for name in ('scope','uuid','public_key','short_id','sni')}))
        command([str(directory/'xray'),'run','-test','-config',str(directory/'server.json')])
        process=subprocess.Popen([str(directory/'xray'),'run','-config',str(directory/'server.json')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            time.sleep(0.5)
            if process.poll() is not None:
                fail('loopback_server_start')
            def web(prefix):
                command(['curl','--silent','--show-error','--fail','--max-time','30',*prefix,'https://example.com/'])
            fixture=SimpleNamespace(config={'tcp_client':str(directory/'client.json')},native=directory,target='127.0.0.1',web=web)
            Harness.tcp(fixture,directory)
        finally:
            stop_process(process)
    result=dict(schema=1,scope='SYNTHETIC_LOOPBACK_REALITY_QUALIFICATION',source_commit=manifest['source_commit'],
        qualification_source_sha256=digest(Path(__file__).read_bytes()),native_sha256=digest(contents['bin/xray']),
        platform='Ubuntu24.04/x86_64',sni=SNI,loopback_https='PASS',node_acceptance='NOT_RUN',node_writes=0,
        production_writes=0,catalog_publications=0,user_invitations=0,paid_events=0,phone_actions=0)
    write_private(output,canonical(result))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    arguments=parser.parse_args()
    print(canonical(qualify(arguments.package,arguments.output)).decode())
