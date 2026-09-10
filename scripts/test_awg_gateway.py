"""Isolated real AWG 2 handshake/data test; no host routes or published ports."""
import base64
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time

IMAGE=os.environ.get('FC_AWG_TEST_IMAGE','family-connect-amneziawg:2-pilot1')

def run(*args,input=None):
    p=subprocess.run(args,input=input,capture_output=True,text=True,timeout=30)
    if p.returncode:raise RuntimeError('Isolated AWG test command failed')
    return p.stdout.strip()

def main():
    prefix='fc-awg-test-'+secrets.token_hex(4)
    server,client=prefix+'-server',prefix+'-client'
    containers=[]
    with tempfile.TemporaryDirectory(prefix=prefix) as directory:
        folder=Path(directory)
        def pair():
            private=run('docker','run','--rm','--network','none','--entrypoint','awg',IMAGE,'genkey')
            public=run('docker','run','--rm','-i','--network','none','--entrypoint','awg',IMAGE,'pubkey',input=private)
            return private,public
        server_key,server_pub=pair();client_key,client_pub=pair()
        params='Jc = 4\nJmin = 40\nJmax = 100\nS1 = 32\nS2 = 64\nS3 = 16\nS4 = 8\nH1 = 1000-1100\nH2 = 2000-2100\nH3 = 3000-3100\nH4 = 4000-4100\n'
        config='[Interface]\nPrivateKey = '+server_key+'\nListenPort = 51821\n'+params+'[Peer]\nPublicKey = '+client_pub+'\nAllowedIPs = 10.78.0.2/32\n'
        fd=os.open(folder/'server.conf',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,'w') as f:f.write(config)
        run('docker','network','create','--internal',prefix)
        try:
            run('docker','run','-d','--name',server,'--network',prefix,'--cap-add','NET_ADMIN',
                '--device','/dev/net/tun','-v',str(folder)+':/keys:ro',IMAGE)
            containers.append(server)
            for _ in range(15):
                try:run('docker','exec',server,'awg','show','awg0','public-key');break
                except RuntimeError:time.sleep(0.5)
            else:raise RuntimeError('AWG server did not start')
            address=json.loads(run('docker','inspect',server))[0]['NetworkSettings']['Networks'][prefix]['IPAddress']
            run('docker','run','-d','--name',client,'--network',prefix,'--cap-add','NET_ADMIN',
                '--device','/dev/net/tun','--entrypoint','sleep',IMAGE,'120')
            containers.append(client)
            config='[Interface]\nPrivateKey = '+client_key+'\n'+params+'[Peer]\nPublicKey = '+server_pub+'\nEndpoint = '+address+':51821\nAllowedIPs = 10.78.0.1/32\n'
            run('docker','exec','-i',client,'python3','-c',
                "import os,sys;fd=os.open('/tmp/client.conf',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(fd,sys.stdin.buffer.read());os.close(fd)",input=config)
            run('docker','exec',client,'amneziawg-go','awg0')
            run('docker','exec',client,'awg','setconf','awg0','/tmp/client.conf')
            run('docker','exec',client,'ip','address','add','10.78.0.2/24','dev','awg0')
            run('docker','exec',client,'ip','link','set','awg0','up')
            run('docker','exec',server,'nft','add','rule','inet','family_connect_awg','input',
                'iifname','awg0','tcp','dport','8080','accept')
            run('docker','exec','-d',server,'python3','-c',
                "from http.server import BaseHTTPRequestHandler,HTTPServer\nclass H(BaseHTTPRequestHandler):\n def do_GET(self):\n  self.send_response(200);self.end_headers();self.wfile.write(b'family-connect-awg-test')\n def log_message(self,*args):pass\nHTTPServer(('10.78.0.1',8080),H).serve_forever()")
            time.sleep(0.5)
            body=run('docker','exec',client,'curl','--noproxy','*','--interface','awg0','--fail',
                     '--silent','--max-time','10','http://10.78.0.1:8080/')
            assert body=='family-connect-awg-test'
            stamp=run('docker','exec',client,'awg','show','awg0','latest-handshakes').split()[1]
            assert 0<=time.time()-int(stamp)<30
            print('PASS: isolated AWG 2 handshake and bound HTTP transfer; no host routes or published ports.')
        finally:
            for name in reversed(containers):run('docker','rm','-f',name)
            run('docker','network','rm',prefix)

if __name__=='__main__':main()
