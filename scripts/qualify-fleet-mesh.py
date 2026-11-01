"""Offline exact-native MESH directory/guard qualification, not data-plane evidence."""

import argparse
import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from pathlib import Path
import platform
import ssl
import tempfile
import threading
import time

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from fleet.bundle import verify
from fleet.contracts import canonical, digest, fail, load
from fleet.material_factory import generate, raw_public
from fleet.operator_harness import command
from fleet.private_files import read_private, write_private


def qualify(package, output):
    if (not Path('/.dockerenv').exists() or platform.machine()!='x86_64'
            or 'VERSION_ID="24.04"' not in Path('/etc/os-release').read_text()):
        fail('isolated_ubuntu24_container_required')
    os.umask(0o077)
    manifest,contents=verify(package/'A-first',Ed25519PublicKey.from_public_bytes((package/'bundle.pub').read_bytes()))
    repository=Path(__file__).resolve().parents[1]
    for name in ('operator_harness.py','material_factory.py'):
        if (repository/'fleet'/name).read_bytes()!=contents['runtime/fleet/'+name]:
            fail('mesh_qualification_source_binding')
    probe=package/'operator-probe-first'
    metadata=load(contents['metadata/operator-probe.json'])
    if probe.is_symlink() or probe.stat().st_nlink!=1 or digest(probe.read_bytes())!=metadata['sha256']:
        fail('mesh_qualification_probe_binding')
    private=Ed25519PrivateKey.generate()
    public=raw_public(X25519PrivateKey.generate())+raw_public(private)
    now=int(time.time())
    slots,clients=generate('fleet-rehearsal-offline',public,private,
        canonical(dict(scope='DISPOSABLE_FLEET_REHEARSAL',token='synthetic-not-a-provider-token')),issued_at=now-1,expires_at=now+300)
    credentials=load(slots['mesh-material'])['credentials']
    def timestamp(value):
        return datetime.datetime.fromtimestamp(value,datetime.timezone.utc).isoformat().replace('+00:00','Z')
    directory=canonical(dict(version=1,family=credentials['family'],issued_at=timestamp(now-1),expires_at=timestamp(now+240),
        seeds=[dict(transport='telemost-webrtc',join_url='https://telemost.yandex.ru/j/12345678901234',gateway=credentials['gateway'])]))
    requests=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*arguments):
            pass

        def do_GET(self):
            requests.append(('GET',self.path))
            if self.path!='/v1/bootstrap/directory':
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(directory)))
            self.end_headers()
            self.wfile.write(directory)

        def do_POST(self):
            requests.append(('POST',self.path))
            self.send_error(404)

    with tempfile.TemporaryDirectory(prefix='fc-offline-mesh-') as temporary:
        root=Path(temporary)
        for name,field in (('certificate.pem','certificate'),('key.pem','private_key'),('authority.pem','authority')):
            write_private(root/name,credentials[field].encode())
        profile=root/'client.json'
        write_private(profile,clients['mesh-profile.json'])
        write_private(root/'mux.json',canonical(dict(mode='public',seconds=0,port=0)))
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version=context.maximum_version=ssl.TLSVersion.TLSv1_3
        context.load_cert_chain(root/'certificate.pem',root/'key.pem')
        context.load_verify_locations(root/'authority.pem')
        context.verify_mode=ssl.CERT_REQUIRED
        context.set_alpn_protocols(['http/1.1'])
        server=HTTPServer(('127.0.0.1',0),Handler)
        server.socket=context.wrap_socket(server.socket,server_side=True)
        worker=threading.Thread(target=server.serve_forever,daemon=True)
        worker.start()
        endpoint='https://127.0.0.1:'+str(server.server_port)
        prefix=[str(probe),'-family-config',str(profile),'-duration','5s']
        try:
            refreshed=command([*prefix,'-broker-url',endpoint,'-bootstrap-cache',str(root/'cache.json'),'-bootstrap-refresh'])
            if (load(refreshed.stdout)['event']!='bootstrap_cache_stored'
                    or load(read_private(root/'cache.json'))!=load(directory)):
                fail('mesh_directory_fixture_rejected')
            rejected=command([*prefix,'-broker-url',endpoint,'-mux-config',str(root/'mux.json')],check=False)
            if rejected.returncode!=1 or rejected.stderr.strip()!=b'control_rejected':
                fail('mesh_directory_only_endpoint_not_enforced')
            guarded=command([*prefix,'-broker-url','https://127.0.0.1:1','-bootstrap-cache',str(root/'missing.json'),
                '-mux-config',str(root/'mux.json')],check=False)
            if (guarded.returncode!=1 or guarded.stderr.strip()!=b'cache_unavailable'
                    or load(guarded.stdout)['event']!='bootstrap_normal_control_unavailable'):
                fail('mesh_guarded_bootstrap_entry_rejected')
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)
        if requests!=[('GET','/v1/bootstrap/directory'),('POST','/v1/rooms/challenge')]:
            fail('mesh_fixture_request_contract')
    result=dict(schema=1,scope='OFFLINE_MESH_DIRECTORY_QUALIFICATION',source_commit=manifest['source_commit'],
        qualification_source_sha256=digest(Path(__file__).read_bytes()),operator_probe_sha256=metadata['sha256'],
        platform='Ubuntu24.04/x86_64',mutual_tls_directory='PASS',direct_room_api_rejected='PASS',guarded_bootstrap_entry='PASS',
        node_acceptance='NOT_RUN',telemost_contact='NOT_RUN',original_probe_used=False,node_writes=0,
        production_writes=0,catalog_publications=0,user_invitations=0,paid_events=0,phone_actions=0)
    write_private(output,canonical(result))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    arguments=parser.parse_args()
    print(canonical(qualify(arguments.package,arguments.output)).decode())
