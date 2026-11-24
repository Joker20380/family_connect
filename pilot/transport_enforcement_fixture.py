"""Disposable native transport fixture. All credentials live in container tmpfs."""
import base64
import fcntl
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import socket
import ssl
import subprocess
import sys
import threading
import time
import uuid

sys.path.insert(0, '/')
import canary

ROOT = canary.ROOT


def launch(name, arguments):
    with (ROOT/(name+'.log')).open('wb') as output:
        process = subprocess.Popen(arguments, stdout=output, stderr=output, start_new_session=True)
    canary.secret(name+'.pid', str(process.pid).encode())
    time.sleep(.3)
    assert process.poll() is None


canary.launch = launch
sys.path.insert(0, '/kit/paid-reconcile.pyz')
from control.friends import paid_beta, transport_policy as policy
import control.friends
control.friends.__path__.append('/kit/paid-transport.pyz/control/friends')
from control.friends.transport_gateway import Gateway, write


def module():
    spec = importlib.util.spec_from_file_location('fixture_gateway', '/kit/awg-gateway.py')
    gateway = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = gateway
    spec.loader.exec_module(gateway)
    gateway.ROOT, gateway.IFACE = ROOT/'friends-awg', 'fcprobe0'
    return gateway


def execute(arguments):
    if arguments[:2] == ['systemctl', 'is-active']:
        name = 'server-awg' if arguments[-1].endswith('awg.service') else 'server-tcp'
        assert (ROOT/(name+'.pid')).exists()
        return b''
    if arguments[:2] == ['systemctl', 'restart']:
        before = time.monotonic()
        canary.stop('server-tcp')
        canary.launch('server-tcp', ['/native/xray', 'run', '-config', str(ROOT/'friends-tcp/server.json')])
        (ROOT/'restart-seconds').write_text(str(time.monotonic()-before))
        return b''
    if arguments[:2] == ['systemctl', 'stop']:
        canary.stop('server-awg' if arguments[-1].endswith('awg.service') else 'server-tcp')
        return b''
    return subprocess.run(arguments, capture_output=True, timeout=8, check=True).stdout


