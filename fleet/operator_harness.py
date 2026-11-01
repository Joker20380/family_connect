"""Operator-only fixed probes. No invitations, payments or node-side PASS signer."""

import base64
import ipaddress
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from cryptography import x509
from cryptography.hazmat.primitives import serialization

from .acceptance import SCOPE, STEPS, sign
from .contracts import canonical, digest, exact, fail, load
from .materials import public_hex
from .private_files import read_private, remove_private, write_private
from .role_config import SNI, key32

PROBE_IDENTITY_SHA256='30b63836c67b99bff6578933db9055d17a272c4abe74a6f6ea38375e3729acad'


def stop_process(process):
    process.terminate()
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=15)


def command(argv, *, timeout=90, check=True, env=None):
    try:
        result=subprocess.run(argv,capture_output=True,timeout=timeout,env=env)
    except (OSError,subprocess.TimeoutExpired):
        fail('operator_probe_unavailable')
    if check and result.returncode:
        fail('operator_probe_failed')
    return result


def mesh_result(raw):
    events=[load(line) for line in raw.splitlines() if line.startswith(b'{')]
    required=('bootstrap_normal_control_unavailable','bootstrap_cache_loaded','bootstrap_closed_before_dedicated')
    if (any(not any(event.get('event')==name for event in events) for name in required)
            or not any(event.get('event')=='family_auth' and event.get('accepted') is True for event in events)
            or not any(event.get('event')=='mux_result' and event.get('status')=='PASS' for event in events)
            or len([event for event in events if event.get('event')=='mux_https' and event.get('passed') is True])!=4
            or len([event for event in events if event.get('event')=='mux_dns' and event.get('passed') is True])!=3
            or not any(event.get('event')=='fleet_probe_egress' and event.get('passed') is True
                       and event.get('expected_rehearsal_egress') is True for event in events)):
        fail('operator_mesh_evidence_incomplete')
    return {step:'PASS' for step in STEPS['mesh']}


