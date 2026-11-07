"""Real engines on disposable internal networks; never contacts production."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import tempfile
import time

from test_fleet_canary import call, cleanup, inspect, verify_container, LABEL, ROOT


def execute(kit, report, faults_only=False):
    os.umask(0o077)
    prefix = 'fc-paid-transport-' + secrets.token_hex(6)
    receipt = dict(result='FAIL', run_id=prefix, production_writes=0, checks={})
    descriptor = os.open(report, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        try:
            with tempfile.TemporaryDirectory(prefix='fc-paid-native-') as temporary:
                context = Path(temporary)
                shutil.copytree(kit, context/'kit')
                shutil.copyfile(ROOT/'pilot/transport_enforcement_fixture.py', context/'transport_fixture.py')
                (context/'Dockerfile').write_text('FROM family-connect-fleet-canary:local\nRUN apt-get update && apt-get install -y --no-install-recommends iptables=1.8.10-3ubuntu2 && rm -rf /var/lib/apt/lists/*\nCOPY kit /kit\nCOPY transport_fixture.py /transport_fixture.py\nENTRYPOINT ["sleep","900"]\n')
                image = 'fc-paid-native:'+prefix
                built = call(['docker', 'build', '-t', image, str(context)], timeout=300, check=False)
                (report.parent/(prefix+'-build.log')).write_bytes(built.stdout+built.stderr)
                if built.returncode:
                    raise RuntimeError('isolated image build failed')
            receipt['image_id'] = inspect('image', image)['Id']
            receipt['kit'] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in kit.iterdir() if path.is_file()}
            receipt['fixture_sha256'] = hashlib.sha256((ROOT/'pilot/transport_enforcement_fixture.py').read_bytes()).hexdigest()
            for network in ('entry', 'egress'):
                subnet = ['--subnet','198.18.'+str(secrets.randbelow(240)+10)+'.0/24'] if network == 'egress' else []
                call(['docker', 'network', 'create', '--internal', '--label', LABEL+'='+prefix, *subnet, prefix+'-'+network])
            containers, details = {}, {}
            for role, network in [('origin','egress'),('gateway','entry'),('client','entry')]:
                command = ['docker','run','-d','--name',prefix+'-'+role,'--label',LABEL+'='+prefix,
                    '--network',prefix+'-'+network,'--read-only','--cap-drop','ALL','--cap-add','NET_BIND_SERVICE',
                    '--security-opt','no-new-privileges:true','--cpus','0.6','--pids-limit','128','--memory','384m',
                    '--tmpfs','/run:mode=755','--tmpfs','/tmp:mode=1777','-e','GOMAXPROCS=2']
                if role != 'origin':
                    command += ['--cap-add','NET_ADMIN','--device','/dev/net/tun']
                if role == 'gateway':
                    command += ['--sysctl','net.ipv4.ip_forward=1']
                containers[role] = call(command+[image]).stdout.decode().strip()
            call(['docker','network','connect',prefix+'-egress',containers['gateway']])
            for role, container in containers.items():
                info = inspect('container', container)
                networks = [prefix+'-egress'] if role == 'origin' else [prefix+'-entry']
                if role == 'gateway':
                    networks.append(prefix+'-egress')
                verify_container(info, prefix, networks, role)
                details[role] = info['NetworkSettings']['Networks']
            def inner(role, action, value, original=False):
                receipt['phase'] = role+':'+action
                result = call(['docker','exec','-i',containers[role],'python3',
                    '/canary.py' if original else '/transport_fixture.py',action],payload=json.dumps(value).encode(),timeout=150,check=False)
                if result.returncode:
                    (report.parent/(prefix+'-failure.private.txt')).write_bytes(result.stderr)
                    raise RuntimeError('native fixture failed')
                return json.loads(result.stdout)
            origin = details['origin'][prefix+'-egress']['IPAddress']
            certificate = inner('origin','origin',dict(address=origin),True)
            call(['docker','exec','-d',containers['origin'],'python3','/transport_fixture.py','echo'])
            client = inner('gateway','gateway',dict(origin=origin, gateway=details['gateway'][prefix+'-entry']['IPAddress'],
                egress=details['gateway'][prefix+'-egress']['IPAddress'],certificate=certificate))
            receipt['checks']['noncohort'] = inner('client','client',client)
            receipt['checks']['active'] = inner('gateway','transition',dict(operation='payment',event_id='native-active-001',seconds=60))
            inner('client','probe',dict(allowed=True))
            if faults_only:
                receipt['checks']['partial_denial']=inner('gateway','partial-denial',{})
                receipt['checks']['all_engines_stopped']=inner('client','probe',dict(allowed=False,foreign=False))
                receipt['checks']['partial_restart']=inner('gateway','restart-denied',{})
                inner('client','probe',dict(allowed=False))
                receipt['checks']['late_registration']=inner('gateway','late-registration',{})
                receipt['checks']['recovery']=inner('gateway','transition',dict(operation='payment',event_id='native-fault-recovery',seconds=3600))
                inner('client','probe',dict(allowed=True))
                receipt['result']='PASS'
                return receipt
            inner('client','streams',{})
            time.sleep(1)
            opened = inner('client','stream-results',{})
            assert all(value['count'] >= 1 and value['stopped'] is None for value in opened.values())
            receipt['checks']['opened_streams'] = {name: value['count'] for name,value in opened.items()}
            receipt['checks']['explicit_expire'] = inner('gateway','transition',dict(operation='expire',event_id='native-expire-001'))
            time.sleep(3)
            stopped = inner('client','stream-results',{})
            assert all(value['stopped'] is not None for value in stopped.values())
            receipt['checks']['open_stream_cutoff_seconds'] = {name: value['stopped']-receipt['checks']['explicit_expire']['operation_started'] for name,value in stopped.items()}
            receipt['checks']['expired_profile'] = inner('client','probe',dict(allowed=False))
            receipt['checks']['late_registration'] = inner('gateway','late-registration',{})
            receipt['checks']['renewal'] = inner('gateway','transition',dict(operation='payment',event_id='native-renewal-001',seconds=65))
            inner('client','probe',dict(allowed=True))
            receipt['checks']['grace'] = inner('gateway','transition',dict(operation='grace',event_id='native-grace-001',seconds=80))
            inner('client','probe',dict(allowed=True))
            inner('client','streams',{})
            boundary = inner('gateway','info',{})['valid_until']
            time.sleep(81)
            receipt['checks']['natural_expiry'] = inner('gateway','info',{})
            stopped = inner('client','stream-results',{})
            assert all(value['stopped'] is not None for value in stopped.values())
            receipt['checks']['natural_cutoff_seconds'] = {name: value['stopped']-boundary for name,value in stopped.items()}
            assert all(-1 <= delay <= 25 for delay in receipt['checks']['natural_cutoff_seconds'].values())
            inner('client','probe',dict(allowed=False))
            receipt['checks']['second_renewal'] = inner('gateway','transition',dict(operation='payment',event_id='native-renewal-002',seconds=3600))
            inner('client','probe',dict(allowed=True))
            inner('client','streams',{})
            lease = inner('gateway','info',{})['valid_until']
            time.sleep(max(0,lease-time.time())+4)
            stopped = inner('client','stream-results',{})
            assert all(value['stopped'] is not None for value in stopped.values())
            receipt['checks']['center_loss_cutoff_seconds'] = {name:value['stopped']-lease for name,value in stopped.items()}
            assert all(-1 <= delay <= 25 for delay in receipt['checks']['center_loss_cutoff_seconds'].values())
            inner('client','probe',dict(allowed=False))
            receipt['checks']['center_recovery'] = inner('gateway','transition',dict(operation='refresh'))
            inner('client','probe',dict(allowed=True))
            receipt['checks']['revoke'] = inner('gateway','transition',dict(operation='revoke',event_id='native-revoke-001'))
            receipt['checks']['terminal_payment'] = inner('gateway','terminal-payment',{})
            inner('client','probe',dict(allowed=False))
            receipt['checks']['restart_denied'] = inner('gateway','restart-denied',{})
            inner('client','probe',dict(allowed=False))
            receipt['checks']['corrupt_state'] = inner('gateway','corrupt-state',{})
            receipt['result'] = 'PASS'
        except Exception as error:
            receipt['error'] = type(error).__name__
            diagnostics = {}
            for role, container in locals().get('containers', {}).items():
                diagnostics[role] = call(['docker','exec',container,'sh','-c',
                    'cat /run/fc-canary/*.log 2>/dev/null; ip route; ss -tnp'], check=False).stdout.decode(errors='replace')
            (report.parent/(prefix+'-logs.private.json')).write_text(json.dumps(diagnostics))
        finally:
            failures = cleanup(prefix)
            receipt['cleanup'] = 'PASS' if not failures else 'FAIL'
            if failures:
                receipt['result'] = 'FAIL'
            json.dump(receipt,output,indent=2)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit',required=True,type=Path)
    parser.add_argument('--report',required=True,type=Path)
    parser.add_argument('--faults-only',action='store_true')
    args = parser.parse_args()
    result = execute(args.kit,args.report,args.faults_only)
    print(json.dumps(result))
    raise SystemExit(result['result'] != 'PASS')
