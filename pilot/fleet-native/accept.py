"""Runs only inside the disposable NET_ADMIN acceptance container."""
import base64
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import uuid

sys.path.insert(0, '/app')
from control.fleet_gateway import PeerCommand, receipt
from control.fleet_ssh import SSHGateway
from control.fleet_process import ProcessFailed, run

ROOT = Path('/run/fleet-test')
PYTHON = '/usr/local/bin/python'
AGENT = '/app/scripts/fleet_agent.py'
HOST = '11.255.255.1'  # Bound only to loopback in the isolated network namespace.


def call(*args, data=None, ok=True):
    p = subprocess.run(args, input=data, capture_output=True, timeout=20)
    if ok and p.returncode:
        raise RuntimeError('native acceptance command failed: '+args[0])
    return p


def secret(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)


def keypair(cli):
    private = call(cli, 'genkey').stdout.strip()
    public = call(cli, 'pubkey', data=private).stdout.decode().strip()
    return private, public


def setup(mode):
    ROOT.mkdir(mode=0o700)
    if mode == 'wg':
        cli, engine, transport, version = '/usr/bin/wg', None, 'wireguard', '1'
        params = ''
    else:
        cli = '/opt/'+mode+'/awg'
        engine = '/opt/'+mode+'/amneziawg-go'
        transport, version = 'amneziawg', ('3.1' if mode == 'awg31' else '2.0')
        params = 'Jc = 4\nJmin = 40\nJmax = 100\n'
        if mode == 'awg31':
            params += ''.join(f'S{i} = 32\nH{i} = {i}\n' for i in range(1,5))
            params += 'HeaderProtectionKey = '+base64.b64encode(os.urandom(32)).decode()+'\nContentPaddingAddition = 0-64\nRandomTrailers = on\nDisableCookies = off\n'
        else:
            params += 'S1 = 32\nS2 = 64\nS3 = 16\nS4 = 8\nH1 = 1000-1100\nH2 = 2000-2100\nH3 = 3000-3100\nH4 = 4000-4100\n'
    server_key, server_pub = keypair(cli)
    client_key, client_pub = keypair(cli)
    _, other_pub = keypair(cli)
    spec = dict(cli=cli, engine=engine, transport=transport, version=version, server_pub=server_pub,
                client_pub=client_pub, other_pub=other_pub)
    secret(ROOT/'spec.json', json.dumps(spec).encode())
    secret(ROOT/'server.conf', b'[Interface]\nPrivateKey = '+server_key+b'\nListenPort = 51820\n'+params.encode()+
           ('[Peer]\nPublicKey = '+other_pub+'\nAllowedIPs = 10.87.0.3/32\n').encode())
    # Transferred privately to the disposable client; never printed in reports.
    secret(ROOT/'client.conf', b'[Interface]\nPrivateKey = '+client_key+b'\n'+params.encode()+
           ('[Peer]\nPublicKey = '+server_pub+'\nEndpoint = SERVER:51820\nAllowedIPs = 10.87.0.1/32\n').encode())
    gateway = dict(gateway_id='native-test', failure_domain='native-test', country='nl', state='active',
        endpoints=[dict(transport=transport,version=version,address=HOST,port=51820)],
        tunnel_pool='10.87.0.0/24', max_devices=100, weight=1.0, egress_budget_mbps=100.0)
    config = dict(schema_version=1,gateway=gateway,state_directory='/var/lib/family-connect/journal',
        bindings=[dict(transport=transport,version=version,binary=cli,interface='fc0',server_public=server_pub,port=51820)])
    secret(Path('/etc/family-connect/fleet-agent.json'), json.dumps(config).encode())
    call('ip','address','add',HOST+'/32','dev','lo')
    for name in ('host','client','wrong'):
        call('ssh-keygen','-q','-t','ed25519','-N','','-f',str(ROOT/name))
    pub = (ROOT/'client.pub').read_text().strip()
    secret(ROOT/'authorized_keys', ('restrict,command="'+PYTHON+' -I '+AGENT+'" '+pub+'\n').encode())
    host_pub = (ROOT/'host.pub').read_text().split()
    secret(ROOT/'known_hosts', (HOST+' '+host_pub[0]+' '+host_pub[1]+'\n').encode())
    wrong_pub = (ROOT/'wrong.pub').read_text().split()
    secret(ROOT/'wrong_hosts', (HOST+' '+wrong_pub[0]+' '+wrong_pub[1]+'\n').encode())
    secret(ROOT/'sshd_config', f'''ListenAddress {HOST}
Port 22
HostKey {ROOT}/host
PidFile {ROOT}/sshd.pid
AuthorizedKeysFile {ROOT}/authorized_keys
PermitRootLogin prohibit-password
PasswordAuthentication no
KbdInteractiveAuthentication no
UsePAM no
AllowUsers root
AllowTcpForwarding no
AllowAgentForwarding no
X11Forwarding no
PermitTunnel no
PermitTTY no
StrictModes yes
LogLevel ERROR
'''.encode())
    call('/usr/sbin/sshd','-f',str(ROOT/'sshd_config'))
    call(PYTHON,'-I',AGENT,'--initialize')
    command = PeerCommand(lease_id=uuid.uuid4().hex,gateway_id='native-test',device=uuid.uuid4().hex,
        wg=client_pub,address='10.87.0.2/32',transport=transport,version=version,
        expires_at=int(time.time())+900,generation=1,operation='present')
    secret(ROOT/'command.json',command.canonical().encode())
    start_server(spec)