def setup_gateway(document):
    import RNS
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from control.friends.access import Access
    from control.friends import support_ids
    from device_identity.device import DeviceIdentity
    client = canary.prepare_gateway(document)
    canary.stop('server-tcp')
    private = base64.b64decode(re.search(r'PrivateKey = ([^\n]+)', client['awg']).group(1))
    identity = DeviceIdentity(RNS.Identity(), X25519PrivateKey.from_private_bytes(private))
    access = Access(ROOT/'registry.sqlite3')
    access.initialize()
    challenge = access.challenge(identity.public_identity, identity.wireguard_public_key, 'activate', access.invite())
    bound = access.complete(identity.prove_transport_key(challenge['challenge']), 'activate')
    extra_bindings = []
    for number in range(62):
        additional = DeviceIdentity.generate()
        challenge = access.challenge(additional.public_identity, additional.wireguard_public_key, 'activate', access.invite())
        extra_bindings.append(access.complete(additional.prove_transport_key(challenge['challenge']), 'activate'))
    with access.db() as database:
        support = support_ids.registered(database, identity.reference)
        database.execute('UPDATE device_support SET platform=?,app_version=?,version_code=?,last_seen=? WHERE device=?',
            ('android', '0.1.18-beta108', 108, int(time.time()), identity.reference))
    with paid_beta.connection(access.path, write=True) as database:
        paid_beta.migrate(database)
    write(ROOT/'identity.json', dict(device=identity.reference, support=support))
    root = ROOT/'friends-awg'
    root.mkdir()
    tcp = ROOT/'friends-tcp'
    tcp.mkdir()
    for name in ('awg', 'amneziawg-go'):
        (root/name).symlink_to('/native/'+name)
    (tcp/'xray').symlink_to('/native/xray')
    write(root/'settings.json', dict(network='10.254.253.0/24', address='10.254.253.1/24', external='eth1'))
    shutil.copyfile('/kit/paid-transport.pyz', root/'paid-transport.pyz')
    (root/'server.conf').write_text((ROOT/'server.awg').read_text().split('[Peer]')[0])
    write(root/'transport-enforcement.json', dict(schema=1, profile=policy.PROFILE, node='gateway-ru', enabled=True))
    write(root/'transport-state.json', dict(schema=1, node='gateway-ru', observed_at=int(time.time()), records={}))
    config = json.loads((ROOT/'server.json').read_text())
    config['log'] = dict(loglevel='warning')
    config['inbounds'][0]['tag'] = 'friends'
    config['inbounds'][0]['settings']['clients'] = [dict(id=bound['tcp_id'], email=bound['device']+'@family.test', flow='xtls-rprx-vision')]
    config['inbounds'][0]['settings']['clients'].extend(dict(id=item['tcp_id'],email=item['device']+'@family.test',flow='xtls-rprx-vision') for item in extra_bindings)
    multiplex = str(uuid.uuid4())
    config['inbounds'][0]['settings']['clients'].append(dict(id=multiplex, email='foreign@fixture.invalid'))
    config['api'] = dict(tag='api', services=['HandlerService'])
    config['inbounds'].append(dict(tag='api', listen='127.0.0.1', port=18085, protocol='dokodemo-door', settings=dict(address='127.0.0.1')))
    config['routing'] = dict(rules=[dict(type='field', inboundTag=['api'], outboundTag='api')])
    write(tcp/'server.json', config)
    client['tcp']['outbounds'][0]['settings']['vnext'][0]['users'][0]['id'] = bound['tcp_id']
    client['mux'] = deepcopy(client['tcp'])
    client['mux']['inbounds'][0]['port'] = 19729
    user = client['mux']['outbounds'][0]['settings']['vnext'][0]['users'][0]
    user['id'] = multiplex
    user.pop('flow')
    client['mux']['outbounds'][0]['mux'] = dict(enabled=True, concurrency=4)
    gateway = module()
    with gateway.database() as database:
        database.execute('INSERT INTO peers(public) VALUES (?)', (bound['public_key'],))
        database.executemany('INSERT INTO peers(public) VALUES (?)', [(item['public_key'],) for item in extra_bindings])
    engine = Gateway(gateway, run=execute)
    engine.accept(policy.snapshot(access.path, 'gateway-ru'))
    execute(['systemctl', 'restart', 'family-connect-friends-tcp.service'])
    engine.apply()
    canary.launch('watch', ['python3', '/transport_fixture.py', 'watch'])
    return client


