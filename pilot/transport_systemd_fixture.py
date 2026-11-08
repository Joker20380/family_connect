"""Disposable systemd/native fixture; never install this on a gateway."""
from copy import deepcopy
import importlib.util
import json
import os
import pwd
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


def restart_services():
    run(['systemctl', 'stop', *SERVICES])
    for service in SERVICES:
        assert run(['systemctl', 'show', service, '-p', 'MainPID', '--value']).stdout.strip() == b'0'
    run(['systemctl', 'start', *SERVICES])


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
    run(['useradd', '--system', '--no-create-home', 'fc-friends'])
    user = pwd.getpwnam('fc-friends')
    for path in (ROOT.parent, ROOT.parent.parent):
        path.chmod(0o755)
    TCP.chmod(0o750)
    os.chown(TCP, 0, user.pw_gid)
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
    os.chown(TCP/'server.json',0,user.pw_gid)
    (TCP/'server.json').chmod(0o640)
    spec = importlib.util.spec_from_file_location('actual_gateway',ROOT/'awg-gateway.py')
    gateway = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = gateway
    spec.loader.exec_module(gateway)
    by_device = {item['device']:item for item in document['envelope']['decisions']}
    registered = [by_device[device] for device in document['registered']]
    primary, other = registered[:2]
    with gateway.database() as database:
        for record in registered:
            database.execute('INSERT INTO peers(public) VALUES (?)',(record['public_key'],))
    from control.friends.transport_gateway import Gateway
    engine = Gateway(gateway)
    engine.accept(document['envelope'])
    engine.apply(starting=True)
    units = Path('/etc/systemd/system')
    (units/SERVICES[1]).write_text('[Unit]\nDescription=Isolated packaged AWG service\n[Service]\nExecStart=/usr/bin/python3 /opt/apps/family_connect/friends-awg/awg-gateway.py run\n')
    shutil.copyfile('/production-tcp.service', units/SERVICES[2])
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
    for attempt in range(50):
        pid = int(run(['systemctl','show',SERVICES[2],'-p','MainPID','--value']).stdout)
        if not pid or Path('/proc/'+str(pid)+'/comm').read_text().strip() == 'xray':
            break
        time.sleep(.1)
    if pid:
        assert Path('/proc/'+str(pid)+'/status').read_text().split('Uid:')[1].split()[0] == str(pwd.getpwnam('fc-friends').pw_uid)
    return dict(state=state,services={service:run(['systemctl','show',service,'-p','MainPID','-p','NRestarts','-p','ActiveState','-p','InvocationID']).stdout.decode() for service in SERVICES},
        preflight=run(['systemctl','show',SERVICES[2],'-p','ExecStartPre']).stdout.decode())


def budget_fault(document):
    started = time.monotonic()
    if document['kind'] == 'lock':
        process = subprocess.Popen([sys.executable, '-c',
            'import fcntl,time,sys; handle=open(sys.argv[1],"a"); fcntl.flock(handle,fcntl.LOCK_EX); time.sleep(30)',str(ROOT/'application.lock')])
    else:
        process = None
        (TCP/'xray').unlink()
        (TCP/'xray').write_text('#!/usr/bin/python3\nimport os,subprocess,sys,time\n'
            'if "api" in sys.argv:\n subprocess.Popen([sys.executable,"-c","import time,pathlib; time.sleep(10); pathlib.Path(\\"/tmp/late-engine-write\\").touch()"]); time.sleep(30)\n'
            'os.execv("/native/xray",["/native/xray",*sys.argv[1:]])\n')
        (TCP/'xray').chmod(0o755)
    try:
        for attempt in range(120):
            result = run(['systemctl','show',SERVICES[0],'-p','Result','--value']).stdout.strip()
            if result != b'success':
                break
            time.sleep(.1)
        assert result == b'exit-code', result
        elapsed = time.monotonic()-started
        assert elapsed < 12
        run(['systemctl','stop',*SERVICES])
        time.sleep(max(0,12-(time.monotonic()-started)))
        assert not Path('/tmp/late-engine-write').exists()
        return dict(kind=document['kind'],bounded_failure_seconds=elapsed,late_write=False)
    finally:
        if process:
            process.terminate();process.wait(timeout=2)
        else:
            (TCP/'xray').unlink();(TCP/'xray').symlink_to('/native/xray')
        if subprocess.run(['systemctl','is-failed','--quiet',SERVICES[0]]).returncode == 0:
            run(['systemctl','reset-failed',SERVICES[0]])
        restart_services()


def diagnostic_fault():
    before = json.loads((ROOT/'transport-state.json').read_text())
    invocation = run(['systemctl', 'show', SERVICES[0], '-p', 'InvocationID', '--value']).stdout.decode().strip()
    assert not (ROOT/'transport-failure.json').exists()
    (TCP/'xray').unlink()
    (TCP/'xray').write_text('#!/usr/bin/python3\nimport os,sys\n'
        'if "api" in sys.argv:\n print("synthetic-private-proof",file=sys.stderr);sys.exit(73)\n'
        'os.execv("/native/xray",["/native/xray",*sys.argv[1:]])\n')
    (TCP/'xray').chmod(0o755)
    started = time.monotonic()
    try:
        while run(['systemctl','show',SERVICES[0],'-p','Result','--value']).stdout.strip() == b'success':
            assert time.monotonic()-started < 10
            time.sleep(.1)
        failure = json.loads((ROOT/'transport-failure.json').read_text())
        assert failure['phase'] == 'engine_query' and failure['mode'] == 'watch'
        assert failure['reason'] == 'COMMAND_FAILED' and failure['command_family'] == 'tcp-query'
        assert failure['returncode'] == 73 and failure['timeout'] is False
        assert failure['invocation_id'] == invocation
        run(['systemctl','stop',*SERVICES])
        assert all(run(['systemctl','show',service,'-p','MainPID','--value']).stdout.strip() == b'0' for service in SERVICES)
        journal = run(['journalctl','_SYSTEMD_INVOCATION_ID='+invocation,'--no-pager','-o','cat']).stdout.decode()
        assert 'synthetic-private-proof' not in journal
        assert '"transport_failure"' in journal
        after = json.loads((ROOT/'transport-state.json').read_text())
        for device, cached in before['records'].items():
            for field in ('decision','prepared','boot','deadline'):
                assert after['records'][device][field] == cached[field]
        stopped_after = time.monotonic()-started
    finally:
        (TCP/'xray').unlink()
        (TCP/'xray').symlink_to('/native/xray')
        restart_services()
    assert json.loads((ROOT/'transport-failure.json').read_text()) == failure
    return dict(result='PASS',stop_seconds=stopped_after,primary=failure,
        durable_restrictions_preserved=True,actual_systemd_recovery=True)


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
    elif action == 'budget-fault':
        result = budget_fault(document)
    elif action == 'diagnostic-fault':
        result = diagnostic_fault()
    elif action == 'restart':
        restart_services()
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
