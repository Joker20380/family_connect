"""Isolated real AWG 2/3.1 handshake/data test; no host routes or published ports."""
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
    modern=os.environ.get('FC_AWG_TEST_PROTOCOL')=='3.1'
    client_address='10.78.42.254' if modern else '10.78.0.2'
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
        if modern:
            params='Jc = 4\nJmin = 40\nJmax = 100\n'+''.join(f'S{i} = 32\nH{i} = {i}\n' for i in range(1,5))+'HeaderProtectionKey = '+base64.b64encode(secrets.token_bytes(32)).decode()+'\nContentPaddingAddition = 0-64\nRandomTrailers = on\nDisableCookies = off\n'
        config='[Interface]\nPrivateKey = '+server_key+'\nListenPort = 51821\n'+params+'[Peer]\nPublicKey = '+client_pub+'\nAllowedIPs = '+client_address+'/32\n'
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
            if modern:run('docker','exec',server,'ip','route','add',client_address+'/32','dev','awg0')
            address=json.loads(run('docker','inspect',server))[0]['NetworkSettings']['Networks'][prefix]['IPAddress']
            run('docker','run','-d','--name',client,'--network',prefix,'--cap-add','NET_ADMIN',
                '--device','/dev/net/tun','--sysctl','net.ipv4.conf.all.src_valid_mark=1',
                '-v',str(Path(__file__).resolve().parents[1])+':/source:ro','--entrypoint','sleep',IMAGE,'180')
            containers.append(client)
            config='[Interface]\nPrivateKey = '+client_key+'\n'+params+'[Peer]\nPublicKey = '+server_pub+'\nEndpoint = '+address+':51821\nAllowedIPs = 10.78.0.1/32\n'
            run('docker','exec','-i',client,'python3','-c',
                "import os,sys;fd=os.open('/tmp/client.conf',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(fd,sys.stdin.buffer.read());os.close(fd)",input=config)
            run('docker','exec',client,'amneziawg-go','awg0')
            run('docker','exec',client,'awg','setconf','awg0','/tmp/client.conf')
            run('docker','exec',client,'ip','address','add',client_address+'/32','dev','awg0')
            run('docker','exec',client,'ip','link','set','awg0','up')
            run('docker','exec',client,'ip','route','add','10.78.0.1/32','dev','awg0')
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
            if modern:
                run('docker','exec',client,'ip','link','delete','awg0')
                baseline=run('docker','exec',client,'ip','route','show','table','all')
                run('docker','exec',client,'sh','/source/clients/linux/install-awg.sh','/source','/opt/awg31')
                profile='[Interface]\nPrivateKey = '+client_key+'\nAddress = '+client_address+'/32\nDNS = 1.1.1.1\nMTU = 1280\n'+params.replace('RandomTrailers = on','RandomTrailers = true').replace('DisableCookies = off','DisableCookies = false')+'[Peer]\nPublicKey = '+server_pub+'\nEndpoint = '+address+':51821\nAllowedIPs = 0.0.0.0/0, ::/0\nPersistentKeepalive = 25\n'
                helper='/usr/local/lib/family-connect-awg/helper'
                ident=run('docker','exec','-i',client,helper,'import',input=profile)
                # Replace only the external HTTPS health service with the isolated
                # bound HTTP peer. Import, awg-quick, routing and cleanup stay real.
                code="""import importlib.machinery,subprocess,sys,time
m=importlib.machinery.SourceFileLoader('fc_helper','/usr/local/lib/family-connect-awg/helper').load_module()
def healthy(ident,expected):
 body=subprocess.check_output(['curl','--noproxy','*','--interface','if!'+ident,'--silent','--fail','--max-time','10','http://10.78.0.1:8080/'])
 assert body==b'family-connect-awg-test'
 stamp=m.command(m.BIN+'/awg','show',ident,'latest-handshakes').split()[1]
 assert 0<=time.time()-int(stamp)<30
m.healthy=healthy
sys.argv=['helper','up',sys.argv[1]]
m.main()
"""
                run('docker','exec',client,'python3','-c',code,ident)
                try:run('docker','exec',client,'sh','/source/clients/linux/install-awg.sh','/source','/opt/awg31')
                except RuntimeError:pass
                else:raise AssertionError('Installer changed an active AWG tunnel')
                assigned=json.loads(run('docker','exec',client,'ip','-j','address','show','dev',ident))
                assert any(a['local']==client_address for a in assigned[0]['addr_info'])
                run('docker','exec',client,helper,'down',ident)
                assert run('docker','exec',client,'ip','route','show','table','all')==baseline
                bad=profile.replace('HeaderProtectionKey = '+params.split('HeaderProtectionKey = ')[1].split('\n')[0],
                                    'HeaderProtectionKey = '+base64.b64encode(secrets.token_bytes(32)).decode())
                bad_ident=run('docker','exec','-i',client,helper,'import',input=bad)
                try:run('docker','exec',client,'python3','-c',code,bad_ident)
                except RuntimeError:pass
                else:raise AssertionError('Wrong protected header key accepted')
                assert run('docker','exec',client,'ip','route','show','table','all')==baseline
                assert not any(item['ifname']==bad_ident for item in json.loads(run('docker','exec',client,'ip','-j','link')))
                print('PASS: installed Linux helper import, full-pool address, userspace up, bound HTTP, wrong-key rejection and route cleanup.')
            print('PASS: isolated AWG '+('3.1 /16 allocation' if modern else '2')+' handshake and bound HTTP transfer; no host routes or published ports.')
        finally:
            for name in reversed(containers):run('docker','rm','-f',name)
            run('docker','network','rm',prefix)

if __name__=='__main__':main()