class Harness:
    def __init__(self, configuration, contents, manifest, *, target, challenge):
        exact(configuration,('native_directory','operator_probe','awg_peer','tcp_client','mesh_profile','probe_identity'))
        self.config=configuration
        self.target=target
        self.challenge=challenge
        self.contents=contents
        self.native=Path(configuration['native_directory'])
        self.probe=Path(configuration['operator_probe'])
        expected={member['path']:member['sha256'] for member in manifest['members']}
        for name in ('amneziawg-go','awg','xray'):
            from .bundle import source_bytes
            if digest(source_bytes(self.native,name,64*1024*1024))!=expected['bin/'+name]:
                fail('operator_native_binding')
        probe_metadata=load(contents['metadata/operator-probe.json'])
        if self.probe.is_symlink() or not self.probe.is_file() or self.probe.stat().st_nlink!=1 or digest(self.probe.read_bytes())!=probe_metadata['sha256']:
            fail('operator_mesh_probe_binding')
        if os.geteuid()!=0:
            fail('operator_awg_root_required')
        addresses=load(command(['ip','-j','address','show']).stdout)
        if target in {entry['local'] for interface in addresses for entry in interface.get('addr_info',[])}:
            fail('operator_must_not_be_target_node')

    def web(self, prefix):
        def request(host, resource):
            options=list(prefix)
            if prefix==['--interface','10.203.217.2']:
                response=command(['dig','-b','10.203.217.2','@9.9.9.9',host,'A','+short']).stdout.decode()
                addresses=[]
                for line in response.splitlines():
                    try:address=ipaddress.IPv4Address(line)
                    except ValueError:continue
                    if address.is_global:addresses.append(str(address))
                if not addresses:fail('operator_awg_https_dns')
                options+=['--resolve',host+':443:'+addresses[0]]
            return command(['curl','--silent','--show-error','--fail','--max-time','45',*options,'https://'+host+resource])
        request('example.com','/')
        egress=request('www.cloudflare.com','/cdn-cgi/trace').stdout.decode()
        if 'ip='+self.target not in egress.splitlines():
            fail('operator_egress_mismatch')

    def awg(self, directory):
        value=load(read_private(self.config['awg_peer']))
        exact(value,('scope','server_public_key','peer_private_key'))
        if value['scope']!='DISPOSABLE_FLEET_REHEARSAL':
            fail('operator_awg_scope')
        key32(value['server_public_key'])
        key32(value['peer_private_key'])
        if command(['ip','link','show','dev','fcrhp0'],check=False).returncode==0:
            fail('operator_awg_interface_busy')
        rules=command(['ip','rule','show']).stdout
        if (command(['ip','route','show','table','50027'],check=False).stdout.strip() or b'50027' in rules
                or any(line.split(b':',1)[0].strip()==b'12027' for line in rules.splitlines())):
            fail('operator_awg_route_busy')
        config=directory/'awg.conf'
        text=('[Interface]\nPrivateKey = '+value['peer_private_key']+'\nJc = 4\nJmin = 40\nJmax = 70\n'
            'S1 = 81\nS2 = 93\nS3 = 17\nS4 = 23\nH1 = 1010123\nH2 = 2020234\nH3 = 3030345\nH4 = 4040456\n'
            '[Peer]\nPublicKey = '+value['server_public_key']+'\nEndpoint = '+self.target+':51827\n'
            'AllowedIPs = 0.0.0.0/0\nPersistentKeepalive = 5\n')
        write_private(config,text.encode())
        process=subprocess.Popen([str(self.native/'amneziawg-go'),'-f','fcrhp0'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        route=False
        rule=False
        try:
            for attempt in range(50):
                if command(['ip','link','show','dev','fcrhp0'],check=False).returncode==0:
                    break
                time.sleep(0.1)
            else:
                fail('operator_awg_start')
            command([str(self.native/'awg'),'setconf','fcrhp0',str(config)])
            command(['ip','address','add','10.203.217.2/30','dev','fcrhp0'])
            command(['ip','link','set','dev','fcrhp0','mtu','1280','up'])
            command(['ip','route','add','default','dev','fcrhp0','table','50027'])
            route=True
            command(['ip','rule','add','priority','12027','from','10.203.217.2','table','50027'])
            rule=True
            dns=command(['dig','-b','10.203.217.2','@9.9.9.9','example.com','A','+short']).stdout
            if not dns.strip():
                fail('operator_awg_dns')
            self.web(['--interface','10.203.217.2'])
            handshake=command([str(self.native/'awg'),'show','fcrhp0','latest-handshakes']).stdout.decode().split()
            if len(handshake)!=2 or handshake[0]!=value['server_public_key'] or int(handshake[1])<self.challenge['started_at']:
                fail('operator_awg_handshake')
        finally:
            clean=True
            try:
                if rule:
                    clean &= command(['ip','rule','del','priority','12027','from','10.203.217.2','table','50027'],check=False).returncode==0
                if route:
                    clean &= command(['ip','route','del','default','dev','fcrhp0','table','50027'],check=False).returncode==0
            finally:
                stop_process(process)
                if command(['ip','link','show','dev','fcrhp0'],check=False).returncode==0:
                    command(['ip','link','delete','fcrhp0'])
                remove_private(config)
            if not clean:
                fail('operator_awg_cleanup')
        return {step:'PASS' for step in STEPS['awg']}

    def tcp(self, directory):
        value=load(read_private(self.config['tcp_client']))
        exact(value,('scope','uuid','public_key','short_id','sni'))
        import re
        import uuid
        if (value['scope']!='DISPOSABLE_FLEET_REHEARSAL' or value['sni']!=SNI
                or str(uuid.UUID(value['uuid']))!=value['uuid'] or not re.fullmatch('[0-9a-f]{16}',value['short_id'])
                or not re.fullmatch('[A-Za-z0-9_-]{43}',value['public_key'])):
            fail('operator_tcp_material')
        import socket
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',19728))
        config=directory/'tcp.json'
        content=dict(log=dict(loglevel='none'),inbounds=[dict(listen='127.0.0.1',port=19728,protocol='socks',settings=dict(auth='noauth',udp=False))],
            outbounds=[dict(protocol='vless',settings=dict(vnext=[dict(address=self.target,port=4443,users=[dict(id=value['uuid'],encryption='none',flow='xtls-rprx-vision')])]),
                streamSettings=dict(network='tcp',security='reality',realitySettings=dict(serverName=SNI,fingerprint='chrome',publicKey=value['public_key'],shortId=value['short_id'],spiderX='/')))])
        write_private(config,canonical(content))
        command([str(self.native/'xray'),'run','-test','-config',str(config)])
        process=subprocess.Popen([str(self.native/'xray'),'run','-config',str(config)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            time.sleep(1)
            if process.poll() is not None:
                fail('operator_tcp_start')
            self.web(['--socks5-hostname','127.0.0.1:19728'])
        finally:
            stop_process(process)
            remove_private(config)
        return {step:'PASS' for step in STEPS['tcp']}

    def mesh(self, directory):
        from device_identity.friends import load_friends_identity
        identity=load_friends_identity(self.config['probe_identity'],create=False)
        public=base64.b64decode(identity.public_identity,validate=True)
        if digest(public)!=PROBE_IDENTITY_SHA256:
            fail('operator_probe_identity_binding')
        credentials=load(read_private(self.config['mesh_profile']))
        leaf=x509.load_pem_x509_certificate(credentials['certificate'].encode())
        if leaf.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)!=public[32:]:
            fail('operator_probe_profile_binding')
        config=directory/'mux.json'
        write_private(config,canonical(dict(mode='public',seconds=0,port=0)))
        environment=dict(PATH=os.environ.get('PATH','/usr/bin:/bin'),HOME=str(directory),FC_REHEARSAL_TARGET_IPV4=self.target)
        cache=directory/'bootstrap.json'
        prepared=command([str(self.probe),'-family-config',self.config['mesh_profile'],'-broker-url','https://'+self.target+':18444',
            '-bootstrap-cache',str(cache),'-bootstrap-refresh','-duration','180s'],timeout=200,env=environment).stdout
        if not any(load(line).get('event')=='bootstrap_cache_stored' for line in prepared.splitlines() if line.startswith(b'{')):
            fail('operator_mesh_directory_unconfirmed')
        raw=command([str(self.probe),'-family-config',self.config['mesh_profile'],'-broker-url','https://127.0.0.1:1',
            '-bootstrap-cache',str(cache),'-mux-config',str(config),'-duration','180s'],timeout=200,env=environment).stdout
        return mesh_result(raw)


def run(harness, authority, *, now=time.time):
    challenge=harness.challenge
    if not now()<challenge['expires_at']:
        fail('operator_challenge_expired')
    roles={role:{step:'NOT_RUN' for step in steps} for role,steps in STEPS.items()}
    cleanup='PASS'
    with tempfile.TemporaryDirectory(prefix='fc-rehearsal-operator-') as temporary:
        directory=Path(temporary)
        try:
            for role in STEPS:
                roles[role]=getattr(harness,role)(directory)
        except Exception:
            cleanup='FAIL'
        finally:
            for path in directory.iterdir():
                if path.is_file() and not path.is_symlink():
                    remove_private(path)
    issued=int(now())
    body={name:challenge[name] for name in ('instance_id','bundle_id','operation_id','verification_nonce','ipv4','local_health_sha256')}
    body.update(schema=1,scope=SCOPE,roles=roles,issued_at=issued,expires_at=min(issued+300,challenge['expires_at']),
        external_evidence_sha256=digest(canonical(roles)),cleanup=cleanup,signer=digest(bytes.fromhex(public_hex(authority.public_key()))))
    return sign(body,authority,now=issued)
