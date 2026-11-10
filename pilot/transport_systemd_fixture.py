"""Disposable systemd/native fixture; never install this on a gateway."""
from copy import deepcopy
import hashlib
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
        assert run(['systemctl', 'show', service, '-p', 'ControlPID', '--value']).stdout.strip() == b'0'
    jobs = run(['systemctl', 'list-jobs', '--no-pager']).stdout.decode()
    assert not any(service in jobs for service in SERVICES)
    for service in SERVICES:
        run(['systemctl', 'start', service])


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
    shutil.copyfile('/production-awg.service', units/SERVICES[1])
    shutil.copyfile('/production-tcp.service', units/SERVICES[2])
    shutil.copyfile('/kit/'+SERVICES[0],units/SERVICES[0])
    for service in SERVICES[1:]:
        drop = units/(service+'.d')
        drop.mkdir()
        (drop/'70-private-files.conf').write_text('[Service]\nUMask=0077\n')
        if service == SERVICES[1]:
            (drop/'80-stop-timeout.conf').write_text('[Service]\nTimeoutStopSec=90\n')
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


def lifecycle_fault(document):
    def properties(service):
        raw = run(['systemctl','show',service,'-p',
            'MainPID,NRestarts,Result,ActiveState,SubState,InvocationID,Restart,BindsTo,After']).stdout.decode()
        return dict(line.split('=',1) for line in raw.splitlines() if '=' in line)
    before = json.loads((ROOT/'transport-state.json').read_text())
    initial = {service:properties(service) for service in SERVICES}
    assert all(value['ActiveState']=='active' for value in initial.values())
    assert all(SERVICES[0] in initial[service]['BindsTo'] for service in SERVICES[1:])
    expected_loop = document['expect_restart_loop']
    assert initial[SERVICES[0]]['Restart'] == ('on-failure' if expected_loop else 'no')
    started = time.monotonic()
    samples = []
    run(['systemctl','kill','--kill-who=main','--signal=SIGKILL',SERVICES[0]])
    try:
        while True:
            current = {service:properties(service) for service in SERVICES}
            samples.append(dict(elapsed=time.monotonic()-started,units=current))
            engines_stopped = all(current[service]['MainPID']=='0' for service in SERVICES[1:])
            if expected_loop:
                if int(current[SERVICES[0]]['NRestarts'])>=2 and engines_stopped:
                    break
            elif time.monotonic()-started>=12:
                assert engines_stopped and current[SERVICES[0]]['MainPID']=='0'
                assert current[SERVICES[0]]['NRestarts']==initial[SERVICES[0]]['NRestarts']
                assert current[SERVICES[0]]['ActiveState']=='failed'
                break
            assert time.monotonic()-started<65, 'Lifecycle did not reach its declared bounded outcome'
            time.sleep(.4)
        jobs = run(['systemctl','list-jobs','--no-pager']).stdout.decode()
        assert not any(service in jobs for service in SERVICES[1:])
        after = json.loads((ROOT/'transport-state.json').read_text())
        for device, record in before['records'].items():
            for field in ('decision','prepared','boot','deadline'):
                assert after['records'][device][field]==record[field]
    finally:
        restart_services()
    return dict(result='RESTART_LOOP_REPRODUCED' if expected_loop else 'RECOVERY_REQUIRED',
        samples=samples,engine_start_jobs='none during automatic watcher-only restart',
        recovery_job_source='explicit operator-equivalent sequential systemctl start',
        manual_recovery=info(),durable_decisions_unchanged=True)


def invalid_start():
    run(['systemctl','stop',*SERVICES])
    path = ROOT/'transport-state.json'
    original = path.read_bytes()
    try:
        path.write_bytes(b'{}')
        process = subprocess.run(['systemctl','start',SERVICES[0]],capture_output=True,timeout=15)
        assert process.returncode!=0
        time.sleep(6)
        assert all(run(['systemctl','show',service,'-p','MainPID','--value']).stdout.strip()==b'0' for service in SERVICES)
        assert run(['systemctl','show',SERVICES[0],'-p','NRestarts','--value']).stdout.strip()==b'0'
    finally:
        path.write_bytes(original)
        restart_services()
    return dict(result='RECOVERY_REQUIRED',invalid_state_never_opened_access=True)


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
        assert failure['boundary'] == 'body'
        queries = [entry for entry in failure['calls'] if entry['kind'] == 'tcp-query']
        assert len(queries) == 1 and queries[0]['started'] is not None
        assert queries[0]['duration'] >= 0 and not queries[0]['completed']
        assert queries[0]['remaining'] <= 8
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


