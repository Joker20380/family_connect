"""Explicit opt-in integration: disposable, isolated WireGuard Docker namespace.

No host routes, published ports or production gateways. Run with Docker access:
python -m scripts.test_product_gateway
"""
import base64
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time

from control.product.gateway_adapter import DockerGateway
from device_identity.device import DeviceIdentity


def main():
    name='fc-peer-test-'+secrets.token_hex(6)
    def docker(*args):
        return subprocess.run(['docker',*args],check=True,capture_output=True,text=True,timeout=10).stdout.strip()
    with tempfile.TemporaryDirectory(prefix='fc-peer-integration-') as temporary:
        keys=Path(temporary)
        server=DeviceIdentity.generate();device=DeviceIdentity.generate();unmanaged=DeviceIdentity.generate()
        (keys/'server.key').write_text(base64.b64encode(server._wireguard_key.private_bytes_raw()).decode())
        (keys/'server.key').chmod(0o600)
        # The image entrypoint is replaced; only an isolated wg0 is created.
        command='ip link add wg0 type wireguard; wg set wg0 private-key /keys/server.key listen-port 51820; touch /tmp/ready; exec sleep 300'
        try:
            docker('run','-d','--name',name,'--network','none','--cap-add','NET_ADMIN',
                   '-v',f'{keys}:/keys:ro','--entrypoint','sh',os.environ.get('FC_GATEWAY_TEST_IMAGE','family-connect-wireguard:reconciliation-test'),'-ec',command)
            for _ in range(30):
                try:docker('exec',name,'test','-f','/tmp/ready');break
                except subprocess.CalledProcessError:time.sleep(.1)
            else:raise RuntimeError('isolated gateway not ready')
            docker('exec',name,'wg','set','wg0','peer',unmanaged.wireguard_public_key,'allowed-ips','10.77.0.3/32')
            adapter=DockerGateway(container=name,keys=keys)
            candidate=dict(public_key=server.wireguard_public_key,port=51820)
            def apply(present):adapter.apply(device.reference,device.wireguard_public_key,
                ['10.77.0.4/32','fd77:92::4/128'],present=present,gateway=candidate)
            apply(True);apply(True)
            assert device.wireguard_public_key in docker('exec',name,'wg','show','wg0','peers')
            # Replay saved files after deleting/recreating the interface.
            restart='ip link del wg0; ip link add wg0 type wireguard; wg set wg0 private-key /keys/server.key listen-port 51820; for peer in /keys/peers/*.conf; do [ ! -f "$peer" ] || wg addconf wg0 "$peer"; done'
            docker('exec',name,'sh','-ec',restart)
            assert device.wireguard_public_key in docker('exec',name,'wg','show','wg0','peers')
            docker('exec',name,'wg','set','wg0','peer',unmanaged.wireguard_public_key,'allowed-ips','10.77.0.3/32')
            apply(False);apply(False)
            # A delayed command from the prior install reads current absent intent.
            docker('exec',name,'/usr/local/bin/family-connect-peer-sync',device.reference,device.wireguard_public_key)
            assert docker('exec',name,'wg','show','wg0','peers')==unmanaged.wireguard_public_key
            docker('exec',name,'sh','-ec',restart)
            assert device.wireguard_public_key not in docker('exec',name,'wg','show','wg0','peers')
            print(json.dumps({'wireguard_install_remove_restart':'passed','unmanaged_peer_preserved':True}))
        finally:
            subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=10)


if __name__=='__main__':main()