def transition(request):
    gateway = module()
    engine = Gateway(gateway, run=execute)
    identity = json.loads((ROOT/'identity.json').read_text())
    operation = request['operation']
    started = time.time()
    if operation not in ('offline', 'refresh'):
        now = int(time.time())
        with paid_beta.connection(ROOT/'registry.sqlite3', write=True) as database:
            values = dict(period_start=now, paid_until=now+request.get('seconds', 3600),
                apk_sha256=paid_beta.PAID_ANDROID_APK_SHA256) if operation == 'payment' else {}
            if operation == 'grace':
                values['grace_until'] = now+request['seconds']
            result = paid_beta.apply_event(database, identity['support'], operation, request['event_id'], 'synthetic-native-fixture', now=now, **values)
    with (gateway.ROOT/'registration.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if operation != 'offline':
            envelope = policy.snapshot(ROOT/'registry.sqlite3', 'gateway-ru')
            if request.get('event_id') == 'native-active-001':
                canary.secret('old-allow.json', json.dumps(envelope).encode())
            engine.accept(envelope)
        engine.apply()
    return dict(operation_started=started, applied_at=time.time(), duration=time.time()-started,
        restart_seconds=float((ROOT/'restart-seconds').read_text()),
        decision=engine.load()['records'][identity['device']]['decision']['state'])


def information():
    engine = Gateway(module(), run=execute)
    identity = json.loads((ROOT/'identity.json').read_text())
    row = engine.load()['records'][identity['device']]
    return dict(decision_count=len(engine.load()['records']),applied=row['applied'], valid_until=row['decision']['valid_until'],
        deadline=row['deadline'], now=time.time(), state=row['decision']['state'])


def start_client(client):
    canary.secret('client.json', json.dumps(client).encode())
    canary.secret('origin.crt', client['certificate'].encode())
    canary.run(['ip', 'route', 'add', 'unreachable', client['origin']+'/32'])
    canary.launch('client-awg', ['/native/amneziawg-go', '-f', 'fcprobe0'])
    canary.wait_for(['ip', 'link', 'show', 'fcprobe0'])
    canary.run(['ip', 'address', 'add', canary.TUNNEL+'/30', 'dev', 'fcprobe0'])
    canary.run(['ip', 'link', 'set', 'fcprobe0', 'mtu', '1280', 'up'])
    canary.run(['ip', 'route', 'replace', client['origin']+'/32', 'dev', 'fcprobe0'])
    canary.secret('valid.awg', client['awg'].encode())
    canary.run(['/native/awg', 'setconf', 'fcprobe0', str(ROOT/'valid.awg')])
    for name in ('tcp', 'mux'):
        client[name]['log'] = dict(loglevel='warning')
        canary.secret(name+'.json', json.dumps(client[name]).encode())
        canary.launch('client-'+name, ['/native/xray', 'run', '-config', str(ROOT/(name+'.json'))])
    return probe(True)


def probe(success, foreign=True):
    client = json.loads((ROOT/'client.json').read_text())
    nonce = uuid.uuid4().hex
    for name, arguments in [('tcp', ['--socks5-hostname', '127.0.0.1:19728']),
            ('awg', ['--interface', canary.TUNNEL, '--resolve', canary.DOMAIN+':443:'+client['origin']])]:
        curl(arguments, nonce, success, client['egress'])
    curl(['--socks5-hostname', '127.0.0.1:19729'], nonce, foreign, client['egress'])
    return dict(awg=success, tcp=success, foreign_mux_user=foreign)


def curl(arguments, nonce, success, peer):
    result = canary.run(['curl','--silent','--show-error','--fail','--max-time','20' if success else '4',
        '--connect-timeout','8' if success else '3','--cacert',str(ROOT/'origin.crt'),
        '--proxy','','--noproxy','',*arguments,'https://'+canary.DOMAIN+'/canary/'+nonce],check=False,timeout=22)
    if success:
        assert result.returncode == 0, 'TLS probe failed: '+result.stderr.decode()
        assert json.loads(result.stdout) == dict(path='/canary/'+nonce, peer=peer)
    else:
        assert result.returncode != 0


def echo_origin():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(ROOT/'tls.crt', ROOT/'tls.key')
    def echo(connection):
        try:
            with context.wrap_socket(connection, server_side=True) as channel:
                while True:
                    data = channel.recv(4096)
                    if not data:
                        break
                    channel.sendall(data)
        except OSError:
            pass
    with socket.create_server(('0.0.0.0', 8443)) as listener:
        while True:
            connection, address = listener.accept()
            threading.Thread(target=echo, args=(connection,), daemon=True).start()


def stream(name, port):
    client = json.loads((ROOT/'client.json').read_text())
    result = dict(started=time.time(), acknowledged=None, stopped=None, count=0)
    try:
        if port:
            channel = socket.create_connection(('127.0.0.1', port), timeout=3)
            channel.sendall(b'\x05\x01\x00')
            assert channel.recv(2) == b'\x05\x00'
            address = canary.DOMAIN.encode()
            channel.sendall(b'\x05\x01\x00\x03'+bytes([len(address)])+address+(8443).to_bytes(2,'big'))
            response = channel.recv(10)
            assert response[:2] == b'\x05\x00'
        else:
            channel = socket.create_connection((client['origin'], 8443), timeout=3, source_address=(canary.TUNNEL, 0))
        context = ssl.create_default_context(cafile=str(ROOT/'origin.crt'))
        with context.wrap_socket(channel, server_hostname=canary.DOMAIN) as channel:
            channel.settimeout(2)
            while True:
                nonce = uuid.uuid4().hex.encode()
                channel.sendall(nonce)
                assert channel.recv(len(nonce)) == nonce
                result.update(acknowledged=time.time(), count=result['count']+1)
                write(ROOT/(name+'.stream.json'), result)
                time.sleep(.1)
    except (OSError, AssertionError):
        result['stopped'] = time.time()
        write(ROOT/(name+'.stream.json'), result)


def main():
    os.umask(0o077)
    ROOT.mkdir(exist_ok=True)
    action = sys.argv[1]
    if action == 'echo':
        echo_origin()
        return
    if action == 'stream':
        stream(sys.argv[2], int(sys.argv[3]))
        return
    if action == 'watch':
        from control.friends.transport_gateway import watch
        watch(module(), run=execute)
        return
    if action == 'run-awg':
        module().run()
        return
    value = json.load(sys.stdin)
    if action == 'gateway':
        result = setup_gateway(value)
    elif action == 'client':
        result = start_client(value)
    elif action == 'transition':
        result = transition(value)
    elif action == 'probe':
        result = probe(value['allowed'], value.get('foreign', True))
    elif action == 'info':
        result = information()
    elif action == 'late-registration':
        import io
        gateway = module()
        engine = Gateway(gateway, run=execute)
        old = json.loads((ROOT/'old-allow.json').read_text())
        identity=json.loads((ROOT/'identity.json').read_text())
        decision = next(item for item in old['decisions'] if item['device']==identity['device'])
        old['decisions']=[decision]
        request = {name: decision[name] for name in ('device', 'public_key', 'tcp_id')}
        request['paid'] = old
        before = engine.path.read_bytes()
        gateway.paid_engine = lambda: engine
        gateway.sys.stdin = io.TextIOWrapper(io.BytesIO(json.dumps(request).encode()))
        try:
            gateway.register()
        except ValueError:
            assert engine.path.read_bytes() == before
            result = dict(rejected=True, state_unchanged=True)
        else:
            raise AssertionError('Late allow accepted')
    elif action == 'partial-denial':
        import io
        canary.stop('watch')
        identity=json.loads((ROOT/'identity.json').read_text())
        with paid_beta.connection(ROOT/'registry.sqlite3',write=True) as database:
            paid_beta.apply_event(database,identity['support'],'expire','native-partial-expire','synthetic-native-fixture',now=int(time.time()))
        gateway=module()
        def failed_restart(arguments):
            if arguments[:2]==['systemctl','restart']:
                raise subprocess.CalledProcessError(1,arguments)
            return execute(arguments)
        engine=Gateway(gateway,run=failed_restart)
        gateway.paid_engine=lambda:engine
        request=dict(operation='reconcile',paid=policy.snapshot(ROOT/'registry.sqlite3','gateway-ru'))
        gateway.sys.stdin=io.TextIOWrapper(io.BytesIO(json.dumps(request).encode()))
        try:
            gateway.register()
        except subprocess.CalledProcessError:
            persisted=json.loads((ROOT/'friends-tcp/server.json').read_text())
            assert identity['device']+'@family.test' not in json.dumps(persisted)
            assert information()['state']=='expired'
            result=dict(fail_closed=True,persisted_denial=True)
        else:
            raise AssertionError('Expected restart fault')
    elif action == 'terminal-payment':
        try:
            transition(dict(operation='payment',event_id='native-terminal-payment',seconds=7200))
        except paid_beta.PaidBetaError:
            result = dict(rejected=True, state=information()['state'])
        else:
            raise AssertionError('Terminal revoke restored')
    elif action == 'corrupt-state':
        canary.stop('watch')
        engine = Gateway(module(), run=execute)
        engine.path.write_text('{}')
        process = subprocess.run(['python3','/transport_fixture.py','watch'], capture_output=True, timeout=15)
        assert process.returncode != 0
        assert json.loads((engine.root/'transport-attempt.json').read_text())['result'] == 'error'
        result = dict(fail_closed=True, watcher_exit=process.returncode)
    elif action == 'restart-denied':
        canary.stop('watch')
        canary.stop('server-awg')
        canary.run(['ip','link','del','fcprobe0'],check=False)
        canary.run(['nft','delete','table','ip','fc_canary'],check=False)
        engine = Gateway(module(), run=execute)
        engine.apply(starting=True)
        execute(['systemctl','restart','family-connect-friends-tcp.service'])
        canary.launch('server-awg', ['python3','/transport_fixture.py','run-awg'])
        canary.wait_for(['ip','link','show','fcprobe0'])
        result = information()
    elif action == 'streams':
        for name, port in [('awg', 0), ('tcp', 19728), ('mux1', 19729), ('mux2', 19729)]:
            canary.stop('stream-'+name)
            canary.launch('stream-'+name, ['python3', '/transport_fixture.py', 'stream', name, str(port)])
        result = {'started': True}
    elif action == 'stream-results':
        result = {name: json.loads((ROOT/(name+'.stream.json')).read_text()) for name in ('awg','tcp','mux1','mux2')}
    else:
        raise ValueError('Unknown fixture action')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
