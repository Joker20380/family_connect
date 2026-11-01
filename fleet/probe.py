"""Standalone read-only host probe transported over authenticated SSH."""

import ipaddress
import json
import os
from pathlib import Path
import platform
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


def collect(request):
    if set(request) != {'ipv4', 'ipv6', 'ports'} or type(request['ports']) is not list:
        raise ValueError('probe_request')
    ipaddress.IPv4Address(request['ipv4'])
    if request['ipv6'] is not None:
        ipaddress.IPv6Address(request['ipv6'])
    if not request['ports'] or len(request['ports'])>32 or any(type(port) is not int or not 1<=port<=65535 for port in request['ports']):
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
    return dict(os=os_release.get('ID','').strip('"'),version=os_release.get('VERSION_ID','').strip('"'),
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


if __name__=='__main__':
    try:
        request=json.loads(sys.stdin.buffer.read(4096))
        print(json.dumps(collect(request),sort_keys=True))
    except Exception:
        print('{"error":"probe_failed"}')
        raise SystemExit(1)