def dns_probe(document):
    assert document['allowed'] is True
    client = json.loads((canary.ROOT/'client.json').read_text())
    answer = canary.run(['dig', '+short', '+tries=1', '+time=3', '-b', canary.TUNNEL,
        '@'+client['origin'], canary.DOMAIN, 'A']).stdout.decode().strip()
    assert answer == client['origin'], 'AWG_DNS_FAILED'
    return dict(awg_dns=True, tcp_dns='SOCKS5 hostname resolved by actual Xray', https=probe(document))


def live_readback():
    spec = importlib.util.spec_from_file_location('replacement_gateway', ROOT/'awg-gateway.py')
    gateway = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gateway)
    from control.friends.transport_gateway import Gateway
    engine = Gateway(gateway)
    with engine.operation(), engine.serialized(), engine.lock():
        state = engine.load()
        live_awg = engine.awg_snapshot()
        live_tcp, unused = engine.tcp_snapshot()
        config = json.loads((TCP/'server.json').read_text())
        persisted_tcp = next(item for item in config['inbounds'] if item.get('tag') == 'friends')['settings']['clients']
        expected_tcp = {(item['email'], item['id'], item.get('flow')) for item in persisted_tcp}
        actual_tcp = {(item['email'], item['account']['id'], item['account'].get('flow')) for item in live_tcp.values()}
        assert actual_tcp == expected_tcp, 'FULL_TCP_SET_MISMATCH'
        with gateway.database() as database:
            registered = {public: gateway.address(index) for index, public in database.execute('SELECT id,public FROM peers')}
        expected_awg = {}
        for device, cached in state['records'].items():
            decision = cached['decision']
            public = decision['public_key']
            allowed = public in registered and engine.allowed(cached)
            applied = cached['applied']
            assert applied['result'] == 'applied' and applied['allowed'] == allowed
            assert applied['expected_revision'] == applied['applied_revision'] == decision['revision']
            expected_user = (device+'@family.test', decision['tcp_id'], 'xtls-rprx-vision')
            assert (expected_user in actual_tcp) == allowed, 'TCP_DECISION_MISMATCH'
            if allowed:
                expected_awg[public] = registered[public]
        assert live_awg == expected_awg, 'FULL_AWG_SET_MISMATCH'
    return dict(canonical_records=len(state['records']), registered=len(registered),
        actual_awg=len(live_awg), actual_tcp=len(actual_tcp),
        full_sets_and_revisions_match=True, observed_at=int(time.time()))


def replacement_context():
    expected = dict(awg='906d6795af1dd4adee7b11bf1e7fa133d4795c8a8d6e2099b34a026f810a3278',
        **{'amneziawg-go':'e7f00e47d6df853ade5dcd2fe79240f01ff897d75088c768316a444c27c87e0f'},
        xray='4f7a4436f86798bbb5c875014e352021a1673710a45e170ccc507c5f59341940')
    actual = {name: hashlib.sha256((Path('/native')/name).read_bytes()).hexdigest() for name in expected}
    assert actual == expected
    units = {service: run(['systemctl','show',service,'-p',
        'User,Group,MemoryMax,TasksMax,Restart,WatchdogUSec,TimeoutStopUSec,KillMode,BindsTo,After,NoNewPrivileges,ProtectSystem,ProtectHome,PrivateTmp,CapabilityBoundingSet,AmbientCapabilities,RestrictAddressFamilies,LimitNOFILE,LimitNPROC']).stdout.decode()
        for service in SERVICES}
    assert 'Restart=no\n' in units[SERVICES[0]]
    assert 'WatchdogUSec=12s\n' in units[SERVICES[0]]
    assert 'User=fc-friends\n' in units[SERVICES[2]]
    assert 'MemoryMax=268435456\n' in units[SERVICES[2]]
    assert 'TasksMax=128\n' in units[SERVICES[2]]
    assert 'ProtectSystem=strict\n' in units[SERVICES[2]]
    assert 'NoNewPrivileges=yes\n' in units[SERVICES[2]]
    return dict(native_hashes=actual, units=units, processes=info(),
        python=run(['/usr/bin/python3','--version']).stdout.decode().strip(),
        xray=run(['/native/xray','version']).stdout.decode().splitlines()[0])


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
    elif action == 'dns-probe':
        result = dns_probe(document)
    elif action == 'live-readback':
        result = live_readback()
    elif action == 'replacement-context':
        result = replacement_context()
    elif action == 'budget-fault':
        result = budget_fault(document)
    elif action == 'diagnostic-fault':
        result = diagnostic_fault()
    elif action == 'lifecycle-fault':
        result = lifecycle_fault(document)
    elif action == 'invalid-start':
        result = invalid_start()
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
