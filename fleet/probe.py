"""Standalone read-only host probe transported over authenticated SSH."""

import ipaddress
import fcntl
import datetime
import json
import os
from pathlib import Path
import platform
import re
import shutil
import socket
import stat
import subprocess
import sys
import urllib.request


def command(argv, *, successful=False):
    try:
        result=subprocess.run(argv,capture_output=True,text=True,timeout=5)
        if successful:
            return result.returncode==0
        return result.stdout.strip() if result.returncode==0 else ''
    except (OSError,subprocess.TimeoutExpired):
        return False if successful else ''


def observation_json(path, *, owner, mode, limit):
    metadata=path.lstat()
    if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid!=owner or metadata.st_nlink!=1
            or stat.S_IMODE(metadata.st_mode)!=mode or metadata.st_size>limit):
        raise ValueError('observation_file_boundary')
    descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(descriptor,'rb') as source:
        current=os.fstat(source.fileno())
        if (current.st_dev,current.st_ino,current.st_size,current.st_nlink)!=(metadata.st_dev,metadata.st_ino,metadata.st_size,1):
            raise ValueError('observation_file_changed')
        return json.loads(source.read(limit+1))


def ready_observation(config, directory, bundle_id, instance_id):
    try:
        metadata=observation_json(config/'metadata.json',owner=0,mode=0o644,limit=65536)
        if metadata['bundle_id']!=bundle_id or metadata['instance_id']!=instance_id:
            raise ValueError('observation_binding')
        ready=observation_json(directory/'ready.json',owner=directory.lstat().st_uid,mode=0o600,limit=8192)
        issued=int(datetime.datetime.fromisoformat(ready['issued_at']).timestamp())
        expires=int(datetime.datetime.fromisoformat(ready['expires_at']).timestamp())
        material_expiry=metadata['material_expires_at']
        if type(material_expiry) is not int or ready['version']!=1:
            raise ValueError('observation_schema')
        return dict(result='OBSERVED',issued_at=issued,expires_at=expires,material_expires_at=material_expiry,
                    exceeds_material_deadline=expires>material_expiry)
    except FileNotFoundError:
        return dict(result='ABSENT')
    except (OSError,ValueError,KeyError,TypeError,OverflowError):
        return dict(result='UNAVAILABLE')


def network_observation():
    try:
        ruleset=json.loads(command(['nft','-j','list','ruleset']))
        chains=[entry['chain'] for entry in ruleset['nftables'] if 'chain' in entry]
        foreign_forward=[item for item in chains if item.get('hook')=='forward' and item.get('table')!='family_connect_rehearsal']
        route=json.loads(command(['ip','-j','route','get','9.9.9.9','from','10.203.217.2','iif','fcrh0']) or '[]')
        link=json.loads(command(['ip','-j','-s','link','show','dev','fcrh0']) or '[]')
        counters={}
        if len(link)==1:
            for direction in ('rx','tx'):
                values=link[0].get('stats64',{}).get(direction,{})
                counters[direction]={name:values[name] for name in ('bytes','packets','errors','dropped') if type(values.get(name)) is int}
        return dict(result='OBSERVED',foreign_forward_chains=len(foreign_forward),
            foreign_forward_drop_policies=sum(item.get('policy')=='drop' for item in foreign_forward),
            forwarded_route_present=len(route)==1 and route[0].get('type','unicast')=='unicast',interface_counters=counters,
            tcp_destination_tls13=command(['openssl','s_client','-connect','www.microsoft.com:443','-servername','www.microsoft.com',
                '-verify_hostname','www.microsoft.com','-verify_return_error','-tls1_3','-brief'],successful=True),
            forwarding=command(['sysctl','-n','net.ipv4.ip_forward'])=='1')
    except (ValueError,KeyError,TypeError):
        return dict(result='UNAVAILABLE')


