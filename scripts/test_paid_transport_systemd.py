"""Real systemd/preflight and native engines on disposable private Docker nodes."""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import traceback

from test_fleet_canary import call, cleanup, inspect, verify_container, LABEL, ROOT


def execute(kit, report, *, recovery_diagnostics=False, lifecycle_diagnostics=False, expect_restart_loop=False):
    os.umask(0o077)
    prefix = 'fc-enforcement-fix-' + secrets.token_hex(5)
    receipt = dict(result='FAIL',run_id=prefix,production_writes=0,checks={})
    containers = {}
    with report.open('x') as output:
        try:
            with tempfile.TemporaryDirectory(prefix='fc-systemd-image-') as temporary:
                context = Path(temporary)
                shutil.copytree(kit,context/'kit')
                shutil.copyfile(ROOT/'pilot/fleet_canary.py', context/'canary.py')
                shutil.copyfile(ROOT/'pilot/transport-production-tcp.service', context/'production-tcp.service')
                shutil.copyfile(ROOT/'pilot/transport-production-awg.service', context/'production-awg.service')
                for source,target in (('transport_enforcement_fixture.py','transport_fixture.py'),('transport_systemd_fixture.py','systemd_fixture.py')):
                    shutil.copyfile(ROOT/'pilot'/source,context/target)
                (context/'Dockerfile').write_text('FROM sha256:af9c993c2fcd60804ef576e2190dee88699830624ec74317a91eb6d9855284e9\nCOPY kit /kit\nCOPY canary.py transport_fixture.py systemd_fixture.py production-tcp.service production-awg.service /\nENTRYPOINT ["sleep","1800"]\n')
                image = prefix+':local'
                built = call(['docker','build','-t',image,str(context)],timeout=300,check=False)
                (report.parent/(prefix+'-build.log')).write_bytes(built.stdout+built.stderr)
                assert built.returncode == 0, 'fixture image build'
            receipt['image_id'] = inspect('image',image)['Id']
            receipt['kit'] = {path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in kit.iterdir() if path.is_file()}
            for kind in ('entry','egress'):
                subnet = ['--subnet',f'198.18.{secrets.randbelow(200)+20}.0/24'] if kind == 'egress' else []
                call(['docker','network','create','--internal','--label',LABEL+'='+prefix,*subnet,prefix+'-'+kind])
            roles = ('origin','client','gateway-ru','nl-amsterdam-1','nl-amsterdam-2')
            for role in roles:
                systemd = role not in ('origin','client')
                network = 'egress' if role == 'origin' else 'entry'
                command = ['docker','run','-d','--name',prefix+'-'+role,'--label',LABEL+'='+prefix,
                    '--network',prefix+'-'+network,'--cpus','.6','--memory','448m','--pids-limit','192',
                    '--tmpfs','/run:mode=755','--tmpfs','/run/lock','--tmpfs','/tmp:mode=1777','-e','GOMAXPROCS=2']
                if systemd:
                    command += ['--cgroupns','private','--cap-add','SYS_ADMIN','--cap-add','NET_ADMIN',
                        '--security-opt','seccomp=unconfined','--security-opt','apparmor=unconfined',
                        '--device','/dev/net/tun','--sysctl','net.ipv4.ip_forward=1','--entrypoint','/bin/sh',image,'-c',
                        'umount /sys/fs/cgroup && mount -t cgroup2 none /sys/fs/cgroup && exec /lib/systemd/systemd --system --unit=multi-user.target']
                else:
                    command += ['--read-only','--cap-drop','ALL','--cap-add','NET_BIND_SERVICE','--security-opt','no-new-privileges:true']
                    if role == 'client':
                        command += ['--cap-add','NET_ADMIN','--device','/dev/net/tun']
                    command += [image]
                containers[role] = call(command).stdout.decode().strip()
                if systemd:
                    call(['docker','network','connect',prefix+'-egress',containers[role]])
            addresses = {}
            for role,container in containers.items():
                actual = inspect('container',container)
                networks = [prefix+'-egress'] if role == 'origin' else [prefix+'-entry']
                if role not in ('origin','client'):
                    networks.append(prefix+'-egress')
                    config = actual['HostConfig']
                    assert not config['Privileged'] and not config['Binds'] and not config['PortBindings'] and not config['PidMode']
                    assert config['CgroupnsMode'] == 'private' and config['Memory'] == 448*1024*1024
                    assert set(actual['NetworkSettings']['Networks']) == set(networks)
                    assert all(mount['Type']=='tmpfs' for mount in actual['Mounts'])
                    assert call(['docker','exec',container,'cat','/proc/1/comm']).stdout.strip()==b'systemd'
                    assert call(['docker','exec',container,'cat','/proc/1/cgroup']).stdout.strip()==b'0::/init.scope'
                else:
                    verify_container(actual,prefix,networks,role)
                addresses[role] = actual['NetworkSettings']['Networks']
            receipt['isolation'] = 'private PID/mount/network/cgroup namespaces; no host mounts/socket/ports; bounded resources'

            def inner(role, action, value=None, script='/systemd_fixture.py', check=True):
                receipt['phase'] = role+':'+action
                process = call(['docker','exec','-i',containers[role],'python3',script,action],payload=json.dumps(value or {}).encode(),timeout=90,check=False)
                if process.returncode:
                    (report.parent/(prefix+'-failure.private.log')).write_bytes(process.stdout+process.stderr)
                    if check:
                        raise RuntimeError('systemd fixture command failed')
                    return process
                return json.loads(process.stdout)

            origin = addresses['origin'][prefix+'-egress']['IPAddress']
            certificate = inner('origin','origin',dict(address=origin),'/canary.py')
            call(['docker','exec','-d',containers['origin'],'python3','/transport_fixture.py','echo'])
            materials = {}
            nodes = roles[2:]
            for node in nodes:
                materials[node] = inner(node,'material',dict(origin=origin,gateway=addresses[node][prefix+'-entry']['IPAddress'],
                    egress=addresses[node][prefix+'-egress']['IPAddress'],certificate=certificate))
            sys.path.insert(0,str(kit/'paid-reconcile.pyz'))
            import RNS
            from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
            from control.friends import paid_beta, transport_policy as policy, transport_reconcile, support_ids
            from control.friends.access import Access
            from device_identity.device import DeviceIdentity
            assert paid_beta.__loader__.archive == str(kit/'paid-reconcile.pyz')
            central = report.parent/(prefix+'-central')
            central.mkdir(mode=0o700)
            access = Access(central/'registry.sqlite3')
            access.initialize()
            private = base64.b64decode(re.search(r'PrivateKey = ([^\n]+)',materials['gateway-ru']['awg']).group(1))
            identities = [DeviceIdentity(RNS.Identity(),X25519PrivateKey.from_private_bytes(private))]+[DeviceIdentity.generate() for index in range(62)]
            bound = []
            for identity in identities:
                challenge = access.challenge(identity.public_identity,identity.wireguard_public_key,'activate',access.invite())
                bound.append(access.complete(identity.prove_transport_key(challenge['challenge']),'activate'))
            with access.db() as database:
                support = support_ids.registered(database,identities[0].reference)
                database.execute('UPDATE device_support SET platform=?,app_version=?,version_code=?,last_seen=? WHERE device=?',
                    ('android','0.1.18-beta108',108,int(time.time()),identities[0].reference))
            with paid_beta.connection(access.path,write=True) as database:
                paid_beta.migrate(database)
            commands = {node:['docker','exec','-i',containers[node],'/usr/bin/python3','/opt/apps/family_connect/friends-awg/awg-gateway.py','register'] for node in nodes}
            commands_path = central/'transport-commands.json'
            commands_path.write_text(json.dumps(commands))
            (central/'transport-enforcement.json').write_text(json.dumps(dict(schema=1,profile=policy.PROFILE,enabled=True,hosts={node:node for node in nodes})))
            client = None
            registrations = dict(zip(nodes, (identities[:19], identities[:4]+identities[19:], identities[1:6])))
            for node in nodes:
                result = inner(node,'setup',dict(node=node,envelope=policy.snapshot(access.path,node),registered=[identity.reference for identity in registrations[node]]))
                if node=='gateway-ru':
                    client=result['client']
                assert 'paid-preflight' in result['info']['preflight']
            inner('client','client',dict(client=client))
            inner('client','probe',dict(allowed=True))
            receipt['checks']['actual_packaged_preflight_all_nodes'] = True

            def operator(kind, event_id, *, start=None, end=None, expect=0):
                args=[sys.executable,'-I',str(kit/'paid-operator.pyz'),'--db',str(access.path),kind,'--support-id',support,
                    '--event-id',event_id,'--reference','synthetic-systemd-only']
                if kind=='activate':
                    utc=lambda value:datetime.fromtimestamp(value,timezone.utc).isoformat().replace('+00:00','Z')
                    args += ['--period-start',utc(start),'--paid-until',utc(end),'--apk-sha256',paid_beta.PAID_ANDROID_APK_SHA256]
                process=call(args,timeout=50,check=False)
                assert process.returncode==expect, process.stdout.decode()
                return json.loads(process.stdout)

            if recovery_diagnostics or lifecycle_diagnostics:
                start=int(time.time());end=start+1200
                operator('activate','diagnostic-active',start=start,end=end)
                assert transport_reconcile.cycle(access.path,commands)==dict.fromkeys(nodes,'applied')
                inner('client','probe',dict(allowed=True))
                if lifecycle_diagnostics:
                    receipt['checks']['active_lifecycle']=inner('gateway-ru','lifecycle-fault',dict(expect_restart_loop=expect_restart_loop))
                    assert transport_reconcile.cycle(access.path,commands)==dict.fromkeys(nodes,'applied')
                    inner('client','probe',dict(allowed=True))
                operator('revoke','diagnostic-terminal')
                assert transport_reconcile.cycle(access.path,commands)==dict.fromkeys(nodes,'applied')
                if lifecycle_diagnostics:
                    receipt['checks']['terminal_lifecycle']=inner('gateway-ru','lifecycle-fault',dict(expect_restart_loop=expect_restart_loop))
                    if not expect_restart_loop:
                        receipt['checks']['corrupt_state_requires_recovery']=inner('gateway-ru','invalid-start')
                else:
                    receipt['checks']['first_failure_and_controlled_recovery']=inner('gateway-ru','diagnostic-fault')
                assert transport_reconcile.cycle(access.path,commands)==dict.fromkeys(nodes,'applied')
                inner('client','probe',dict(allowed=False))
                receipt['checks']['terminal_deny_and_noncohort_after_recovery']=True
                receipt['checks']['active_actual_https']=True
                receipt['result']='PASS'
                return receipt

            start=int(time.time());end=start+150
            blocked=dict(commands);blocked[nodes[-1]]=[sys.executable,'-c','raise SystemExit(1)']
            commands_path.write_text(json.dumps(blocked))
            denied=operator('activate','systemd-first-paid',start=start,end=end,expect=2)
            assert denied['reason']=='TRANSPORT_PREPARATION_REQUIRED'
            with paid_beta.connection(access.path) as database:
                assert database.execute('SELECT count(*) FROM paid_beta_subscriptions').fetchone()[0]==0
            inner('client','probe',dict(allowed=False))
            assert transport_reconcile.cycle(access.path,commands)==dict.fromkeys(nodes,'applied')
            inner('client','probe',dict(allowed=False))
            receipt['checks']['unavailable_node_blocks_only_first_enrollment'] = True
            wrapper=central/'lost_ack.py'
            wrapper.write_text('import subprocess,sys,json\nrequest=sys.stdin.buffer.read()\nprocess=subprocess.run(json.loads(sys.argv[1]),input=request,stdout=subprocess.DEVNULL)\nraise SystemExit(1)\n')
            blocked[nodes[-1]]=[sys.executable,str(wrapper),json.dumps(commands[nodes[-1]])]
            commands_path.write_text(json.dumps(blocked))
            operator('activate','systemd-first-paid',start=start,end=end,expect=2)
            inner('gateway-ru','restart')
            inner('client','probe',dict(allowed=False))
            receipt['checks']['pending_membership_survives_real_service_restart']=True
            commands_path.write_text(json.dumps(commands))
            accepted=operator('activate','systemd-first-paid',start=start,end=end)
            assert not accepted['duplicate']
            assert operator('activate','systemd-first-paid',start=start,end=end)['duplicate']
            assert transport_reconcile.cycle(access.path,commands)==dict.fromkeys(nodes,'applied')
            inner('client','probe',dict(allowed=True))
            receipt['checks']['lost_ack_retry_canonical_exact_replay'] = True
            inner('client','streams',script='/transport_fixture.py')
            time.sleep(1)
            opened=inner('client','stream-results',script='/transport_fixture.py')
            assert all(row['count'] and row['stopped'] is None for row in opened.values())
            while time.time() < end:
                time.sleep(min(20, max(0,end-time.time())))
                assert transport_reconcile.cycle(access.path,commands)==dict.fromkeys(nodes,'applied')
            time.sleep(6)
            info=inner('gateway-ru','info')
            assert all('ActiveState=active' in value for value in info['services'].values())
            stopped=inner('client','stream-results',script='/transport_fixture.py')
            delays={name:row['stopped']-end for name,row in stopped.items()}
            assert all(-1<=delay<=25 for delay in delays.values())
            receipt['checks']['natural_expiry_seconds']=delays
            inner('client','probe',dict(allowed=False))
            start=int(time.time());end=start+1200
            operator('activate','systemd-renewal',start=start,end=end)
            assert transport_reconcile.cycle(access.path,commands)==dict.fromkeys(nodes,'applied')
            inner('client','probe',dict(allowed=True))
            before=inner('gateway-ru','info')
            assert transport_reconcile.cycle(access.path,commands)==dict.fromkeys(nodes,'applied')
            after=inner('gateway-ru','info')
            assert before['services']==after['services']
            receipt['checks']['renewal_and_duplicate_no_extra_restart']=True
            stable_services = {node:inner(node,'info')['services'] for node in nodes}
            stable_started = time.monotonic()
            cycles = []
            while time.monotonic()-stable_started < 360:
                with ThreadPoolExecutor(max_workers=2) as pool:
                    request={key:bound[1][key] for key in ('device','public_key','tcp_id')}
                    request['paid']=policy.snapshot(access.path,'gateway-ru',device=identities[1].reference)
                    registration=pool.submit(call,commands['gateway-ru'],payload=json.dumps(request).encode(),timeout=20)
                    refresh=pool.submit(transport_reconcile.cycle,access.path,commands)
                    assert registration.result().returncode==0
                    assert refresh.result()==dict.fromkeys(nodes,'applied')
                cycles.append(time.monotonic()-stable_started)
                time.sleep(20)
            receipt['checks']['stable_63_records_19_48_5'] = dict(seconds=time.monotonic()-stable_started, cycles=cycles)
            before=inner('gateway-ru','info')
            after=before
            for node in nodes:
                assert inner(node,'info')['services'] == stable_services[node], 'unexpected restart during stable window'
                journal=call(['docker','exec',containers[node],'journalctl','-u',SERVICES_WATCH,'-o','cat','--no-pager']).stdout
                (report.parent/(prefix+'-'+node+'-progress.private.log')).write_bytes(journal)
                measurements=[json.loads(line) for line in journal.decode().splitlines() if line.startswith('{"transport_progress')]
                passes=[item['transport_progress'] for item in measurements if 'transport_progress' in item and item['transport_progress']['result']=='complete']
                gaps=[item['transport_progress_gap'] for item in measurements if 'transport_progress_gap' in item]
                maximum=dict(total=max(item['total'] for item in passes),progress_gap=max(gaps),
                    stages={stage:max(item['stages'].get(stage,0) for item in passes) for stage in {stage for item in passes for stage in item['stages']}})
                assert maximum['total']<8 and maximum['progress_gap']<12
                receipt['checks']['maxima_'+node]=maximum
            lease=after['state']['records'][identities[0].reference]['decision']['valid_until']
            inner('client','streams',script='/transport_fixture.py')
            time.sleep(max(0,lease-time.time())+6)
            inner('client','probe',dict(allowed=False))
            after=inner('gateway-ru','info')
            assert before['services'][SERVICES_WATCH]==after['services'][SERVICES_WATCH]
            stopped=inner('client','stream-results',script='/transport_fixture.py')
            receipt['checks']['paid_lease_cutoff_noncohort_survives']={name:row['stopped']-lease for name,row in stopped.items()}
            assert all(-1<=delay<=25 for delay in receipt['checks']['paid_lease_cutoff_noncohort_survives'].values())
            with ThreadPoolExecutor(max_workers=2) as pool:
                request=dict(bound[2],paid=policy.snapshot(access.path,'gateway-ru',device=identities[2].reference))
                request={key:request[key] for key in ('device','public_key','tcp_id','paid')}
                registration=pool.submit(call,commands['gateway-ru'],payload=json.dumps(request).encode(),timeout=20)
                refresh=pool.submit(transport_reconcile.cycle,access.path,commands)
                assert registration.result().returncode==0 and refresh.result()==dict.fromkeys(nodes,'applied')
            inner('client','probe',dict(allowed=True))
            receipt['checks']['concurrent_registration_and_watcher']=True
            inner('gateway-ru','fault')
            operator('expire','systemd-expire-fault')
            failed=transport_reconcile.cycle(access.path,commands)
            assert failed['gateway-ru']=='unavailable'
            info=inner('gateway-ru','info')
            assert all('ActiveState=active' not in value for key,value in info['services'].items() if key!=SERVICES_WATCH)
            inner('gateway-ru','recover')
            assert transport_reconcile.cycle(access.path,commands)==dict.fromkeys(nodes,'applied')
            inner('client','probe',dict(allowed=False))
            receipt['checks']['actual_preflight_failure_and_recovery']=True
            operator('activate','systemd-renewal-after-failure',start=int(time.time()),end=end+600)
            assert transport_reconcile.cycle(access.path,commands)==dict.fromkeys(nodes,'applied')
            receipt['checks']['restored_profile_after_engine_restart']=inner('client','probe',dict(allowed=True))
            for interval in range(7):
                time.sleep(20)
                assert transport_reconcile.cycle(access.path,commands)==dict.fromkeys(nodes,'applied')
            for fault in ('lock', 'engine'):
                receipt['checks']['bounded_'+fault] = inner('gateway-ru','budget-fault',dict(kind=fault))
                assert transport_reconcile.cycle(access.path,commands)==dict.fromkeys(nodes,'applied')
                inner('client','probe',dict(allowed=True))
            operator('revoke','systemd-terminal-revoke')
            assert transport_reconcile.cycle(access.path,commands)==dict.fromkeys(nodes,'applied')
            inner('gateway-ru','restart')
            inner('client','probe',dict(allowed=False))
            receipt['checks']['restart_denial_noncohort_survives']=True
            receipt['result']='PASS'
        except Exception as error:
            (report.parent/(prefix+'-traceback.private.txt')).write_text(traceback.format_exc())
            receipt['error']=type(error).__name__+':'+str(error)[:300]
            diagnostics={role:call(['docker','exec',container,'sh','-c','journalctl --no-pager -n 160; cat /run/fc-canary/*.log 2>/dev/null; ip route; ip address; iptables -t nat -S; /native/awg show all'],check=False).stdout.decode(errors='replace') for role,container in containers.items()}
            (report.parent/(prefix+'-diagnostics.private.json')).write_text(json.dumps(diagnostics))
        finally:
            failures=cleanup(prefix)
            receipt['cleanup']='FAIL' if failures else 'PASS'
            if failures:receipt['result']='FAIL'
            json.dump(receipt,output,indent=2)
    return receipt


SERVICES_WATCH='family-connect-paid-watch.service'

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--recovery-diagnostics',action='store_true',help='Only first-failure diagnostics, controlled recovery and real positive/deny flows')
    parser.add_argument('--lifecycle-diagnostics',action='store_true',help='Watcher loss, dependent stops, restart behavior, retained deny and controlled recovery')
    parser.add_argument('--expect-restart-loop',action='store_true',help='Reproduce the historical loop using the exact old package, not candidate acceptance')
    args=parser.parse_args()
    assert not args.expect_restart_loop or args.lifecycle_diagnostics
    result=execute(args.kit.resolve(),args.report,recovery_diagnostics=args.recovery_diagnostics,
        lifecycle_diagnostics=args.lifecycle_diagnostics,expect_restart_loop=args.expect_restart_loop)
    print(json.dumps(result))
    raise SystemExit(result['result']!='PASS')