def start_server(spec):
    if spec['engine']:
        call(spec['engine'],'fc0')
    else:
        call('ip','link','add','fc0','type','wireguard')
    call(spec['cli'],'setconf','fc0',str(ROOT/'server.conf'))
    call('ip','address','add','10.87.0.1/24','dev','fc0')
    call('ip','link','set','fc0','up')


def check(stage):
    spec = json.loads((ROOT/'spec.json').read_text())
    command = PeerCommand.model_validate_json((ROOT/'command.json').read_bytes())
    adapter = SSHGateway(host=HOST,key=ROOT/'client',known_hosts=ROOT/'known_hosts',user='root')
    def peers():
        return call(spec['cli'],'show','fc0','allowed-ips').stdout.decode()
    def rejected(argv, payload):
        try:
            run(argv,payload=payload,timeout=10)
        except ProcessFailed:
            return
        raise AssertionError('forbidden SSH request accepted')
    if stage == 'admit':
        wrong = SSHGateway(host=HOST,key=ROOT/'client',known_hosts=ROOT/'wrong_hosts',user='root')
        rejected(wrong.argv,command.canonical().encode())
        wrong_identity = SSHGateway(host=HOST,key=ROOT/'wrong',known_hosts=ROOT/'known_hosts',user='root')
        rejected(wrong_identity.argv,command.canonical().encode())
        rejected(adapter.argv[:-1]+['id'],b'')
        rejected(adapter.argv[:-1]+['fleet-v1 --initialize'],b'')
        rejected(adapter.argv,b'{}')
        assert command.wg not in peers()
        # Test-only forced-command wrapper: real SSH + real peer effect, then
        # process death before the journal can mark done or send a receipt.
        secret(ROOT/'crash.py', b'''import os,sys
sys.path.insert(0,'/app')
from scripts import fleet_agent
build=fleet_agent.build
def crash_build(config):
    agent=build(config)
    ensure=agent.backend.ensure
    def crash(command,*,lock_fd):
        ensure(command,lock_fd=lock_fd)
        os._exit(73)
    agent.backend.ensure=crash
    return agent
fleet_agent.build=crash_build
fleet_agent.main()
''')
        authorized=(ROOT/'authorized_keys').read_bytes()
        try:
            (ROOT/'authorized_keys').write_bytes(authorized.replace(AGENT.encode(),str(ROOT/'crash.py').encode()))
            rejected(adapter.argv,command.canonical().encode())
        finally:
            (ROOT/'authorized_keys').write_bytes(authorized)
        assert command.wg+'\t10.87.0.2/32' in peers()
        with sqlite3.connect('/var/lib/family-connect/journal/gateway.db') as db:
            assert db.execute('SELECT done FROM commands WHERE lease_id=?',(command.lease_id,)).fetchone()==(0,)
        assert adapter.execute(command)==receipt(command)
        assert adapter.execute(command)==receipt(command)
        with sqlite3.connect('/var/lib/family-connect/journal/gateway.db') as db:
            assert db.execute('SELECT done FROM commands WHERE lease_id=?',(command.lease_id,)).fetchone()==(1,)
    elif stage == 'restart':
        call('ip','link','delete','fc0')
        start_server(spec)
        assert command.wg not in peers()
        result=json.loads(call(PYTHON,'-I',AGENT,'--recover').stdout)
        assert result == {'recovered':1}
        assert adapter.execute(command)==receipt(command)
    elif stage == 'remove':
        removal=command.model_copy(update={'operation':'absent','generation':2})
        assert adapter.execute(removal)==receipt(removal)
        assert adapter.execute(removal)==receipt(removal)
        rejected(adapter.argv,command.canonical().encode())
        assert command.wg not in peers()
    elif stage == 'reuse':
        new=command.model_copy(update={'lease_id':uuid.uuid4().hex})
        assert adapter.execute(new)==receipt(new)
        removal=command.model_copy(update={'operation':'absent','generation':2})
        assert adapter.execute(removal)==receipt(removal)
    else:
        raise ValueError('unknown acceptance stage')
    assert spec['other_pub']+'\t10.87.0.3/32' in peers()
    if stage!='remove':
        assert command.wg+'\t10.87.0.2/32' in peers()
    print(json.dumps({'stage':stage,'passed':True}))


if __name__=='__main__':
    if sys.argv[1]=='setup':setup(sys.argv[2])
    else:check(sys.argv[1])
