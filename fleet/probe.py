"""Standalone read-only host probe transported over authenticated SSH."""

import ipaddress
import fcntl
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
    return dict(files=files, services=states, remote_writes=0)


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