def observations(bundle_id, instance_id):
    if (not re.fullmatch(r'gw-[0-9a-f]{32}', bundle_id)
            or not re.fullmatch(r'fleet-rehearsal-[a-z0-9-]+', instance_id)):
        raise ValueError('probe_diagnostic_binding')
    config = Path('/etc/family-connect/rehearsal')/bundle_id
    paths = {name: config/name for name in ('metadata.json','validated.json','awg.conf','tcp.json',
                                            'profile','profile/gateway.json','publisher.env','firewall.nft')}
    paths['configuration'] = config
    paths.update({'filesystem-root':Path('/'),'etc-parent':Path('/etc'),
                  'family-parent':config.parent.parent,'rehearsal-parent':config.parent})
    paths['run-directory'] = Path('/run/family-connect-rehearsal')/instance_id
    paths['ready-export'] = paths['run-directory']/'ready.json'
    files = {}
    for name, path in paths.items():
        try:
            info = path.lstat()
            files[name] = dict(present=True, mode=oct(stat.S_IMODE(info.st_mode)), uid=info.st_uid,
                               gid=info.st_gid, symlink=stat.S_ISLNK(info.st_mode), links=info.st_nlink)
            if name in ('filesystem-root','etc-parent','family-parent','rehearsal-parent',
                        'configuration','profile','profile/gateway.json'):
                try:
                    files[name]['extended_attribute_count'] = len(os.listxattr(path,follow_symlinks=False))
                    descriptor = os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
                    try:
                        flags = int.from_bytes(fcntl.ioctl(descriptor,0x80086601,bytes(8)),sys.byteorder)
                        files[name]['unexpected_inode_flags'] = flags & ~(0x80000 | (0x1000 if stat.S_ISDIR(info.st_mode) else 0))
                    finally:
                        os.close(descriptor)
                except OSError:
                    files[name]['extended_metadata'] = 'UNAVAILABLE'
        except FileNotFoundError:
            files[name] = dict(present=False)
    states = {}
    fields = ('LoadState','ActiveState','SubState','Result','ExecMainCode','ExecMainStatus','NRestarts')
    for role in ('prepare','awg','tcp','mesh','snapshot','monitoring'):
        raw = command(['systemctl','show','fc-rehearsal-'+role+'.service','--property='+','.join(fields)])
        values = dict(line.split('=',1) for line in raw.splitlines() if '=' in line)
        states[role] = {name:value for name,value in values.items() if name in fields
                        and re.fullmatch('[a-z0-9_-]{1,48}',value)}
    return dict(files=files, services=states, remote_writes=0,
                ready_lifetime=ready_observation(config,paths['run-directory'],bundle_id,instance_id),
                network=network_observation())


def collect(request):
    fields = {'ipv4', 'ipv6', 'ports'}
    if set(request) not in (fields, fields | {'bundle_id','instance_id'}) or type(request['ports']) is not list:
        raise ValueError('probe_request')
    if 'bundle_id' in request and (type(request['bundle_id']) is not str or type(request['instance_id']) is not str
            or not re.fullmatch(r'gw-[0-9a-f]{32}',request['bundle_id'])
            or not re.fullmatch(r'fleet-rehearsal-[a-z0-9-]+',request['instance_id'])):
        raise ValueError('probe_diagnostic_binding')
    ipaddress.IPv4Address(request['ipv4'])
    if request['ipv6'] is not None:
        ipaddress.IPv6Address(request['ipv6'])
    if len(request['ports'])>32 or any(type(port) is not int or not 1<=port<=65535 for port in request['ports']):
        raise ValueError('probe_ports')
    os_release=dict(line.split('=',1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
    memory=dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
    addresses=json.loads(command(['ip','-j','address','show']) or '[]')
    found={entry['local'] for interface in addresses for entry in interface.get('addr_info',[])}
    try:
        socket.getaddrinfo('example.com',443)
        resolver=True
    except OSError:
        resolver=False
    try:
        with urllib.request.urlopen('https://example.com/',timeout=10) as response:
            https=response.status==200
    except Exception:
        https=False
    listeners=command(['ss','-H','-lntu'])
    ports=set()
    for line in listeners.splitlines():
        fields=line.split()
        if len(fields)>=5 and fields[4].rsplit(':',1)[-1].isdigit():
            ports.add(int(fields[4].rsplit(':',1)[-1]))
    instance_file=Path('/var/lib/family-connect/instance.json')
    existing=None
    if instance_file.exists():
        existing=json.loads(instance_file.read_bytes()).get('instance_id','unknown')
    tun=Path('/dev/net/tun')
    report = dict(os=os_release.get('ID','').strip('"'),version=os_release.get('VERSION_ID','').strip('"'),
        architecture=platform.machine(),kernel=platform.release(),cpu=os.cpu_count() or 0,
        ram_mb=int(memory['MemTotal'].split()[0])//1024,disk_mb=shutil.disk_usage('/opt').free//1024//1024,
        time_sync=command(['timedatectl','show','--property=NTPSynchronized','--value'])=='yes',
        tun=tun.exists() and stat.S_ISCHR(tun.stat().st_mode),
        ipv4=request['ipv4'] if request['ipv4'] in found else None,
        ipv6=request['ipv6'] if request['ipv6'] is None or request['ipv6'] in found else 'missing',
        resolver=resolver,https=https,systemd=Path('/proc/1/comm').read_text().strip()=='systemd',
        firewall='iptables-nft' if 'nf_tables' in command(['iptables','--version']) else 'nftables' if shutil.which('nft') else 'unsupported',
        security='apparmor-supported' if command(['aa-status','--enabled'],successful=True) and Path('/sys/module/apparmor/parameters/enabled').exists() and Path('/sys/module/apparmor/parameters/enabled').read_text().strip()=='Y' else 'unsupported',
        ports_available=bool(listeners) and not set(request['ports']) & ports,
        pending_reboot=Path('/var/run/reboot-required').exists(),existing_instance=existing)
    if 'bundle_id' in request:
        report['diagnostics'] = observations(request['bundle_id'],request['instance_id'])
    return report


if __name__=='__main__':
    try:
        request=json.loads(sys.stdin.buffer.read(4096))
        print(json.dumps(collect(request),sort_keys=True))
    except Exception:
        print('{"error":"probe_failed"}')
        raise SystemExit(1)
