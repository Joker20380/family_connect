"""Disposable systemd/native fixture; never install this on a gateway."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

sys.path.insert(0, '/')
import transport_fixture as traffic
import canary

sys.path.insert(0, '/kit/paid-reconcile.pyz')
from control.friends import transport_policy as policy
from control.friends.transport_gateway import write

ROOT = Path('/opt/apps/family_connect/friends-awg')
TCP = ROOT.parent/'friends-tcp'
SERVICES = ('family-connect-paid-watch.service', 'family-connect-friends-awg.service', 'family-connect-friends-tcp.service')
def checked_curl(arguments, nonce, success, peer):
    result = canary.run(['curl', '--silent', '--show-error', '--fail',
        '--max-time', '25' if success else '4', '--connect-timeout', '20' if success else '3',
        '--cacert', str(canary.ROOT/'origin.crt'), '--proxy', '', '--noproxy', '',
        *arguments, 'https://'+canary.DOMAIN+'/canary/'+nonce], check=False, timeout=27)
    if success:
        assert result.returncode == 0, 'probe '+repr(arguments)+': '+result.stderr.decode()
        assert json.loads(result.stdout) == dict(path='/canary/'+nonce, peer=peer)
    else:
        assert result.returncode != 0


traffic.curl = checked_curl


def run(arguments, **kwargs):
    return subprocess.run(arguments, capture_output=True, check=True, timeout=35, **kwargs)


def material(document):
    client = canary.prepare_gateway({key: document[key] for key in ('origin','gateway','egress','certificate')})
    canary.stop('server-awg')
    canary.stop('server-tcp')
    canary.run(['ip','link','del','fcprobe0'], check=False)
    canary.run(['nft','delete','table','ip','fc_canary'], check=False)
    write(canary.ROOT/'material.json',client)
    return client


def setup(document):
    client = json.loads((canary.ROOT/'material.json').read_text())
    ROOT.mkdir(parents=True)
    TCP.mkdir()
    for name in ('awg','amneziawg-go'):
        (ROOT/name).symlink_to('/native/'+name)
    (TCP/'xray').symlink_to('/native/xray')
    for name in ('paid-transport.pyz','awg-gateway.py'):
        shutil.copyfile('/kit/'+name, ROOT/name)
        (ROOT/name).chmod(0o600)
    write(ROOT/'settings.json',dict(network='10.254.253.0/24',address='10.254.253.1/24',external='eth1'))
    (ROOT/'server.conf').write_text((canary.ROOT/'server.awg').read_text().split('[Peer]')[0])
    write(ROOT/'transport-enforcement.json',dict(schema=1,profile=policy.PROFILE,node=document['node'],enabled=True))
    write(ROOT/'transport-state.json',dict(schema=1,node=document['node'],records={},observed_at=int(time.time())))
    config = json.loads((canary.ROOT/'server.json').read_text())
    config['log'] = dict(loglevel='warning')
    inbound = config['inbounds'][0]
    inbound['tag'] = 'friends'
    multiplex = str(uuid.uuid4())
    inbound['settings']['clients'] = [dict(id=multiplex,email='foreign@fixture.invalid')]
    config['api'] = dict(tag='api',services=['HandlerService'])
    config['inbounds'].append(dict(tag='api',listen='127.0.0.1',port=18085,protocol='dokodemo-door',settings=dict(address='127.0.0.1')))
    config['routing'] = dict(rules=[dict(type='field',inboundTag=['api'],outboundTag='api')])
    write(TCP/'server.json',config)
    spec = importlib.util.spec_from_file_location('actual_gateway',ROOT/'awg-gateway.py')
    gateway = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = gateway
    spec.loader.exec_module(gateway)
    by_device = {item['device']:item for item in document['envelope']['decisions']}
    primary, other = [by_device[device] for device in document['registered']]
    with gateway.database() as database:
        for record in (primary,other):
            database.execute('INSERT INTO peers(public) VALUES (?)',(record['public_key'],))
    from control.friends.transport_gateway import Gateway
    engine = Gateway(gateway)
    engine.accept(document['envelope'])
    engine.apply(starting=True)
    units = Path('/etc/systemd/system')
    (units/SERVICES[1]).write_text('[Unit]\nDescription=Isolated packaged AWG service\n[Service]\nExecStart=/usr/bin/python3 /opt/apps/family_connect/friends-awg/awg-gateway.py run\n')
    (units/SERVICES[2]).write_text('[Unit]\nDescription=Isolated exact Xray service\n[Service]\nExecStart=/native/xray run -config /opt/apps/family_connect/friends-tcp/server.json\n')
    shutil.copyfile('/kit/'+SERVICES[0],units/SERVICES[0])
    for service in SERVICES[1:]:
        drop = units/(service+'.d')
        drop.mkdir()
        shutil.copyfile('/kit/paid-dependency.conf',drop/'90-paid.conf')
    shutil.copyfile('/kit/paid-tcp-preflight.conf',units/(SERVICES[2]+'.d')/'91-paid-preflight.conf')
    run(['systemctl','daemon-reload'])
    run(['systemctl','start',*SERVICES])
    for attempt in range(30):
        if (ROOT/'transport-attempt.json').exists():
            break
        time.sleep(.3)
    client['tcp']['outbounds'][0]['settings']['vnext'][0]['users'][0]['id'] = primary['tcp_id']
    client['mux'] = deepcopy(client['tcp'])
    client['mux']['inbounds'][0]['port'] = 19729
    client['mux']['outbounds'][0]['settings']['vnext'][0]['users'][0].update(id=multiplex)
    client['mux']['outbounds'][0]['settings']['vnext'][0]['users'][0].pop('flow')
    client['mux']['outbounds'][0]['mux'] = dict(enabled=True,concurrency=4)
    client['noncohort'] = deepcopy(client['tcp'])
    client['noncohort']['inbounds'][0]['port'] = 19730
    client['noncohort']['outbounds'][0]['settings']['vnext'][0]['users'][0]['id'] = other['tcp_id']
    return dict(client=client,info=info())


def info():
    state = json.loads((ROOT/'transport-state.json').read_text())
    return dict(state=state,services={service:run(['systemctl','show',service,'-p','MainPID','-p','NRestarts','-p','ActiveState','-p','InvocationID']).stdout.decode() for service in SERVICES},
        preflight=run(['systemctl','show',SERVICES[2],'-p','ExecStartPre']).stdout.decode())


def start_client(document):
    client = document['client']
    canary.secret('client.json',json.dumps(client).encode())
    canary.secret('origin.crt',client['certificate'].encode())
    canary.run(['ip','route','add','unreachable',client['origin']+'/32'])
    canary.launch('client-awg',['/native/amneziawg-go','-f','fcprobe0'])
    canary.wait_for(['ip','link','show','fcprobe0'])
    canary.run(['ip','address','add',canary.TUNNEL+'/30','dev','fcprobe0'])
    canary.run(['ip','link','set','fcprobe0','mtu','1280','up'])
    canary.run(['ip','route','replace',client['origin']+'/32','dev','fcprobe0'])
    canary.secret('valid.awg',client['awg'].encode())
    canary.run(['/native/awg','setconf','fcprobe0',str(canary.ROOT/'valid.awg')])
    for name in ('tcp','mux','noncohort'):
        client[name]['log']=dict(loglevel='warning')
        canary.secret(name+'.json',json.dumps(client[name]).encode())
        canary.launch('client-'+name,['/native/xray','run','-config',str(canary.ROOT/(name+'.json'))])
    return probe(dict(allowed=True))


def probe(document):
    started = time.monotonic()
    client = json.loads((canary.ROOT/'client.json').read_text())
    import uuid
    nonce = uuid.uuid4().hex
    traffic.curl(['--socks5-hostname','127.0.0.1:19730'],nonce,True,client['egress'])
    return dict(traffic.probe(document['allowed']), elapsed_seconds=time.monotonic()-started)


def main():
    os.umask(0o077)
    canary.ROOT.mkdir(mode=0o700,exist_ok=True)
    action = sys.argv[1]
    document = json.load(sys.stdin)
    if action == 'material':
        result = material(document)
    elif action == 'setup':
        result = setup(document)
    elif action == 'info':
        result = info()
    elif action == 'client':
        result = start_client(document)
    elif action == 'probe':
        result = probe(document)
    elif action == 'restart':
        run(['systemctl','restart',*SERVICES])
        result = info()
    elif action == 'fault':
        drop = Path('/etc/systemd/system')/(SERVICES[2]+'.d')/'99-fixture-fault.conf'
        drop.write_text('[Service]\nExecStartPre=/bin/false\n')
        run(['systemctl','daemon-reload'])
        result = dict(injected=True)
    elif action == 'recover':
        run(['systemctl', 'stop', *SERVICES])
        (Path('/etc/systemd/system')/(SERVICES[2]+'.d')/'99-fixture-fault.conf').unlink()
        run(['systemctl','daemon-reload'])
        for service in SERVICES:
            if subprocess.run(['systemctl', 'is-failed', '--quiet', service]).returncode == 0:
                run(['systemctl', 'reset-failed', service])
        run(['systemctl','start',*SERVICES])
        result = info()
    else:
        raise ValueError('Unknown fixture action')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
